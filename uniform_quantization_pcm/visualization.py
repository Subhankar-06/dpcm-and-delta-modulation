"""
Visualization Module for Uniform Quantization and PCM Laboratory Simulation.

Generates 5 publication-quality Matplotlib figures to visualize signal quantization,
staircase characteristics, error waveforms, error histograms, and SQNR vs bit depth.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any
from config import FIGURES_DIR
from quantizer import quantize_uniform, generate_sinusoid, SignalConfig

# Apply clean professional plot styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14
})


def plot_waveform_comparison(t: np.ndarray, 
                             signal: np.ndarray, 
                             quantized_signal: np.ndarray, 
                             bits: int = 4, 
                             save_path: str = os.path.join(FIGURES_DIR, "waveform.png")):
    """
    Plot 1 — Original vs Quantized Signal (Staircase Effect).

    Demonstrates the continuous analog input waveform alongside the discrete-level
    quantized output waveform for a representative bit depth.
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    
    # Plot continuous signal
    ax.plot(t[:500], signal[:500], label="Original Continuous Signal x(t)", 
            color="#1f77b4", linewidth=2.0, alpha=0.85)
    
    # Plot quantized signal with step style to highlight staircase effect
    ax.plot(t[:500], quantized_signal[:500], label=f"Quantized Waveform x_q(t) ({bits} bits, L={2**bits})", 
            color="#ff7f0e", linewidth=1.8, drawstyle="steps-mid", linestyle="--")

    ax.set_title(f"Plot 1: Original vs Quantized Signal ({bits}-Bit Uniform Quantizer)", fontweight="bold")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude (Volts)")
    ax.set_ylim(-1.25, 1.25)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f" Saved Plot 1: {save_path}")


def plot_staircase_characteristic(bits: int = 3, 
                                  save_path: str = os.path.join(FIGURES_DIR, "staircase.png")):
    """
    Plot 2 — Staircase Quantizer Characteristic (x -> x_q Input-Output Transfer Curve).

    Shows uniform staircase mapping over range [-1, 1], representation levels, and step size Δ.
    """
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    
    # Fine grid of input amplitudes x in [-1, 1]
    x_fine = np.linspace(-1.0, 1.0, 2000)
    xq_fine, _, delta, levels = quantize_uniform(x_fine, bits=bits)
    
    # Plot ideal linear line x_q = x
    ax.plot(x_fine, x_fine, 'k--', label="Ideal Line (x_q = x)", alpha=0.5, linewidth=1.5)
    
    # Plot staircase transfer characteristic
    ax.plot(x_fine, xq_fine, color="#d62728", linewidth=2.2, drawstyle="steps-mid",
            label=f"Mid-Rise Quantizer Transfer Curve ({bits} bits, L={2**bits})")
    
    # Plot horizontal lines for representation levels
    for i, level in enumerate(levels):
        ax.axhline(level, color="blue", linestyle=":", alpha=0.3)

    # Highlight step size Δ on plot
    if len(levels) > 1:
        mid_idx = len(levels) // 2
        ax.annotate(f"Step size Δ = {delta:.4f} V", 
                    xy=(levels[mid_idx], levels[mid_idx]), 
                    xytext=(levels[mid_idx] - 0.4, levels[mid_idx] + 0.2),
                    arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                    fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1, alpha=0.7))

    ax.set_title(f"Plot 2: Staircase Input-Output Characteristic ({bits}-Bit Mid-Rise Quantizer)", fontweight="bold")
    ax.set_xlabel("Input Amplitude x (V)")
    ax.set_ylabel("Quantized Amplitude x_q (V)")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.legend(loc="upper left", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f" Saved Plot 2: {save_path}")


def plot_error_waveforms(t: np.ndarray, 
                         signal: np.ndarray, 
                         bit_depths: List[int] = [2, 3, 4, 8],
                         save_path: str = os.path.join(FIGURES_DIR, "error_waveform.png")):
    """
    Plot 3 — Quantization Error Waveforms e[k] = x[k] - x_q[k].

    Displays quantization error over time for multiple bit depths, proving visually
    that error magnitude decreases dramatically as resolution increases.
    """
    fig, axes = plt.subplots(len(bit_depths), 1, figsize=(10, 2.5 * len(bit_depths)), sharex=True, dpi=300)
    
    colors = ["#d62728", "#2ca02c", "#9467bd", "#1f77b4"]
    
    for idx, bits in enumerate(bit_depths):
        ax = axes[idx]
        quantized_signal, _, delta, _ = quantize_uniform(signal, bits)
        error = signal - quantized_signal
        
        ax.plot(t[:400], error[:400], color=colors[idx % len(colors)], linewidth=1.2,
                label=f"{bits} Bits (L={2**bits}, Δ={delta:.4f} V)")
        ax.axhline(delta/2, color="gray", linestyle=":", alpha=0.7, label=f"+Δ/2 ({delta/2:.4f})")
        ax.axhline(-delta/2, color="gray", linestyle=":", alpha=0.7, label=f"-Δ/2 ({-delta/2:.4f})")
        
        ax.set_ylabel("Error (V)")
        ax.legend(loc="upper right", frameon=True, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.5)

    axes[-1].set_xlabel("Time (seconds)")
    fig.suptitle("Plot 3: Quantization Error Waveforms e(t) = x(t) - x_q(t) Across Bit Depths", fontweight="bold", y=0.995)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f" Saved Plot 3: {save_path}")


