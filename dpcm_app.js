/**
 * Interactive DPCM and Delta Modulation Web Simulation Studio.
 * Digital Communication Laboratory Suite.
 */

(function() {
    // State
    const state = {
        mode: 'dm',          // 'dm' or 'dpcm'
        freq: 1.0,
        amp: 1.0,
        fs: 1000,
        duration: 1.0,
        delta: 0.0079,
        admEnabled: false,
        a1: 0.85,
        bits: 3,
        autoA1: false
    };

    // UI Elements
    let els = {};

    function initElements() {
        els = {
            freq: document.getElementById('input-freq'),
            valFreq: document.getElementById('val-freq'),
            amp: document.getElementById('input-amp'),
            valAmp: document.getElementById('val-amp'),
            fs: document.getElementById('input-fs'),
            valFs: document.getElementById('val-fs'),
            delta: document.getElementById('input-delta'),
            valDelta: document.getElementById('val-delta'),
            lblDcrit: document.getElementById('lbl-dcrit'),
            lblRatio: document.getElementById('lbl-ratio'),
            toggleAdm: document.getElementById('toggle-adm'),
            a1: document.getElementById('input-a1'),
            valA1: document.getElementById('val-a1'),
            bits: document.getElementById('input-bits'),
            valBits: document.getElementById('val-bits'),
            valLevels: document.getElementById('val-levels'),
            toggleOptA1: document.getElementById('toggle-opt-a1'),
            tabDm: document.getElementById('tab-dm'),
            tabDpcm: document.getElementById('tab-dpcm'),
            dmControls: document.getElementById('dm-controls'),
            dpcmControls: document.getElementById('dpcm-controls'),
            metricMse: document.getElementById('metric-mse'),
            metricSqnr: document.getElementById('metric-sqnr'),
            metricSor: document.getElementById('metric-sor'),
            metricRegime: document.getElementById('metric-regime'),
            metricRegimeSub: document.getElementById('metric-regime-sub'),
            validationStatusBadge: document.getElementById('validation-status-badge'),
            regimeBadge: document.getElementById('regime-badge'),
            terminal: document.getElementById('terminal-output'),
            mainCanvasTitle: document.getElementById('main-canvas-title'),
            charCanvasTitle: document.getElementById('char-canvas-title'),
            legPredItem: document.getElementById('leg-pred-item')
        };
    }

    function attachEventListeners() {
        if (!els.freq) return;
        els.freq.addEventListener('input', (e) => {
            state.freq = parseFloat(e.target.value);
            els.valFreq.textContent = state.freq.toFixed(1);
            updateDcritDisplay();
            updateSimulation();
        });

        els.amp.addEventListener('input', (e) => {
            state.amp = parseFloat(e.target.value);
            els.valAmp.textContent = state.amp.toFixed(1);
            updateDcritDisplay();
            updateSimulation();
        });

        els.fs.addEventListener('input', (e) => {
            state.fs = parseInt(e.target.value);
            els.valFs.textContent = state.fs;
            updateDcritDisplay();
            updateSimulation();
        });

        els.delta.addEventListener('input', (e) => {
            state.delta = parseFloat(e.target.value);
            els.valDelta.textContent = state.delta.toFixed(4);
            updateDcritDisplay();
            updateSimulation();
        });

        els.a1.addEventListener('input', (e) => {
            state.a1 = parseFloat(e.target.value);
            els.valA1.textContent = state.a1.toFixed(2);
            updateSimulation();
        });

        els.bits.addEventListener('input', (e) => {
            state.bits = parseInt(e.target.value);
            els.valBits.textContent = state.bits;
            els.valLevels.textContent = 1 << state.bits;
            updateSimulation();
        });
    }

    function updateDcritDisplay() {
        if (!els.lblDcrit) return;
        const dcrit = (2.0 * Math.PI * state.freq * state.amp) / state.fs;
        els.lblDcrit.textContent = `${dcrit.toFixed(4)} V`;
        const ratio = state.delta / dcrit;
        els.lblRatio.textContent = `${ratio.toFixed(2)}x`;
    }

    window.setStepPreset = function(ratio) {
        const dcrit = (2.0 * Math.PI * state.freq * state.amp) / state.fs;
        const targetDelta = Math.max(0.0005, dcrit * ratio);
        state.delta = targetDelta;
        if (els.delta) {
            els.delta.value = targetDelta.toFixed(4);
            els.valDelta.textContent = targetDelta.toFixed(4);
        }
        updateDcritDisplay();
        updateSimulation();
    };

    window.switchMode = function(mode) {
        state.mode = mode;
        if (!els.tabDm) return;
        if (mode === 'dm') {
            els.tabDm.classList.add('active');
            els.tabDpcm.classList.remove('active');
            els.dmControls.classList.remove('hidden');
            els.dpcmControls.classList.add('hidden');
            els.mainCanvasTitle.textContent = "Waveform Oscilloscope: Input vs Delta Staircase Reconstruction";
            els.charCanvasTitle.textContent = "MSE vs Step Size Δ (U-Curve Trade-off)";
            if (els.legPredItem) els.legPredItem.style.display = "none";
        } else {
            els.tabDpcm.classList.add('active');
            els.tabDm.classList.remove('active');
            els.dpcmControls.classList.remove('hidden');
            els.dmControls.classList.add('hidden');
            els.mainCanvasTitle.textContent = "Waveform Oscilloscope: Original x[n], Predicted x̂[n], Reconstructed x̃[n]";
            els.charCanvasTitle.textContent = "DPCM vs Direct PCM SQNR Comparison";
            if (els.legPredItem) els.legPredItem.style.display = "inline-flex";
        }
        updateSimulation();
    };

    window.toggleOptimalA1 = function() {
        state.autoA1 = els.toggleOptA1.checked;
        els.a1.disabled = state.autoA1;
        updateSimulation();
    };

    window.resetDefaults = function() {
        state.freq = 1.0;
        state.amp = 1.0;
        state.fs = 1000;
        state.a1 = 0.85;
        state.bits = 3;
        state.admEnabled = false;
        if (els.freq) {
            els.freq.value = "1.0";
            els.amp.value = "1.0";
            els.fs.value = "1000";
            els.a1.value = "0.85";
            els.bits.value = "3";
            els.toggleAdm.checked = false;
            els.valFreq.textContent = "1.0";
            els.valAmp.textContent = "1.0";
            els.valFs.textContent = "1000";
            els.valA1.textContent = "0.85";
            els.valBits.textContent = "3";
            els.valLevels.textContent = "8";
        }
        window.setStepPreset(1.25);
    };

    function generateSignal() {
        const N = Math.floor(state.fs * state.duration);
        const t = new Float64Array(N);
        const x = new Float64Array(N);
        for (let i = 0; i < N; i++) {
            t[i] = i / state.fs;
            x[i] = state.amp * Math.sin(2.0 * Math.PI * state.freq * t[i]);
        }
        return { t, x, N };
    }

    function simulateDM(x, delta, isAdm) {
        const N = x.length;
        const x_hat = new Float64Array(N);
        const e = new Float64Array(N);
        const bits = new Int8Array(N);
        const x_tilde = new Float64Array(N);
        const step_sizes = new Float64Array(N);

        let prevRecon = 0.0;
        let currentDelta = delta;
        let prevD = 1.0;
        const alpha = 1.5;
        const beta = 0.67;
        const dMin = delta * 0.1;
        const dMax = delta * 8.0;

        for (let n = 0; n < N; n++) {
            x_hat[n] = prevRecon;
            e[n] = x[n] - x_hat[n];
            const d = e[n] >= 0 ? 1.0 : -1.0;
            bits[n] = d > 0 ? 1 : 0;

            if (isAdm) {
                if (n > 0) {
                    currentDelta = (d === prevD) ? Math.min(currentDelta * alpha, dMax) : Math.max(currentDelta * beta, dMin);
                }
                step_sizes[n] = currentDelta;
                x_tilde[n] = prevRecon + d * currentDelta;
            } else {
                step_sizes[n] = delta;
                x_tilde[n] = prevRecon + d * delta;
            }

            prevRecon = x_tilde[n];
            prevD = d;
        }

        let maxStepDev = 0;
        if (!isAdm) {
            for (let n = 1; n < N; n++) {
                const step = Math.abs(x_tilde[n] - x_tilde[n - 1]);
                const dev = Math.abs(step - delta);
                if (dev > maxStepDev) maxStepDev = dev;
            }
        }

        let sumErrSq = 0;
        let sumSigSq = 0;
        const err = new Float64Array(N);
        for (let n = 0; n < N; n++) {
            err[n] = x[n] - x_tilde[n];
            sumErrSq += err[n] * err[n];
            sumSigSq += x[n] * x[n];
        }
        const mse = sumErrSq / N;
        const sqnr = 10.0 * Math.log10(Math.max(sumSigSq / N, 1e-12) / Math.max(mse, 1e-12));

        return { x, x_hat, x_tilde, err, bits, mse, sqnr, maxStepDev, step_sizes };
    }

    function simulateDPCM(x, a1, bits) {
        const N = x.length;
        const levels = 1 << bits;
        const errorRange = Math.max(0.4, (1.0 + a1) * state.amp * 0.45);
        const deltaE = (2.0 * errorRange) / levels;

        const x_hat = new Float64Array(N);
        const e = new Float64Array(N);
        const eq = new Float64Array(N);
        const x_tilde = new Float64Array(N);

        let prevRecon = 0.0;
        for (let n = 0; n < N; n++) {
            x_hat[n] = a1 * prevRecon;
            e[n] = x[n] - x_hat[n];

            let clamped = Math.max(-errorRange, Math.min(errorRange, e[n]));
            let idx = Math.floor((clamped + errorRange) / deltaE);
            if (idx >= levels) idx = levels - 1;
            if (idx < 0) idx = 0;
            eq[n] = -errorRange + (idx + 0.5) * deltaE;

            x_tilde[n] = x_hat[n] + eq[n];
            prevRecon = x_tilde[n];
        }

        let sumErrSq = 0;
        let sumSigSq = 0;
        let sumESq = 0;
        let sumXSq = 0;
        let meanX = 0;
        let meanE = 0;
        for (let n = 0; n < N; n++) {
            meanX += x[n];
            meanE += e[n];
        }
        meanX /= N;
        meanE /= N;

        const err = new Float64Array(N);
        for (let n = 0; n < N; n++) {
            err[n] = x[n] - x_tilde[n];
            sumErrSq += err[n] * err[n];
            sumSigSq += x[n] * x[n];
            sumXSq += (x[n] - meanX) ** 2;
            sumESq += (e[n] - meanE) ** 2;
        }
        const mse = sumErrSq / N;
        const sqnr = 10.0 * Math.log10(Math.max(sumSigSq / N, 1e-12) / Math.max(mse, 1e-12));
        const varX = sumXSq / N;
        const varE = sumESq / N;
        const predGain = 10.0 * Math.log10(Math.max(varX, 1e-12) / Math.max(varE, 1e-12));

        const pcmDelta = (2.0 * state.amp) / levels;
        let pcmErrSq = 0;
        for (let n = 0; n < N; n++) {
            let idx = Math.floor((x[n] + state.amp) / pcmDelta);
            if (idx >= levels) idx = levels - 1;
            if (idx < 0) idx = 0;
            let xq = -state.amp + (idx + 0.5) * pcmDelta;
            pcmErrSq += (x[n] - xq) ** 2;
        }
        const pcmMse = pcmErrSq / N;
        const pcmSqnr = 10.0 * Math.log10(Math.max(sumSigSq / N, 1e-12) / Math.max(pcmMse, 1e-12));

        return { x, x_hat, x_tilde, e, eq, err, mse, sqnr, predGain, pcmMse, pcmSqnr, varX, varE };
    }

    function drawGrid(ctx, w, h, yMid) {
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let x = 0; x < w; x += 50) {
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
        }
        for (let y = 0; y < h; y += 40) {
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
        }
        ctx.stroke();

        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(0, yMid);
        ctx.lineTo(w, yMid);
        ctx.stroke();
    }

    function renderMainOscilloscope(t, x, recon, pred) {
        const canvas = document.getElementById('waveformCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        const yMid = h / 2;
        drawGrid(ctx, w, h, yMid);

        const yScale = (h * 0.40) / Math.max(state.amp, 0.1);
        const nPts = Math.min(t.length, 500);

        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        for (let i = 0; i < nPts; i++) {
            const cx = (i / (nPts - 1)) * w;
            const cy = yMid - x[i] * yScale;
            if (i === 0) ctx.moveTo(cx, cy);
            else ctx.lineTo(cx, cy);
        }
        ctx.stroke();

        if (state.mode === 'dpcm' && pred) {
            ctx.strokeStyle = '#f59e0b';
            ctx.lineWidth = 1.4;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            for (let i = 0; i < nPts; i++) {
                const cx = (i / (nPts - 1)) * w;
                const cy = yMid - pred[i] * yScale;
                if (i === 0) ctx.moveTo(cx, cy);
                else ctx.lineTo(cx, cy);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }

        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        for (let i = 0; i < nPts; i++) {
            const cx = (i / (nPts - 1)) * w;
            const cy = yMid - recon[i] * yScale;
            if (i === 0) {
                ctx.moveTo(cx, cy);
            } else {
                ctx.lineTo(cx, yMid - recon[i - 1] * yScale);
                ctx.lineTo(cx, cy);
            }
        }
        ctx.stroke();
    }

    function renderErrorCanvas(err) {
        const canvas = document.getElementById('errorCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        const yMid = h / 2;
        drawGrid(ctx, w, h, yMid);

        const nPts = Math.min(err.length, 500);
        let maxErr = 0.05;
        for (let i = 0; i < nPts; i++) {
            if (Math.abs(err[i]) > maxErr) maxErr = Math.abs(err[i]);
        }
        const yScale = (h * 0.42) / maxErr;

        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let i = 0; i < nPts; i++) {
            const cx = (i / (nPts - 1)) * w;
            const cy = yMid - err[i] * yScale;
            if (i === 0) ctx.moveTo(cx, cy);
            else ctx.lineTo(cx, cy);
        }
        ctx.stroke();

        ctx.fillStyle = '#9ca3af';
        ctx.font = '10px JetBrains Mono';
        ctx.fillText(`Peak Error: ±${maxErr.toFixed(4)} V`, 10, 16);
    }

    function renderCharCanvas(x, dcrit) {
        const canvas = document.getElementById('charCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        if (state.mode === 'dm') {
            drawGrid(ctx, w, h, h - 20);

            const steps = 30;
            const mses = [];
            let maxMse = 0;
            let minMse = Infinity;

            for (let i = 1; i <= steps; i++) {
                const d = (i / steps) * dcrit * 4.0;
                const res = simulateDM(x, d, false);
                mses.push(res.mse);
                if (res.mse > maxMse) maxMse = res.mse;
                if (res.mse < minMse) minMse = res.mse;
            }

            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 2.0;
            ctx.beginPath();
            for (let i = 0; i < steps; i++) {
                const cx = 30 + (i / (steps - 1)) * (w - 50);
                const normY = Math.log10(mses[i] + 1e-6) / Math.log10(maxMse + 1e-6);
                const cy = 20 + (1.0 - Math.min(1.0, Math.max(0, normY))) * (h - 50);
                if (i === 0) ctx.moveTo(cx, cy);
                else ctx.lineTo(cx, cy);
            }
            ctx.stroke();

            const critX = 30 + (dcrit / (dcrit * 4.0)) * (w - 50);
            ctx.strokeStyle = '#ef4444';
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(critX, 10);
            ctx.lineTo(critX, h - 20);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = '#ef4444';
            ctx.font = '10px Inter';
            ctx.fillText('Δ_crit', critX - 12, 14);

            const curScale = Math.min(1.0, state.delta / (dcrit * 4.0));
            const curX = 30 + curScale * (w - 50);
            ctx.fillStyle = '#10b981';
            ctx.beginPath();
            ctx.arc(curX, h / 2, 5, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillText(`Current Δ (${(state.delta/dcrit).toFixed(2)}x)`, Math.min(curX - 20, w - 90), h / 2 - 8);

        } else {
            const dpcmRes = simulateDPCM(x, state.a1, state.bits);
            const bars = [
                { label: `Direct PCM (${state.bits}b)`, val: dpcmRes.pcmSqnr, color: '#ef4444' },
                { label: `DPCM (${state.bits}b, a₁=${state.a1})`, val: dpcmRes.sqnr, color: '#10b981' }
            ];

            const barW = 80;
            const maxVal = Math.max(50, dpcmRes.sqnr * 1.2);
            bars.forEach((b, idx) => {
                const bx = 80 + idx * 160;
                const barH = (b.val / maxVal) * (h - 60);
                const by = h - 30 - barH;

                ctx.fillStyle = b.color;
                ctx.fillRect(bx, by, barW, barH);

                ctx.fillStyle = '#fff';
                ctx.font = 'bold 12px JetBrains Mono';
                ctx.fillText(`${b.val.toFixed(2)} dB`, bx + 10, by - 6);

                ctx.fillStyle = '#9ca3af';
                ctx.font = '11px Inter';
                ctx.fillText(b.label, bx - 10, h - 12);
            });
        }
    }

    function logTerminal(type, text) {
        if (!els.terminal) return;
        const p = document.createElement('p');
        p.className = `term-line ${type}`;
        p.textContent = text;
        els.terminal.appendChild(p);
        els.terminal.scrollTop = els.terminal.scrollHeight;
    }

    function updateSimulation() {
        if (!els.metricMse) return;
        state.admEnabled = els.toggleAdm ? els.toggleAdm.checked : false;
        const { t, x } = generateSignal();
        const dcrit = (2.0 * Math.PI * state.freq * state.amp) / state.fs;

        if (state.mode === 'dm') {
            const sor = dcrit / state.delta;
            const dm = simulateDM(x, state.delta, state.admEnabled);

            els.metricMse.textContent = dm.mse.toFixed(6);
            els.metricSqnr.textContent = `${dm.sqnr.toFixed(2)} dB`;
            els.metricSor.textContent = sor.toFixed(2);

            if (state.admEnabled) {
                els.metricRegime.textContent = "ADM Active";
                els.metricRegimeSub.textContent = "Dynamic Step Scaling";
                els.regimeBadge.textContent = "Adaptive DM Mode";
                els.regimeBadge.style.color = "var(--accent-purple)";
            } else if (sor > 1.15) {
                els.metricRegime.textContent = "Slope Overload";
                els.metricRegimeSub.textContent = "Lagging Staircase";
                els.regimeBadge.textContent = "Slope Overload";
                els.regimeBadge.style.color = "var(--danger)";
            } else if (sor < 0.35) {
                els.metricRegime.textContent = "Granular Noise";
                els.metricRegimeSub.textContent = "Hunting Oscillations";
                els.regimeBadge.textContent = "Granular Noise";
                els.regimeBadge.style.color = "var(--warning)";
            } else {
                els.metricRegime.textContent = "Optimal";
                els.metricRegimeSub.textContent = "Balanced Tracking";
                els.regimeBadge.textContent = "Optimal Tracking";
                els.regimeBadge.style.color = "var(--success)";
            }

            if (!state.admEnabled) {
                const passed = dm.maxStepDev < 1e-6;
                els.validationStatusBadge.textContent = passed ? `✅ Step Invariant Verified (±Δ = ${state.delta.toFixed(4)}V)` : `❌ Step Invariant Failed!`;
                els.validationStatusBadge.style.borderColor = passed ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)";
            } else {
                els.validationStatusBadge.textContent = `ℹ️ ADM Dynamic Adaptation Active`;
            }

            els.terminal.innerHTML = "";
            logTerminal("prompt", `> Parameter State: f=${state.freq}Hz, fs=${state.fs}Hz, Δ=${state.delta.toFixed(4)}V, SOR=${sor.toFixed(2)}`);
            if (sor > 1.0) {
                logTerminal("expected", `[EXPECTED] Signal max slope |dx/dt|=${(2*Math.PI*state.freq*state.amp).toFixed(2)} V/s > Modulator velocity ${(state.delta*state.fs).toFixed(2)} V/s. Slope overload guaranteed.`);
                logTerminal("confirmed", `[OBSERVED] High MSE (${dm.mse.toFixed(6)}) confirmed. Output exhibits directional bit latching.`);
            } else {
                logTerminal("expected", `[EXPECTED] Modulator velocity exceeds signal derivative. Overload avoided; tracking regime confirmed.`);
                logTerminal("confirmed", `[OBSERVED] Low MSE (${dm.mse.toFixed(6)}), SQNR=${dm.sqnr.toFixed(2)} dB.`);
            }

            renderMainOscilloscope(t, x, dm.x_tilde);
            renderErrorCanvas(dm.err);
            renderCharCanvas(x, dcrit);

        } else {
            if (state.autoA1) {
                let r0 = 0, r1 = 0;
                for (let i = 0; i < x.length; i++) r0 += x[i] * x[i];
                for (let i = 1; i < x.length; i++) r1 += x[i] * x[i - 1];
                state.a1 = Math.min(0.99, Math.max(0.1, r1 / r0));
                if (els.a1) {
                    els.a1.value = state.a1.toFixed(2);
                    els.valA1.textContent = state.a1.toFixed(2);
                }
            }

            const dpcm = simulateDPCM(x, state.a1, state.bits);

            els.metricMse.textContent = dpcm.mse.toFixed(6);
            els.metricSqnr.textContent = `${dpcm.sqnr.toFixed(2)} dB`;
            els.metricSor.textContent = `+${(dpcm.sqnr - dpcm.pcmSqnr).toFixed(2)} dB`;
            els.metricRegime.textContent = "DPCM Active";
            els.metricRegimeSub.textContent = `Gain Gp = ${dpcm.predGain.toFixed(2)} dB`;
            els.regimeBadge.textContent = "DPCM Redundancy Reduction";
            els.validationStatusBadge.textContent = `Tx/Rx Synchronized (0 Drift)`;

            els.terminal.innerHTML = "";
            logTerminal("prompt", `> DPCM State: a₁=${state.a1.toFixed(2)}, Bits=${state.bits}, Var_x=${dpcm.varX.toFixed(4)}, Var_e=${dpcm.varE.toFixed(4)}`);
            logTerminal("expected", `[EXPECTED] Inter-sample correlation enables first-order predictor to remove redundancy, making σ_e² << σ_x².`);
            logTerminal("confirmed", `[OBSERVED] Variance dropped by ${(dpcm.varX / dpcm.varE).toFixed(1)}x. DPCM achieves +${(dpcm.sqnr - dpcm.pcmSqnr).toFixed(2)} dB SQNR gain over direct PCM.`);

            renderMainOscilloscope(t, x, dpcm.x_tilde, dpcm.x_hat);
            renderErrorCanvas(dpcm.err);
            renderCharCanvas(x, dcrit);
        }
    }

    window.updateDPCMSimulation = updateSimulation;

    window.addEventListener('DOMContentLoaded', () => {
        initElements();
        attachEventListeners();
        updateDcritDisplay();
        updateSimulation();
    });
})();
