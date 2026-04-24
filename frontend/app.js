/**
 * app.js — PhishShield Frontend (CONTINUOUS STREAMING VERSION)
 * 
 * CRITICAL FIXES:
 * - WebSocket created ONCE, stays open
 * - MediaRecorder starts ONCE with timeslice=2000
 * - ondataavailable fires automatically every 2 seconds
 * - NO stop/restart cycle
 * - TRUE continuous streaming
 */

// ─── Configuration ────────────────────────────────────────────────────────────
const WS_URL = "ws://localhost:8000/ws/analyze";

// ─── State ────────────────────────────────────────────────────────────────────
let mediaRecorder = null;
let audioStream = null;
let websocket = null;
let callTimer = null;
let callSeconds = 0;
let chunkCount = 0;
let isListening = false;
let historyRows = [];
let audioContext = null;
let analyzerNode = null;
let waveformAnimFrame = null;

// ─── DOM References ───────────────────────────────────────────────────────────
const btnStart = document.getElementById("btn-start");
const btnStop = document.getElementById("btn-stop");
const statusPill = document.getElementById("status-pill");
const statusText = document.getElementById("status-text");
const timerDisplay = document.getElementById("timer-display");
const transcriptText = document.getElementById("transcript-text");
const chunkCounter = document.getElementById("chunk-counter");
const flagsGrid = document.getElementById("flags-grid");
const historyTbody = document.getElementById("history-tbody");
const waveformCanvas = document.getElementById("waveform-canvas");
const waveBars = document.getElementById("wave-bars");
const waveformStatus = document.getElementById("waveform-status");
const micError = document.getElementById("mic-error");
const wsStatusEl = document.getElementById("ws-status");

const gaugeWrapper = document.getElementById("gauge-wrapper");
const gaugeFill = document.getElementById("gauge-fill");
const gaugeScore = document.getElementById("gauge-score");
const gaugeLevel = document.getElementById("gauge-level");

const voiceBar = document.getElementById("voice-bar");
const contentBar = document.getElementById("content-bar");
const voiceVal = document.getElementById("voice-val");
const contentVal = document.getElementById("content-val");
const categoryTag = document.getElementById("category-tag");
const recommendationBox = document.getElementById("recommendation-box");
const recommendationText = document.getElementById("recommendation-text");

const alertBanner = document.getElementById("alert-banner");
const alertInner = document.getElementById("alert-inner");
const alertTitle = document.getElementById("alert-title");
const alertSubtitle = document.getElementById("alert-subtitle");
const alertIcon = document.getElementById("alert-icon");

const GAUGE_CIRCUMFERENCE = 565.49;
const MAX_HISTORY_ROWS = 5;

// ─── Waveform Visualization ───────────────────────────────────────────────────

function setupWaveformVisualizer(stream) {
  if (!stream) return;

  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  analyzerNode = audioContext.createAnalyser();
  analyzerNode.fftSize = 1024;
  analyzerNode.smoothingTimeConstant = 0.8;

  const source = audioContext.createMediaStreamSource(stream);
  source.connect(analyzerNode);

  const bufferLength = analyzerNode.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  const ctx = waveformCanvas.getContext("2d");

  waveBars.style.display = "none";
  waveformCanvas.style.display = "block";

  function draw() {
    waveformAnimFrame = requestAnimationFrame(draw);
    analyzerNode.getByteTimeDomainData(dataArray);

    const W = waveformCanvas.width;
    const H = waveformCanvas.height;

    ctx.fillStyle = "rgba(11, 17, 30, 0.4)";
    ctx.fillRect(0, 0, W, H);

    ctx.lineWidth = 2;
    ctx.strokeStyle = "#3b82f6";
    ctx.shadowBlur = 8;
    ctx.shadowColor = "#2563eb";
    ctx.beginPath();

    const sliceWidth = W / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * H) / 2;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      x += sliceWidth;
    }

    ctx.lineTo(W, H / 2);
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  draw();
}

