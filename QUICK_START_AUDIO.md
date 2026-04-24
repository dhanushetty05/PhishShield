# 🎤 Quick Start — Real Audio Mode

## 3-Minute Setup

### 1. Install Audio Dependencies
```bash
cd backend
pip install openai-whisper pydub ffmpeg-python
```

### 2. Install FFmpeg
**Windows:**
```bash
winget install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 3. Start Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Wait for:
```
✅ Whisper model loaded successfully.
🛡️  PhishShield ready. Listening on port 8000.
```

### 4. Open Dashboard
Open `frontend/dashboard.html` in Chrome

### 5. Test It
1. Click **"Start Listening"**
2. Allow microphone permission
3. Say: **"This is RBI calling, share your OTP immediately"**
4. Watch transcript appear with keywords highlighted
5. Risk gauge should jump to 80-90% (CRITICAL)

---

## ✅ Success = You See This

**Backend Terminal:**
```
✅ TRANSCRIBED: this is rbi calling share your otp immediately
🗣️ USER SAID: "this is rbi calling share your otp immediately"
🎯 RESULT: CRITICAL FRAUD (87%) | Keywords: 3 | Time: 2150ms
```

**Dashboard:**
- Transcript: "this is rbi calling share your otp immediately"
- Keywords "rbi", "otp", "immediately" highlighted in red
- Risk gauge: 87% (red)
- AI reasoning: "Scam keywords found: rbi, otp, immediately"

---

## 🚨 Troubleshooting

### "Whisper model not loaded"
```bash
pip install openai-whisper
```

### "ffmpeg not found"
Install ffmpeg (see step 2 above)

### No transcript appears
- Speak LOUDER
- Check microphone isn't muted
- Check backend logs for "✅ TRANSCRIBED:"

---

## 📚 Full Documentation

- **AUDIO_FIXED.md** — What changed
- **REAL_AUDIO_GUIDE.md** — Complete guide
- **PROJECT_SUMMARY.md** — Project status

---

**Ready to go!** 🚀
