/**
 * Uniform Quantization & PCM Web Studio — DSP Engine & Interactive Visualizer
 * Digital Communication Laboratory Suite
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. Global Application State
    // -------------------------------------------------------------------------
    const state = {
        bits: 4,
        amplitude: 1.0,
        frequency: 1.0,
        samplingRate: 1000,
        numSamples: 1000,
        mode: 'midrise', // 'midrise' or 'midtread'
        audioSource: 'quantized',
        audioActive: false,
        activeTab: 'tab-waveform',
        hoverSampleIdx: null
    };

    // Web Audio API Context
    let audioCtx = null;
    let audioNode = null;
    let gainNode = null;

    // Canvas Contexts
    const canvases = {
        waveform: document.getElementById('canvas-waveform'),
        staircase: document.getElementById('canvas-staircase'),
        errorWave: document.getElementById('canvas-error-wave'),
        errorHist: document.getElementById('canvas-error-hist'),
        sqnr: document.getElementById('canvas-sqnr')
    };

    // -------------------------------------------------------------------------
    // 2. Core DSP Math Algorithms
    // -------------------------------------------------------------------------

    /** Generate continuous-time normalized sinusoidal signal */
    function generateSignal() {
        const N = state.numSamples;
        const dt = 1.0 / state.samplingRate;
        const t = new Float64Array(N);
        const signal = new Float64Array(N);

        for (let k = 0; k < N; k++) {
            t[k] = k * dt;
            signal[k] = state.amplitude * Math.sin(2 * Math.PI * state.frequency * t[k]);
        }
        return { t, signal };
    }

    /** Mid-Rise / Mid-Tread Uniform Quantizer */
    function quantizeUniform(signal, bits, mode = 'midrise', minVal = -1.0, maxVal = 1.0) {
        const N = signal.length;
        const L = Math.pow(2, bits);
        const delta = (maxVal - minVal) / L;
        
        const quantized = new Float64Array(N);
        const indices = new Int32Array(N);
        const levels = new Float64Array(L);

        if (mode === 'midrise') {
            // Mid-rise quantization levels: q_i = minVal + (i + 0.5) * delta
            for (let i = 0; i < L; i++) {
                levels[i] = minVal + (i + 0.5) * delta;
            }
            for (let k = 0; k < N; k++) {
                let idx = Math.floor((signal[k] - minVal) / delta);
                if (idx < 0) idx = 0;
                if (idx >= L) idx = L - 1;
                indices[k] = idx;
                quantized[k] = levels[idx];
            }
        } else {
            // Mid-tread quantization: level at 0.0
            for (let i = 0; i < L; i++) {
                levels[i] = (i - L / 2) * delta;
            }
            for (let k = 0; k < N; k++) {
                let idx = Math.round(signal[k] / delta) + Math.floor(L / 2);
                if (idx < 0) idx = 0;
                if (idx >= L) idx = L - 1;
                indices[k] = idx;
                quantized[k] = levels[idx];
            }
        }

        return { quantized, indices, delta, levels, L };
    }

    /** Convert Integer Index to PCM Binary String */
    function pcmEncode(index, bits) {
        return index.toString(2).padStart(bits, '0');
    }

    /** Calculate Statistical Metrics: MSE, SQNR, Theory Comparison */
    function computeMetrics(signal, quantized, bits, delta) {
        const N = signal.length;
        let sumErrorSq = 0;
        let sumSignalSq = 0;
        let maxError = 0;
        const error = new Float64Array(N);

        for (let k = 0; k < N; k++) {
            const err = signal[k] - quantized[k];
            error[k] = err;
            sumErrorSq += err * err;
            sumSignalSq += signal[k] * signal[k];
            if (Math.abs(err) > maxError) {
                maxError = Math.abs(err);
            }
        }

        const mse = sumErrorSq / N;
        const px = sumSignalSq / N;
        const rmsError = Math.sqrt(mse);
        
        const sqnrSim = mse > 0 ? 10 * Math.log10(px / mse) : 99.9;
        const sqnrTheory = 6.02 * bits + 1.76;
        const diff = sqnrSim - sqnrTheory;
        const agrees = Math.abs(diff) <= 1.0;

        return {
            bits,
            levels: Math.pow(2, bits),
            delta,
            mse,
            maxError,
            rmsError,
            px,
            sqnrSim,
            sqnrTheory,
            diff,
            agrees,
            error
        };
    }

    // -------------------------------------------------------------------------
    // 3. Canvas 2D Rendering Engine
    // -------------------------------------------------------------------------

    function setupCanvasDPI(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        let w = rect.width;
        let h = rect.height;

        const defaultW = parseFloat(canvas.getAttribute('width')) || 900;
        const defaultH = parseFloat(canvas.getAttribute('height')) || 420;

        if (!w || w <= 0) w = defaultW;
        if (!h || h <= 0) h = defaultH;

        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);

        const ctx = canvas.getContext('2d');
        ctx.resetTransform();
        ctx.scale(dpr, dpr);
        return { ctx, width: w, height: h };
    }


    /** Draw Tab 1: Waveforms (Continuous vs Quantized Staircase) */
    function renderWaveformCanvas(t, signal, quantized, bits) {
        const { ctx, width, height } = setupCanvasDPI(canvases.waveform);
        ctx.clearRect(0, 0, width, height);

        const margin = { top: 30, right: 30, bottom: 40, left: 55 };
        const plotW = width - margin.left - margin.right;
        const plotH = height - margin.top - margin.bottom;

        // Render Grid & Axes
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let y = margin.top; y <= margin.top + plotH; y += plotH / 4) {
            ctx.moveTo(margin.left, y);
            ctx.lineTo(margin.left + plotW, y);
        }
        ctx.stroke();

        // Zero line
        const zeroY = margin.top + plotH / 2;
        ctx.strokeStyle = '#475569';
        ctx.beginPath();
        ctx.moveTo(margin.left, zeroY);
        ctx.lineTo(margin.left + plotW, zeroY);
        ctx.stroke();

        const numPoints = Math.min(signal.length, 300);
        const mapX = (idx) => margin.left + (idx / (numPoints - 1)) * plotW;
        const mapY = (val) => zeroY - (val / 1.25) * (plotH / 2);

        // 1. Continuous Reference Sinusoid
        ctx.strokeStyle = '#4facfe';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        for (let k = 0; k < numPoints; k++) {
            const x = mapX(k);
            const y = mapY(signal[k]);
            if (k === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // 2. Quantized Staircase Waveform (Steps)
        ctx.strokeStyle = '#ff7f0e';
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let k = 0; k < numPoints - 1; k++) {
            const x1 = mapX(k);
            const x2 = mapX(k + 1);
            const y = mapY(quantized[k]);
            ctx.moveTo(x1, y);
            ctx.lineTo(x2, y);
            // vertical transition
            const nextY = mapY(quantized[k + 1]);
            ctx.lineTo(x2, nextY);
        }
        ctx.stroke();

        // Interactive Hover Readout
        if (state.hoverSampleIdx !== null && state.hoverSampleIdx < numPoints) {
            const hIdx = state.hoverSampleIdx;
            const hX = mapX(hIdx);
            ctx.strokeStyle = '#00f2fe';
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(hX, margin.top);
            ctx.lineTo(hX, margin.top + plotH);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw point highlight
            ctx.fillStyle = '#ff7f0e';
            ctx.beginPath();
            ctx.arc(hX, mapY(quantized[hIdx]), 5, 0, 2 * Math.PI);
            ctx.fill();
        }

        // Axes Labels
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter';
        ctx.fillText('Time (s)', margin.left + plotW / 2 - 20, height - 10);
        ctx.fillText('+1.0 V', 15, margin.top + 10);
        ctx.fillText(' 0.0 V', 15, zeroY + 4);
        ctx.fillText('-1.0 V', 15, margin.top + plotH);
    }

    /** Draw Tab 2: Staircase Characteristic (x -> x_q) */
    function renderStaircaseCanvas(bits, mode) {
        const { ctx, width, height } = setupCanvasDPI(canvases.staircase);
        ctx.clearRect(0, 0, width, height);

        const margin = { top: 30, right: 30, bottom: 45, left: 55 };
        const plotW = width - margin.left - margin.right;
        const plotH = height - margin.top - margin.bottom;

        const zeroX = margin.left + plotW / 2;
        const zeroY = margin.top + plotH / 2;

        // Grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(margin.left, zeroY); ctx.lineTo(margin.left + plotW, zeroY);
        ctx.moveTo(zeroX, margin.top); ctx.lineTo(zeroX, margin.top + plotH);
        ctx.stroke();

        const mapX = (v) => zeroX + (v / 1.2) * (plotW / 2);
        const mapY = (v) => zeroY - (v / 1.2) * (plotH / 2);

        // Ideal Line x_q = x
        ctx.strokeStyle = '#aaaaaa';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(mapX(-1.0), mapY(-1.0));
        ctx.lineTo(mapX(1.0), mapY(1.0));
        ctx.stroke();
        ctx.setLineDash([]);

        // Staircase Characteristic
        const N = 1000;
        const xFine = new Float64Array(N);
        for (let i = 0; i < N; i++) {
            xFine[i] = -1.0 + (i / (N - 1)) * 2.0;
        }
        const { quantized: xqFine, delta, levels } = quantizeUniform(xFine, bits, mode);

        // Draw quantization level lines
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.15)';
        for (let l of levels) {
            const y = mapY(l);
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(margin.left + plotW, y);
            ctx.stroke();
        }

        // Draw staircase
        ctx.strokeStyle = '#e74c3c';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        for (let k = 0; k < N - 1; k++) {
            const x1 = mapX(xFine[k]);
            const x2 = mapX(xFine[k + 1]);
            const y = mapY(xqFine[k]);
            if (k === 0) ctx.moveTo(x1, y);
            else ctx.lineTo(x1, y);
            ctx.lineTo(x2, y);
        }
        ctx.stroke();

        // Labels
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter';
        ctx.fillText('Input Amplitude x (V)', zeroX - 50, height - 10);
        ctx.fillText('Quantized x_q (V)', 10, margin.top - 10);
    }

    /** Draw Tab 3: Error Waveform & Histogram */
    function renderErrorCanvas(t, error, delta) {
        // 1. Error Waveform
        const { ctx: ctxWave, width: wWave, height: hWave } = setupCanvasDPI(canvases.errorWave);
        ctxWave.clearRect(0, 0, wWave, hWave);
        
        const m = { top: 20, right: 20, bottom: 30, left: 45 };
        const pw = wWave - m.left - m.right;
        const ph = hWave - m.top - m.bottom;
        const zeroY = m.top + ph / 2;

        ctxWave.strokeStyle = '#1e293b';
        ctxWave.beginPath();
        ctxWave.moveTo(m.left, zeroY); ctxWave.lineTo(m.left + pw, zeroY);
        ctxWave.stroke();

        // Bounds +/- delta/2
        const mapY = (val) => zeroY - (val / (delta * 0.85)) * (ph / 2);
        ctxWave.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctxWave.setLineDash([3, 3]);
        ctxWave.beginPath();
        ctxWave.moveTo(m.left, mapY(delta / 2)); ctxWave.lineTo(m.left + pw, mapY(delta / 2));
        ctxWave.moveTo(m.left, mapY(-delta / 2)); ctxWave.lineTo(m.left + pw, mapY(-delta / 2));
        ctxWave.stroke();
        ctxWave.setLineDash([]);

        // Error trace
        const numP = Math.min(error.length, 300);
        ctxWave.strokeStyle = '#2ecc71';
        ctxWave.lineWidth = 1.5;
        ctxWave.beginPath();
        for (let k = 0; k < numP; k++) {
            const x = m.left + (k / (numP - 1)) * pw;
            const y = mapY(error[k]);
            if (k === 0) ctxWave.moveTo(x, y);
            else ctxWave.lineTo(x, y);
        }
        ctxWave.stroke();

        // 2. Error Histogram
        const { ctx: ctxHist, width: wHist, height: hHist } = setupCanvasDPI(canvases.errorHist);
        ctxHist.clearRect(0, 0, wHist, hHist);

        const numBins = 25;
        const bins = new Int32Array(numBins);
        const binWidth = delta / numBins;
        const minE = -delta / 2;

        for (let i = 0; i < error.length; i++) {
            let b = Math.floor((error[i] - minE) / binWidth);
            if (b < 0) b = 0;
            if (b >= numBins) b = numBins - 1;
            bins[b]++;
        }

        const maxCount = Math.max(...bins, 1);
        const barW = (wHist - m.left - m.right) / numBins;

        ctxHist.fillStyle = 'rgba(46, 204, 113, 0.6)';
        ctxHist.strokeStyle = '#1e293b';
        for (let b = 0; b < numBins; b++) {
            const h = (bins[b] / maxCount) * ph;
            const x = m.left + b * barW;
            const y = m.top + ph - h;
            ctxHist.fillRect(x, y, barW - 1, h);
        }

        // Ideal uniform PDF line
        ctxHist.strokeStyle = '#e74c3c';
        ctxHist.lineWidth = 2;
        const idealY = m.top + ph * 0.25;
        ctxHist.beginPath();
        ctxHist.moveTo(m.left, idealY);
        ctxHist.lineTo(m.left + pw, idealY);
        ctxHist.stroke();
    }

    /** Draw Tab 4: SQNR vs Bit Depth */
    function renderSQNRCanvas(currentBits) {
        const { ctx, width, height } = setupCanvasDPI(canvases.sqnr);
        ctx.clearRect(0, 0, width, height);

        const margin = { top: 30, right: 40, bottom: 45, left: 55 };
        const plotW = width - margin.left - margin.right;
        const plotH = height - margin.top - margin.bottom;

        const bitList = [2, 3, 4, 5, 6, 7, 8];
        const mapX = (b) => margin.left + ((b - 2) / 6) * plotW;
        const mapY = (sqnr) => margin.top + plotH - (sqnr / 60) * plotH;

        // Grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let s = 0; s <= 60; s += 10) {
            const y = mapY(s);
            ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotW, y);
        }
        ctx.stroke();

        // 1. Theoretical Line
        ctx.strokeStyle = '#e74c3c';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        for (let b of bitList) {
            const th = 6.02 * b + 1.76;
            const x = mapX(b);
            const y = mapY(th);
            if (b === 2) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // 2. Simulated Points & Line
        const dummySignal = generateSignal().signal;
        ctx.strokeStyle = '#4facfe';
        ctx.fillStyle = '#4facfe';
        ctx.lineWidth = 2.5;
        ctx.beginPath();

        for (let b of bitList) {
            const { quantized, delta } = quantizeUniform(dummySignal, b, state.mode);
            const metrics = computeMetrics(dummySignal, quantized, b, delta);
            const x = mapX(b);
            const y = mapY(metrics.sqnrSim);

            if (b === 2) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Draw markers
        for (let b of bitList) {
            const { quantized, delta } = quantizeUniform(dummySignal, b, state.mode);
            const metrics = computeMetrics(dummySignal, quantized, b, delta);
            const x = mapX(b);
            const y = mapY(metrics.sqnrSim);

            ctx.beginPath();
            ctx.arc(x, y, b === currentBits ? 7 : 4, 0, 2 * Math.PI);
            ctx.fillStyle = b === currentBits ? '#00f2fe' : '#4facfe';
            ctx.fill();

            if (b === currentBits) {
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // Value text
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px Fira Code';
            ctx.fillText(`${metrics.sqnrSim.toFixed(1)} dB`, x - 15, y - 10);
        }

        // Axis labels
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px Inter';
        ctx.fillText('Quantization Bit Depth (n)', margin.left + plotW / 2 - 60, height - 10);
        ctx.fillText('SQNR (dB)', 10, margin.top - 10);
    }

    // -------------------------------------------------------------------------
    // 4. Web Audio Synthesizer Engine
    // -------------------------------------------------------------------------

    function toggleAudio() {
        if (!state.audioActive) {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            audioCtx.resume();
            startAudioSynth();
            state.audioActive = true;
            document.getElementById('btn-audio-toggle').classList.add('active');
            document.getElementById('audio-btn-text').innerText = 'Synthesizer ON';
        } else {
            stopAudioSynth();
            state.audioActive = false;
            document.getElementById('btn-audio-toggle').classList.remove('active');
            document.getElementById('audio-btn-text').innerText = 'Synthesizer Off';
        }
    }

    function startAudioSynth() {
        if (!audioCtx) return;
        stopAudioSynth();

        const bufferSize = audioCtx.sampleRate * 2;
        const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const data = buffer.getChannelData(0);

        const freq = 440.0; // Audio pitch frequency for physical listening
        const { signal } = generateSignal();
        const { quantized, delta } = quantizeUniform(signal, state.bits, state.mode);
        const metrics = computeMetrics(signal, quantized, state.bits, delta);

        let sourceSignal = quantized;
        if (state.audioSource === 'reference') sourceSignal = signal;
        if (state.audioSource === 'error') sourceSignal = metrics.error;

        // Loop synthesized waveform into audio buffer
        for (let i = 0; i < bufferSize; i++) {
            const idx = Math.floor((i / audioCtx.sampleRate) * freq * state.numSamples) % state.numSamples;
            data[i] = sourceSignal[idx] * 0.3; // volume scale
        }

        audioNode = audioCtx.createBufferSource();
        audioNode.buffer = buffer;
        audioNode.loop = true;

        gainNode = audioCtx.createGain();
        gainNode.gain.value = 0.2;

        audioNode.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        audioNode.start();
    }

    function stopAudioSynth() {
        if (audioNode) {
            try { audioNode.stop(); audioNode.disconnect(); } catch (e) {}
            audioNode = null;
        }
    }

    // -------------------------------------------------------------------------
    // 5. DOM Update & Event Handling
    // -------------------------------------------------------------------------

    function updateApp() {
        // 1. Calculate DSP data
        const { t, signal } = generateSignal();
        const { quantized, indices, delta, levels, L } = quantizeUniform(signal, state.bits, state.mode);
        const metrics = computeMetrics(signal, quantized, state.bits, delta);

        // 2. Update Header & Sidebar Control Badges
        document.getElementById('val-bits').innerText = `${state.bits} Bits (L=${L})`;
        document.getElementById('val-amp').innerText = `${state.amplitude.toFixed(2)} V`;
        document.getElementById('val-freq').innerText = `${state.frequency.toFixed(1)} Hz`;
        document.getElementById('val-fs').innerText = `${state.samplingRate} Hz`;

        // 3. Update Metric Bar Cards
        document.getElementById('metric-levels').innerText = L;
        document.getElementById('metric-delta').innerText = `${delta.toFixed(4)} V`;
        document.getElementById('metric-mse').innerText = metrics.mse.toExponential(3);
        document.getElementById('metric-sqnr-sim').innerText = `${metrics.sqnrSim.toFixed(2)} dB`;
        document.getElementById('metric-sqnr-th').innerText = `${metrics.sqnrTheory.toFixed(2)} dB`;
        
        const diffElem = document.getElementById('metric-sqnr-diff');
        diffElem.innerText = `Diff: ${metrics.diff > 0 ? '+' : ''}${metrics.diff.toFixed(2)} dB`;

        const agreeElem = document.getElementById('metric-agreement');
        agreeElem.innerText = metrics.agrees ? 'YES' : 'NO';
        agreeElem.className = `metric-badge ${metrics.agrees ? 'pass' : 'fail'}`;

        // 4. Render Active Tab Canvas
        renderWaveformCanvas(t, signal, quantized, state.bits);
        renderStaircaseCanvas(state.bits, state.mode);
        renderErrorCanvas(t, metrics.error, delta);
        renderSQNRCanvas(state.bits);

        // 5. Update PCM Bitstream Table Inspector (First 16 samples)
        const tableBody = document.getElementById('pcm-table-body');
        tableBody.innerHTML = '';
        const count = Math.min(16, signal.length);

        for (let k = 0; k < count; k++) {
            const row = document.createElement('tr');
            const word = pcmEncode(indices[k], state.bits);
            const err = metrics.error[k];

            row.innerHTML = `
                <td>${k}</td>
                <td>${(t[k] * 1000).toFixed(2)} ms</td>
                <td>${signal[k].toFixed(4)} V</td>
                <td>${indices[k]}</td>
                <td><span class="pcm-word">${word}</span></td>
                <td>${quantized[k].toFixed(4)} V</td>
                <td>${err >= 0 ? '+' : ''}${err.toFixed(4)} V</td>
            `;
            tableBody.appendChild(row);
        }

        // Restart Audio if currently playing
        if (state.audioActive) {
            startAudioSynth();
        }
    }


    // -------------------------------------------------------------------------
    // 6. Bind Event Listeners
    // -------------------------------------------------------------------------

    // Range Sliders
    document.getElementById('slider-bits').addEventListener('input', (e) => {
        state.bits = parseInt(e.target.value);
        updateApp();
    });

    document.getElementById('slider-amp').addEventListener('input', (e) => {
        state.amplitude = parseFloat(e.target.value);
        updateApp();
    });

    document.getElementById('slider-freq').addEventListener('input', (e) => {
        state.frequency = parseFloat(e.target.value);
        updateApp();
    });

    document.getElementById('slider-fs').addEventListener('input', (e) => {
        state.samplingRate = parseInt(e.target.value);
        updateApp();
    });

    // Quantizer Convention Toggle
    document.getElementById('btn-midrise').addEventListener('click', () => {
        state.mode = 'midrise';
        document.getElementById('btn-midrise').classList.add('active');
        document.getElementById('btn-midtread').classList.remove('active');
        updateApp();
    });

    document.getElementById('btn-midtread').addEventListener('click', () => {
        state.mode = 'midtread';
        document.getElementById('btn-midtread').classList.add('active');
        document.getElementById('btn-midrise').classList.remove('active');
        updateApp();
    });

    // Audio Controls
    document.getElementById('btn-audio-toggle').addEventListener('click', toggleAudio);
    document.getElementById('select-audio-source').addEventListener('change', (e) => {
        state.audioSource = e.target.value;
        if (state.audioActive) startAudioSynth();
    });

    // Reset Defaults Button
    document.getElementById('btn-reset').addEventListener('click', () => {
        state.bits = 4;
        state.amplitude = 1.0;
        state.frequency = 1.0;
        state.samplingRate = 1000;
        state.mode = 'midrise';

        document.getElementById('slider-bits').value = 4;
        document.getElementById('slider-amp').value = 1.0;
        document.getElementById('slider-freq').value = 1.0;
        document.getElementById('slider-fs').value = 1000;
        document.getElementById('btn-midrise').classList.add('active');
        document.getElementById('btn-midtread').classList.remove('active');

        updateApp();
    });

    // Tab Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            state.activeTab = tabId;
            updateApp();
        });
    });

    // Save Canvas Image Button
    document.getElementById('btn-export-canvas').addEventListener('click', () => {
        let activeCanvas = canvases.waveform;
        if (state.activeTab === 'tab-staircase') activeCanvas = canvases.staircase;
        if (state.activeTab === 'tab-sqnr') activeCanvas = canvases.sqnr;

        const link = document.createElement('a');
        link.download = `pcm_quantization_${state.bits}bits_${state.activeTab}.png`;
        link.href = activeCanvas.toDataURL('image/png');
        link.click();
    });

    // Interactive Canvas Mouse Hover
    canvases.waveform.addEventListener('mousemove', (e) => {
        const rect = canvases.waveform.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const margin = { left: 55, right: 30 };
        const plotW = rect.width - margin.left - margin.right;
        
        if (mouseX >= margin.left && mouseX <= rect.width - margin.right) {
            const relX = (mouseX - margin.left) / plotW;
            const numP = 300;
            const idx = Math.floor(relX * numP);
            state.hoverSampleIdx = idx;

            const { signal } = generateSignal();
            const { quantized, indices } = quantizeUniform(signal, state.bits, state.mode);
            if (idx < signal.length) {
                const word = pcmEncode(indices[idx], state.bits);
                document.getElementById('hover-readout').innerText = 
                    `Sample #${idx} | x=${signal[idx].toFixed(3)}V | Index=${indices[idx]} | PCM: ${word} | x_q=${quantized[idx].toFixed(3)}V`;
            }
        } else {
            state.hoverSampleIdx = null;
            document.getElementById('hover-readout').innerText = 'Hover over canvas to inspect sample data';
        }
        updateApp();
    });

    canvases.waveform.addEventListener('mouseleave', () => {
        state.hoverSampleIdx = null;
        document.getElementById('hover-readout').innerText = 'Hover over canvas to inspect sample data';
        updateApp();
    });

    // Resize Window Handler
    window.addEventListener('resize', () => {
        updateApp();
    });

    // -------------------------------------------------------------------------
    // 7. Initial App Startup
    // -------------------------------------------------------------------------
    updateApp();
});