def plot_error_histogram(signal: np.ndarray, 
                         bits: int = 4, 
                         save_path: str = os.path.join(FIGURES_DIR, "error_histogram.png")):
    """
    Plot 4 — Quantization Error Histogram & PDF Distribution.

    Compares experimental error distribution against the theoretical uniform distribution
    U[-Δ/2, +Δ/2].
    """
    quantized_signal, _, delta, _ = quantize_uniform(signal, bits)
    error = signal - quantized_signal
    
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    
    # Histogram of simulated error
    count, bins, ignored = ax.hist(error, bins=35, density=True, color="#2ca02c", alpha=0.6,
                                  edgecolor="black", label=f"Simulated Error Histogram ({bits} bits)")
    
    # Overlay theoretical uniform PDF: f_E(e) = 1/Δ for e in [-Δ/2, Δ/2]
    e_theoretical = np.linspace(-delta, delta, 1000)
    pdf_theoretical = np.where(np.abs(e_theoretical) <= delta/2, 1.0 / delta, 0.0)
    
    ax.plot(e_theoretical, pdf_theoretical, color="darkred", linewidth=2.5,
            label=f"Ideal Uniform PDF U[-Δ/2, +Δ/2] (Height = 1/Δ = {1/delta:.2f})")

    ax.set_title(f"Plot 4: Quantization Error Distribution ({bits}-Bit Quantizer)", fontweight="bold")
    ax.set_xlabel("Quantization Error e[k] (Volts)")
    ax.set_ylabel("Probability Density")
    ax.set_xlim(-delta * 0.8, delta * 0.8)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f" Saved Plot 4: {save_path}")


def plot_sqnr_vs_bits(all_metrics: List[Dict[str, Any]], 
                      save_path: str = os.path.join(FIGURES_DIR, "sqnr_vs_bits.png")):
    """
    Plot 5 — SQNR vs Bit Depth (6.02 dB/bit Slope).

    Compares simulated SQNR curve with the theoretical 6.02n + 1.76 dB straight line.
    """
    bits_list = [m["bits"] for m in all_metrics]
    sqnr_sim = [m["sqnr_sim"] for m in all_metrics]
    sqnr_theory = [m["sqnr_theory"] for m in all_metrics]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    
    # Plot theoretical linear relationship
    ax.plot(bits_list, sqnr_theory, 'r--o', label="Theoretical SQNR (6.02n + 1.76 dB)", 
            linewidth=2.0, markersize=7)
    
    # Plot experimental simulated SQNR
    ax.plot(bits_list, sqnr_sim, 'b-s', label="Simulated SQNR (10 log10(P_x / P_e))", 
            linewidth=2.0, markersize=8)

    # Annotate points with values and 6.02 dB slope
    for b, s_sim, s_th in zip(bits_list, sqnr_sim, sqnr_theory):
        ax.annotate(f"{s_sim:.2f} dB", xy=(b, s_sim), xytext=(b - 0.15, s_sim + 2.5),
                    fontsize=9, fontweight="bold", color="navy")

    ax.set_title("Plot 5: SQNR vs Bit Depth (Demonstrating ~6.02 dB/Bit Relationship)", fontweight="bold")
    ax.set_xlabel("Number of Quantization Bits (n)")
    ax.set_ylabel("Signal-to-Quantization-Noise Ratio (dB)")
    ax.set_xticks(bits_list)
    ax.set_ylim(0, max(sqnr_theory) + 10)
    ax.legend(loc="upper left", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f" Saved Plot 5: {save_path}")


def generate_all_plots(t: np.ndarray, signal: np.ndarray, all_metrics: List[Dict[str, Any]]):
    """Generate and save all 5 required Matplotlib laboratory figures."""
    # Plot 1: 4-bit waveform comparison
    quantized_4bit, _, _, _ = quantize_uniform(signal, bits=4)
    plot_waveform_comparison(t, signal, quantized_4bit, bits=4)
    
    # Plot 2: 3-bit staircase transfer characteristic
    plot_staircase_characteristic(bits=3)
    
    # Plot 3: Quantization error waveforms for 2, 3, 4, 8 bits
    plot_error_waveforms(t, signal, bit_depths=[2, 3, 4, 8])
    
    # Plot 4: Error histogram for 4 bits
    plot_error_histogram(signal, bits=4)
    
    # Plot 5: SQNR vs Bit Depth
    plot_sqnr_vs_bits(all_metrics)
