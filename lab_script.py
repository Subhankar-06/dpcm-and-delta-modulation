"""
===================================================================================
Digital Communication Lab Experiment: Sampling Theorem & Sinc Reconstruction
===================================================================================
Objectives:
  1. Verify the Sampling Theorem for a two-tone signal:
     x(t) = sin(2*pi*f1*t) + 0.5*sin(2*pi*f2*t)
  2. Test sampling rate fs in three cases:
     - Above Nyquist rate (fs > 2*fmax)
     - At Nyquist rate (fs = 2*fmax)
     - Below Nyquist rate (fs < 2*fmax)
  3. Reconstruct continuous signal using Whittaker-Shannon Sinc Interpolation.
  4. Display comparable time- and frequency-domain plots, and continuous error.
===================================================================================
"""

import numpy as np
import matplotlib.pyplot as plt

def main():
    # --- 1. Signal Parameters ---
    f1 = 5.0    # Frequency of Tone 1 (Hz)
    A1 = 1.0    # Amplitude of Tone 1
    f2 = 12.0   # Frequency of Tone 2 (Hz)
    A2 = 0.5    # Amplitude of Tone 2

    fmax = max(f1, f2)
    nyquist_rate = 2 * fmax  # 24 Hz

    print("=" * 60)
    print(" SAMPLING THEOREM & SINC RECONSTRUCTION SIMULATOR")
    print("=" * 60)
    print(f"Tone 1: f1 = {f1} Hz, A1 = {A1}")
    print(f"Tone 2: f2 = {f2} Hz, A2 = {A2}")
    print(f"Maximum Frequency fmax = {fmax} Hz")
    print(f"Nyquist Rate 2*fmax    = {nyquist_rate} Hz")
    print("=" * 60)

    # Time window & high-resolution continuous plotting grid
    T_window = 1.0  # 1.0 second duration
    f_plot = 2000   # High plotting resolution (2000 Hz) simulating continuous time
    t_dense = np.linspace(0, T_window, int(T_window * f_plot), endpoint=False)

    # Reference continuous two-tone signal
    x_dense = A1 * np.sin(2 * np.pi * f1 * t_dense) + A2 * np.sin(2 * np.pi * f2 * t_dense)

    # --- 2. Define Three Sampling Cases ---
    sampling_cases = [
        {"name": "Above Nyquist", "fs": 36.0, "color": "green"},
        {"name": "At Nyquist",    "fs": 24.0, "color": "orange"},
        {"name": "Below Nyquist", "fs": 14.0, "color": "red"}
    ]

    # Set up 3x3 subplot layout
    fig, axes = plt.subplots(3, 3, figsize=(15, 10))
    fig.suptitle('Sampling of Two-Tone Signal in 3 Regimes & Sinc Reconstruction', fontsize=14, fontweight='bold')

    for idx, c in enumerate(sampling_cases):
        fs = c["fs"]
        Ts = 1.0 / fs
        t_samples = np.arange(0, T_window, Ts)
        x_samples = A1 * np.sin(2 * np.pi * f1 * t_samples) + A2 * np.sin(2 * np.pi * f2 * t_samples)

        # Whittaker-Shannon Sinc Interpolation:
        # x_recon(t) = sum_n x[n] * sinc((t - n*Ts)/Ts)
        # Note: np.sinc(u) calculates sin(pi*u)/(pi*u)
        sinc_matrix = np.sinc((t_dense[:, None] - t_samples[None, :]) / Ts)
        x_recon = np.dot(sinc_matrix, x_samples)

        # Continuous Error & Metrics
        error_signal = x_dense - x_recon
        rmse = np.sqrt(np.mean(error_signal**2))
        sdr = 10 * np.log10(np.sum(x_dense**2) / (np.sum(error_signal**2) + 1e-12))

        # Alias calculation for tones
        alias1 = np.abs(f1 - round(f1 / fs) * fs)
        alias2 = np.abs(f2 - round(f2 / fs) * fs)

        print(f"\n[Case {idx+1}] {c['name']} (fs = {fs} Hz, Ratio = {fs/nyquist_rate:.2f}x)")
        print(f"  -> Reconstruction RMSE: {rmse:.4f}")
        print(f"  -> Signal-to-Distortion: {sdr:.2f} dB")
        print(f"  -> Tone 1 ({f1} Hz) Alias in [0, fs/2]: {alias1:.1f} Hz")
        print(f"  -> Tone 2 ({f2} Hz) Alias in [0, fs/2]: {alias2:.1f} Hz")

        # --- Column 1: Time-Domain (Reference, Samples, Reconstructed) ---
        ax_time = axes[idx, 0]
        ax_time.plot(t_dense, x_dense, 'c--', label='Reference x(t)', alpha=0.8, lw=1.5)
        ax_time.plot(t_dense, x_recon, 'm-', label='Reconstructed x_r(t)', lw=2.0)
        markerline, stemlines, _ = ax_time.stem(t_samples, x_samples, linefmt='g-', markerfmt='go', basefmt=' ')
        plt.setp(stemlines, alpha=0.6)
        plt.setp(markerline, markersize=4)
        ax_time.set_title(f"{c['name']} (fs={fs}Hz) - Time Domain\nRMSE={rmse:.4f}", fontsize=10)
        ax_time.set_ylabel("Amplitude")
        ax_time.grid(True, alpha=0.3)
        if idx == 0:
            ax_time.legend(loc='upper right', fontsize=8)

        # --- Column 2: Frequency-Domain (FFT Magnitude Spectrum) ---
        ax_freq = axes[idx, 1]
        N = len(x_recon)
        freqs = np.fft.rfftfreq(N, 1.0 / f_plot)
        # Apply Hann window to prevent leakage
        spectrum = np.abs(np.fft.rfft(x_recon * np.hanning(N))) * (4.0 / N)
        ax_freq.plot(freqs, spectrum, color=c['color'], lw=1.8)
        ax_freq.set_xlim(0, 30)
        ax_freq.set_ylim(0, 1.2)
        ax_freq.axvline(fs / 2, color='gray', linestyle=':', label=f'Nyquist Limit fs/2={fs/2}Hz')
        ax_freq.set_title(f"{c['name']} - Magnitude Spectrum", fontsize=10)
        ax_freq.set_ylabel("|X(f)|")
        ax_freq.grid(True, alpha=0.3)
        ax_freq.legend(loc='upper right', fontsize=8)

        # --- Column 3: Reconstruction Error e(t) = x(t) - x_r(t) ---
        ax_err = axes[idx, 2]
        ax_err.plot(t_dense, error_signal, 'r-', lw=1.5)
        ax_err.set_title(f"{c['name']} - Reconstruction Error e(t)", fontsize=10)
        ax_err.set_ylabel("Error")
        ax_err.grid(True, alpha=0.3)

    axes[2, 0].set_xlabel("Time (s)")
    axes[2, 1].set_xlabel("Frequency (Hz)")
    axes[2, 2].set_xlabel("Time (s)")

    plt.tight_layout()
    plot_filename = "sampling_simulation_results.png"
    plt.savefig(plot_filename, dpi=300)
    print(f"\nSaved simulation plot to '{plot_filename}'.")
    plt.close('all')

if __name__ == "__main__":
    main()
