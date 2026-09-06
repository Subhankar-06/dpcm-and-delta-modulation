"""
Automated Test Suite for DPCM and Delta Modulation Laboratory.

Uses Python's built-in unittest framework to verify:
1. DPCM predictor, quantizer, and reconstruction explicit separation.
2. Transmitter vs Receiver reconstruction equivalence (zero drift).
3. Prediction redundancy reduction: sigma_e^2 < sigma_x^2 and positive Prediction Gain.
4. MANDATORY DELTA MODULATOR VALIDATION: each output step changes by exactly +Delta or -Delta.
5. Delta modulation slope overload detection (SOR > 1) and granular noise behavior.
6. Input frequency variation effect on reconstruction MSE.
7. Adaptive Delta Modulation (ADM) dynamic step expansion and contraction.
8. MSE vs Step size sweep forming a U-shaped curve with an internal minimum.
"""

import os
import sys
import unittest
import numpy as np

# Ensure package directory is in Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dpcm import (predict, quantize_prediction_error, reconstruct,
                  simulate_dpcm, simulate_pcm, compute_optimal_a1)
from delta_modulation import (compute_critical_step_size,
                              simulate_linear_delta_modulation,
                              simulate_adaptive_delta_modulation,
                              validate_delta_modulator_steps,
                              sweep_step_size_mse)
from analysis import (compute_slope_overload_ratio,
                      analyze_bit_run_lengths,
                      evaluate_dm_regime,
                      diagnose_dm_discrepancies)


