"""
Visualization Suite for DPCM and Delta Modulation Laboratory.

Generates 6 publication-quality figures:
1. fig1_dpcm_prediction.png: Original vs Predicted Samples & Reconstruction.
2. fig2_dpcm_vs_pcm_errors.png: PCM vs DPCM Error Comparison & Error Distributions.
3. fig3_delta_staircase_regimes.png: Delta Staircase for Small, Moderate, and Large Step Sizes.
4. fig4_mse_vs_step_size.png: MSE vs Step Size Curve identifying Slope Overload & Granular Noise.
5. fig5_frequency_variation.png: Slowly vs Rapidly Varying Inputs under Delta Modulation.
6. fig6_adm_vs_ldm.png: Adaptive Delta Modulation (ADM) vs Linear Delta Modulation (LDM).
"""

import os
from typing import Dict, Any
import numpy as np
import matplotlib.pyplot as plt


# Set high quality plotting parameters
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8


def plot_dpcm_prediction(dpcm_res: Dict[str, Any], t: np.ndarray, save_path: str):
    """Figure 1: Original/Predicted samples, reconstructed samples, and prediction error."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    
    # Plot window: first 1.0 second or 500 samples
    n_plot = min(len(t), 400)
    t_sub = t[:n_plot]
    
    # Top subplot: Original, Predicted, and Reconstructed
    ax1.plot(t_sub, dpcm_res["x"][:n_plot], 'b-', lw=1.8, label=r'Original $x[n]$')
    ax1.plot(t_sub, dpcm_res["x_hat"][:n_plot], 'r--', lw=1.5, label=r'Predicted $\hat{x}[n] = a_1 \tilde{x}[n-1]$')
    ax1.step(t_sub, dpcm_res["x_tilde_tx"][:n_plot], 'g:', where='mid', lw=1.4, alpha=0.85, label=r'Reconstructed $\tilde{x}[n]$')
    ax1.set_title(f'First-Order DPCM Predictor & Reconstruction ($a_1 = {dpcm_res["a1"]:.2f}$, Bits = {dpcm_res["bits"]})', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Amplitude (V)', fontsize=10)
    ax1.legend(loc='upper right', framealpha=0.9)
    ax1.grid(True, alpha=0.3, ls='--')
    
    # Bottom subplot: Prediction Error vs Quantized Prediction Error
    ax2.plot(t_sub, dpcm_res["e"][:n_plot], color='#d95f02', lw=1.4, label=r'Prediction Error $e[n] = x[n] - \hat{x}[n]$')
    ax2.step(t_sub, dpcm_res["eq"][:n_plot], color='#7570b3', where='mid', lw=1.2, alpha=0.8, label=r'Quantized Error $e_q[n]$')
    ax2.axhline(0, color='gray', lw=0.7, ls=':')
    ax2.set_title(f'Prediction Error Signals (Variance $\sigma_e^2 = {dpcm_res["var_e"]:.5f}$, Gain $G_p = {dpcm_res["prediction_gain_db"]:.2f}$ dB)', fontsize=11)
    ax2.set_xlabel('Time (seconds)', fontsize=10)
    ax2.set_ylabel('Error Amplitude (V)', fontsize=10)
    ax2.legend(loc='upper right', framealpha=0.9)
    ax2.grid(True, alpha=0.3, ls='--')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_pcm_vs_dpcm(dpcm_res: Dict[str, Any], pcm_res: Dict[str, Any], t: np.ndarray, save_path: str):
    """Figure 2: Compare PCM and DPCM prediction/quantization errors and histograms."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 8))
    
    n_plot = min(len(t), 350)
    t_sub = t[:n_plot]
    
    # 1. PCM Quantization Error in time
    ax1.plot(t_sub, pcm_res["error"][:n_plot], color='#e41a1c', lw=1.3, label=r'PCM Error $e_{\mathrm{pcm}}[n]$')
    ax1.axhline(0, color='gray', lw=0.6, ls=':')
    ax1.set_title(f'PCM Quantization Error ({pcm_res["bits"]} bits, SQNR = {pcm_res["sqnr_db"]:.2f} dB)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Error (V)', fontsize=10)
    ax1.grid(True, alpha=0.3, ls='--')
    ax1.legend(loc='upper right')
    
    # 2. DPCM Reconstruction Error in time
    ax2.plot(t_sub, dpcm_res["reconstruction_error"][:n_plot], color='#377eb8', lw=1.3, label=r'DPCM Error $x[n] - \tilde{x}[n]$')
    ax2.axhline(0, color='gray', lw=0.6, ls=':')
    ax2.set_title(f'DPCM Reconstruction Error ({dpcm_res["bits"]} bits, SQNR = {dpcm_res["sqnr_db"]:.2f} dB)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Error (V)', fontsize=10)
    ax2.grid(True, alpha=0.3, ls='--')
    ax2.legend(loc='upper right')
    
    # 3. Dynamic Range Comparison: Signal x[n] vs DPCM Error e[n]
    ax3.plot(t_sub, dpcm_res["x"][:n_plot], 'k--', alpha=0.7, lw=1.2, label=r'Original Signal $x[n]$')
    ax3.plot(t_sub, dpcm_res["e"][:n_plot], color='#ff7f00', lw=1.4, label=r'DPCM Input $e[n]$ (Redundancy Reduced)')
    ax3.set_title(f'Dynamic Range Reduction: Max |x|={np.max(np.abs(dpcm_res["x"])):.2f} V vs Max |e|={np.max(np.abs(dpcm_res["e"])):.2f} V', fontsize=10)
    ax3.set_xlabel('Time (seconds)', fontsize=10)
    ax3.set_ylabel('Amplitude (V)', fontsize=10)
    ax3.grid(True, alpha=0.3, ls='--')
    ax3.legend(loc='upper right')
    
    # 4. Error Distributions / Histograms
    ax4.hist(pcm_res["error"], bins=30, alpha=0.6, color='#e41a1c', density=True, label=f'PCM Error (MSE = {pcm_res["mse"]:.5f})')
    ax4.hist(dpcm_res["reconstruction_error"], bins=30, alpha=0.6, color='#377eb8', density=True, label=f'DPCM Error (MSE = {dpcm_res["mse"]:.5f})')
    ax4.set_title(f'Error Distribution Comparison (SQNR Gain = +{dpcm_res["sqnr_db"] - pcm_res["sqnr_db"]:.2f} dB)', fontsize=10)
    ax4.set_xlabel('Error Magnitude (V)', fontsize=10)
    ax4.set_ylabel('Probability Density', fontsize=10)
    ax4.grid(True, alpha=0.3, ls='--')
    ax4.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_delta_staircase_regimes(
    dm_small: Dict[str, Any],
    dm_mod: Dict[str, Any],
    dm_large: Dict[str, Any],
    t: np.ndarray,
    delta_crit: float,
    save_path: str
):
    """Figure 3: Delta Modulation staircase across small, moderate, and large step sizes."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    
    n_plot = min(len(t), 400)
    t_sub = t[:n_plot]
    
    cases = [
        ("Small Step Size (Slope Overload Distortion)", dm_small, '#e41a1c',
         f"Delta = {dm_small['delta']:.4f} V < Delta_crit ({delta_crit:.4f} V) | SOR = {delta_crit/dm_small['delta']:.2f}"),
        ("Moderate Step Size (Optimal Balanced Tracking)", dm_mod, '#2ca02c',
         f"Delta = {dm_mod['delta']:.4f} V ~ Delta_crit ({delta_crit:.4f} V) | SOR = {delta_crit/dm_mod['delta']:.2f}"),
        ("Large Step Size (Granular Noise Dominated)", dm_large, '#1f77b4',
         f"Delta = {dm_large['delta']:.4f} V >> Delta_crit ({delta_crit:.4f} V) | SOR = {delta_crit/dm_large['delta']:.2f}")
    ]
    
    for ax, (title, dm, color, subtitle) in zip(axes, cases):
        ax.plot(t_sub, dm["x"][:n_plot], 'k--', lw=1.2, alpha=0.7, label='Input Signal $x[n]$')
        ax.step(t_sub, dm["x_tilde"][:n_plot], color=color, where='mid', lw=1.6, label=f'Delta Staircase (MSE = {dm["mse"]:.5f})')
        ax.set_title(f"{title}\n{subtitle}", fontsize=11, fontweight='bold')
        ax.set_ylabel('Amplitude (V)', fontsize=9)
        ax.grid(True, alpha=0.3, ls='--')
        ax.legend(loc='upper right', framealpha=0.9, fontsize=9)
        
    axes[-1].set_xlabel('Time (seconds)', fontsize=10)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_mse_vs_step_size(sweep_res: Dict[str, Any], save_path: str):
    """Figure 4: MSE versus Step Size Curve identifying Slope Overload and Granular Noise regions."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    deltas = sweep_res["deltas"]
    scales = sweep_res["scales"]
    mse_values = sweep_res["mse_values"]
    delta_crit = sweep_res["delta_crit"]
    opt_delta = sweep_res["optimal_delta"]
    min_mse = sweep_res["min_mse"]
    
    ax.plot(deltas, mse_values, 'b-o', markersize=4, lw=1.8, label=r'Total Reconstruction MSE $(\epsilon^2)$')
    
    # Mark critical step size
    ax.axvline(delta_crit, color='#e41a1c', linestyle='--', lw=1.4, label=r'Theoretical $\Delta_{\mathrm{crit}} = \frac{2\pi f A}{f_s}$')
    
    # Mark optimal empirical minimum
    ax.axvline(opt_delta, color='#2ca02c', linestyle='-.', lw=1.4, label=f'Optimal Empirical $\\Delta^* = {opt_delta:.4f}$ V')
    ax.plot(opt_delta, min_mse, 'go', markersize=8)
    
    # Annotate regions
    ax.axvspan(deltas[0], delta_crit, alpha=0.15, color='red', label='Slope-Overload Dominated Region')
    ax.axvspan(delta_crit * 2.0, deltas[-1], alpha=0.15, color='orange', label='Granular-Noise Dominated Region')
    
    ax.annotate('Minimum MSE\n(Optimal Trade-off)',
                xy=(opt_delta, min_mse),
                xytext=(opt_delta + 0.005, min_mse * 1.6),
                arrowprops=dict(facecolor='green', shrink=0.08, width=1.5, headwidth=8),
                fontsize=10, fontweight='bold', color='green')
    
    ax.set_title(r'Delta Modulation: Mean Squared Error (MSE) vs. Step Size $\Delta$', fontsize=13, fontweight='bold')
    ax.set_xlabel(r'Step Size $\Delta$ (Volts)', fontsize=11)
    ax.set_ylabel('Mean Squared Error (MSE)', fontsize=11)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, ls='--')
    ax.legend(loc='upper right', framealpha=0.9, fontsize=9)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_frequency_variation(
    dm_slow: Dict[str, Any],
    dm_rapid: Dict[str, Any],
    t_slow: np.ndarray,
    t_rapid: np.ndarray,
    f_slow: float,
    f_rapid: float,
    save_path: str
):
    """Figure 5: Testing slowly and rapidly varying inputs with fixed step size."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7))
    
    n_plot = 400
    
    # 1. Slowly varying input
    ax1.plot(t_slow[:n_plot], dm_slow["x"][:n_plot], 'k--', lw=1.2, alpha=0.7, label=f'Slow Input ($f = {f_slow}$ Hz)')
    ax1.step(t_slow[:n_plot], dm_slow["x_tilde"][:n_plot], 'g-', where='mid', lw=1.5, label=f'Delta Staircase (MSE = {dm_slow["mse"]:.5f})')
    ax1.set_title(f'Slowly Varying Input ($f = {f_slow}$ Hz): Slope Overload Avoided, Granular Hunting Visible', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Amplitude (V)', fontsize=10)
    ax1.grid(True, alpha=0.3, ls='--')
    ax1.legend(loc='upper right')
    
    # 2. Rapidly varying input
    ax2.plot(t_rapid[:n_plot], dm_rapid["x"][:n_plot], 'k--', lw=1.2, alpha=0.7, label=f'Rapid Input ($f = {f_rapid}$ Hz)')
    ax2.step(t_rapid[:n_plot], dm_rapid["x_tilde"][:n_plot], 'r-', where='mid', lw=1.5, label=f'Delta Staircase (MSE = {dm_rapid["mse"]:.5f})')
    ax2.set_title(f'Rapidly Varying Input ($f = {f_rapid}$ Hz): Severe Slope Overload (Staircase Lags Max Derivative)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Time (seconds)', fontsize=10)
    ax2.set_ylabel('Amplitude (V)', fontsize=10)
    ax2.grid(True, alpha=0.3, ls='--')
    ax2.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_adm_vs_ldm(
    ldm_res: Dict[str, Any],
    adm_res: Dict[str, Any],
    t: np.ndarray,
    save_path: str
):
    """Figure 6: Adaptive Delta Modulation (ADM) vs Linear Delta Modulation (LDM)."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    
    n_plot = min(len(t), 400)
    t_sub = t[:n_plot]
    
    # 1. Staircase comparison
    ax1.plot(t_sub, ldm_res["x"][:n_plot], 'k--', lw=1.2, alpha=0.7, label='Original Signal $x[n]$')
    ax1.step(t_sub, ldm_res["x_tilde"][:n_plot], 'r-', where='mid', lw=1.4, alpha=0.85, label=f'Linear DM (Fixed $\\Delta = {ldm_res["delta"]:.4f}$, MSE={ldm_res["mse"]:.5f})')
    ax1.step(t_sub, adm_res["x_tilde"][:n_plot], 'g-', where='mid', lw=1.5, label=f'Adaptive DM (Song/Jayant, MSE={adm_res["mse"]:.5f})')
    ax1.set_title('Adaptive Delta Modulation (ADM) vs Linear Delta Modulation (LDM)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Amplitude (V)', fontsize=9)
    ax1.grid(True, alpha=0.3, ls='--')
    ax1.legend(loc='upper right', framealpha=0.9)
    
    # 2. ADM Dynamic Step Size Evolution
    ax2.plot(t_sub, adm_res["step_sizes"][:n_plot], color='#984ea3', lw=1.4, label=r'Dynamic Step Size $\Delta[n]$')
    ax2.set_title(r'Adaptive Step Size Scaling $\Delta[n]$ (Expands on Steep Slopes, Contracts in Flat Regions)', fontsize=10)
    ax2.set_ylabel(r'$\Delta[n]$ (V)', fontsize=9)
    ax2.grid(True, alpha=0.3, ls='--')
    ax2.legend(loc='upper right')
    
    # 3. Instantaneous Error Comparison
    ax3.plot(t_sub, ldm_res["error"][:n_plot], 'r-', lw=1.2, alpha=0.7, label='LDM Error')
    ax3.plot(t_sub, adm_res["error"][:n_plot], 'g-', lw=1.2, label='ADM Error')
    ax3.axhline(0, color='gray', lw=0.6, ls=':')
    ax3.set_title(f'Error Waveform Comparison (SQNR Gain of ADM: +{adm_res["sqnr_db"] - ldm_res["sqnr_db"]:.2f} dB)', fontsize=10)
    ax3.set_xlabel('Time (seconds)', fontsize=10)
    ax3.set_ylabel('Error (V)', fontsize=9)
    ax3.grid(True, alpha=0.3, ls='--')
    ax3.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
