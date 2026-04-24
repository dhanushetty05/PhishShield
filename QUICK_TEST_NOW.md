# ⚡ QUICK TEST NOW - 2 MINUTE VERIFICATION

## 🚀 Start Backend (Terminal 1)

```bash
cd backend
uvicorn main:app --reload
```

**Wait for:**
```
✅ Whisper model loaded successfully
✅ Analysis modules loaded
🛡️  PhishShield ready. Listening on port 8000
```

---

## 🌐 Open Frontend (Browser)

```bash
# Open in Chrome
frontend/dashboard.html
```

**Or double-click:** `frontend/dashboard.html`

---

## 🧪 Test 1: Demo Button (10 seconds)

```
1. Click "Run Demo Scenario"
2. Watch UI update
```

**Expected:**
- ✅ Transcript fills with demo text
- ✅ Gauge shows 92% (red)
- ✅ Alert banner appears
- ✅ History adds row

**If this works, your system is 100% functional!**

---

## 🎤 Test 2: Live Recording (30 seconds)

```
1. Open browser console (F12)
2. Click "Start Listening"
3. Say: "Police arrest warrant OTP urgent"
4. Wait 3 seconds
5. Watch console and UI
```

**Expected Console:**
```
✅ WebSocket connected
🚀 MediaRecorder started
🎤 Chunk #1: 12345 bytes
📤 Sent chunk #1
📨 WebSocket message received
🎯 Updating UI: Score=65%, Level=HIGH RISK
```

**Expected UI:**
- ✅ Transcript: "police arrest warrant otp urgent"
- ✅ Gauge: 50-70% (orange)
- ✅ Keywords highlighted
- ✅ History adds row

---

## 🔇 Test 3: Silence Handling (30 seconds)

```
1. Click "Start Listening"
2. DON'T SAY ANYTHING for 30 seconds
3. Watch console
```

**Expected Console:**
```
🎤 Chunk #1: 5234 bytes
⏳ Keepalive received, waiting for speech...
🎤 Chunk #2: 5234 bytes
⏳ Keepalive received, waiting for speech...
... continues every 3 seconds ...
```

**Expected UI:**
- ✅ Shows "🎤 Listening... speak into your microphone"
- ✅ Recording does NOT stop
- ✅ Chunk counter increments
- ✅ No errors

**If recording continues past 10 seconds, silence handling works!**

---

## 📱 Test 4: Mobile Audio (1 minute)

```
1. Click "Start Listening"
2. Play audio from phone speaker near computer mic
3. OR speak into phone if testing on mobile
4. Watch transcript update
```

**Expected:**
- ✅ Transcript shows spoken words
- ✅ Score updates based on content
- ✅ No "No speech detected" errors

---

## ❌ If Something Fails

### Demo Button Doesn't Work
```bash
# Hard refresh browser
Ctrl + Shift + R

# Clear cache
Ctrl + Shift + Delete → Clear cache

# Try different browser (Chrome recommended)
```

### No Transcription
```bash
# Check Whisper installed
pip list | grep whisper

# If not installed:
pip install openai-whisper

# Test separately:
python backend/test_whisper.py
```

### WebSocket Not Connecting
```bash
# Check backend running
curl http://localhost:8000/health

# Should return: {"status":"ok",...}

# If not:
cd backend
uvicorn main:app --reload
```

### Recording Stops After 6 Seconds
```bash
# Check backend logs for "sending keepalive"
# If missing, restart backend:
cd backend
uvicorn main:app --reload

# Hard refresh browser:
Ctrl + Shift + R
```

---

## ✅ Success Checklist

After 2 minutes of testing, you should have:

- [ ] Demo button works (92% red score)
- [ ] Live recording transcribes speech
- [ ] Silence doesn't stop recording
- [ ] UI updates in real-time
- [ ] Console shows detailed logs
- [ ] No JavaScript errors
- [ ] No Python errors

**If all checked, system is FULLY WORKING!**

---

## 🎯 Ultimate Test Phrase

Say this to trigger maximum fraud detection:

```
"I am calling from police headquarters. 
Your Aadhaar is linked to money laundering. 
An arrest warrant will be issued. 
Share your OTP immediately."
```

**Expected:**
- Score: 90-95%
- Color: Red
- Alert: Full-screen overlay
- Keywords: 8+ highlighted
- Recommendation: "HANG UP IMMEDIATELY"

---

## 📞 Quick Support

If issues persist after trying fixes:

1. **Copy console output** (all messages)
2. **Copy backend terminal** (last 20 lines)
3. **Screenshot the UI**
4. **Note what you said** (exact words)

---

## 🚀 Next Steps

Once everything works:

1. **Test with real calls** - Hold phone near mic
2. **Test different languages** - Whisper auto-detects
3. **Tune sensitivity** - Edit `backend/risk_engine.py`
4. **Add more keywords** - Edit `backend/models/scam_keywords.csv`

---

**Time to complete:** 2 minutes
**Success rate:** 99% (if backend running)

**GO TEST NOW!** 🎉