function stopWaveformVisualizer() {
  if (waveformAnimFrame) {
    cancelAnimationFrame(waveformAnimFrame);
    waveformAnimFrame = null;
  }
  if (audioContext) {
    audioContext.close().catch(() => {});
    audioContext = null;
    analyzerNode = null;
  }
  waveBars.style.display = "flex";
  waveformCanvas.style.display = "none";
  const bars = waveBars.querySelectorAll(".wave-bar");
  bars.forEach(bar => bar.classList.add("idle"));
}

// ─── WebSocket Management ─────────────────────────────────────────────────────

function connectWebSocket() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    console.log("✅ WebSocket already open");
    return;
  }

  console.log("🔌 Connecting WebSocket...");
  websocket = new WebSocket(WS_URL);
  setWsStatus("Connecting...", "var(--warn)");

  websocket.onopen = () => {
    console.log("✅ WebSocket connected");
    setWsStatus("Connected", "var(--safe)");

    // 🔥 START MEDIARECORDER ONLY AFTER WEBSOCKET IS OPEN
    if (audioStream && isListening) {
      startMediaRecorder();
    }
  };

  websocket.onmessage = (event) => {
    try {
      const result = JSON.parse(event.data);
      console.log("📨 WebSocket message received:", result);
      handleAnalysisResult(result);
    } catch (err) {
      console.error("❌ Failed to parse WebSocket message:", err);
      console.error("Raw data:", event.data);
    }
  };

  websocket.onerror = (err) => {
    console.error("❌ WebSocket error:", err);
    setWsStatus("Connection error", "var(--crit)");
  };

  websocket.onclose = (event) => {
    console.warn(`WebSocket closed: code=${event.code}`);
    setWsStatus("Disconnected", "var(--text-muted)");

    // Only stop if unexpected close (not user-initiated)
    if (isListening && event.code !== 1000) {
      console.warn("⚠️ Unexpected WebSocket close");
      stopListening();
    }
  };
}

function setWsStatus(text, color) {
  if (wsStatusEl) {
    wsStatusEl.textContent = `WebSocket: ${text}`;
    wsStatusEl.style.color = color || "var(--text-muted)";
  }
}

// ─── MediaRecorder Management ─────────────────────────────────────────────────

function startMediaRecorder() {
  if (!audioStream) {
    console.error("❌ No audio stream available");
    return;
  }

  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    console.warn("⚠️ MediaRecorder already running");
    return;
  }

  const options = { mimeType: "audio/webm" };
  mediaRecorder = new MediaRecorder(audioStream, options);

  // 🔥 CRITICAL: This fires automatically every 2 seconds
  mediaRecorder.ondataavailable = async (event) => {
    if (!event.data || event.data.size === 0) {
      console.warn("⚠️ Empty audio chunk");
      return;
    }

    chunkCount++;
    console.log(`🎤 Chunk #${chunkCount}: ${event.data.size} bytes`);

    // Send to backend
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      try {
        websocket.send(event.data);
        console.log(`📤 Sent chunk #${chunkCount}`);
      } catch (err) {
        console.error(`❌ Failed to send chunk #${chunkCount}:`, err);
      }
    } else {
      console.error(`❌ WebSocket not open (state: ${websocket?.readyState})`);
    }

    // 🔥 DO NOT STOP OR RESTART — MediaRecorder continues automatically
  };

  mediaRecorder.onerror = (event) => {
    console.error("❌ MediaRecorder error:", event.error);
  };

  mediaRecorder.onstop = () => {
    console.log("⏹️ MediaRecorder stopped");
  };

  // 🔥 START WITH TIMESLICE = 3000ms (3 seconds for better audio quality)
  // ondataavailable will fire every 3 seconds automatically
  mediaRecorder.start(3000);
  console.log("🚀 MediaRecorder started (3-second chunks, continuous)");
}

// ─── Recording Controls ───────────────────────────────────────────────────────

