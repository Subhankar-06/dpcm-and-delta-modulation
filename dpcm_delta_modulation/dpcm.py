"""
First-Order Differential Pulse Code Modulation (DPCM) Module.

Explicitly isolates:
1. Prediction: x_hat[n] = a1 * x_tilde[n-1]
2. Quantization: eq[n] = Q(e[n])
3. Reconstruction: x_tilde[n] = x_hat[n] + eq[n]

Also implements baseline PCM quantization to compare prediction/quantization errors,
dynamic range reduction, variance reduction, and Prediction Gain.
"""

from typing import Dict, Tuple, Any
import numpy as np


def compute_optimal_a1(signal: np.ndarray) -> float:
    """
    Compute the optimal first-order predictor coefficient a1 from the 
    normalized autocorrelation at lag 1: a1 = R_xx(1) / R_xx(0).
    """
    r0 = np.mean(signal ** 2)
    if r0 < 1e-12:
        return 0.0
    r1 = np.mean(signal[1:] * signal[:-1])
    return float(r1 / r0)


def predict(x_tilde_prev: float, a1: float) -> float:
    """
    First-order linear predictor calculation.
    
    x_hat[n] = a1 * x_tilde[n-1]
    
    Parameters
    ----------
    x_tilde_prev : float
        Previous reconstructed sample (from transmitter feedback loop).
    a1 : float
        Predictor coefficient.
        
    Returns
    -------
    float
        Predicted sample x_hat[n].
    """
    return float(a1 * x_tilde_prev)


def quantize_prediction_error(e: float, bits: int, error_range: float) -> Tuple[float, int]:
    """
    Mid-rise uniform quantization of the prediction error e[n].
    
    Range: [-error_range, +error_range]
    Levels: L = 2^bits
    Step size: Delta = 2 * error_range / L
    
    Parameters
    ----------
    e : float
        Instantaneous prediction error sample.
    bits : int
        Quantizer resolution in bits.
    error_range : float
        Peak error dynamic range bound (error bounded in [-error_range, +error_range]).
        
    Returns
    -------
    eq : float
        Quantized error value.
    idx : int
        Integer quantization code index (0 to 2^bits - 1).
    """
    levels = 1 << bits  # 2^bits
    delta = (2.0 * error_range) / levels
    
    # Clip input within dynamic range to avoid unbounded overflow
    clipped_e = np.clip(e, -error_range, error_range)
    
    # Calculate mid-rise index
    idx = int(np.floor((clipped_e + error_range) / delta))
    if idx >= levels:
        idx = levels - 1
    if idx < 0:
        idx = 0
        
    # Mid-rise representation level: min + (idx + 0.5) * delta
    eq = -error_range + (idx + 0.5) * delta
    return float(eq), idx


def reconstruct(x_hat: float, eq: float) -> float:
    """
    Reconstruct sample by summing prediction and quantized error.
    
    x_tilde[n] = x_hat[n] + eq[n]
    
    Parameters
    ----------
    x_hat : float
        Predicted sample.
    eq : float
        Quantized error.
        
    Returns
    -------
    float
        Reconstructed sample x_tilde[n].
    """
    return float(x_hat + eq)


