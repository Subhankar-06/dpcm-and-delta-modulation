/* ==========================================================================
   Sampling Theorem & Sinc Reconstruction Studio - Main JS Engine
   ========================================================================== */

// --- Global State ---
const state = {
    f1: 5.0,
    a1: 1.0,
    f2: 12.0,
    a2: 0.5,
    fs: 36.0,
    fplot: 2000,
    tWindow: 1.0,
    showSincPulses: false,
    showStemLines: true,
    currentTab: 'sandbox',
    preset: 'above',
    
    // Animation & Audio State
    tOffset: 0.0,
    isAnimating: false,
    animSpeed: 1.0,
    audioPlaying: null // 'ref' | 'recon' | null
};

// Web Audio API Context
let audioCtx = null;
let audioNodes = [];

// Chart instances
let chartTimeSampled = null;
let chartTimeRecon = null;
let chartFreqSpectrum = null;
let chartError = null;

// Comparison matrix chart instances
const compareCharts = {
    timeAbove: null, freqAbove: null, errAbove: null,
    timeAt: null, freqAt: null, errAt: null,
    timeBelow: null, freqBelow: null, errBelow: null
};

// --- Mathematical DSP Utilities ---

/**
 * Evaluates two-tone continuous reference signal: x(t) = A1 sin(2π f1 t) + A2 sin(2π f2 t)
 */
function evalSignal(t, f1 = state.f1, a1 = state.a1, f2 = state.f2, a2 = state.a2, tOffset = state.tOffset) {
    const time = t + tOffset;
    return a1 * Math.sin(2 * Math.PI * f1 * time) + a2 * Math.sin(2 * Math.PI * f2 * time);
}

/**
 * Normalized Sinc function: sinc(u) = sin(π u) / (π u)
 */
function sinc(u) {
    if (Math.abs(u) < 1e-9) return 1.0;
    const piU = Math.PI * u;
    return Math.sin(piU) / piU;
}

/**
 * Computes folded/aliased frequency in range [0, fs/2] for a component freq f
 */
function calculateAliasFrequency(f, fs) {
    const fn = fs / 2;
    // k fold index
    const k = Math.round(f / fs);
    const alias = Math.abs(f - k * fs);
    return alias;
}

/**
 * Fast Discrete Fourier Transform / Magnitude Spectrum
 */
function computeSpectrum(timeArray, signalArray, maxFreq = 40) {
    const N = signalArray.length;
    const dt = timeArray[1] - timeArray[0];
    const fsPlot = 1 / dt;
    const numFreqBins = 250;
    
    const freqs = [];
    const magnitudes = [];

    const df = maxFreq / numFreqBins;

    for (let k = 0; k < numFreqBins; k++) {
        const freq = k * df;
        let realSum = 0;
        let imagSum = 0;

        // Hann window function to minimize spectral leakage
        for (let n = 0; n < N; n++) {
            const w = 0.5 * (1 - Math.cos((2 * Math.PI * n) / (N - 1)));
            const angle = 2 * Math.PI * freq * timeArray[n];
            const val = signalArray[n] * w;
            realSum += val * Math.cos(angle);
            imagSum += val * Math.sin(angle);
        }

        // Hann window normalization factor = 2 / sum(w) ≈ 4/N
        const mag = (4 / N) * Math.sqrt(realSum * realSum + imagSum * imagSum);
        freqs.push(freq);
        magnitudes.push(mag);
    }

    return { freqs, magnitudes };
}

// --- Main Simulation Calculator ---