async function startListening() {
  if (isListening) {
    console.warn("⚠️ Already listening");
    return;
  }

  console.log("🎙️ Starting listening...");
  isListening = true;
  chunkCount = 0;

  micError.classList.remove("visible");

  // Request microphone
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      }
    });
    console.log("✅ Microphone access granted");
  } catch (err) {
    console.error("❌ Microphone access denied:", err);
    micError.classList.add("visible");
    isListening = false;
    return;
  }

  // Set up waveform
  setupWaveformVisualizer(audioStream);

  const bars = waveBars.querySelectorAll(".wave-bar");
  bars.forEach(bar => bar.classList.remove("idle"));

  // Start timer
  callSeconds = 0;
  callTimer = setInterval(() => {
    callSeconds++;
    updateTimer(callSeconds);
  }, 1000);

  // Update UI
  setStatus("listening");
  btnStart.disabled = true;
  btnStop.disabled = false;
  waveformStatus.textContent = "Recording...";
  timerDisplay.classList.add("active");
  updateWaveformActive(true);

  // 🎨 Add recording class to body to trigger animations
  document.body.classList.add('recording');

  // 🔥 Connect WebSocket (MediaRecorder starts in websocket.onopen)
  connectWebSocket();
}

function stopListening() {
  console.log("⏹️ Stopping listening...");
  isListening = false;

  // Stop MediaRecorder
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  mediaRecorder = null;

  // Stop microphone
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop());
    audioStream = null;
  }

  // Clear timer
  clearInterval(callTimer);
  callTimer = null;

  // Stop waveform
  stopWaveformVisualizer();
  waveformStatus.textContent = "Stopped";

  // Update UI
  setStatus("idle");
  btnStart.disabled = false;
  btnStop.disabled = true;
  timerDisplay.classList.remove("active");
  updateWaveformActive(false);

  // 🎨 Remove recording and fraud-detected classes from body
  document.body.classList.remove('recording');
  document.body.classList.remove('fraud-detected');

  // Close WebSocket
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.close(1000, "User stopped listening");
  }

  console.log(`✅ Session ended: ${chunkCount} chunks, ${callSeconds}s`);
}

// ─── UI Update Functions ──────────────────────────────────────────────────────

function setStatus(state) {
  statusPill.className = `status-pill ${state}`;
  const labels = { idle: "IDLE", listening: "LISTENING", analyzing: "ANALYZING" };
  statusText.textContent = labels[state] || state.toUpperCase();
}

function updateTimer(seconds) {
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  timerDisplay.textContent = `${mins}:${secs}`;
}

