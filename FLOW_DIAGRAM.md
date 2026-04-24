# 🔄 PhishShield Real-Time Streaming Flow

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER SPEAKS                             │
│                    "Hello, I am from RBI"                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER (Frontend)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MediaRecorder captures audio every 2 seconds            │  │
│  │  Chunk: WebM/Opus format (~45KB)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket.send(audio_bytes)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND WebSocket (main.py)                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  while True:  ← INFINITE LOOP (never exits)              │ │
│  │      audio_bytes = await websocket.receive_bytes()       │ │
│  │      # Process chunk...                                  │ │
│  │      await websocket.send_json(response)                 │ │
│  │      # Loop continues...                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Step 1: Convert WebM → WAV                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  pydub.AudioSegment.from_file(webm)                      │ │
│  │  → 16kHz mono WAV (~32KB)                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  Step 2: Transcribe with Whisper                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  whisper.transcribe(wav_file)                            │ │
│  │  → "i am from rbi"                                       │ │
│  │  Time: ~1.9 seconds                                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  Step 3: Accumulate Transcript                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  accumulated_transcript = ""                             │ │
│  │  Chunk 1: "hello"                                        │ │
│  │  Chunk 2: "hello i am from rbi"                         │ │
│  │  Chunk 3: "hello i am from rbi share your otp"          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  Step 4: Content Analysis                                      │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  content_analyzer.analyze(accumulated_transcript)        │ │
│  │  → matched_keywords: ["rbi", "otp"]                      │ │
│  │  → pattern_categories: ["Authority Impersonation"]       │ │
│  │  Time: ~50ms                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  Step 5: Risk Calculation                                      │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  risk_engine.compute(voice_result, content_result)       │ │
│  │  → final_score: 0.87 (87%)                               │ │
│  │  → risk_level: "CRITICAL FRAUD"                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  Step 6: Build JSON Response                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  {                                                        │ │
│  │    "chunk_number": 3,                                    │ │
│  │    "latest_chunk_text": "share your otp",               │ │
│  │    "accumulated_transcript": "hello i am from rbi...",  │ │
│  │    "final_score_pct": 87,                               │ │
│  │    "risk_level": "CRITICAL FRAUD",                      │ │
│  │    "matched_keywords": ["rbi", "otp"],                  │ │
│  │    "recommendation": "HANG UP IMMEDIATELY"              │ │
│  │  }                                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                             │                                   │
│                             ▼                                   │
│  Step 7: Send Response (DO NOT CLOSE)                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  await websocket.send_json(response)                     │ │
│  │  # Loop continues — connection stays open                │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket.onmessage(json)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER (Frontend)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  handleAnalysisResult(result)                            │  │
│  │  → Update transcript display                             │  │
│  │  → Update risk gauge (87%)                               │  │
│  │  → Highlight keywords ("rbi", "otp")                     │  │
│  │  → Show AI reasoning                                     │  │
│  │  → Update recommendation                                 │  │
│  │  → Show fraud overlay if score >= 70%                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USER SEES RESULT                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Transcript: "hello i am from rbi share your otp"        │  │
│  │  Risk Gauge: 87% (RED)                                   │  │
│  │  Keywords: "rbi", "otp" (highlighted)                    │  │
│  │  Alert: "🚨 CRITICAL FRAUD DETECTED"                     │  │
│  │  Recommendation: "HANG UP IMMEDIATELY"                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ User continues speaking...
                             │
                             ▼
                    (Loop repeats for next chunk)
```

---

## Timeline (Per Chunk)

```
0.0s  │ User speaks
      │
2.0s  │ Browser sends chunk
      │ ↓ WebSocket
2.1s  │ Backend receives (100ms network)
      │ ↓ Convert audio
2.2s  │ WebM → WAV (100ms)
      │ ↓ Transcribe
4.1s  │ Whisper transcription (1900ms)
      │ ↓ Accumulate
4.1s  │ Add to accumulated_transcript (1ms)
      │ ↓ Analyze
4.2s  │ Content analysis (50ms)
      │ ↓ Calculate risk
4.2s  │ Risk engine (10ms)
      │ ↓ Send response
4.2s  │ WebSocket send (50ms network)
      │ ↓ Update UI
4.3s  │ Frontend updates (50ms)
      │
      │ ✅ User sees result
      │
      │ Loop continues...
```

**Total Latency:** ~2.3 seconds from when you stop speaking to when transcript appears

---

## Key Features

### 🔄 Continuous Loop
```python
while True:  # Never exits
    receive → process → send → repeat
```

### 📝 Transcript Accumulation
```python
Chunk 1: "hello"
Chunk 2: "hello i am from rbi"
Chunk 3: "hello i am from rbi share your otp"
```

### 🎯 Risk Score Evolution
```
Chunk 1: 10% (SAFE)
Chunk 2: 55% (SUSPICIOUS)
Chunk 3: 87% (CRITICAL)
```

### 🔌 Connection Persistence
```
Connect → Chunk 1 → Chunk 2 → Chunk 3 → ... → Chunk N → Disconnect
         (connection stays open entire time)
```

---

## Error Handling

```
┌─────────────────────────────────────────────────────────────┐
│  while True:                                                │
│      try:                                                   │
│          audio_bytes = await websocket.receive_bytes()     │
│      except WebSocketDisconnect:                           │
│          logger.info("Client disconnected")                │
│          break  ← Only break on disconnect                 │
│                                                             │
│      try:                                                   │
│          # Process chunk...                                │
│          await websocket.send_json(response)               │
│      except Exception as e:                                │
│          # Send error response but KEEP LOOP RUNNING       │
│          await websocket.send_json(error_response)         │
│          # Loop continues...                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Comparison: Before vs After

### ❌ BEFORE (Broken)
```
Connect
   ↓
Receive 1 chunk
   ↓
Process
   ↓
Send response
   ↓
Function exits ← CONNECTION CLOSES
```

### ✅ AFTER (Fixed)
```
Connect
   ↓
┌──────────────┐
│ while True:  │ ← INFINITE LOOP
│   Receive    │
│   Process    │
│   Send       │
│   (repeat)   │
└──────────────┘
   ↓
Disconnect (only when user clicks Stop)
```

---

## Success Indicators

✅ Backend logs show multiple chunks (1, 2, 3, 4...)  
✅ Each chunk shows growing "📝 FULL:" transcript  
✅ Frontend transcript keeps growing  
✅ No "disconnected" until user clicks Stop  
✅ Can speak for 30+ seconds continuously  
✅ Risk score updates based on cumulative keywords  

---

**Version:** 3.2.0  
**Status:** ✅ Fully Implemented  
**Action:** Test it now!
