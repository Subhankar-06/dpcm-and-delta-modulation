"""
Configuration Module for DPCM and Delta Modulation Laboratory Suite.

Defines signal parameters, predictor configurations, step sizes for delta modulation,
ADM adaptation parameters, and output paths for results and plots.
"""

from dataclasses import dataclass
import os
import numpy as np


@dataclass
class SignalConfig:
    """Configuration settings for test input signals."""
    amplitude: float = 1.0          # Peak amplitude (V)
    frequency: float = 1.0          # Base signal frequency (Hz)
    sampling_rate: float = 1000.0   # Sampling rate (Hz)
    duration: float = 2.0           # Duration in seconds
    
    @property
    def num_samples(self) -> int:
        return int(self.sampling_rate * self.duration)
    
    @property
    def time_step(self) -> float:
        return 1.0 / self.sampling_rate
    
    @property
    def max_slope(self) -> float:
        """Maximum slope of sinusoidal signal: |dx/dt|_max = 2 * pi * f * A."""
        return 2.0 * np.pi * self.frequency * self.amplitude


@dataclass
class DPCMConfig:
    """Configuration settings for first-order DPCM predictor."""
    predictor_coeff: float = 0.85   # First-order predictor coefficient a1
    quantizer_bits: int = 3         # Quantizer bit depth for prediction error e[n]
    auto_correlation_coeff: bool = False  # If True, compute optimal a1 = R_xx(1)/R_xx(0)


@dataclass
class DeltaModulationConfig:
    """Configuration settings for Delta Modulation and Adaptive Delta Modulation."""
    # Critical step size for slope overload avoidance: Delta_crit = (2*pi*f*A) / fs
    # Small step: Delta < Delta_crit (severe slope overload)
    # Moderate step: Delta ~ Delta_crit to 1.5 * Delta_crit (balanced/optimal)
    # Large step: Delta >> Delta_crit (granular noise dominated)
    step_size_scale_small: float = 0.30      # Factor relative to Delta_crit
    step_size_scale_moderate: float = 1.25   # Factor relative to Delta_crit
    step_size_scale_large: float = 5.00      # Factor relative to Delta_crit

    # ADM (Adaptive Delta Modulation) Parameters: Song / Jayant adaptation
    adm_alpha: float = 1.50         # Multiplier when consecutive bits have same sign (expansion)
    adm_beta: float = 0.67          # Multiplier when consecutive bits have alternate signs (contraction)
    adm_delta_min_ratio: float = 0.10  # Delta_min = Delta_crit * ratio
    adm_delta_max_ratio: float = 8.00  # Delta_max = Delta_crit * ratio


# Project Directories and Output Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
RESULTS_CSV = os.path.join(RESULTS_DIR, "metrics.csv")


def ensure_directories_exist():
    """Ensure output directories for results and figures exist."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)
