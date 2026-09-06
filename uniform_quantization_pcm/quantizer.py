"""
Uniform Quantizer Module (First Principles Implementation).

This module implements a normalized sinusoidal signal generator and a reusable 
mid-rise uniform quantizer without using high-level quantization libraries.
"""

import numpy as np
from config import SignalConfig

def generate_sinusoid(config: SignalConfig = SignalConfig()):
    """
    Generate a smooth, normalized sinusoidal signal.

    Parameters
    ----------
    config : SignalConfig
        Dataclass containing signal amplitude, frequency, sampling rate, and length.

    Returns
    -------
    t : np.ndarray
        Time vector of length `num_samples`.
    signal : np.ndarray
        Normalized sinusoidal signal bounded strictly within [-1.0, 1.0].
    """
    # Time vector (seconds)
    t = np.linspace(0, (config.num_samples - 1) / config.sampling_rate, config.num_samples)
    
    # Raw sinusoid: x(t) = A * sin(2 * pi * f * t)
    raw_signal = config.amplitude * np.sin(2 * np.pi * config.frequency * t)
    
    # Explicit normalization to guarantee exact fit within [-1.0, +1.0]
    max_abs = np.max(np.abs(raw_signal))
    if max_abs > 0:
        signal = raw_signal / max_abs
    else:
        signal = raw_signal

    return t, signal


def quantize_uniform(signal: np.ndarray, bits: int, min_val: float = -1.0, max_val: float = 1.0):
    """
    Perform mid-rise uniform quantization on an input signal.

    Quantization Convention:
    ------------------------
    - Type: Mid-Rise Uniform Quantizer.
    - Partitioning: The continuous input range [min_val, max_val] of width 
      R = max_val - min_val is divided into L = 2^bits equal intervals of step size Δ = R / L.
    - Decision Boundaries: d_i = min_val + i * Δ, for i = 0, ..., L.
    - Quantization Levels (Representation values): 
      q_i = min_val + (i + 0.5) * Δ, for i = 0, ..., L - 1.
      Notice there is no representation level at exactly 0.0 (the origin rises across 0).
    - Endpoint Handling: Input samples x satisfy min_val <= x <= max_val. 
      The index is calculated via floor((x - min_val) / Δ) and clipped to [0, L - 1].
      This maps the upper boundary x = max_val to index L - 1.

    Parameters
    ----------
    signal : np.ndarray
        Continuous-amplitude input signal array.
    bits : int
        Quantization bit depth (number of bits per sample, e.g., 2, 3, 4, 6, 8).
    min_val : float, optional
        Lower boundary of quantizer dynamic range (default is -1.0).
    max_val : float, optional
        Upper boundary of quantizer dynamic range (default is 1.0).

    Returns
    -------
    quantized_signal : np.ndarray
        Array of discrete quantized values matching the input shape.
    indices : np.ndarray
        Array of integer quantization indices (0 <= index <= L - 1).
    delta : float
        Quantization step size Δ = (max_val - min_val) / L.
    levels : np.ndarray
        Array of representation quantization level values of length L.
    """
    # 1. Calculate number of quantization levels L = 2^bits
    L = 2 ** bits

    # 2. Calculate quantization step size Δ
    dynamic_range = max_val - min_val
    delta = dynamic_range / L

    # 3. Map input sample to quantization index i in [0, L - 1]
    raw_index = np.floor((signal - min_val) / delta).astype(int)
    indices = np.clip(raw_index, 0, L - 1)

    # 4. Generate quantized representation levels
    levels = min_val + (np.arange(L) + 0.5) * delta

    # 5. Generate quantized signal sample values
    quantized_signal = levels[indices]

    return quantized_signal, indices, delta, levels