function runSimulation(params = state) {
    const { f1, a1, f2, a2, fs, fplot, tWindow } = params;

    // 1. Continuous High-Density Plotting Grid
    const numDense = Math.floor(tWindow * fplot);
    const dtPlot = tWindow / (numDense - 1);
    const tDense = new Float64Array(numDense);
    const xDense = new Float64Array(numDense);

    for (let i = 0; i < numDense; i++) {
        tDense[i] = i * dtPlot;
        xDense[i] = evalSignal(tDense[i], f1, a1, f2, a2);
    }

    // 2. Physical Discrete Sampler
    const Ts = 1 / fs;
    const numSamples = Math.floor(tWindow * fs) + 1;
    const tSamples = new Float64Array(numSamples);
    const xSamples = new Float64Array(numSamples);

    for (let n = 0; n < numSamples; n++) {
        tSamples[n] = n * Ts;
        xSamples[n] = evalSignal(tSamples[n], f1, a1, f2, a2);
    }

    // 3. Whittaker-Shannon Sinc Interpolation Reconstruction
    const xRecon = new Float64Array(numDense);
    const sincPulses = state.showSincPulses ? [] : null;

    for (let n = 0; n < numSamples; n++) {
        const tn = tSamples[n];
        const xn = xSamples[n];
        
        if (state.showSincPulses) {
            const pulse = new Float64Array(numDense);
            for (let i = 0; i < numDense; i++) {
                const u = (tDense[i] - tn) / Ts;
                pulse[i] = xn * sinc(u);
            }
            sincPulses.push(pulse);
        }

        for (let i = 0; i < numDense; i++) {
            const u = (tDense[i] - tn) / Ts;
            xRecon[i] += xn * sinc(u);
        }
    }

    // 4. Continuous Error Signal & Metrics
    const errorSignal = new Float64Array(numDense);
    let sumSqError = 0;
    let sumSqRef = 0;
    let maxAbsErr = 0;

    for (let i = 0; i < numDense; i++) {
        const err = xDense[i] - xRecon[i];
        errorSignal[i] = err;
        sumSqError += err * err;
        sumSqRef += xDense[i] * xDense[i];
        if (Math.abs(err) > maxAbsErr) maxAbsErr = Math.abs(err);
    }

    const rmse = Math.sqrt(sumSqError / numDense);
    const sdr = 10 * Math.log10(sumSqRef / (sumSqError + 1e-12));

    // 5. Spectra Computation
    const maxFreqPlot = Math.max(35, Math.max(f1, f2) * 2.2);
    const refSpectrum = computeSpectrum(tDense, xDense, maxFreqPlot);
    const reconSpectrum = computeSpectrum(tDense, xRecon, maxFreqPlot);

    // 6. Aliasing Analysis
    const fmax = Math.max(f1, f2);
    const nyquistRate = 2 * fmax;
    const alias1 = calculateAliasFrequency(f1, fs);
    const alias2 = calculateAliasFrequency(f2, fs);

    return {
        tDense, xDense,
        tSamples, xSamples,
        xRecon, sincPulses,
        errorSignal,
        rmse, sdr, maxAbsErr,
        nyquistRate,
        alias1, alias2,
        refSpectrum, reconSpectrum,
        numSamples
    };
}

// --- Chart Rendering & UI Updates ---