function handleAnalysisResult(result) {
  // 🔥 Log every result for debugging
  console.log("📊 Analysis Result:", result);
  
  // 🔥 Skip keepalive messages (don't update UI for empty chunks)
  if (result.is_keepalive) {
    console.log("⏳ Keepalive received, waiting for speech...");
    return;
  }
  
  if (isListening) setStatus("listening");

  const score = result.final_score_pct ?? Math.round((result.final_score ?? 0) * 100);
  const riskLevel = result.risk_level ?? "SAFE";
  const color = result.color ?? "green";
  
  // 🎨 Toggle fraud-detected class based on score
  if (score >= 60) {
    document.body.classList.add('fraud-detected');
  } else {
    document.body.classList.remove('fraud-detected');
  }
  
  // 🔥 Log score update with full details
  console.log(`🎯 Updating UI: Score=${score}%, Level=${riskLevel}, Color=${color}`);
  console.log(`   Raw scores: final_score=${result.final_score}, final_score_pct=${result.final_score_pct}`);
  console.log(`   Voice: ${result.voice_fraud_score}, Content: ${result.content_fraud_score}`);

  // 🔥 ALWAYS update gauge (even for 0%) - FORCE REFRESH
  console.log(`   Calling updateGauge with: score=${score}, level=${riskLevel}, color=${color}`);
  updateGauge(score, riskLevel, color);
  
  // 🔥 Double-check gauge was updated
  setTimeout(() => {
    const currentScore = gaugeScore ? gaugeScore.textContent : 'NOT FOUND';
    const currentLevel = gaugeLevel ? gaugeLevel.textContent : 'NOT FOUND';
    console.log(`   Gauge after update: score=${currentScore}, level=${currentLevel}`);
  }, 100);

  // Update score breakdown
  const vScore = Math.round((result.voice_fraud_score ?? 0) * 100);
  const cScore = Math.round((result.content_fraud_score ?? 0) * 100);

  // 🔥 Force update with null checks
  if (voiceBar) voiceBar.style.width = `${vScore}%`;
  if (contentBar) contentBar.style.width = `${cScore}%`;
  if (voiceVal) voiceVal.textContent = `${vScore}%`;
  if (contentVal) contentVal.textContent = `${cScore}%`;
  
  console.log(`📊 Score Breakdown: Voice=${vScore}%, Content=${cScore}%`);

  // Update transcript (use accumulated from backend)
  const accumulatedText = result.accumulated_transcript || result.transcript || "";
  const latestChunk = result.latest_chunk_text || "";
  
  // 🔥 ALWAYS update chunk counter
  const chunkNum = result.chunk_number || chunkCount;
  if (chunkCounter) {
    chunkCounter.textContent = `${chunkNum} chunk${chunkNum !== 1 ? 's' : ''} processed`;
  }
  
  // 🔥 Show transcript if available, otherwise show listening message
  if (accumulatedText.trim()) {
    transcriptText.innerHTML = highlightKeywords(
      escapeHtml(accumulatedText),
      result.matched_keywords ?? []
    );
    transcriptText.scrollTop = transcriptText.scrollHeight;
    
    if (latestChunk) {
      console.log(`📝 Chunk #${chunkNum}: "${latestChunk}"`);
    }
  } else if (isListening) {
    // Show listening message only when actively recording
    transcriptText.innerHTML = `<span class="transcript-placeholder">🎤 Listening... speak into your microphone</span>`;
  } else {
    // Show idle message when not recording
    transcriptText.innerHTML = `<span class="transcript-placeholder">Click "Start Listening" to begin</span>`;
  }

  // Update AI reasoning
  updateAIReasoning(result);

  // Update flags
  updateFlags(result.voice_flags ?? [], result.matched_keywords ?? [], result.pattern_categories ?? []);

  // Update category
  if (categoryTag) {
    categoryTag.textContent = result.category || "Unknown";
  }

  // Update recommendation
  if (recommendationBox) {
    recommendationBox.className = `recommendation-box ${color}`;
  }
  if (recommendationText) {
    recommendationText.textContent = result.recommendation ?? "";
  }

  // Update alert banner
  updateAlertBanner(score, riskLevel, result.short_warning ?? "");

  // Show fraud overlay if critical
  if (score >= 70) {
    showFraudOverlay();
  }

  // Update waveform color
  updateWaveformColor(color);

  // Add to history
  addHistoryRow(result);

  console.log(`🎯 Result: ${score}% [${riskLevel}] — ${accumulatedText.slice(0, 60)}${accumulatedText.length > 60 ? '...' : ''}`);
}

