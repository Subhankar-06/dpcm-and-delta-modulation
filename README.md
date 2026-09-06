# Digital Communication Laboratory Suite 🌊

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-00f2fe?style=for-the-badge&logo=github)](https://subhankar-06.github.io/two-tone-signal-sampling-dsp/)
[![Tests](https://img.shields.io/badge/Unit_Tests-All%20Passed-10b981?style=for-the-badge&logo=pytest)](dpcm_delta_modulation/tests/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)](https://python.org)

🌐 **Live Web Application**: [https://subhankar-06.github.io/two-tone-signal-sampling-dsp/](https://subhankar-06.github.io/two-tone-signal-sampling-dsp/)

An integrated, interactive Web Studio and Python DSP simulation suite designed for Digital Communication courses. Combines multiple foundational laboratory experiments into a single unified platform:

1. **Experiment 4: Uniform Quantization and Pulse Code Modulation (PCM)**
2. **Experiment 5: Differential PCM (DPCM) & Delta Modulation (DM / ADM)**
3. **Whittaker-Shannon Sampling Theorem, Sinc Reconstruction & Aliasing**

---

## 🌟 Interactive Web Platform Overview

The live web application features a **multi-experiment tabbed interface**:

- **Exp 4: Uniform Quantization & PCM Studio**:
  - Interactive mid-rise and mid-tread uniform quantizers across bit depths $n \in \{2, 3, 4, 6, 8\}$.
  - Empirical vs Theoretical $\text{SQNR} \approx 6.02 n + 1.76 \text{ dB}$ derivation and dynamic verification.
  - Live PCM binary word inspector table displaying the raw bit stream (`0000` to `1111`).
  - Error probability density function (PDF) histogram vs ideal uniform distribution $U[-\Delta/2, +\Delta/2]$.
  - Web Audio acoustic synthesizer to listen to quantization noise.

- **Exp 5: DPCM & Delta Modulation Studio**:
  - First-order linear predictor $\hat{x}[n] = a_1 \tilde{x}[n-1]$ with sample redundancy reduction.
  - Linear Delta Modulation (LDM) with fixed step size $\Delta$, featuring 1-click presets:
    - **Small Step ($\Delta < \Delta_{\text{crit}}$)**: Visualizing severe **Slope Overload Distortion**.
    - **Moderate Step ($\Delta \approx \Delta_{\text{crit}}$)**: Demonstrating **Optimal Balanced Tracking**.
    - **Large Step ($\Delta \gg \Delta_{\text{crit}}$)**: Visualizing **Granular Hunting Noise**.
  - **Dynamic MSE vs. Step Size U-Curve**: Live real-time tracker displaying the physical trade-off between slope overload and granular noise.
  - **Adaptive Delta Modulation (ADM)**: Song/Jayant dynamic step scaling toggle.
  - **Mandatory Step Invariant Validator**: Validates that all output steps change by exactly $\pm\Delta$.

---

## 📊 Summary of Quantitative Results

### Experiment 4: Uniform Quantization & PCM
| Resolution ($n$) | Levels ($L = 2^n$) | Step Size ($\Delta$) | Empirical MSE | Simulated SQNR (dB) | Theoretical SQNR (dB) | Discrepancy |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2 Bits** | 4 | 0.50000 V | 0.020833 | **13.80 dB** | 13.80 dB | 0.00 dB |
| **3 Bits** | 8 | 0.25000 V | 0.005208 | **19.82 dB** | 19.82 dB | 0.00 dB |
| **4 Bits** | 16 | 0.12500 V | 0.001302 | **25.85 dB** | 25.84 dB | +0.01 dB |
| **6 Bits** | 64 | 0.03125 V | 0.000081 | **37.89 dB** | 37.88 dB | +0.01 dB |
| **8 Bits** | 256 | 0.00781 V | 0.000005 | **49.93 dB** | 49.92 dB | +0.01 dB |

### Experiment 5: DPCM & Delta Modulation
| Experiment / Parameter | Operating Regime | Measured MSE | SQNR (dB) | Theoretical Gain / Bound | Key Physical Observation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **DPCM ($a_1 = 0.85, b=3$)** | Redundancy Reduction | **0.003975** | **20.99 dB** | $G_p = +15.21 \text{ dB}$ | Variance reduced by $33\times$; +1.90 dB over PCM |
| **Direct PCM ($b=3$)** | Direct Quantization | 0.006161 | 19.09 dB | Baseline (0 dB) | Standard uniform quantization noise |
| **DM: Small Step** ($0.30\Delta_{\text{crit}}$) | **Slope Overload** | 0.365760 | 1.36 dB | $\text{SOR} = 3.33$ | Staircase falls behind signal derivative |
| **DM: Moderate Step** ($1.25\Delta_{\text{crit}}$) | **Optimal Tracking** | **0.000021** | **43.86 dB** | $\text{SOR} = 0.80$ | Minimal distortion; balanced trade-off |
| **DM: Large Step** ($5.00\Delta_{\text{crit}}$) | **Granular Noise** | 0.000329 | 31.81 dB | $\text{MSE} \approx \Delta^2/3$ | Rapid hunting oscillations in flat regions |
| **DM: Rapid Input** ($f = 4.0 \text{ Hz}$) | Severe Overload | 0.373213 | 1.27 dB | $\text{SOR} = 3.20$ | $18,071\times$ higher distortion than slow input |
| **Adaptive DM (ADM)** | Dynamic Scaling | **0.000033** | **41.87 dB** | Song / Jayant | Eliminates overload while preserving fine steps |

---

## 📁 Repository Organization

```
├── index.html                           # Unified Laboratory Web Application (Exp 4 & Exp 5)
├── styles.css                           # Unified CSS styling & glassmorphism theme
├── app.js                               # Uniform Quantization & PCM DSP Engine
├── dpcm_app.js                          # DPCM & Delta Modulation DSP Engine
├── dpcm/                                # Direct standalone route for DPCM studio
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── dpcm_delta_modulation/               # Experiment 5: Python DSP Package
│   ├── config.py                        # Signal, predictor & step size configuration
│   ├── dpcm.py                          # First-order predictor & PCM baseline comparator
│   ├── delta_modulation.py              # Linear DM, Adaptive DM, and step sweep engine
│   ├── analysis.py                      # SOR, granular noise bounds, diagnostics
│   ├── visualization.py                 # Matplotlib 6-figure publication plotting suite
│   ├── main.py                          # Master CLI lab runner
│   ├── README.md                        # Experiment 5 comprehensive lab manual
│   ├── requirements.txt
│   ├── tests/
│   │   └── test_dpcm_dm.py              # 8 automated unit tests (unittest)
│   └── results/
│       ├── metrics.csv                  # Numerical metrics export
│       └── figures/                     # 6 generated publication figures (300 DPI)
├── uniform_quantization_pcm/            # Experiment 4: Python DSP Package
│   ├── config.py
│   ├── quantizer.py
│   ├── pcm.py
│   ├── analysis.py
│   ├── visualization.py
│   ├── main.py
│   ├── README.md                        # Experiment 4 comprehensive lab manual
│   ├── requirements.txt
│   ├── tests/
│   │   └── test_quantizer.py
│   └── results/
└── .github/workflows/
    └── deploy.yml                       # Automated GitHub Pages deployment workflow
```

---

## 🚀 Execution Guide

### 1. Run Automated Unit Tests
```powershell
# Run DPCM & Delta Modulation tests (Exp 5)
python -m unittest discover -s dpcm_delta_modulation/tests -p "test_*.py" -v

# Run Uniform Quantization & PCM tests (Exp 4)
python -m unittest discover -s uniform_quantization_pcm/tests -p "test_*.py" -v
```

### 2. Execute Python Laboratory Simulations
```powershell
# Run DPCM & Delta Modulation simulation (generates figures & metrics)
python dpcm_delta_modulation/main.py

# Run Uniform Quantization & PCM simulation
python uniform_quantization_pcm/main.py
```

### 3. Open Interactive Web Studio Locally
Open `index.html` in any modern web browser or start a local HTTP server:
```powershell
python -m http.server 8000
```
Then navigate to `http://localhost:8000`.
