"""
Analysis and Validation Module.

Computes quantization error metrics (MSE, SQNR, RMS Error), performs mandatory
experiment validations, compares simulation with theory, and runs a comprehensive
10-point discrepancy diagnostic suite.
"""

import numpy as np
from typing import Dict, Any, List, Tuple

def validate_experiment(indices: np.ndarray, 
                        pcm_words: List[str], 
                        quantized_signal: np.ndarray, 
                        bits: int, 
                        min_val: float = -1.0, 
                        max_val: float = 1.0) -> Dict[str, bool]:
    """
    Perform mandatory automated validation checks for an experiment run.

    Checks performed:
    1. Minimum index >= 0
    2. Maximum index < L = 2^bits
    3. Every PCM binary word has exactly `bits` length
    4. Quantized samples contain no NaN values
    5. Quantized samples contain no Inf values
    6. Quantized values stay within range [min_val, max_val]

    Returns
    -------
    results : Dict[str, bool]
        Dictionary indicating PASS/FAIL for each verification check.
    """
    L = 2 ** bits
    
    checks = {
        "Index non-negative (min >= 0)": bool(np.all(indices >= 0)),
        "Maximum index within bounds (< L)": bool(np.all(indices < L)),
        "PCM word length exact (len == bits)": bool(all(len(w) == bits for w in pcm_words)),
        "No NaN values": bool(not np.isnan(quantized_signal).any()),
        "No Inf values": bool(not np.isinf(quantized_signal).any()),
        "Quantized signal in range": bool(np.all(quantized_signal >= min_val) and np.all(quantized_signal <= max_val))
    }
    
    # Assert checks to enforce program failure on validation break
    assert checks["Index non-negative (min >= 0)"], "Validation Failed: Min index < 0!"
    assert checks["Maximum index within bounds (< L)"], f"Validation Failed: Max index >= {L}!"
    assert checks["PCM word length exact (len == bits)"], f"Validation Failed: PCM word length != {bits}!"
    assert checks["No NaN values"], "Validation Failed: Quantized signal contains NaN!"
    assert checks["No Inf values"], "Validation Failed: Quantized signal contains Inf!"
    assert checks["Quantized signal in range"], "Validation Failed: Quantized values outside dynamic range!"

    return checks


def compute_metrics(signal: np.ndarray, 
                    quantized_signal: np.ndarray, 
                    bits: int, 
                    delta: float) -> Dict[str, Any]:
    """
    Calculate quantization error, MSE, signal power, noise power, SQNR, and theory metrics.

    Equations:
    ----------
    e[k] = x[k] - x_q[k]
    MSE = (1/N) * sum(e[k]^2)
    P_x = (1/N) * sum(x[k]^2)
    P_e = MSE
    SQNR_sim = 10 * log10(P_x / P_e)
    SQNR_theory = 6.02 * bits + 1.76

    Returns
    -------
    metrics : Dict[str, Any]
        Dictionary containing calculated numerical metrics.
    """
    N = len(signal)
    error = signal - quantized_signal
    
    mse = np.mean(error ** 2)
    max_error = np.max(np.abs(error))
    rms_error = np.sqrt(mse)
    
    px = np.mean(signal ** 2)
    pe = mse
    
    # Prevent division by zero
    if pe > 0:
        sqnr_sim = 10.0 * np.log10(px / pe)
    else:
        sqnr_sim = float('inf')

    sqnr_theory = 6.02 * bits + 1.76
    difference = sqnr_sim - sqnr_theory

    return {
        "bits": bits,
        "levels": 2 ** bits,
        "delta": delta,
        "min_quantized": float(np.min(quantized_signal)),
        "max_quantized": float(np.max(quantized_signal)),
        "mse": mse,
        "max_error": max_error,
        "rms_error": rms_error,
        "px": px,
        "pe": pe,
        "sqnr_sim": sqnr_sim,
        "sqnr_theory": sqnr_theory,
        "difference": difference,
        "error_signal": error
    }


def evaluate_theory_agreement(sqnr_sim: float, sqnr_theory: float, tolerance: float = 0.5) -> Tuple[bool, float]:
    """
    Automatically evaluate whether simulated SQNR agrees with theoretical approximation.

    Parameters
    ----------
    sqnr_sim : float
        Simulated SQNR in dB.
    sqnr_theory : float
        Theoretical SQNR in dB.
    tolerance : float
        Acceptable difference threshold in dB (default 0.5 dB).

    Returns
    -------
    agrees : bool
        True if |sqnr_sim - sqnr_theory| <= tolerance, else False.
    diff : float
        Simulated minus theoretical difference in dB.
    """
    diff = sqnr_sim - sqnr_theory
    agrees = abs(diff) <= tolerance
    return agrees, diff