function initCharts() {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)';
    Chart.defaults.plugins.tooltip.borderColor = '#1e293b';
    Chart.defaults.plugins.tooltip.borderWidth = 1;

    // Common axis styling
    const getAxisConfig = (xTitle, yTitle) => ({
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { font: { size: 10 } },
        title: { display: true, text: xTitle, color: '#64748b', font: { size: 11 } }
    });

    // Chart 1: Time Domain Reference & Samples
    const ctx1 = document.getElementById('chart-time-sampled').getContext('2d');
    chartTimeSampled = new Chart(ctx1, {
        type: 'line',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: { ...getAxisConfig('Time t (seconds)'), type: 'linear' },
                y: { ...getAxisConfig('', 'Amplitude x(t)'), min: -3.0, max: 3.0 }
            },
            plugins: { legend: { display: false } }
        }
    });

    // Chart 2: Reconstructed Waveform
    const ctx2 = document.getElementById('chart-time-recon').getContext('2d');
    chartTimeRecon = new Chart(ctx2, {
        type: 'line',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: { ...getAxisConfig('Time t (seconds)'), type: 'linear' },
                y: { ...getAxisConfig('', 'Amplitude xᵣ(t)'), min: -3.0, max: 3.0 }
            },
            plugins: { legend: { display: false } }
        }
    });

    // Chart 3: Magnitude Spectra
    const ctx3 = document.getElementById('chart-freq-spectrum').getContext('2d');
    chartFreqSpectrum = new Chart(ctx3, {
        type: 'line',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: { ...getAxisConfig('Frequency f (Hz)'), type: 'linear' },
                y: { ...getAxisConfig('', 'Magnitude |X(f)|'), min: 0, max: 1.2 }
            },
            plugins: { legend: { display: true, labels: { boxWidth: 12, font: { size: 10 } } } }
        }
    });

    // Chart 4: Error Signal
    const ctx4 = document.getElementById('chart-error').getContext('2d');
    chartError = new Chart(ctx4, {
        type: 'line',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: { ...getAxisConfig('Time t (seconds)'), type: 'linear' },
                y: { ...getAxisConfig('', 'Error e(t)'), min: -2.0, max: 2.0 }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function updateSandboxUI() {
    const sim = runSimulation();

    // 1. Update Label Text & Badges
    document.getElementById('val-f1').textContent = `${state.f1.toFixed(1)} Hz`;
    document.getElementById('val-a1').textContent = state.a1.toFixed(1);
    document.getElementById('val-f2').textContent = `${state.f2.toFixed(1)} Hz`;
    document.getElementById('val-a2').textContent = state.a2.toFixed(1);
    document.getElementById('val-fs').textContent = `${state.fs.toFixed(1)} Hz`;
    document.getElementById('val-2fmax').textContent = `${sim.nyquistRate.toFixed(1)} Hz`;
    document.getElementById('val-fplot').textContent = `${state.fplot} Hz`;
    document.getElementById('val-twindow').textContent = `${state.tWindow.toFixed(1)} s`;

    document.getElementById('lbl-fs1').textContent = state.fs.toFixed(1);
    document.getElementById('lbl-fs2').textContent = (state.fs / 2).toFixed(1);
    document.getElementById('lbl-fplot').textContent = state.fplot;
    document.getElementById('lbl-nsamples').textContent = sim.numSamples;

    // Diagnostic Metrics
    const ratio = state.fs / sim.nyquistRate;
    document.getElementById('metric-ratio').textContent = `${ratio.toFixed(2)}×`;
    document.getElementById('metric-rmse').textContent = sim.rmse.toFixed(4);
    document.getElementById('metric-sdr').textContent = sim.sdr > 50 ? '> 50 dB' : `${sim.sdr.toFixed(1)} dB`;

    const statusEl = document.getElementById('metric-status');
    if (ratio > 1.02) {
        statusEl.textContent = 'Above Nyquist';
        statusEl.style.color = '#00e676';
    } else if (Math.abs(ratio - 1.0) <= 0.02) {
        statusEl.textContent = 'At Nyquist';
        statusEl.style.color = '#ffb703';
    } else {
        statusEl.textContent = 'Below Nyquist';
        statusEl.style.color = '#ff3366';
    }

    // Alias Breakdown
    const isAliased1 = Math.abs(sim.alias1 - state.f1) > 0.01;
    const isAliased2 = Math.abs(sim.alias2 - state.f2) > 0.01;
    
    document.getElementById('alias-details').innerHTML = `
        Tone 1 (${state.f1} Hz): <strong style="color: ${isAliased1 ? '#ff3366' : '#00e676'}">${sim.alias1.toFixed(1)} Hz ${isAliased1 ? '⚡ (Aliased)' : '(Preserved)'}</strong><br>
        Tone 2 (${state.f2} Hz): <strong style="color: ${isAliased2 ? '#ff3366' : '#00e676'}">${sim.alias2.toFixed(1)} Hz ${isAliased2 ? '⚡ (Aliased!)' : '(Preserved)'}</strong>
    `;

    // --- Prepare Chart Datasets ---

    // Array formatting helper
    const toPoints = (tArr, xArr) => {
        const pts = [];
        for (let i = 0; i < tArr.length; i++) {
            pts.push({ x: tArr[i], y: xArr[i] });
        }
        return pts;
    };

    // Stem plot generator
    const stemLines = [];
    if (state.showStemLines) {
        for (let n = 0; n < sim.tSamples.length; n++) {
            stemLines.push({ x: sim.tSamples[n], y: 0 });
            stemLines.push({ x: sim.tSamples[n], y: sim.xSamples[n] });
            stemLines.push({ x: null, y: null }); // break segment
        }
    }

    // Chart 1 Update: Reference & Stem Samples
    chartTimeSampled.data.datasets = [
        {
            label: 'Reference x(t)',
            data: toPoints(sim.tDense, sim.xDense),
            borderColor: '#00f2fe',
            borderWidth: 2,
            pointRadius: 0
        },
        {
            label: 'Stem Lines',
            data: stemLines,
            borderColor: 'rgba(0, 230, 118, 0.4)',
            borderWidth: 1.5,
            pointRadius: 0,
            showLine: true
        },
        {
            label: 'Samples x[n]',
            data: toPoints(sim.tSamples, sim.xSamples),
            backgroundColor: '#00e676',
            borderColor: '#ffffff',
            borderWidth: 1.5,
            pointRadius: 4,
            showLine: false
        }
    ];
    chartTimeSampled.update();

    // Chart 2 Update: Reconstructed Waveform
    const reconDatasets = [
        {
            label: 'Reference x(t)',
            data: toPoints(sim.tDense, sim.xDense),
            borderColor: '#00f2fe',
            borderWidth: 2,
            borderDash: [4, 4],
            pointRadius: 0
        },
        {
            label: 'Reconstructed xᵣ(t)',
            data: toPoints(sim.tDense, sim.xRecon),
            borderColor: '#ff0844',
            borderWidth: 2.5,
            pointRadius: 0
        }
    ];

    if (state.showSincPulses && sim.sincPulses) {
        sim.sincPulses.forEach((pulse, idx) => {
            reconDatasets.push({
                label: `Sinc ${idx}`,
                data: toPoints(sim.tDense, pulse),
                borderColor: 'rgba(138, 43, 226, 0.3)',
                borderWidth: 1,
                pointRadius: 0
            });
        });
    }

    chartTimeRecon.data.datasets = reconDatasets;
    chartTimeRecon.update();

    // Chart 3 Update: Frequency Spectra
    const refSpecPoints = sim.refSpectrum.freqs.map((f, i) => ({ x: f, y: sim.refSpectrum.magnitudes[i] }));
    const reconSpecPoints = sim.reconSpectrum.freqs.map((f, i) => ({ x: f, y: sim.reconSpectrum.magnitudes[i] }));

    chartFreqSpectrum.data.datasets = [
        {
            label: 'Reference Spectrum',
            data: refSpecPoints,
            borderColor: '#00f2fe',
            borderWidth: 2,
            pointRadius: 0
        },
        {
            label: 'Reconstructed Spectrum',
            data: reconSpecPoints,
            borderColor: '#ff0844',
            borderWidth: 2,
            borderDash: [3, 3],
            pointRadius: 0
        }
    ];
    chartFreqSpectrum.update();

    // Chart 4 Update: Error Signal
    chartError.data.datasets = [
        {
            label: 'Error e(t)',
            data: toPoints(sim.tDense, sim.errorSignal),
            borderColor: '#a855f7',
            backgroundColor: 'rgba(168, 85, 247, 0.1)',
            fill: true,
            borderWidth: 1.5,
            pointRadius: 0
        }
    ];
    chartError.update();

    // Update Python Script Export View
    updatePythonCodeView();
}

// --- 3-Case Comparison Matrix View Engine ---

function initComparisonMatrix() {
    const cases = [
        { key: 'Above', fs: 36.0, color: '#00e676' },
        { key: 'At', fs: 24.0, color: '#ffb703' },
        { key: 'Below', fs: 14.0, color: '#ff3366' }
    ];

    cases.forEach(c => {
        const sim = runSimulation({ ...state, fs: c.fs });

        const toPts = (tA, xA) => {
            const pts = [];
            for (let i = 0; i < tA.length; i++) pts.push({ x: tA[i], y: xA[i] });
            return pts;
        };

        // Time chart
        const ctxTime = document.getElementById(`chart-compare-time-${c.key.toLowerCase()}`).getContext('2d');
        compareCharts[`time${c.key}`] = new Chart(ctxTime, {
            type: 'line',
            data: {
                datasets: [
                    { data: toPts(sim.tDense, sim.xDense), borderColor: '#00f2fe', borderWidth: 1.5, borderDash: [3,3], pointRadius: 0 },
                    { data: toPts(sim.tDense, sim.xRecon), borderColor: c.color, borderWidth: 2, pointRadius: 0 },
                    { data: toPts(sim.tSamples, sim.xSamples), backgroundColor: '#ffffff', pointRadius: 2.5, showLine: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                scales: { x: { type: 'linear', display: false }, y: { min: -2.5, max: 2.5, ticks: { font: { size: 9 } } } },
                plugins: { legend: { display: false } }
            }
        });

        // Spectrum chart
        const ctxFreq = document.getElementById(`chart-compare-freq-${c.key.toLowerCase()}`).getContext('2d');
        const specPts = sim.reconSpectrum.freqs.map((f, i) => ({ x: f, y: sim.reconSpectrum.magnitudes[i] }));
        compareCharts[`freq${c.key}`] = new Chart(ctxFreq, {
            type: 'line',
            data: {
                datasets: [
                    { data: specPts, borderColor: c.color, borderWidth: 1.5, pointRadius: 0, fill: true, backgroundColor: `${c.color}22` }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                scales: { x: { type: 'linear', ticks: { font: { size: 9 } } }, y: { min: 0, max: 1.2, ticks: { font: { size: 9 } } } },
                plugins: { legend: { display: false } }
            }
        });

        // Error chart
        const ctxErr = document.getElementById(`chart-compare-err-${c.key.toLowerCase()}`).getContext('2d');
        compareCharts[`err${c.key}`] = new Chart(ctxErr, {
            type: 'line',
            data: {
                datasets: [
                    { data: toPts(sim.tDense, sim.errorSignal), borderColor: '#a855f7', borderWidth: 1.2, pointRadius: 0 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                scales: { x: { type: 'linear', ticks: { font: { size: 9 } } }, y: { min: -1.5, max: 1.5, ticks: { font: { size: 9 } } } },
                plugins: { legend: { display: false } }
            }
        });
    });
}

// --- Python Script Code Generator ---

function updatePythonCodeView() {
    const code = `"""
Digital Communication Lab: Two-Tone Signal Sampling, Aliasing & Sinc Reconstruction
===================================================================================
Signal: x(t) = A1*sin(2*pi*f1*t) + A2*sin(2*pi*f2*t)
Parameters: f1 = ${state.f1} Hz, f2 = ${state.f2} Hz, fs = ${state.fs} Hz
Nyquist Rate = 2 * max(f1, f2) = ${2 * Math.max(state.f1, state.f2)} Hz
"""

import numpy as np
import matplotlib.pyplot as plt

# --- 1. Signal & Sampling Parameters ---
f1, A1 = ${state.f1}, ${state.a1}  # Tone 1
f2, A2 = ${state.f2}, ${state.a2} # Tone 2
T_window = ${state.tWindow}  # Time window duration in seconds

# Physical sampling rates for 3 test cases
fs_cases = {
    'Above Nyquist (36 Hz)': 36.0,
    'At Nyquist (24 Hz)': 24.0,
    'Below Nyquist (14 Hz)': 14.0
}

# High-density plotting grid simulating continuous-time analog signal
f_plot = ${state.fplot}
t_dense = np.linspace(0, T_window, int(T_window * f_plot))

# Reference continuous two-tone signal
def two_tone_signal(t):
    return A1 * np.sin(2 * np.pi * f1 * t) + A2 * np.sin(2 * np.pi * f2 * t)

x_dense = two_tone_signal(t_dense)

# --- 2. Simulation & Sinc Reconstruction Loop ---
fig, axes = plt.subplots(3, 3, figsize=(14, 9), sharex='col')
fig.suptitle('Sampling Theorem & Sinc Interpolation Analysis', fontsize=14, fontweight='bold')

for idx, (title, fs) in enumerate(fs_cases.items()):
    Ts = 1.0 / fs
    t_samples = np.arange(0, T_window, Ts)
    x_samples = two_tone_signal(t_samples)

    # Whittaker-Shannon Sinc Interpolation
    # x_r(t) = sum_n x[n] * sinc((t - n*Ts) / Ts)
    # Note: np.sinc(u) computes sin(pi*u)/(pi*u)
    sinc_matrix = np.sinc((t_dense[:, None] - t_samples[None, :]) / Ts)
    x_recon = np.dot(sinc_matrix, x_samples)

    # Continuous error signal & RMSE
    error_signal = x_dense - x_recon
    rmse = np.sqrt(np.mean(error_signal**2))

    # --- Plotting Time Domain ---
    ax_time = axes[idx, 0]
    ax_time.plot(t_dense, x_dense, 'c--', label='Reference x(t)', alpha=0.7)
    ax_time.plot(t_dense, x_recon, 'm-', label='Reconstructed x_r(t)', lw=1.5)
    ax_time.stem(t_samples, x_samples, linefmt='g-', markerfmt='go', basefmt=' ', label='Samples x[n]')
    ax_time.set_title(f'{title} - Time Domain (RMSE={rmse:.4f})', fontsize=10)
    ax_time.set_ylabel('Amplitude')
    if idx == 0: ax_time.legend(fontsize=8)

    # --- Plotting Magnitude Spectrum (FFT) ---
    ax_freq = axes[idx, 1]
    N = len(x_recon)
    freqs = np.fft.rfftfreq(N, 1/f_plot)
    spectrum = np.abs(np.fft.rfft(x_recon * np.hanning(N))) * (4.0 / N)
    ax_freq.plot(freqs, spectrum, 'm-')
    ax_freq.set_xlim(0, 30)
    ax_freq.set_title(f'{title} - Magnitude Spectrum', fontsize=10)
    ax_freq.set_ylabel('|X(f)|')

    # --- Plotting Reconstruction Error ---
    ax_err = axes[idx, 2]
    ax_err.plot(t_dense, error_signal, 'r-')
    ax_err.set_title(f'{title} - Error e(t)', fontsize=10)
    ax_err.set_ylabel('Error')

axes[2, 0].set_xlabel('Time (s)')
axes[2, 1].set_xlabel('Frequency (Hz)')
axes[2, 2].set_xlabel('Time (s)')

plt.tight_layout()
plt.show()
`;

    document.getElementById('python-code-content').textContent = code;
}

function copyPythonCode() {
    const codeText = document.getElementById('python-code-content').textContent;
    navigator.clipboard.writeText(codeText).then(() => {
        const btnText = document.getElementById('copy-status');
        btnText.textContent = 'Copied to Clipboard! ✓';
        setTimeout(() => { btnText.textContent = 'Copy Python Script'; }, 2000);
    });
}

// --- Tab Navigation & Presets ---

function switchTab(tabId) {
    state.currentTab = tabId;

    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    document.getElementById(`tab-${tabId}`).classList.add('active');
    document.getElementById(`view-${tabId}`).classList.add('active');

    if (tabId === 'sandbox') {
        updateSandboxUI();
    }
}

function setPreset(presetName) {
    state.preset = presetName;
    document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`preset-${presetName}`).classList.add('active');

    state.f1 = 5.0;
    state.f2 = 12.0;
    document.getElementById('slider-f1').value = 5.0;
    document.getElementById('slider-f2').value = 12.0;

    const fmax = Math.max(state.f1, state.f2); // 12 Hz, Nyquist = 24 Hz

    if (presetName === 'above') {
        state.fs = 36.0;
    } else if (presetName === 'at') {
        state.fs = 24.0;
    } else if (presetName === 'below') {
        state.fs = 14.0;
    }

    document.getElementById('slider-fs').value = state.fs;
    updateSandboxUI();
}

// --- Wave Animation & Web Audio Synthesis Engine ---

let lastAnimTime = 0;

function toggleWaveAnimation() {
    state.isAnimating = !state.isAnimating;
    const btn = document.getElementById('btn-play-wave');
    const lbl = document.getElementById('lbl-play-wave');

    if (state.isAnimating) {
        btn.classList.add('running');
        lbl.textContent = 'Pause Wave';
        lastAnimTime = performance.now();
        requestAnimationFrame(animLoop);
    } else {
        btn.classList.remove('running');
        lbl.textContent = 'Run Wave';
    }
}

function animLoop(now) {
    if (!state.isAnimating) return;

    const dt = (now - lastAnimTime) / 1000;
    lastAnimTime = now;

    // Increment continuous time offset
    state.tOffset += dt * 0.25 * state.animSpeed;

    updateSandboxUI();
    requestAnimationFrame(animLoop);
}

// --- Web Audio Synthesis ---

function toggleAudio(type) {
    if (state.audioPlaying === type) {
        stopAudio();
        return;
    }

    stopAudio();
    state.audioPlaying = type;

    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }

    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }

    const sim = runSimulation();
    const baseFreq = 220; // A3 musical pitch reference (220 Hz)

    let tone1Freq = baseFreq;
    let tone2Freq = baseFreq * (state.f2 / state.f1);

    if (type === 'recon') {
        tone1Freq = baseFreq * (sim.alias1 / state.f1);
        tone2Freq = baseFreq * (sim.alias2 / state.f1);
    }

    const masterGain = audioCtx.createGain();
    masterGain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    masterGain.connect(audioCtx.destination);

    // Osc 1
    const osc1 = audioCtx.createOscillator();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(tone1Freq, audioCtx.currentTime);
    const g1 = audioCtx.createGain();
    g1.gain.setValueAtTime(state.a1, audioCtx.currentTime);
    osc1.connect(g1);
    g1.connect(masterGain);
    osc1.start();

    // Osc 2
    const osc2 = audioCtx.createOscillator();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(tone2Freq, audioCtx.currentTime);
    const g2 = audioCtx.createGain();
    g2.gain.setValueAtTime(state.a2, audioCtx.currentTime);
    osc2.connect(g2);
    g2.connect(masterGain);
    osc2.start();

    audioNodes = [osc1, osc2, masterGain];

    const btnRef = document.getElementById('btn-audio-ref');
    const btnRecon = document.getElementById('btn-audio-recon');

    if (type === 'ref') btnRef.classList.add('playing');
    if (type === 'recon') btnRecon.classList.add('playing');
}

function stopAudio() {
    audioNodes.forEach(node => {
        if (node.stop) node.stop();
        if (node.disconnect) node.disconnect();
    });
    audioNodes = [];
    state.audioPlaying = null;

    document.getElementById('btn-audio-ref').classList.remove('playing');
    document.getElementById('btn-audio-recon').classList.remove('playing');
}

// --- Event Listener Initialization ---

function initEventListeners() {
    const bindSlider = (id, key, fn = parseFloat) => {
        document.getElementById(id).addEventListener('input', (e) => {
            state[key] = fn(e.target.value);
            updateSandboxUI();
        });
    };

    bindSlider('slider-f1', 'f1');
    bindSlider('slider-a1', 'a1');
    bindSlider('slider-f2', 'f2');
    bindSlider('slider-a2', 'a2');
    bindSlider('slider-fs', 'fs');
    bindSlider('slider-fplot', 'fplot', parseInt);
    bindSlider('slider-twindow', 'tWindow');

    document.getElementById('slider-anim-speed').addEventListener('input', (e) => {
        state.animSpeed = parseFloat(e.target.value);
        document.getElementById('val-anim-speed').textContent = `${state.animSpeed.toFixed(1)}×`;
    });

    document.getElementById('chk-sinc-pulses').addEventListener('change', (e) => {
        state.showSincPulses = e.target.checked;
        updateSandboxUI();
    });

    document.getElementById('chk-stem-lines').addEventListener('change', (e) => {
        state.showStemLines = e.target.checked;
        updateSandboxUI();
    });
}

// Initial Bootstrapping
window.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initEventListeners();
    updateSandboxUI();
    initComparisonMatrix();
});
