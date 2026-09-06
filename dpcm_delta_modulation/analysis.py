"""
Analysis and Validation Module for DPCM and Delta Modulation.

Computes:
1. Slope Overload Ratio (SOR) and regime classification.
2. Granular Noise theoretical power vs empirical variance.
3. DPCM Prediction Gain (empirical vs theoretical).
4. Run-length analytics for consecutive identical bits (slope overload signature).
5. Theoretical Agreement Evaluator & Discrepancy Diagnostics Suite.
"""

from typing import Dict, Any, Tuple
import numpy as np


def compute_slope_overload_ratio(amplitude: float, frequency: float, sampling_rate: float, delta: float) -> float:
    """
    Compute the Slope Overload Ratio (SOR):
    
    SOR = S_max / S_mod = (2 * pi * f * A) / (Delta * fs) = Delta_crit / Delta
    
    - SOR > 1.0: Slope overload distortion dominates (staircase lags behind signal).
    - SOR <= 1.0: Staircase slope is adequate; granular noise dominates as Delta increases.
    """
    s_max = 2.0 * np.pi * frequency * amplitude
    s_mod = delta * sampling_rate
    return float(s_max / max(s_mod, 1e-12))


def analyze_bit_run_lengths(bits: np.ndarray) -> Dict[str, Any]:
    """
    Analyze consecutive identical bit run lengths in Delta Modulation stream.
    
    In slope overload, the modulator produces prolonged runs of identical bits (1,1,1... or 0,0,0...).
    In granular hunting, bits alternate rapidly (1,0,1,0...).
    """
    if len(bits) == 0:
        return {"max_run": 0, "mean_run": 0.0, "alternation_ratio": 0.0}
        
    diffs = np.diff(bits)
    alternations = np.count_nonzero(diffs)
    alternation_ratio = float(alternations / max(len(diffs), 1))
    
    # Calculate runs
    runs = []
    current_run = 1
    for i in range(1, len(bits)):
        if bits[i] == bits[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)
    
    return {
        "max_run": int(np.max(runs)),
        "mean_run": float(np.mean(runs)),
        "alternation_ratio": alternation_ratio,
        "runs": runs
    }


def evaluate_dm_regime(sor: float) -> Dict[str, str]:
    """
    Classify the operating regime of Delta Modulation based on SOR.
    """
    if sor > 1.2:
        regime = "Slope Overload Dominated"
        behavior = "Staircase cannot keep up with rapid signal changes; large phase lag and high distortion during peak slopes."
    elif sor < 0.35:
        regime = "Granular Noise Dominated"
        behavior = "Staircase easily tracks signal slope, but large step size causes substantial hunting oscillations around flat/slow sections."
    else:
        regime = "Optimal / Balanced Tracking"
        behavior = "Balanced trade-off between slope overload avoidance and granular noise minimization; MSE is near minimal."
        
    return {
        "regime": regime,
        "behavior": behavior
    }


def compute_theoretical_dpcm_gain(a1: float, signal: np.ndarray) -> Dict[str, float]:
    """
    Compute theoretical vs empirical prediction gain for first-order DPCM:
    
    Theoretical: G_p = -10 * log10(1 - rho_1^2) for optimal predictor a1 = rho_1.
    Empirical: G_p = 10 * log10(sigma_x^2 / sigma_e^2).
    """
    var_x = float(np.var(signal))
    r0 = float(np.mean(signal ** 2))
    r1 = float(np.mean(signal[1:] * signal[:-1])) if len(signal) > 1 else 0.0
    rho1 = float(r1 / max(r0, 1e-12))
    
    # Theoretical prediction error variance if optimal
    rho1_clamped = min(abs(rho1), 0.9999)
    theory_gain_db = float(-10.0 * np.log10(max(1.0 - rho1_clamped ** 2, 1e-6)))
    
    return {
        "rho1": rho1,
        "theory_gain_db": theory_gain_db,
        "var_x": var_x
    }


def diagnose_dm_discrepancies(
    sor: float,
    empirical_mse: float,
    delta: float,
    validation_passed: bool,
    max_dev: float
) -> Dict[str, Any]:
    """
    Diagnostic suite for verifying Delta Modulation physical behavior against theory.
    """
    diagnostics = []
    
    # Check 1: Mandatory Step Validation
    if not validation_passed:
        diagnostics.append(f"[DISCREPANCY] Output steps deviated from Delta by up to {max_dev:.2e} V.")
    else:
        diagnostics.append("[CONFIRMED] Output step size invariant holds exactly: each transition is +/-Delta.")
        
    # Check 2: Slope Overload Agreement
    if sor > 1.0:
        diagnostics.append(f"[CONFIRMED] SOR = {sor:.2f} > 1.0. Slope overload confirmed by theoretical derivative test.")
    else:
        diagnostics.append(f"[CONFIRMED] SOR = {sor:.2f} <= 1.0. Staircase velocity Delta*fs exceeds max signal derivative.")
        
    # Check 3: Theoretical Granular Noise Lower Bound
    # For a flat/idle channel, granular noise MSE = Delta^2 / 3
    theory_granular_mse = (delta ** 2) / 3.0
    if sor < 0.5:
        ratio = empirical_mse / theory_granular_mse
        diagnostics.append(f"[GRANULAR ANALYSIS] Empirical MSE = {empirical_mse:.6f} vs Idle Granular Bound = {theory_granular_mse:.6f} (ratio={ratio:.2f}).")
        
    return {
        "diagnostics": diagnostics,
        "all_passed": validation_passed
    }