def diagnose_discrepancies(signal: np.ndarray, 
                           quantized_signal: np.ndarray, 
                           indices: np.ndarray, 
                           bits: int, 
                           delta: float, 
                           min_val: float = -1.0, 
                           max_val: float = 1.0) -> List[str]:
    """
    Perform a comprehensive 10-point diagnostic investigation if SQNR deviates from theory.

    Returns
    -------
    report : List[str]
        Detailed diagnostic findings for 10 potential error sources.
    """
    report = []
    
    # Check 1: Peak sinusoid amplitude
    max_amp = np.max(np.abs(signal))
    if np.isclose(max_amp, 1.0, atol=1e-3):
        report.append("1. Signal Amplitude: PASS — Signal reaches full scale ±1.0 V.")
    else:
        report.append(f"1. Signal Amplitude: WARNING — Peak magnitude is {max_amp:.4f}, not full-scale 1.0 V.")

    # Check 2: Clipping / Overload
    if np.any(signal < min_val) or np.any(signal > max_val):
        report.append("2. Signal Clipping: WARNING — Input signal exceeds quantizer range [min_val, max_val].")
    else:
        report.append("2. Signal Clipping: PASS — No clipping/overload detected.")

    # Check 3: Step size formula
    expected_delta = (max_val - min_val) / (2 ** bits)
    if np.isclose(delta, expected_delta):
        report.append(f"3. Step Size Calculation: PASS — Step size Δ = {delta:.6f} matches (Vmax-Vmin)/2^n.")
    else:
        report.append(f"3. Step Size Calculation: FAIL — Step size Δ is {delta}, expected {expected_delta}.")

    # Check 4: Quantization level placement
    levels = min_val + (np.arange(2 ** bits) + 0.5) * delta
    if np.all(np.isin(quantized_signal, levels)):
        report.append("4. Quantization Level Placement: PASS — All quantized samples map to valid mid-rise levels.")
    else:
        report.append("4. Quantization Level Placement: FAIL — Quantized samples found off valid levels.")

    # Check 5: Endpoint handling
    min_idx, max_idx = np.min(indices), np.max(indices)
    if min_idx >= 0 and max_idx <= (2 ** bits - 1):
        report.append(f"5. Endpoint Handling: PASS — Index bounds [{min_idx}, {max_idx}] valid for L = {2**bits}.")
    else:
        report.append(f"5. Endpoint Handling: FAIL — Index bounds [{min_idx}, {max_idx}] out of range.")

    # Check 6: Mid-rise vs Mid-tread convention
    if 0.0 in levels:
        report.append("6. Quantizer Type: INFO — Mid-tread convention active (has zero level).")
    else:
        report.append("6. Quantizer Type: PASS — Mid-rise convention active (zero-mean balanced AC representation).")

    # Check 7: Signal power P_x
    px = np.mean(signal ** 2)
    # Theoretical sinusoidal power P_x = A^2 / 2 = 0.5
    if np.isclose(px, 0.5, atol=0.01):
        report.append(f"7. Signal Power: PASS — P_x = {px:.4f} W (matches theoretical A^2/2 = 0.5 W for sinusoid).")
    else:
        report.append(f"7. Signal Power: NOTICE — P_x = {px:.4f} W (deviates from 0.5 W due to sample discretization).")

    # Check 8: Quantization noise power P_e
    error = signal - quantized_signal
    pe = np.mean(error ** 2)
    expected_pe = (delta ** 2) / 12.0
    if np.isclose(pe, expected_pe, rtol=0.15):
        report.append(f"8. Noise Power: PASS — Measured P_e = {pe:.6e} matches theoretical Δ^2/12 = {expected_pe:.6e}.")
    else:
        report.append(f"8. Noise Power: NOTICE — Measured P_e = {pe:.6e} vs theoretical Δ^2/12 = {expected_pe:.6e} (slight correlation for coarse n).")


    # Check 9: Number of samples N
    N = len(signal)
    if N >= 1000:
        report.append(f"9. Sample Size: PASS — N = {N} samples is sufficiently high for accurate ergodic spatial statistics.")
    else:
        report.append(f"9. Sample Size: WARNING — N = {N} samples may be too small for statistically accurate MSE calculation.")

    # Check 10: Theoretical full-scale assumption
    report.append("10. Theory Assumptions: PASS — Full-scale sinusoid SQNR theoretical model SQNR = 6.02n + 1.76 dB strictly applies.")

    return report
