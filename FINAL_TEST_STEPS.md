# ✅ FINAL TEST STEPS - Voice Capture Fix

## Your UI is Safe ✅
- `frontend/dashboard.html` - UNCHANGED
- `frontend/style.css` - UNCHANGED  
- `frontend/app.js` - Only minor backend communication fixes

## What I Fixed (Backend Only)
1. Better audio conversion (handles mobile audio)
2. Improved Whisper transcription settings
3. Better logging to see what's happening
4. Keepalive system to prevent timeouts

---

## 🎯 Test Right Now (2 Minutes)

### Test 1: Demo Button (Proves Backend Works)
```
1. Open: frontend/dashboard.html
2. Click: "Run Demo Scenario"
3. Expected: Gauge turns RED (92%), transcript fills
```

**If this works:** Backend is 100% functional ✅

---

### Test 2: Live Microphone (Proves Voice Capture Works)
```
1. Press F12 (open console)
2. Click: "Start Listening"
3. Click: "Allow" when browser asks for microphone
4. Speak LOUDLY: "POLICE ARREST WARRANT OTP URGENT"
5. Wait 3 seconds
6. Check console and UI
```

**Expected Console:**
```
✅ WebSocket connected
🚀 MediaRecorder started (3-second chunks, continuous)
🎤 Chunk #1: 15234 bytes
📤 Sent chunk #1
📨 WebSocket message received: {final_score_pct: 65, ...}
🎯 Updating UI: Score=65%, Level=HIGH RISK, Color=orange
```

**Expected UI:**
- Transcript: "police arrest warrant otp urgent"
- Gauge: 50-70% (orange color)
- History: 1 row added
- AI Reasoning: Shows keywords detected
- Detected Signals: Shows "🔑 police", "🔑 arrest warrant", etc.

**Expected Backend (PowerShell window):**
```
📦 Chunk #1: 15234 bytes from 127.0.0.1
   ✅ Converted: 15234 → 48576 bytes (45ms)
   ⏱️ Transcription: 520ms
   🗣️ TRANSCRIBED: "police arrest warrant otp urgent"
   📝 ACCUMULATED: "police arrest warrant otp urgent"
   ⏱️ Content: 12ms
   🎯 Result: HIGH RISK (65%) | Keywords: 4 | Time: 580ms
```

---

## 🐛 Troubleshooting

### Problem: "Demo button doesn't work"
**Cause:** Backend not running or crashed
**Fix:**
```bash
# Kill and restart backend
taskkill /F /IM python.exe
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Problem: "Microphone permission denied"
**Cause:** Browser blocked microphone
**Fix:**
1. Click microphone icon in address bar (🎤)
2. Select "Allow"
3. Refresh page (F5)
4. Try again

---

### Problem: "No chunks in console"
**Cause:** Microphone not working or too quiet
**Fix:**
1. Check Windows sound settings (microphone not muted)
2. Speak LOUDER (shout if needed)
3. Move closer to microphone
4. Try test-microphone.html first to verify mic works

---

### Problem: "Chunks sent but no transcription"
**Cause:** Whisper not detecting speech (audio too quiet)
**Fix:**
1. Speak MUCH LOUDER
2. Reduce background noise
3. Use headset microphone if available
4. Check backend logs for "✅ TRANSCRIBED:" message

---

### Problem: "Transcription works but UI doesn't update"
**Cause:** Frontend not receiving WebSocket messages
**Fix:**
1. Hard refresh: Ctrl + Shift + R
2. Check console for "📨 WebSocket message received"
3. If missing, check WebSocket connection status (bottom right)

---

## 📊 What Each Component Does

### Frontend (Your UI - Unchanged)
- Captures microphone audio
- Sends 3-second chunks to backend via WebSocket
- Receives analysis results
- Updates UI (gauge, transcript, history, etc.)

### Backend (Fixed)
- Receives audio chunks via WebSocket
- Converts WebM → WAV format
- Transcribes with Whisper
- Analyzes for fraud keywords
- Sends results back to frontend

### The Flow:
```
Microphone → MediaRecorder → WebSocket → Backend
                                            ↓
                                    Convert Audio
                                            ↓
                                    Transcribe (Whisper)
                                            ↓
                                    Analyze Keywords
                                            ↓
Frontend ← WebSocket ← Results ← Calculate Score
    ↓
Update UI (gauge, transcript, history)
```

---

## 🎤 Test Phrases (Copy & Speak)

### Low Risk (Should stay green 0-30%)
```
"Hello, how are you today? I'm calling to confirm your appointment."
```

### Medium Risk (Should turn yellow 30-60%)
```
"Your account needs verification. Please confirm your account number."
```

### High Risk (Should turn orange 60-80%)
```
"Your account will be frozen. Transfer money immediately to avoid legal action."
```

### Critical (Should turn red 80-100%)
```
"I am calling from police headquarters. Your Aadhaar is linked to money laundering. 
An arrest warrant will be issued. Share your OTP immediately or you will be arrested."
```

---

## ✅ Success Indicators

You know it's working when:

1. **Demo button:** Gauge turns red (92%)
2. **Start Listening:** Status changes to "LISTENING" (green)
3. **Speaking:** Console shows chunks being sent
4. **Backend:** Shows transcription in PowerShell window
5. **UI Updates:** Transcript appears, gauge moves, history fills

---

## 📞 What to Tell Me If It Still Doesn't Work

Copy and paste these:

1. **Console output** (F12 → Console tab):
```
[Paste everything here]
```

2. **Backend output** (PowerShell window):
```
[Paste last 20 lines here]
```

3. **What happens:**
- [ ] Demo button works / doesn't work
- [ ] Microphone permission granted / denied
- [ ] Chunks appear in console / don't appear
- [ ] Backend shows transcription / doesn't show
- [ ] UI updates / doesn't update

4. **Error messages:**
```
[Paste any red error messages here]
```

---

## 🚀 Quick Commands

### Restart Everything:
```bash
# Kill backend
taskkill /F /IM python.exe

# Start backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Wait 5 seconds, then open dashboard
start frontend/dashboard.html
```

### Check Backend Health:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "ok",
  "whisper_loaded": true,
  "keywords_loaded": true,
  "keyword_count": 273
}
```

---

## 💡 Pro Tips

1. **Speak LOUD** - Whisper needs clear audio
2. **Wait 3 seconds** - Chunks are sent every 3 seconds
3. **Check console** - Shows exactly what's happening
4. **Check backend** - Shows transcription in real-time
5. **Use test phrases** - Guaranteed to trigger detection

---

**Your original UI is completely safe and unchanged!**
**Just follow the test steps above and tell me what happens.** 🎉
