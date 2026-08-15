# Two-Tone Signal Sampling, Sinc Reconstruction & Aliasing DSP Suite 🌊

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-00f2fe?style=for-the-badge&logo=github)](https://subhankar-06.github.io/two-tone-signal-sampling-dsp/)

🌐 **Live Web Application**: [https://subhankar-06.github.io/two-tone-signal-sampling-dsp/](https://subhankar-06.github.io/two-tone-signal-sampling-dsp/)

An interactive Web Studio and Python DSP simulation suite designed for Digital Communication courses to demonstrate and verify the **Whittaker-Shannon Sampling Theorem**, **Sinc Interpolation**, and **Aliasing Dynamics** for a two-tone signal:

$$x(t) = A_1 \sin(2\pi f_1 t) + A_2 \sin(2\pi f_2 t)$$

Default parameters: $f_1 = 5.0 \text{ Hz}$, $f_2 = 12.0 \text{ Hz}$ ($f_{\max} = 12.0 \text{ Hz}$, Nyquist Rate $2f_{\max} = 24.0 \text{ Hz}$).

---

## 🌟 Key Features

1. **Decoupled Sampling & Plotting Resolutions**:
   - **Continuous Plotting Grid ($f_{\text{plot}} = 2000 \text{ Hz}$)**: High-resolution grid simulating true continuous-time analog signals.
   - **Physical Sampling Rate ($f_s$)**: Discrete physical sampler acquiring samples at $t_n = n/f_s$.

2. **3 Fundamental Sampling Regimes**:
   - **Above Nyquist ($f_s = 36 \text{ Hz} > 24 \text{ Hz}$)**: Over-sampled regime ($1.50\times$). Perfect Whittaker-Shannon sinc reconstruction ($\text{RMSE} \approx 0$).
   - **At Nyquist ($f_s = 24 \text{ Hz} = 2f_{\max}$)**: Critical sampling boundary ($1.00\times$). Phase-sensitive critical recovery.
   - **Below Nyquist ($f_s = 14 \text{ Hz} < 24 \text{ Hz}$)**: Sub-Nyquist regime ($0.58\times$). Aliasing active — the $12.0 \text{ Hz}$ component folds back to $|12 - 14| = \mathbf{2.0 \text{ Hz}}$, creating false low-frequency distortion.

3. **▶ Runnable Animated Oscilloscope Wave**:
   - 60 FPS real-time traveling wave animation ($t \to t + t_{\text{offset}}$) allowing dynamic observation of wave propagation, discrete stem points, sinc reconstruction, and continuous error signal.

4. **🔊 Web Audio Acoustic Synthesizer**:
   - Acoustic synthesis using Web Audio API to **listen** to the reference vs reconstructed audio. In sub-Nyquist mode, hear the aliased $2.0 \text{ Hz}$ beat frequency pitch distortion.

5. **📊 Spectral & Error Analytics**:
   - FFT magnitude spectrum of reference vs reconstructed signal with Hann windowing.
   - Continuous time-domain reconstruction error $e(t) = x(t) - x_r(t)$.
   - Real-time RMSE, Signal-to-Distortion Ratio (SDR in dB), and theoretical alias frequency calculator.

---

## 📊 Quantitative Simulation Results

| Sampling Regime | Physical Rate ($f_s$) | Nyquist Ratio | Tone 2 ($12\text{Hz}$) Alias | Reconstruction RMSE | SDR (dB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Above Nyquist** | **36.0 Hz** | $1.50\times$ | $12.0 \text{ Hz}$ (Preserved) | **0.0470** | **24.51 dB** |
| **At Nyquist** | **24.0 Hz** | $1.00\times$ | $12.0 \text{ Hz}$ (Preserved) | **0.3831** | **6.29 dB** |
| **Below Nyquist** | **14.0 Hz** | $0.58\times$ | **$2.0 \text{ Hz}$ (Aliased!)** | **0.5119** | **3.78 dB** |

---

## 📐 Mathematical Foundations

### Whittaker-Shannon Sinc Interpolation
$$x_r(t) = \sum_{n=0}^{N-1} x[n] \cdot \operatorname{sinc}\left( \frac{t - n T_s}{T_s} \right)$$
where $\operatorname{sinc}(u) = \frac{\sin(\pi u)}{\pi u}$.

### Alias Frequency Derivation
When $f_s < 2f_{\max}$, spectral components fold into $[0, f_s/2]$ via:
$$f_{\text{alias}} = | f - k \cdot f_s |, \quad k = \operatorname{round}(f / f_s)$$
For $f_2 = 12 \text{ Hz}$ sampled at $f_s = 14 \text{ Hz}$:
$$f_{\text{alias}, 2} = | 12 - 1 \times 14 | = 2.0 \text{ Hz}$$

---

## 🚀 Quick Start

### Option 1: Web DSP Studio (Interactive Browser UI)

Simply serve `index.html` with any local web server:

```bash
# Python local server
python -m http.server 8080
```
Open `http://localhost:8080` in your web browser.

### Option 2: Python Script (`lab_script.py`)

Run the standalone Python simulation script using NumPy & Matplotlib:

```bash
# Install dependencies if needed
pip install numpy matplotlib

# Execute Python lab simulation
python lab_script.py
```
This generates and saves `sampling_simulation_results.png` directly to your directory.

---

## 📁 Repository Structure

```
├── index.html                       # Main HTML layout for Web Studio
├── styles.css                       # Futuristic dark theme design system
├── app.js                           # DSP Math Engine, Sinc Matrix & Web Audio
├── lab_script.py                    # Standalone Python lab script
├── sampling_simulation_results.png  # Generated 3-case simulation plot
└── README.md                        # Documentation
```

---

## 📜 License
MIT License. Free for educational and laboratory use.
