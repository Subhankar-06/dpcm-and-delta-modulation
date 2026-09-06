# Uniform Quantization and Pulse Code Modulation (PCM) — Digital Communication Laboratory Suite 🌊

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-00f2fe?style=for-the-badge&logo=github)](https://subhankar-06.github.io/uniform-quantization-pcm-dsp/)

🌐 **Live Web Application**: [https://subhankar-06.github.io/uniform-quantization-pcm-dsp/](https://subhankar-06.github.io/uniform-quantization-pcm-dsp/)

A complete, standalone Python DSP laboratory project demonstrating **Mid-Rise Uniform Quantization**, **Manual Binary PCM Encoding**, **Quantization Error & MSE Analysis**, and **Empirical vs Theoretical Signal-to-Quantization-Noise Ratio (SQNR)** derivation for sinusoidal signals across bit depths $n \in \{2, 3, 4, 6, 8\}$.


---

## 1. Aim

To study the fundamental principles of **Uniform Quantization** and **Pulse Code Modulation (PCM)** encoding on a normalized sinusoidal analog signal, to evaluate quantization error, Mean Squared Error (MSE), and SQNR across varying bit depths ($n = 2, 3, 4, 6, 8$), and to compare experimental simulation results against the theoretical approximation:

$$\text{SQNR} \approx 6.02 n + 1.76 \text{ dB}$$

---

## 2. Objectives

- Implement a normalized sinusoidal signal generator from first principles.
- Implement a reusable mid-rise uniform quantizer without using external quantization library APIs.
- Manually generate $n$-bit binary PCM encoding strings for integer quantization indices ($0 \le \text{index} \le 2^n - 1$).
- Perform mandatory automated validation assertions on all simulation outputs.
- Quantify the physical relationship:
  $$n \uparrow \implies L = 2^n \uparrow \implies \Delta \downarrow \implies |e[k]| \downarrow \implies \text{MSE} \downarrow \implies \text{SQNR} \uparrow$$
- Generate 5 publication-quality Matplotlib figures displaying waveforms, staircase transfer functions, error signals, error PDFs, and the $6.02 \text{ dB/bit}$ linear SQNR curve.
- Export all numerical lab measurements to `results/results.csv`.

---

## 3. Theory

### Uniform Quantization
Quantization is the process of mapping a continuous-amplitude signal $x(t)$ into a finite set of discrete representation levels. In a **uniform quantizer**, the total dynamic range $R = V_{\max} - V_{\min}$ is divided into $L = 2^n$ equal intervals of width (step size) $\Delta$:

$$\Delta = \frac{V_{\max} - V_{\min}}{L} = \frac{V_{\max} - V_{\min}}{2^n}$$

In a **mid-rise uniform quantizer**:
- Decision boundaries: $d_i = V_{\min} + i \cdot \Delta$, for $i = 0, 1, \dots, L$.
- Representation levels: $q_i = V_{\min} + (i + 0.5) \cdot \Delta$, for $i = 0, 1, \dots, L-1$.
- The origin ($0.0$) lies on a decision boundary rather than a level, providing a zero-mean balanced AC representation.

### Pulse Code Modulation (PCM) Encoding
PCM converts each integer index $i \in [0, L-1]$ into an $n$-bit binary code word. For example, with $n = 3$ bits ($L = 8$), index $i = 5$ is encoded as the 3-bit binary string `"101"`.

### Quantization Error and Noise Power
The instantaneous quantization error $e[k]$ is defined as:

$$e[k] = x[k] - x_q[k]$$

Assuming the error $e[k]$ is uniformly distributed over $[-\Delta/2, +\Delta/2]$ with zero mean, its Probability Density Function (PDF) is:

$$f_E(e) = \begin{cases} \frac{1}{\Delta}, & -\frac{\Delta}{2} \le e \le \frac{\Delta}{2} \\ 0, & \text{otherwise} \end{cases}$$

The quantization noise power $P_e$ equals the Mean Squared Error (MSE):

$$P_e = \text{MSE} = E[e^2] = \int_{-\Delta/2}^{+\Delta/2} e^2 \cdot \frac{1}{\Delta} \, de = \frac{\Delta^2}{12}$$

### Theoretical SQNR Derivation (The 6.02 dB/Bit Rule)
For a normalized full-scale sinusoid $x(t) = A \sin(2\pi f t)$ bounded in $[-1, 1]$ (where $A = 1$ and $V_{\max} - V_{\min} = 2$):
- Signal Power: $P_x = \frac{A^2}{2} = 0.5 \text{ W}$
- Step Size: $\Delta = \frac{2}{2^n} = 2^{1-n}$
- Noise Power: $P_e = \frac{\Delta^2}{12} = \frac{(2^{1-n})^2}{12} = \frac{4 \cdot 2^{-2n}}{12} = \frac{2^{-2n}}{3}$

Calculating the Signal-to-Quantization-Noise Ratio:

$$\text{SQNR} = \frac{P_x}{P_e} = \frac{0.5}{2^{-2n} / 3} = 1.5 \times 2^{2n}$$

Expressed in decibels (dB):

$$\text{SQNR}_{\text{dB}} = 10 \log_{10}(1.5 \times 2^{2n}) = 10 \log_{10}(1.5) + 10 \log_{10}(2^{2n})$$

$$\text{SQNR}_{\text{dB}} = 1.7609 + 2n \cdot (10 \log_{10} 2) = 1.7609 + 2n \cdot (3.0103) \approx \mathbf{6.02 n + 1.76 \text{ dB}}$$

---

## 4. Mathematical Equations

1. **Normalized Input Signal**:
   $$x[k] = \sin(2\pi f k / f_s), \quad k = 0, 1, \dots, N-1$$

2. **Quantization Index Mapping**:
   $$i[k] = \operatorname{clip}\left( \left\lfloor \frac{x[k] - V_{\min}}{\Delta} \right\rfloor, 0, L-1 \right)$$

3. **Reconstructed Quantized Signal**:
   $$x_q[k] = V_{\min} + (i[k] + 0.5) \cdot \Delta$$

4. **Mean Squared Error (MSE)**:
   $$\text{MSE} = \frac{1}{N} \sum_{k=0}^{N-1} (x[k] - x_q[k])^2$$

5. **Simulated SQNR**:
   $$\text{SQNR}_{\text{sim}} = 10 \log_{10} \left( \frac{\frac{1}{N} \sum_{k=0}^{N-1} x[k]^2}{\text{MSE}} \right)$$

6. **Theoretical SQNR**:
   $$\text{SQNR}_{\text{theory}} = 6.02 n + 1.76 \text{ dB}$$

---

## 5. Project Structure

```text
uniform_quantization_pcm/
│
├── main.py               # Main CLI runner, terminal output & pipeline orchestrator
├── quantizer.py          # Mid-rise uniform quantizer (first principles)
├── pcm.py                # Manual PCM encoder & decoder
├── analysis.py           # Metrics, validations, theory evaluator & 10-point diagnostics
├── visualization.py      # Matplotlib generator for 5 laboratory figures
├── config.py             # Global simulation settings & paths
├── requirements.txt      # Dependencies (numpy, matplotlib)
├── README.md             # Complete lab documentation & submission report
│
├── results/
│   ├── results.csv       # Exported numerical lab data
│   └── figures/          # High-resolution PNG figures
│       ├── waveform.png          # Plot 1: Original vs Quantized Signal (4-Bit)
│       ├── staircase.png         # Plot 2: Staircase Transfer Function
│       ├── error_waveform.png    # Plot 3: Error Waveforms Across Bit Depths
│       ├── error_histogram.png   # Plot 4: Quantization Error Histogram vs Uniform PDF
│       └── sqnr_vs_bits.png      # Plot 5: SQNR vs Bit Depth (6.02 dB/bit Slope)
│
└── tests/
    └── test_quantizer.py # Automated unit test suite (unittest framework)
```

---

## 6. Installation & Quick Start

### Option 1: Python DSP Laboratory Suite (`main.py`)
Run the Python simulation script and unit test suite:

```bash
cd uniform_quantization_pcm

# 1. Install dependencies if needed
pip install -r requirements.txt

# 2. Run automated unit tests
python -m unittest discover -s tests

# 3. Execute Python laboratory simulation
python main.py
```

---

### Option 2: Interactive Web DSP Studio (Browser UI)
Launch the interactive HTML5 Web Studio with live Canvas 2D oscilloscope, PCM bitstream inspector, and Web Audio acoustic synthesizer:

```bash
# Serve the web studio directory
python -m http.server 8080 --directory web
```
Open **`http://localhost:8080`** in your web browser.


---

## 7. Python Implementation Details

- **`quantizer.py`**: Calculates $\Delta = \frac{V_{\max} - V_{\min}}{2^n}$, computes discrete indices via element-wise NumPy array arithmetic `np.floor((signal - min_val)/delta)`, clips boundary values to $[0, L-1]$, and maps to representation levels.
- **`pcm.py`**: Uses bitwise right-shift `(index >> bit_pos) & 1` in Python loops to build exact $n$-bit binary string words (e.g. `"101"`) without using external conversion libraries.
- **`analysis.py`**: Enforces mandatory runtime `assert` assertions verifying index bounds, binary word length, non-NaN/Inf states, and dynamic range compliance.

---

## 8. Automated Validation Suite

For every bit depth $n \in \{2, 3, 4, 6, 8\}$, the program executes:
- `assert np.all(indices >= 0)`
- `assert np.all(indices < L)`
- `assert all(len(word) == bits for word in pcm_words)`
- Checks for zero NaN or Inf values in quantized outputs.
- Verifies range bounds $-1.0 \le x_q \le 1.0$.

Terminal Validation Output:
```text
Validation for n = 4 bits
✓ Index non-negative (min >= 0): PASS
✓ Maximum index within bounds (< L): PASS
✓ PCM word length exact (len == bits): PASS
✓ No NaN values: PASS
✓ No Inf values: PASS
✓ Quantized signal in range: PASS
```

---

## 9. Experimental Results

Summary of numerical measurements generated during simulation:

| Bits ($n$) | Levels ($L$) | Step Size $\Delta$ (V) | MSE ($P_e$) | Max Error (V) | RMS Error (V) | SQNR Sim (dB) | SQNR Theory (dB) | Difference (dB) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2** | 4 | 0.500000 | $2.619 \times 10^{-2}$ | 0.250000 | 0.161836 | **12.81** | 13.80 | -0.99 |
| **3** | 8 | 0.250000 | $6.161 \times 10^{-3}$ | 0.125000 | 0.078493 | **19.09** | 19.82 | -0.73 |
| **4** | 16 | 0.125000 | $1.471 \times 10^{-3}$ | 0.062500 | 0.038357 | **25.31** | 25.84 | -0.53 |
| **6** | 64 | 0.031250 | $8.736 \times 10^{-5}$ | 0.015625 | 0.009347 | **37.58** | 37.88 | -0.30 |
| **8** | 256 | 0.007812 | $5.251 \times 10^{-6}$ | 0.003906 | 0.002292 | **49.79** | 49.92 | -0.13 |

---

## 10. Required Laboratory Visualizations

### Plot 1 — Original vs Quantized Waveform (`results/figures/waveform.png`)
Displays the smooth continuous sinusoid alongside the discrete step waveform $x_q(t)$ for 4 bits ($L=16$), highlighting the physical staircase quantization effect.

### Plot 2 — Staircase Quantizer Transfer Curve (`results/figures/staircase.png`)
Plots the transfer function $x \to x_q$ over $[-1.0, 1.0]$ for a 3-bit quantizer ($L=8$), indicating decision boundaries, representation levels, and step size $\Delta = 0.25 \text{ V}$.

### Plot 3 — Quantization Error Waveforms (`results/figures/error_waveform.png`)
Subplots comparing instantaneous error $e(t) = x(t) - x_q(t)$ for $n = 2, 3, 4, 8$ bits, illustrating how error amplitude shrinks within $[-\Delta/2, +\Delta/2]$ as bit depth increases.

### Plot 4 — Quantization Error Histogram (`results/figures/error_histogram.png`)
Compares the empirical error distribution against the ideal uniform PDF $U[-\Delta/2, +\Delta/2]$ with height $1/\Delta$.

### Plot 5 — SQNR vs Bit Depth (`results/figures/sqnr_vs_bits.png`)
Graph of Simulated SQNR vs Theoretical SQNR across bit depths $n \in \{2, 3, 4, 6, 8\}$, visually proving the linear $\mathbf{6.02 \text{ dB/bit}}$ slope.

---

## 11. Parameter-Variation Expected Observations

Before running each bit depth, physical expectations were printed:
- **2 Bits**: Coarse quantization ($L=4, \Delta=0.50 \text{ V}$) resulting in severe staircase distortion and low SQNR (~13.8 dB).
- **3 Bits**: Step size drops by half ($\Delta=0.25 \text{ V}$), quadrupling noise power reduction and adding ~6 dB to SQNR (~19.8 dB).
- **4 Bits**: $L=16$ levels with $\Delta=0.125 \text{ V}$; staircase steps become noticeably smoother with SQNR ~25.8 dB.
- **6 Bits**: $L=64$ granular levels ($\Delta=0.03125 \text{ V}$); noise power drops sharply with SQNR ~37.9 dB.
- **8 Bits**: High-resolution quantization ($L=256, \Delta \approx 0.0078 \text{ V}$); output waveform is visually identical to continuous input with SQNR ~49.9 dB.

---

## 12. Observed Results & Interpretations

Post-simulation observations confirmed:
- Doubling the number of quantization levels ($n \to n+1$) halves the step size $\Delta \to \Delta/2$.
- Quantization noise power $P_e = \text{MSE}$ decreases by a factor of approximately 4 ($1/2^2$) per added bit.
- SQNR increases by approximately $6.02 \text{ dB}$ per bit, adhering strictly to theory.

---

## 13. Comparison with Theory

- **Tolerance**: Set to $\pm 1.0 \text{ dB}$.
- **Agreement**: **YES** (All bit depths agree within 1.0 dB).
- At high bit depths ($n=6, 8$), the difference between simulation and theory shrinks to $-0.30 \text{ dB}$ and $-0.13 \text{ dB}$, confirming excellent convergence to the ideal theoretical linear model.

---

## 14. 10-Point Discrepancy Diagnostics

The automated diagnostic suite verified:
1. **Signal Amplitude**: PASS — Peak magnitude reaches full scale $\pm 1.0 \text{ V}$.
2. **Signal Clipping**: PASS — No clipping/overload detected.
3. **Step Size Calculation**: PASS — Step size $\Delta = (V_{\max} - V_{\min})/2^n$ verified.
4. **Quantization Level Placement**: PASS — Quantized samples land on valid mid-rise levels.
5. **Endpoint Handling**: PASS — Index range $[0, L-1]$ satisfied.
6. **Quantizer Type**: PASS — Mid-rise zero-mean AC representation confirmed.
7. **Signal Power**: PASS — $P_x = 0.5000 \text{ W}$ matches $A^2/2$.
8. **Noise Power**: PASS — Measured $P_e$ matches theoretical $\Delta^2/12$.
9. **Sample Size**: PASS — $N=2000$ samples provides accurate ergodic statistics.
10. **Theoretical Model**: PASS — Full-scale sinusoidal SQNR model $6.02n + 1.76 \text{ dB}$ applies.

---

## 15. Discussion

The slight difference of $-0.99 \text{ dB}$ at $n=2$ bits arises because the theoretical formula $6.02n + 1.76 \text{ dB}$ assumes that quantization error $e[k]$ is completely uncorrelated with the input signal $x[k]$. For coarse 2-bit quantization, the error retains weak correlation with the sinusoidal shape. As bit depth increases to $n=8$, quantization noise becomes strictly independent and uniformly distributed, causing empirical SQNR to converge to within $0.13 \text{ dB}$ of theoretical predictions.

---

## 16. Conclusion

This project successfully demonstrated the fundamental principles of **Uniform Quantization** and **PCM Encoding**. The implementation verified from first principles that increasing bit depth increases quantization resolution exponentially ($L = 2^n$), reduces quantization step size linearly ($\Delta \propto 2^{-n}$), decreases mean squared error quadratically ($\text{MSE} \propto 2^{-2n}$), and increases Signal-to-Quantization-Noise Ratio linearly by **$6.02 \text{ dB}$ per bit**.
