# 🎯 TEST NOW - Quick Guide

## ✅ System Status
- Backend: Starting (check PowerShell window)
- Frontend: Opening in browser
- Model: Whisper "tiny" (FAST - 2-3 seconds)

---

## 🚀 Quick Test (30 seconds)

### Step 1: Wait for Backend (5 seconds)
Look at the PowerShell window that just opened.

**Wait for:**
```
Loading Whisper 'tiny' model (FAST - 2-3 seconds per chunk)...
✅ Whisper model loaded successfully
✅ Analysis modules loaded
🛡️  PhishShield ready. Listening on port 8000
```

---

### Step 2: Test Demo Button (10 seconds)
```
1. In browser, click "Run Demo Scenario"
2. Watch gauge turn RED (92%)
3. See transcript fill with demo text
```

**If this works:** Backend is 100% functional! ✅

---

### Step 3: Test Live Voice (30 seconds)
```
1. Press F12 (open console)
2. Click "Start Listening"
3. Click "Allow" for microphone
4. Speak LOUDLY: "POLICE ARREST WARRANT OTP URGENT"
5. Wait 3 seconds
6. Watch UI update
```

**Expected Results:**

**Console (F12):**
```
✅ WebSocket connected
🚀 MediaRecorder started (3-second chunks, continuous)
🎤 Chunk #1: 48462 bytes
📤 Sent chunk #1
📨 WebSocket message received: {final_score_pct: 65, ...}
🎯 Updating UI: Score=65%, Level=HIGH RISK, Color=orange
```

**Backend (PowerShell):**
```
📦 Chunk #1: 48462 bytes from 127.0.0.1
✅ Converted: 48462 → 96044 bytes WAV (3000ms)
⏱️ Transcription: 2500ms  ← FAST!
✅ TRANSCRIBED: "police arrest warrant otp urgent"
🎯 Result: HIGH RISK (65%) | Keywords: 4
```

**UI:**
- ✅ Transcript: "police arrest warrant otp urgent"
- ✅ Gauge: 65% (orange)
- ✅ History: 1 row added
- ✅ AI Reasoning: Shows keywords
- ✅ Detected Signals: Shows fraud indicators

---

## 🎤 Test Phrases

### Quick Test (Verify it works)
```
"Hello testing one two three"
```
**Expected:** Transcribes in 2-3 seconds, stays green

### Medium Fraud (50-70%)
```
"Police arrest warrant OTP urgent"
```
**Expected:** Orange gauge, keywords highlighted

### Maximum Fraud (90%+)
```
"I am calling from police headquarters. Your Aadhaar is linked to money laundering. 
An arrest warrant will be issued. Share your OTP immediately."
```
**Expected:** Red gauge, full alerts

---

## 🐛 Quick Fixes

### Backend not starting?
```bash
# Check if port 8000 is free
netstat -ano | findstr :8000

# If something is using it, kill it
taskkill /F /PID [PID_NUMBER]

# Restart
.\quick-restart.bat
```

### Browser not opening?
```
Manually open: http://localhost:5500/frontend/dashboard.html
Or: Double-click frontend/dashboard.html
```

### Microphone not working?
```
1. Click microphone icon in address bar
2. Select "Allow"
3. Refresh page (F5)
```

---

## ✅ Success Indicators

You know it's working when:

1. ✅ Demo button shows 92% red
2. ✅ "Start Listening" changes status to "LISTENING"
3. ✅ Console shows chunks being sent
4. ✅ Backend shows transcription (2-3 seconds!)
5. ✅ UI updates (gauge, transcript, history)

---

## 📞 What to Tell Me

After testing, tell me:

1. **Demo button:** Works / Doesn't work
2. **Transcription speed:** X seconds
3. **UI updates:** Yes / No
4. **Any errors:** Copy from console or backend
5. **What you said:** Exact words

---

**Everything is ready! Just wait for backend to load, then test!** 🚀

**Look for the PowerShell window to show "🛡️ PhishShield ready"**
