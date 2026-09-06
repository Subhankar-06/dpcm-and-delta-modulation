"""
Delta Modulation (DM) and Adaptive Delta Modulation (ADM) Module.

Includes:
1. Linear Delta Modulation (LDM) with fixed step size Delta.
2. Mandatory Step Property Validator: checks that each output step is exactly +Delta or -Delta.
3. Adaptive Delta Modulation (ADM) using Song/Jayant adaptive step sizing.
4. Theoretical critical step size calculations for slope-overload avoidance.
5. Step size sweep engine for generating MSE versus step size curves.
"""

from typing import Dict, Tuple, Any, List
import numpy as np


def compute_critical_step_size(amplitude: float, frequency: float, sampling_rate: float) -> float:
    """
    Compute the theoretical critical step size Delta_crit to prevent slope overload:
    
    |dx/dt|_max = 2 * pi * f * A
    S_mod = Delta * fs
    Delta_crit = (2 * pi * f * A) / fs
    """
    return float((2.0 * np.pi * frequency * amplitude) / sampling_rate)


def validate_delta_modulator_steps(x_tilde: np.ndarray, delta: float, tolerance: float = 1e-9) -> Tuple[bool, float, str]:
    """
    MANDATORY VALIDATION:
    Inspect whether each delta-modulator output step changes by exactly +Delta or -Delta.
    
    Checks: | |x_tilde[n] - x_tilde[n-1]| - Delta | < tolerance for all n >= 1.
    
    Returns
    -------
    passed : bool
        True if all step transitions are exactly Delta within tolerance.
    max_deviation : float
        Maximum deviation observed from Delta.
    message : str
        Detailed diagnostic verification report string.
    """
    if len(x_tilde) < 2:
        return True, 0.0, "Validation bypassed: Signal length < 2."
    
    step_diffs = np.abs(np.diff(x_tilde))
    deviations = np.abs(step_diffs - delta)
    max_dev = float(np.max(deviations))
    passed = bool(max_dev <= tolerance)
    
    if passed:
        msg = f"PASS: All {len(step_diffs)} output steps change by exactly +/-Delta ({delta:.6f} V). Max dev = {max_dev:.2e} V."
    else:
        msg = f"FAIL: Step deviation detected! Max deviation = {max_dev:.6f} V exceeded tolerance {tolerance:.2e}."
        
    return passed, max_dev, msg


def simulate_linear_delta_modulation(
    signal: np.ndarray,
    sampling_rate: float,
    delta: float,
    initial_recon: float = 0.0
) -> Dict[str, Any]:
    """
    Simulate Linear Delta Modulation (LDM).
    
    Transmitter:
      x_hat[n] = x_tilde[n-1]
      e[n] = x[n] - x_hat[n]
      d[n] = +1 if e[n] >= 0 else -1   (1-bit quantization decision)
      eq[n] = d[n] * Delta
      x_tilde[n] = x_hat[n] + eq[n] = x_tilde[n-1] + eq[n]
      
    Receiver:
      x_tilde_rx[n] = x_tilde_rx[n-1] + d[n] * Delta
    """
    n_samples = len(signal)
    
    x_hat = np.zeros(n_samples, dtype=np.float64)
    e = np.zeros(n_samples, dtype=np.float64)
    bits = np.zeros(n_samples, dtype=np.int8)      # 1 for +Delta, 0 for -Delta
    d = np.zeros(n_samples, dtype=np.float64)     # +1.0 or -1.0
    eq = np.zeros(n_samples, dtype=np.float64)    # +Delta or -Delta
    x_tilde = np.zeros(n_samples, dtype=np.float64)
    
    prev_recon = initial_recon
    for n in range(n_samples):
        # 1. Prediction (ideal accumulator feedback)
        x_hat[n] = prev_recon
        
        # 2. Prediction error
        e[n] = signal[n] - x_hat[n]
        
        # 3. 1-bit quantization
        if e[n] >= 0.0:
            d[n] = 1.0
            bits[n] = 1
        else:
            d[n] = -1.0
            bits[n] = 0
            
        eq[n] = d[n] * delta
        
        # 4. Reconstruction
        x_tilde[n] = x_hat[n] + eq[n]
        prev_recon = x_tilde[n]
        
    # Receiver reconstruction (identical accumulator driven by 1-bit stream)
    x_tilde_rx = np.zeros(n_samples, dtype=np.float64)
    prev_rx = initial_recon
    for n in range(n_samples):
        x_tilde_rx[n] = prev_rx + (1.0 if bits[n] == 1 else -1.0) * delta
        prev_rx = x_tilde_rx[n]
        
    # Mandatory Step Assertion
    passed_validation, max_dev, val_msg = validate_delta_modulator_steps(x_tilde, delta)
    
    # Error metrics
    error = signal - x_tilde
    mse = float(np.mean(error ** 2))
    sig_power = float(np.mean(signal ** 2))
    sqnr_db = float(10.0 * np.log10(sig_power / max(mse, 1e-12)))
    
    return {
        "x": signal,
        "x_hat": x_hat,
        "e": e,
        "bits": bits,
        "d": d,
        "eq": eq,
        "x_tilde": x_tilde,
        "x_tilde_rx": x_tilde_rx,
        "delta": delta,
        "error": error,
        "mse": mse,
        "sqnr_db": sqnr_db,
        "validation_passed": passed_validation,
        "validation_max_dev": max_dev,
        "validation_message": val_msg
    }


