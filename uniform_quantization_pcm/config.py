"""
Configuration Module for Uniform Quantization and PCM Laboratory Simulation.

Defines signal parameters, bit depths, tolerance levels, and file paths.
"""

from dataclasses import dataclass
import os

@dataclass
class SignalConfig:
    """Configuration settings for the input sinusoidal signal."""
    amplitude: float = 1.0          # Normalized peak amplitude (V)
    frequency: float = 1.0          # Signal frequency (Hz)
    sampling_rate: float = 1000.0   # Sampling frequency (Hz)
    num_samples: int = 2000         # Total number of discrete time samples

# Experiment Bit Depths to evaluate
BIT_DEPTHS = [2, 3, 4, 6, 8]

# Tolerance for automated agreement check with theoretical SQNR (dB)
# A 1.0 dB tolerance accounts for slight noise-signal correlation at low bit depths (n=2,3)
SQNR_TOLERANCE_DB = 1.0


# Directories and Output Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
RESULTS_CSV = os.path.join(RESULTS_DIR, "results.csv")

def ensure_directories_exist():
    """Ensure output directories for results and figures exist."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)
