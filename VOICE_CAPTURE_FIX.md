me:
1. What you see in browser console (F12)
2. What you see in backend PowerShell window
3. What happens when you click "Start Listening"
4. Any error messages

---

**Your original UI is safe and unchanged!** 🎉
estart-backend.bat` - Easy restart script

I DID NOT change:
- ❌ `frontend/dashboard.html` - Your UI is unchanged
- ❌ `frontend/style.css` - Your styles are unchanged
- ❌ `frontend/app.js` - Only minor fixes (keepalive handling)

---

## Next Steps

1. **First:** Open test-microphone.html and verify mic works
2. **Second:** Open dashboard.html and try "Run Demo Scenario"
3. **Third:** Click "Start Listening" and speak test phrases
4. **Fourth:** Check console and backend logs

If you still have issues, tell hon -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Wait 10 seconds

# 5. Open FRESH browser window
# 6. Go to: http://localhost:8000/health
# Should see: {"status":"ok"}

# 7. Open: frontend/dashboard.html
# 8. Try again
```

---

## What I Changed (Backend Only)

I ONLY changed backend files to fix voice capture:
- ✅ `backend/main.py` - Better logging, audio conversion, transcription
- ✅ `backend/test_audio_capture.py` - Diagnostic script
- ✅ `test-microphone.html` - Microphone test tool
- ✅ `r "✅ Converted"
   - [ ] Backend shows "⏱️ Transcription"

9. Transcription Working?
   - [ ] Backend shows "✅ TRANSCRIBED: [your words]"
   - [ ] Frontend transcript updates
   - [ ] Keywords highlighted

10. UI Updating?
    - [ ] Gauge animates
    - [ ] Score shows percentage
    - [ ] History table fills
    - [ ] AI Reasoning updates

---

## If NOTHING Works

Try this nuclear option:

```bash
# 1. Close ALL browser windows
# 2. Kill backend
taskkill /F /IM python.exe

# 3. Restart backend
cd backend
pytet Connected?
   - [ ] Console shows "✅ WebSocket connected"
   - [ ] Bottom right shows "WebSocket: Connected" (green)

6. Recording Started?
   - [ ] Clicked "Start Listening"
   - [ ] Status shows "LISTENING" (green)
   - [ ] Waveform animating
   - [ ] Timer counting up

7. Audio Chunks Sending?
   - [ ] Console shows "🎤 Chunk #1: XXXX bytes"
   - [ ] Console shows "📤 Sent chunk #1"
   - [ ] Chunk counter incrementing

8. Backend Receiving?
   - [ ] Backend window shows "📦 Chunk #1"
   - [ ] Backend showsow open with "PhishShield Backend"
   - [ ] Shows "🛡️ PhishShield ready"
   - [ ] No error messages

2. Frontend Loaded?
   - [ ] Dashboard.html open in browser
   - [ ] Shows "PhishShield Live Detection"
   - [ ] Buttons visible (Start Listening, Stop, Demo)

3. Microphone Permission?
   - [ ] Browser asked for permission
   - [ ] You clicked "Allow"
   - [ ] No red X on microphone icon in address bar

4. Console Open?
   - [ ] Press F12
   - [ ] Console tab selected
   - [ ] Can see log messages

5. WebSocke four five"
```

### Test 2: Fraud Keywords (should trigger detection)
```
"Police arrest warrant OTP urgent"
```
**Expected:** 50-70% score, orange gauge

### Test 3: Maximum Fraud (should trigger all alerts)
```
"I am calling from police headquarters. Your Aadhaar is linked to money laundering. 
An arrest warrant will be issued. Share your OTP immediately."
```
**Expected:** 90%+ score, red gauge, full alerts

---

## Debugging Checklist

Run through this checklist:

1. Backend Running?
   - [ ] PowerShell windend: .\restart-backend.bat

### Issue 4: "Transcription empty"
**Fix:**
1. Speak LOUDER and CLEARER
2. Move closer to microphone
3. Reduce background noise
4. Try test phrase: "POLICE ARREST WARRANT OTP URGENT"

### Issue 5: "UI not updating"
**Fix:**
1. Hard refresh: Ctrl + Shift + R
2. Clear cache: Ctrl + Shift + Delete
3. Check console for errors (F12)
4. Make sure you're speaking (not silent)

---

## Test Phrases (Use These)

### Test 1: Simple (should transcribe easily)
```
"Hello testing one two threrophone icon in browser address bar
2. Select "Allow"
3. Refresh page (F5)
4. Try again

### Issue 2: "No chunks captured"
**Fix:**
1. Check microphone is plugged in
2. Check Windows sound settings (microphone not muted)
3. Try different browser (Chrome recommended)
4. Check microphone works in other apps

### Issue 3: "WebSocket not connected"
**Fix:**
1. Check backend is running (look for PowerShell window)
2. Check URL: http://localhost:8000/health
3. Should return: {"status":"ok",...}
4. If not, restart backs loaded
🛡️  PhishShield ready. Listening on port 8000
✅ WebSocket connected from 127.0.0.1
📦 Chunk #1: 12345 bytes from 127.0.0.1
   ✅ Converted: 12345 → 45678 bytes (50ms)
   ⏱️ Transcription: 450ms
   ✅ TRANSCRIBED: "police arrest warrant otp urgent"
```

**If you see transcription:** Everything works! ✅
**If "No speech detected":** Speak louder or closer to mic ❌
**If conversion fails:** Audio format issue ❌

---

## Common Issues & Fixes

### Issue 1: "Microphone access denied"
**Fix:**
1. Click the michield initialized
✅ WebSocket connected
🚀 MediaRecorder started (3-second chunks, continuous)
🎤 Chunk #1: 12345 bytes
📤 Sent chunk #1
📨 WebSocket message received: {...}
```

**If you see this:** System is working, just need to speak louder ✅
**If WebSocket not connected:** Backend issue ❌
**If no chunks:** Microphone issue ❌

---

### Step 3: Check Backend Logs
```
Look at the PowerShell window titled "PhishShield Backend"
```

**Expected Backend Output:**
```
✅ Whisper model loaded successfully
✅ Analysis modulephone"
3. Grant permission when asked
4. Speak: "Hello testing one two three"
5. Check if you see "Chunk #1: XXXX bytes"
```

**If you see chunks:** Microphone works ✅
**If no chunks:** Microphone permission issue ❌

---

### Step 2: Test Dashboard (1 minute)
```
1. Open: frontend/dashboard.html
2. Open browser console (F12)
3. Click "Start Listening"
4. Grant microphone permission
5. Speak clearly: "Police arrest warrant OTP urgent"
6. Watch console for messages
```

**Expected Console Output:**
```
✅ PhishSP BY STEP

## Current Status
- ✅ Backend is running (port 8000)
- ✅ Frontend dashboard.html is open
- ✅ All dependencies installed (Whisper, pydub, etc.)
- ❌ Voice not being captured/transcribed

## The Problem
The issue is likely one of these:
1. Microphone permission not granted
2. Audio chunks too small/empty
3. Whisper not transcribing properly
4. WebSocket not receiving audio

## Quick Fix Steps

### Step 1: Test Microphone (30 seconds)
```
1. Open: test-microphone.html (already created)
2. Click "Test Micro# 🎤 VOICE CAPTURE FIX - STE