function updateGauge(score, riskLevel, color) {
  const clampedScore = Math.max(0, Math.min(100, score));
  const offset = GAUGE_CIRCUMFERENCE - (clampedScore / 100) * GAUGE_CIRCUMFERENCE;
  
  // 🔥 Force update with detailed logging
  console.log(`🎨 Gauge Update: ${clampedScore}% (offset: ${offset}, level: ${riskLevel}, color: ${color})`);
  console.log(`   Elements exist: gaugeFill=${!!gaugeFill}, gaugeScore=${!!gaugeScore}, gaugeLevel=${!!gaugeLevel}`);
  
  if (gaugeFill) {
    gaugeFill.style.strokeDashoffset = offset;
    console.log(`   ✅ Updated gaugeFill.strokeDashoffset = ${offset}`);
  } else {
    console.error(`   ❌ gaugeFill element not found!`);
  }
  
  if (gaugeScore) {
    gaugeScore.textContent = clampedScore;
    console.log(`   ✅ Updated gaugeScore.textContent = ${clampedScore}`);
  } else {
    console.error(`   ❌ gaugeScore element not found!`);
  }
  
  if (gaugeLevel) {
    gaugeLevel.textContent = riskLevel;
    console.log(`   ✅ Updated gaugeLevel.textContent = ${riskLevel}`);
  } else {
    console.error(`   ❌ gaugeLevel element not found!`);
  }
  
  if (gaugeWrapper) {
    gaugeWrapper.className = `gauge-wrapper ${color}`;
    
    if (color === "red") {
      gaugeWrapper.classList.add("crit-pulse");
    } else {
      gaugeWrapper.classList.remove("crit-pulse");
    }
    console.log(`   ✅ Updated gaugeWrapper.className = gauge-wrapper ${color}`);
  } else {
    console.error(`   ❌ gaugeWrapper element not found!`);
  }
}

function updateAlertBanner(score, riskLevel, shortWarning) {
  if (score >= 61) {
    const isCritical = score >= 81;
    alertBanner.classList.add("visible");

    if (isCritical) {
      alertInner.classList.remove("warn-banner");
      alertIcon.textContent = "🚨";
      alertTitle.textContent = "CRITICAL FRAUD DETECTED";
      alertSubtitle.textContent = shortWarning || "Hang up immediately. Do not share any personal information.";
    } else {
      alertInner.classList.add("warn-banner");
      alertIcon.textContent = "⚠️";
      alertTitle.textContent = "HIGH RISK CALL";
      alertSubtitle.textContent = shortWarning || "Do not share OTPs, passwords, or bank details.";
    }
  } else if (score < 31) {
    alertBanner.classList.remove("visible");
  }
}

function dismissAlert() {
  alertBanner.classList.remove("visible");
}

function updateWaveformColor(color) {
  if (!analyzerNode) return;
  const colors = {
    green: "#22c55e",
    yellow: "#eab308",
    orange: "#f97316",
    red: "#ef4444",
  };
  window.__waveformColor = colors[color] || "#3b82f6";
}

function updateFlags(voiceFlags, matchedKeywords, patternCategories) {
  const allTags = [];

  const voiceFlagLabels = {
    low_mfcc_variance: "🤖 AI Voice Pattern",
    unnatural_pitch: "📊 Unnatural Pitch",
    abnormal_pitch_range: "📉 Abnormal Pitch Range",
    voice_switching_detected: "🔄 Voice Switch Detected",
    high_zero_crossing_rate: "📻 Robotic Audio",
    near_silent_audio: "🔇 Near-Silent Audio",
    analysis_failed: "⚠️ Analysis Error",
  };

  voiceFlags.forEach(flag => {
    const label = voiceFlagLabels[flag] || flag.replace(/_/g, " ");
    allTags.push({ text: label, type: "voice" });
  });

  const topKeywords = matchedKeywords.slice(0, 5);
  topKeywords.forEach(kw => {
    allTags.push({ text: `🔑 "${kw}"`, type: "content" });
  });

  patternCategories.slice(0, 2).forEach(cat => {
    allTags.push({ text: `🎯 ${cat}`, type: "content" });
  });

  if (allTags.length === 0) {
    flagsGrid.innerHTML = `<span class="flag-tag none">✓ No fraud signals detected</span>`;
    return;
  }

  flagsGrid.innerHTML = allTags.map(tag =>
    `<span class="flag-tag ${tag.type}">${escapeHtml(tag.text)}</span>`
  ).join("");
}