def simulate_adaptive_delta_modulation(
    signal: np.ndarray,
    sampling_rate: float,
    delta_init: float,
    alpha: float = 1.5,
    beta: float = 0.67,
    delta_min: float = 1e-4,
    delta_max: float = 1.0,
    initial_recon: float = 0.0
) -> Dict[str, Any]:
    """
    Simulate Adaptive Delta Modulation (ADM) using Song/Jayant adaptation.
    
    Adapts step size Delta[n] dynamically:
    - If current bit d[n] == previous bit d[n-1]:
        Consecutive steps in same direction -> Slope Overload detected!
        Delta[n] = min(Delta[n-1] * alpha, Delta_max)
    - If current bit d[n] != previous bit d[n-1]:
        Alternating steps -> Granular hunting / flat region detected!
        Delta[n] = max(Delta[n-1] * beta, delta_min)
    """
    n_samples = len(signal)
    
    x_hat = np.zeros(n_samples, dtype=np.float64)
    e = np.zeros(n_samples, dtype=np.float64)
    bits = np.zeros(n_samples, dtype=np.int8)
    d = np.zeros(n_samples, dtype=np.float64)
    eq = np.zeros(n_samples, dtype=np.float64)
    x_tilde = np.zeros(n_samples, dtype=np.float64)
    step_sizes = np.zeros(n_samples, dtype=np.float64)
    
    prev_recon = initial_recon
    current_delta = delta_init
    prev_d = 1.0
    
    for n in range(n_samples):
        x_hat[n] = prev_recon
        e[n] = signal[n] - x_hat[n]
        
        # 1-bit quantization
        if e[n] >= 0.0:
            d[n] = 1.0
            bits[n] = 1
        else:
            d[n] = -1.0
            bits[n] = 0
            
        # ADM Step Adaptation Rule
        if n > 0:
            if d[n] == prev_d:
                # Same direction: expand step size
                current_delta = min(current_delta * alpha, delta_max)
            else:
                # Reversal: contract step size
                current_delta = max(current_delta * beta, delta_min)
        else:
            current_delta = delta_init
            
        step_sizes[n] = current_delta
        eq[n] = d[n] * current_delta
        x_tilde[n] = x_hat[n] + eq[n]
        
        prev_recon = x_tilde[n]
        prev_d = d[n]
        
    error = signal - x_tilde
    mse = float(np.mean(error ** 2))
    sig_power = float(np.mean(signal ** 2))
    sqnr_db = float(10.0 * np.log10(sig_power / max(mse, 1e-12)))
    
    return {
        "x": signal,
        "x_hat": x_hat,
        "e": e,
        "bits": bits,
        "d": d,
        "eq": eq,
        "x_tilde": x_tilde,
        "step_sizes": step_sizes,
        "error": error,
        "mse": mse,
        "sqnr_db": sqnr_db
    }


def sweep_step_size_mse(
    signal: np.ndarray,
    sampling_rate: float,
    delta_crit: float,
    num_points: int = 50,
    min_scale: float = 0.1,
    max_scale: float = 6.0
) -> Dict[str, Any]:
    """
    Perform step size parameter sweep to compute MSE vs Delta curve.
    
    Returns
    -------
    dict
        - 'deltas': array of step sizes
        - 'scales': array of delta / delta_crit
        - 'mse_values': array of corresponding MSEs
        - 'optimal_delta': step size achieving minimum MSE
        - 'optimal_scale': scale achieving minimum MSE
        - 'min_mse': minimum MSE value
    """
    scales = np.linspace(min_scale, max_scale, num_points)
    deltas = scales * delta_crit
    mse_values = np.zeros(num_points, dtype=np.float64)
    
    for i, delta in enumerate(deltas):
        res = simulate_linear_delta_modulation(signal, sampling_rate, delta)
        mse_values[i] = res["mse"]
        
    min_idx = int(np.argmin(mse_values))
    
    return {
        "deltas": deltas,
        "scales": scales,
        "mse_values": mse_values,
        "optimal_delta": float(deltas[min_idx]),
        "optimal_scale": float(scales[min_idx]),
        "min_mse": float(mse_values[min_idx]),
        "delta_crit": delta_crit
    }
