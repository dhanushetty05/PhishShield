# 🎤 Real Audio Setup Guide — PhishShield

## What Changed

I've fixed the audio pipeline to work with REAL microphone input and continuous transcription:

### ✅ Fixed Issues:
1. **Whisper transcription** now runs on every audio chunk
2. **Transcript accumulation** — all speech is combined into one continuous text
3. **Better logging** — you'll see exactly what Whisper hears
4. **Continuous listening** — doesn't stop after one chunk
5. **WebSocket stays open** — no disconnections during recording

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Audio Dependencies

```bash
cd backend
pip install openai-whisper pydub ffmpeg-python librosa soundfile
```

### Step 2: Install FFmpeg (Required for Audio Conversion)

**Windows:**
```bash
winget install ffmpeg
# OR download from: https://ffmpeg.org/download.html
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Step 3: Start Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🎯 How It Works Now

### Audio Flow:
```
Your Voice
    ↓
Microphone (browser captures)
    ↓
MediaRecorder (2-second chunks)
    ↓
WebSocket → Backend
    ↓
Convert WebM → WAV (pydub + ffmpeg)
    ↓
Whisper Transcription (tiny model, ~1-2 seconds)
    ↓
Content Analysis (keywords + NLP)
    ↓
Risk Score Calculation
    ↓
WebSocket → Frontend
    ↓
Dashboard Updates (transcript accumulates)
```

### What You'll See:

1. **In Browser Console:**
   - "🎤 Chunk: 45678 bytes"
   - "📤 Sending..."

2. **In Backend Terminal:**
   - "📦 Audio: 45678 bytes → WAV: 32000 bytes"
   - "✅ TRANSCRIBED: hello this is a test"
   - "🗣️ USER SAID: \"hello this is a test\""
   - "🎯 RESULT: SAFE (15%) | Keywords: 0 | Time: 1850ms"

3. **In Dashboard:**
   - Transcript appears and grows as you speak
   - Keywords highlighted in red
   - Risk gauge updates every 2 seconds
   - AI reasoning shows detected patterns

---

## 🧪 Testing

### Test 1: Normal Speech
```
Say: "Hello, this is a test of the microphone"
Expected: SAFE (0-20%), no keywords
```

### Test 2: Suspicious Keywords
```
Say: "I need your OTP and bank account number"
Expected: SUSPICIOUS (40-60%), keywords: "OTP", "bank account"
```

### Test 3: Fraud Scenario
```
Say: "This is RBI calling. Your Aadhaar is blocked. Share your OTP immediately or you will be arrested"
Expected: CRITICAL (80-95%), keywords: "RBI", "Aadhaar", "OTP", "arrested"
```

---

## 🔍 Troubleshooting

### Issue 1: "Whisper model not loaded"

**Symptom:** Backend logs show "⚠️ Whisper model not loaded — skipping transcription"

**Solution:**
```bash
pip install openai-whisper
```

On first run, Whisper will download the `tiny` model (~75MB). This is normal.

---

### Issue 2: "Audio conversion failed"

**Symptom:** Backend logs show "Audio conversion failed: [Errno 2] No such file or directory: 'ffmpeg'"

**Solution:** Install ffmpeg (see Step 2 above)

**Verify installation:**
```bash
ffmpeg -version
```

Should show version info. If not, ffmpeg isn't in your PATH.

---

### Issue 3: No transcript appears

**Symptom:** Dashboard shows "Listening..." but no text appears

**Possible causes:**

1. **Microphone not working:**
   - Check browser console for errors
   - Try speaking LOUDER
   - Check Windows sound settings (microphone not muted)

2. **Whisper too slow:**
   - Current model: `tiny` (fastest, ~1-2 seconds)
   - If still slow, your CPU might be overloaded
   - Close other apps

3. **Audio chunks too short:**
   - Current: 2-second chunks
   - Whisper needs at least 1 second of speech
   - Try speaking for 3-4 seconds continuously

---

### Issue 4: Transcript is gibberish

**Symptom:** Whisper transcribes random words that don't match what you said

**Causes:**
- Background noise (fan, music, traffic)
- Microphone too far away
- Low-quality microphone
- Speaking too quietly

**Solutions:**
- Move closer to microphone
- Reduce background noise
- Speak clearly and at normal volume
- Use a better microphone (headset recommended)

---

### Issue 5: "WebSocket connection failed"

**Symptom:** Dashboard shows "WebSocket: Failed to connect"

**Solution:**
1. Check backend is running: `http://localhost:8000/health`
2. Restart backend: `Ctrl+C` then `uvicorn main:app --host 0.0.0.0 --port 8000`
3. Check firewall isn't blocking port 8000

---

## ⚡ Performance Tips

### Current Setup (Optimized for Demo):
- **Whisper model:** `tiny` (75MB, ~1-2 seconds per chunk)
- **Chunk interval:** 2 seconds
- **Voice analysis:** DISABLED (saves 15-20 seconds per chunk)
- **Total latency:** ~2-3 seconds per update

### If You Want Faster:
```python
# In backend/main.py, line 60:
whisper_model = whisper.load_model("tiny")  # ← Already using fastest
```

### If You Want More Accurate:
```python
# In backend/main.py, line 60:
whisper_model = whisper.load_model("base")  # ← Better accuracy, 3-4 seconds
```