function addHistoryRow(result) {
  if (!historyTbody) return;
  
  const score = result.final_score_pct ?? Math.round((result.final_score ?? 0) * 100);
  const riskLevel = result.risk_level ?? "SAFE";
  const color = result.color ?? "green";
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const topKw = (result.matched_keywords ?? [])[0] || "—";

  const rowData = { score, riskLevel, color, timeStr, category: result.category ?? "Unknown", topKw };
  historyRows.unshift(rowData);
  if (historyRows.length > MAX_HISTORY_ROWS) historyRows.pop();

  // 🔥 Log history update
  console.log(`📋 History: Added row #${historyRows.length} (${score}% ${riskLevel})`);

  historyTbody.innerHTML = historyRows.map((row, i) => {
    const badgeClass = { green: "safe", yellow: "warn", orange: "high", red: "crit" }[row.color] || "safe";
    return `
      <tr>
        <td style="font-family:var(--font-mono); color:var(--text-muted);">${historyRows.length - i}</td>
        <td style="font-family:var(--font-mono);">${escapeHtml(row.timeStr)}</td>
        <td style="font-family:var(--font-mono); font-weight:600;">${row.score}%</td>
        <td><span class="risk-badge ${badgeClass}">${escapeHtml(row.riskLevel)}</span></td>
        <td>${escapeHtml(row.category)}</td>
        <td style="font-family:var(--font-mono); font-size:0.8rem; color:var(--text-muted);">
          ${escapeHtml(topKw)}
        </td>
      </tr>
    `;
  }).join("");
}

function updateAIReasoning(result) {
  const reasoningContainer = document.getElementById("ai-reasoning");
  if (!reasoningContainer) return;

  reasoningContainer.innerHTML = "";

  const score = result.final_score_pct ?? 0;
  const keywords = result.matched_keywords ?? [];
  const voiceFlags = result.voice_flags ?? [];
  const category = result.category ?? "Unknown";

  const reasons = [];

  if (score < 30) {
    reasons.push({
      icon: "✅",
      text: "No significant fraud indicators detected",
      type: "safe"
    });
  } else {
    if (voiceFlags.length > 0) {
      const flagText = voiceFlags.map(f => f.replace(/_/g, " ")).join(", ");
      reasons.push({
        icon: "🎵",
        text: `Voice anomalies detected: ${flagText}`,
        type: score >= 70 ? "danger" : "warning"
      });
    }

    if (keywords.length > 0) {
      const topKeywords = keywords.slice(0, 3).join(", ");
      reasons.push({
        icon: "🔑",
        text: `Scam keywords found: "${topKeywords}"`,
        type: "danger"
      });
    }

    if (category !== "Unknown") {
      reasons.push({
        icon: "🎯",
        text: `Classified as: ${category}`,
        type: score >= 70 ? "danger" : "warning"
      });
    }

    if (score >= 80) {
      reasons.push({
        icon: "🚨",
        text: "CRITICAL: Multiple fraud indicators align — high confidence scam",
        type: "danger"
      });
    } else if (score >= 60) {
      reasons.push({
        icon: "⚠️",
        text: "HIGH RISK: Strong fraud patterns detected",
        type: "danger"
      });
    } else if (score >= 30) {
      reasons.push({
        icon: "⚡",
        text: "SUSPICIOUS: Some fraud indicators present — stay alert",
        type: "warning"
      });
    }
  }

  reasons.forEach(reason => {
    const item = document.createElement("div");
    item.className = `reasoning-item ${reason.type}`;
    item.innerHTML = `
      <span class="reasoning-icon">${reason.icon}</span>
      <span class="reasoning-text">${escapeHtml(reason.text)}</span>
    `;
    reasoningContainer.appendChild(item);
  });
}

function showFraudOverlay() {
  const overlay = document.getElementById("fraud-overlay");
  if (overlay) {
    overlay.classList.remove("hidden");
  }
}

function dismissFraudOverlay() {
  const overlay = document.getElementById("fraud-overlay");
  if (overlay) {
    overlay.classList.add("hidden");
  }
}

