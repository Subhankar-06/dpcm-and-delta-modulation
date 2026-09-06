"""
Automated Test Suite for Uniform Quantizer and PCM Encoder.

Uses Python's built-in unittest framework to verify index ranges, PCM binary word lengths,
quantized output bounds, step-size resolution scaling, and SQNR growth.
"""

import sys
import os
import unittest
import numpy as np

# Ensure parent directory is in Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import SignalConfig
from quantizer import generate_sinusoid, quantize_uniform
from pcm import encode_pcm, decode_pcm
from analysis import compute_metrics, validate_experiment

class TestUniformQuantizerAndPCM(unittest.TestCase):
    """Unit test suite for uniform quantizer and PCM encoding engine."""

    def setUp(self):
        """Set up standard sinusoidal signal for tests."""
        self.config = SignalConfig(amplitude=1.0, frequency=1.0, sampling_rate=1000.0, num_samples=2000)
        self.t, self.signal = generate_sinusoid(self.config)

    def test_index_range(self):
        """Verify integer quantization indices satisfy 0 <= index < L = 2^bits for all bit depths."""
        for bits in [2, 3, 4, 6, 8]:
            L = 2 ** bits
            quantized_signal, indices, delta, levels = quantize_uniform(self.signal, bits)
            self.assertTrue(np.all(indices >= 0), f"Index below 0 for {bits} bits")
            self.assertTrue(np.all(indices < L), f"Index >= L ({L}) for {bits} bits")
            self.assertEqual(np.min(indices), 0, f"Min index should reach 0 for full scale sinusoid")
            self.assertEqual(np.max(indices), L - 1, f"Max index should reach L-1 ({L-1})")

    def test_pcm_word_length(self):
        """Verify every PCM binary word is exactly `bits` long."""
        for bits in [2, 3, 4, 6, 8]:
            _, indices, _, _ = quantize_uniform(self.signal, bits)
            pcm_words = encode_pcm(indices, bits)
            self.assertEqual(len(pcm_words), len(indices))
            for word in pcm_words:
                self.assertEqual(len(word), bits, f"PCM word '{word}' length != {bits}")

    def test_quantized_range_and_validity(self):
        """Verify quantized signal samples are non-NaN, non-Inf, and within [-1.0, 1.0]."""
        for bits in [2, 3, 4, 6, 8]:
            quantized_signal, indices, delta, levels = quantize_uniform(self.signal, bits)
            self.assertFalse(np.isnan(quantized_signal).any(), f"NaN detected in {bits}-bit quantized signal")
            self.assertFalse(np.isinf(quantized_signal).any(), f"Inf detected in {bits}-bit quantized signal")
            self.assertTrue(np.all(quantized_signal >= -1.0), f"Quantized sample < -1.0 for {bits} bits")
            self.assertTrue(np.all(quantized_signal <= 1.0), f"Quantized sample > 1.0 for {bits} bits")

    def test_bit_depth_step_reduction(self):
        """Verify that increasing bit depth monotonically decreases quantization step size Δ."""
        bit_depths = [2, 3, 4, 6, 8]
        deltas = []
        for bits in bit_depths:
            _, _, delta, _ = quantize_uniform(self.signal, bits)
            deltas.append(delta)
        
        for i in range(len(deltas) - 1):
            self.assertGreater(deltas[i], deltas[i+1], f"Step size did not decrease from {bit_depths[i]} to {bit_depths[i+1]} bits")

    def test_sqnr_monotonic_increase(self):
        """Verify that simulated SQNR strictly increases as bit depth increases."""
        bit_depths = [2, 3, 4, 6, 8]
        sqnrs = []
        for bits in bit_depths:
            quantized_signal, _, delta, _ = quantize_uniform(self.signal, bits)
            metrics = compute_metrics(self.signal, quantized_signal, bits, delta)
            sqnrs.append(metrics["sqnr_sim"])

        for i in range(len(sqnrs) - 1):
            self.assertLess(sqnrs[i], sqnrs[i+1], f"SQNR did not increase from {bit_depths[i]} to {bit_depths[i+1]} bits")

    def test_pcm_encode_decode_roundtrip(self):
        """Verify PCM encoder and decoder reconstruct identical quantization indices."""
        for bits in [2, 3, 4, 6]:
            quantized_signal, indices, delta, _ = quantize_uniform(self.signal, bits)
            pcm_words = encode_pcm(indices, bits)
            recon_signal, recon_indices = decode_pcm(pcm_words, bits)
            np.testing.assert_array_equal(indices, recon_indices)
            np.testing.assert_allclose(quantized_signal, recon_signal, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