### If You Want to Enable Voice Analysis:
```python
# In backend/main.py, around line 180:
# Change this:
voice_result = {
    "voice_fraud_score": 0.0,
    "flags": [],
    "is_silent": len(transcript) == 0
}

# To this:
t_voice = time.monotonic()
voice_result = voice_analyzer.analyze(wav_bytes)
voice_ms = (time.monotonic() - t_voice) * 1000
logger.info(f"⏱️ Voice analysis: {voice_ms:.0f}ms")
```

**Warning:** Voice analysis adds 15-20 seconds per chunk on CPU!

---

## 📊 Expected Performance

### On Modern CPU (i5/i7/Ryzen 5):
- Audio conversion: ~100-200ms
- Whisper transcription: ~1000-2000ms
- Content analysis: ~50-100ms
- **Total:** ~1.5-2.5 seconds per chunk

### On Older CPU:
- Audio conversion: ~200-500ms
- Whisper transcription: ~3000-5000ms
- Content analysis: ~100-200ms
- **Total:** ~3.5-5.5 seconds per chunk

---

## 🎬 Demo Mode vs Real Audio

### Demo Mode (Current Default):
- ✅ Works instantly
- ✅ No audio setup needed
- ✅ Shows all UI features
- ❌ Not real-time
- ❌ Doesn't use microphone

### Real Audio Mode (After Setup):
- ✅ Uses real microphone
- ✅ Real-time transcription
- ✅ Continuous listening
- ✅ Accumulates transcript
- ⚠️ Requires ffmpeg + Whisper
- ⚠️ 2-3 second latency

**For demo/presentation:** Use demo button  
**For testing real audio:** Use "Start Listening" button

---

## 🔧 Advanced Configuration

### Change Chunk Interval:

In `frontend/app.js`, line 200:
```javascript
mediaRecorder.start(2000);  // ← 2000ms = 2 seconds
```

**Shorter (1 second):** Faster updates, more CPU usage  
**Longer (5 seconds):** Slower updates, less CPU usage

### Change Whisper Language:

In `backend/main.py`, line 95:
```python
result = whisper_model.transcribe(
    tmp_path,
    language="en",  # ← Change to "hi" for Hindi, "auto" for auto-detect
    ...
)
```

### Disable Transcript Accumulation:

In `frontend/app.js`, around line 350:
```javascript
// Change this:
if (fullTranscript) {
  fullTranscript += " " + transcript;
} else {
  fullTranscript = transcript;
}

// To this (show only latest chunk):
fullTranscript = transcript;
```

---

## 📝 What Changed in Code

### Backend (`main.py`):
1. ✅ Whisper transcription now ALWAYS runs (was skipped before)
2. ✅ Better logging with emojis (easy to see what's happening)
3. ✅ Transcript logged every time
4. ✅ Voice analysis still disabled (for speed)

### Frontend (`app.js`):
1. ✅ Added `fullTranscript` variable to accumulate text
2. ✅ Transcript appends instead of replaces
3. ✅ Auto-scroll to bottom of transcript
4. ✅ Better placeholder text
5. ✅ Reset transcript on stop

---

## ✅ Success Checklist

When everything is working, you should see:

- [ ] Backend starts without errors
- [ ] Dashboard loads without errors
- [ ] Click "Start Listening" → microphone permission granted
- [ ] Speak into microphone
- [ ] Backend logs show: "✅ TRANSCRIBED: [your words]"
- [ ] Dashboard transcript updates with your words
- [ ] Keywords highlighted if you say fraud terms
- [ ] Risk gauge updates
- [ ] AI reasoning panel shows analysis
- [ ] Can speak continuously for 30+ seconds
- [ ] Transcript keeps growing
- [ ] Click "Stop Listening" → everything stops cleanly

---

## 🆘 Still Not Working?

### Check Backend Logs:

Look for these lines:
```
✅ Whisper model loaded successfully.
✅ Voice fraud model loaded from ...
✅ Analysis modules loaded.
🛡️  PhishShield ready. Listening on port 8000.
```

If you see errors here, dependencies aren't installed correctly.

### Check Browser Console:

Look for these lines:
```
✅ WebSocket connected
🎤 Chunk: 45678 bytes
📤 Sending...
```

If you see errors here, WebSocket isn't connecting.

### Test Whisper Directly:

```bash
cd backend
python
>>> import whisper
>>> model = whisper.load_model("tiny")
>>> result = model.transcribe("test.wav")
>>> print(result["text"])
```

If this fails, Whisper isn't installed correctly.

---

## 🎯 Summary

**What you need:**
1. `pip install openai-whisper pydub ffmpeg-python`
2. Install ffmpeg system-wide
3. Start backend
4. Click "Start Listening"
5. Speak into microphone
6. Watch transcript appear in real-time

**What you'll get:**
- Real-time speech-to-text
- Continuous transcript accumulation
- Fraud keyword detection
- Risk score updates every 2 seconds
- AI reasoning explanations

**Performance:**
- ~2-3 seconds latency per chunk
- Works on any modern CPU
- No GPU required

---

**Last Updated:** April 24, 2026  
**Version:** 3.1.0  
**Status:** Real Audio Ready 🎤