async function runDemoScenario() {
  const demoTranscript = "Hello sir, I am calling from RBI headquarters. Your Aadhaar card is linked to an illegal money laundering account. An arrest warrant has been issued in your name. You will be arrested within 2 hours. Do not tell anyone about this call. To cancel the warrant, you must pay 50,000 rupees bail amount immediately. Please share your OTP to verify your identity.";

  const demoResult = {
    final_score: 0.92,
    final_score_pct: 92,
    risk_level: "CRITICAL FRAUD",
    color: "red",
    voice_fraud_score: 0.78,
    content_fraud_score: 0.98,
    transcript: demoTranscript,
    accumulated_transcript: demoTranscript,
    matched_keywords: ["rbi", "aadhaar", "arrest warrant", "money laundering", "otp", "immediately", "do not tell anyone", "pay"],
    voice_flags: ["unnatural_pitch", "low_mfcc_variance"],
    category: "Police / Government Impersonation",
    pattern_categories: ["Authority Impersonation", "Threat Language", "Secrecy Demand", "Money Transfer Request"],
    recommendation: "HANG UP IMMEDIATELY. This shows all markers of a fraud call. Do NOT share any information, make any payments, or follow any instructions. Report this number to the National Cyber Crime Helpline: 1930 or visit cybercrime.gov.in.",
    short_warning: "🚨 CRITICAL FRAUD DETECTED — HANG UP NOW",
    processing_time_ms: 850,
    voice_model_used: true
  };

  setStatus("analyzing");
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  handleAnalysisResult(demoResult);
  setStatus("idle");
  
  chunkCount++;
  if (chunkCounter) {
    chunkCounter.textContent = `${chunkCount} chunk${chunkCount !== 1 ? "s" : ""} processed`;
  }
}

function updateWaveformActive(active) {
  const container = document.querySelector(".waveform-container");
  if (container) {
    if (active) {
      container.classList.add("active");
    } else {
      container.classList.remove("active");
    }
  }
}

// ─── Text Utilities ───────────────────────────────────────────────────────────

function escapeHtml(text) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}

function highlightKeywords(escapedHtml, keywords) {
  if (!keywords || keywords.length === 0) return escapedHtml;

  let result = escapedHtml;
  const sorted = [...keywords].sort((a, b) => b.length - a.length);

  sorted.forEach(kw => {
    if (!kw || kw.length < 2) return;
    const escaped = escapeHtml(kw);
    const regex = new RegExp(`(?<!<[^>]*)\\b${escaped.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "gi");
    result = result.replace(regex, match =>
      `<span class="keyword-highlight">${match}</span>`
    );
  });

  return result;
}

// ─── Initialization ───────────────────────────────────────────────────────────

function init() {
  if (!window.MediaRecorder) {
    micError.innerHTML = `
      <strong>❌ Browser Not Supported</strong><br />
      PhishShield requires a modern browser with MediaRecorder support.<br />
      Please use Google Chrome 80+ or Firefox 75+.
    `;
    micError.classList.add("visible");
    btnStart.disabled = true;
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    micError.innerHTML = `
      <strong>⚠️ Microphone API Unavailable</strong><br />
      Your browser doesn't support microphone access, or you're not using HTTPS.<br />
      Try running the page over <code>http://localhost</code> or use Chrome.
    `;
    micError.classList.add("visible");
    btnStart.disabled = true;
    return;
  }

  console.log("✅ PhishShield initialized");

  // Test backend connection
  const testWs = new WebSocket(WS_URL);
  testWs.onopen = () => {
    setWsStatus("Backend reachable ✓", "var(--safe)");
    testWs.close(1000, "Preflight check");
  };
  testWs.onerror = () => {
    setWsStatus("Backend not reachable — start uvicorn server", "var(--crit)");
  };
}

document.addEventListener("DOMContentLoaded", init);

// Expose functions for HTML onclick
window.startListening = startListening;
window.stopListening = stopListening;
window.dismissAlert = dismissAlert;
window.dismissFraudOverlay = dismissFraudOverlay;
window.runDemoScenario = runDemoScenario;