def simulate_dpcm(
    signal: np.ndarray,
    bits: int = 3,
    a1: float = 0.85,
    error_range: float = None
) -> Dict[str, Any]:
    """
    Execute full first-order DPCM transmitter and receiver simulation.
    
    Parameters
    ----------
    signal : np.ndarray
        Input sampled analog signal x[n].
    bits : int
        Quantizer resolution for error signal.
    a1 : float
        Predictor coefficient.
    error_range : float, optional
        Quantization dynamic range for prediction error. If None, estimated
        conservatively from peak signal amplitude and predictor coefficient.
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'x': Original signal
        - 'x_hat': Predicted samples
        - 'e': Unquantized prediction error
        - 'eq': Quantized prediction error
        - 'indices': Quantizer code indices
        - 'x_tilde_tx': Transmitter reconstructed signal
        - 'x_tilde_rx': Receiver reconstructed signal
        - 'delta_e': Quantizer step size
        - 'reconstruction_error': x - x_tilde
        - 'mse': Mean squared reconstruction error
        - 'sqnr_db': Signal-to-quantization-noise ratio in dB
        - 'var_x': Signal variance
        - 'var_e': Prediction error variance
        - 'prediction_gain_db': 10 * log10(var_x / var_e)
    """
    n_samples = len(signal)
    
    # Determine appropriate error range if not specified
    if error_range is None:
        peak_amp = np.max(np.abs(signal))
        # Conservatively size dynamic range: e = x[n] - a1 * x[n-1]
        # Max theoretical error is ~ (1 + a1) * peak_amp, but typical error is much smaller:
        error_range = max(0.5, float((1.0 + abs(a1)) * peak_amp * 0.45))
        
    delta_e = (2.0 * error_range) / (1 << bits)
    
    x_hat = np.zeros(n_samples, dtype=np.float64)
    e = np.zeros(n_samples, dtype=np.float64)
    eq = np.zeros(n_samples, dtype=np.float64)
    indices = np.zeros(n_samples, dtype=np.int32)
    x_tilde_tx = np.zeros(n_samples, dtype=np.float64)
    
    # --- Transmitter Simulation Loop ---
    prev_tx_recon = 0.0
    for n in range(n_samples):
        # 1. Prediction step
        x_hat[n] = predict(prev_tx_recon, a1)
        
        # 2. Prediction error
        e[n] = signal[n] - x_hat[n]
        
        # 3. Error quantization
        eq_val, idx = quantize_prediction_error(e[n], bits, error_range)
        eq[n] = eq_val
        indices[n] = idx
        
        # 4. Reconstruction in transmitter feedback loop
        x_tilde_tx[n] = reconstruct(x_hat[n], eq[n])
        prev_tx_recon = x_tilde_tx[n]
        
    # --- Receiver Simulation Loop ---
    # The receiver receives the stream of quantized error indices (or eq)
    x_tilde_rx = np.zeros(n_samples, dtype=np.float64)
    x_hat_rx = np.zeros(n_samples, dtype=np.float64)
    prev_rx_recon = 0.0
    for n in range(n_samples):
        # Predict based on prior receiver reconstructed sample
        x_hat_rx[n] = predict(prev_rx_recon, a1)
        # Reconstruct exactly as transmitter does
        x_tilde_rx[n] = reconstruct(x_hat_rx[n], eq[n])
        prev_rx_recon = x_tilde_rx[n]
        
    # --- Metrics Computation ---
    recon_error = signal - x_tilde_tx
    mse = float(np.mean(recon_error ** 2))
    var_x = float(np.var(signal))
    var_e = float(np.var(e))
    prediction_gain_db = float(10.0 * np.log10(max(var_x, 1e-12) / max(var_e, 1e-12)))
    
    sig_power = float(np.mean(signal ** 2))
    sqnr_db = float(10.0 * np.log10(sig_power / max(mse, 1e-12)))
    
    return {
        "x": signal,
        "x_hat": x_hat,
        "e": e,
        "eq": eq,
        "indices": indices,
        "x_tilde_tx": x_tilde_tx,
        "x_tilde_rx": x_tilde_rx,
        "delta_e": delta_e,
        "error_range": error_range,
        "reconstruction_error": recon_error,
        "mse": mse,
        "sqnr_db": sqnr_db,
        "var_x": var_x,
        "var_e": var_e,
        "prediction_gain_db": prediction_gain_db,
        "a1": a1,
        "bits": bits
    }


def simulate_pcm(signal: np.ndarray, bits: int, signal_range: float = 1.0) -> Dict[str, Any]:
    """
    Direct PCM quantization of input signal for baseline comparison.
    
    Uses standard mid-rise uniform quantizer across [-signal_range, +signal_range].
    """
    levels = 1 << bits
    delta = (2.0 * signal_range) / levels
    
    clipped = np.clip(signal, -signal_range, signal_range)
    indices = np.floor((clipped + signal_range) / delta).astype(np.int32)
    indices = np.clip(indices, 0, levels - 1)
    
    # Mid-rise representation level
    x_q = -signal_range + (indices + 0.5) * delta
    error = signal - x_q
    mse = float(np.mean(error ** 2))
    
    sig_power = float(np.mean(signal ** 2))
    sqnr_db = float(10.0 * np.log10(sig_power / max(mse, 1e-12)))
    
    return {
        "x": signal,
        "x_q": x_q,
        "error": error,
        "indices": indices,
        "delta": delta,
        "mse": mse,
        "sqnr_db": sqnr_db,
        "var_error": float(np.var(error)),
        "bits": bits
    }