class TestDPCMAndDeltaModulation(unittest.TestCase):
    """Unit test suite for DPCM and Delta Modulation simulation."""

    def setUp(self):
        """Set up standard 1.0 Hz sinusoidal test signal sampled at 1000 Hz."""
        self.fs = 1000.0
        self.duration = 1.0
        self.n_samples = int(self.fs * self.duration)
        self.t = np.linspace(0, (self.n_samples - 1) / self.fs, self.n_samples)
        self.x = 1.0 * np.sin(2.0 * np.pi * 1.0 * self.t)

    def test_dpcm_explicit_separation(self):
        """Task 14: Verify explicit decoupling of prediction, quantization, and reconstruction."""
        prev_recon = 0.5
        a1 = 0.8
        
        # 1. Prediction step
        x_hat = predict(prev_recon, a1)
        self.assertAlmostEqual(x_hat, 0.4, places=6, msg="Prediction calculation mismatch")
        
        # 2. Error Quantization step
        target_error = 0.15
        eq, idx = quantize_prediction_error(target_error, bits=3, error_range=0.8)
        self.assertTrue(0 <= idx < 8, f"Quantizer index {idx} out of range [0, 7]")
        self.assertLess(abs(eq - target_error), 0.2, "Quantization error unexpectedly large")
        
        # 3. Reconstruction step
        x_tilde = reconstruct(x_hat, eq)
        self.assertAlmostEqual(x_tilde, x_hat + eq, places=6,
                               msg="Reconstruction must equal prediction + quantized error")

    def test_dpcm_tx_rx_equivalence(self):
        """Verify that receiver perfectly matches transmitter reconstruction without drift."""
        res = simulate_dpcm(self.x, bits=3, a1=0.85)
        tx = res["x_tilde_tx"]
        rx = res["x_tilde_rx"]
        max_diff = float(np.max(np.abs(tx - rx)))
        self.assertLess(max_diff, 1e-12, f"Tx and Rx diverged: max diff = {max_diff:.2e}")

    def test_dpcm_reduces_redundancy_and_improves_sqnr(self):
        """Task 14 & 15: Verify prediction reduces error variance and DPCM outperforms PCM."""
        dpcm_res = simulate_dpcm(self.x, bits=3, a1=0.85)
        pcm_res = simulate_pcm(self.x, bits=3, signal_range=1.0)
        
        # Prediction error variance should be substantially smaller than signal variance
        self.assertLess(dpcm_res["var_e"], dpcm_res["var_x"],
                        "Prediction failed to reduce signal variance!")
        self.assertGreater(dpcm_res["prediction_gain_db"], 0.0,
                           "Prediction gain Gp must be strictly positive")
        
        # DPCM achieves lower MSE and higher SQNR than PCM for same bit depth
        self.assertLess(dpcm_res["mse"], pcm_res["mse"],
                        "DPCM MSE should be smaller than PCM MSE")
        self.assertGreater(dpcm_res["sqnr_db"], pcm_res["sqnr_db"],
                           "DPCM SQNR should exceed PCM SQNR")

    def test_mandatory_delta_modulator_step_validation(self):
        """MANDATORY VALIDATION: Inspect whether each delta output step changes by exactly +Delta or -Delta."""
        delta_crit = compute_critical_step_size(1.0, 1.0, self.fs)
        
        for scale in [0.25, 1.0, 3.5]:
            delta = delta_crit * scale
            res = simulate_linear_delta_modulation(self.x, self.fs, delta)
            
            # Direct check using validator helper
            passed, max_dev, msg = validate_delta_modulator_steps(res["x_tilde"], delta)
            self.assertTrue(passed, f"Step validator failed for scale {scale}: {msg}")
            self.assertLess(max_dev, 1e-9, f"Max deviation {max_dev:.2e} exceeded tolerance")
            
            # Step differences in time
            diffs = np.abs(np.diff(res["x_tilde"]))
            self.assertTrue(np.allclose(diffs, delta, atol=1e-9),
                            f"Not all output steps equal +/-{delta}")

    def test_slope_overload_vs_granular_noise_regimes(self):
        """Task 16: Verify slope overload in small step size and granular noise in large step size."""
        delta_crit = compute_critical_step_size(1.0, 1.0, self.fs)
        
        # Small step size: Delta < Delta_crit (Slope Overload)
        small_delta = delta_crit * 0.25
        res_small = simulate_linear_delta_modulation(self.x, self.fs, small_delta)
        sor_small = compute_slope_overload_ratio(1.0, 1.0, self.fs, small_delta)
        run_small = analyze_bit_run_lengths(res_small["bits"])
        
        self.assertGreater(sor_small, 1.0, "Small step size must have SOR > 1.0")
        self.assertGreater(run_small["max_run"], 10,
                           "Slope overload must produce extended consecutive bit runs")
        
        # Large step size: Delta >> Delta_crit (Granular Noise)
        large_delta = delta_crit * 5.0
        res_large = simulate_linear_delta_modulation(self.x, self.fs, large_delta)
        sor_large = compute_slope_overload_ratio(1.0, 1.0, self.fs, large_delta)
        run_large = analyze_bit_run_lengths(res_large["bits"])
        
        self.assertLess(sor_large, 0.3, "Large step size must have low SOR < 0.3")
        self.assertGreater(run_large["alternation_ratio"], 0.3,
                           "Granular noise must have high bit alternation rate")

    def test_frequency_variation_slope_overload(self):
        """Task 17: Test slowly and rapidly varying inputs."""
        duration = 1.0
        t_slow = np.linspace(0, duration, int(self.fs * duration))
        x_slow = np.sin(2.0 * np.pi * 0.5 * t_slow)
        
        t_rapid = np.linspace(0, duration, int(self.fs * duration))
        x_rapid = np.sin(2.0 * np.pi * 5.0 * t_rapid)
        
        delta = compute_critical_step_size(1.0, 1.0, self.fs)
        
        res_slow = simulate_linear_delta_modulation(x_slow, self.fs, delta)
        res_rapid = simulate_linear_delta_modulation(x_rapid, self.fs, delta)
        
        # Rapid signal has 10x higher slope -> severe slope overload -> much higher MSE
        self.assertGreater(res_rapid["mse"], 5.0 * res_slow["mse"],
                           "Rapidly varying input must produce much higher MSE than slow input")

    def test_adaptive_delta_modulation(self):
        """Task 18: Verify ADM dynamic step adaptation."""
        delta_crit = compute_critical_step_size(1.0, 1.0, self.fs)
        adm_res = simulate_adaptive_delta_modulation(
            self.x, self.fs,
            delta_init=delta_crit * 0.5,
            alpha=1.5,
            beta=0.67,
            delta_min=delta_crit * 0.1,
            delta_max=delta_crit * 8.0
        )
        
        steps = adm_res["step_sizes"]
        self.assertGreater(np.max(steps), np.min(steps), "ADM step sizes must dynamically adapt")
        self.assertEqual(len(adm_res["x_tilde"]), len(self.x))
        self.assertLess(adm_res["mse"], 0.05, "ADM should maintain low MSE on normalized sinusoid")

    def test_mse_vs_step_size_sweep(self):
        """Verify MSE vs step size sweep forms a U-shaped curve with an internal minimum."""
        delta_crit = compute_critical_step_size(1.0, 1.0, self.fs)
        sweep = sweep_step_size_mse(self.x, self.fs, delta_crit, num_points=30)
        
        opt_idx = int(np.argmin(sweep["mse_values"]))
        self.assertTrue(0 < opt_idx < len(sweep["mse_values"]) - 1,
                        "Optimal delta must be an internal minimum forming a U-curve")


if __name__ == "__main__":
    unittest.main()
