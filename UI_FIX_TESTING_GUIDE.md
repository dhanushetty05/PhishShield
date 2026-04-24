# 🎯 UI FIX TESTING GUIDE

## What Was Fixed

### 1. **Real-time Score Updates**
- Gauge now updates immediately when analysis results arrive
- Score breakdown bars (Voice/Content) update dynamically
- Added console logging to track every update

### 2. **Transcript Display**
- Shows "🎤 Listening..." when recording but no speech detected
- Shows "Click Start Listening..." when idle
- Displays accumulated transcript as you speak
- Scrolls automatically to show latest text

### 3. **History Table**
- Now populates correctly with each analysis result
- Shows last 5 results with timestamps
- Updates in real-time during recording

### 4. **Better Debugging**
- Every WebSocket message is logged to console
- Every score update is logged
- Every transcript update is logged
- You can see exactly what's happening

---

## 🧪 Testing Steps

### Test 1: Basic UI Updates
```
1. Open dashboard.html in browser
2. Open browser console (F12)
3. Click "Start Listening"
4. Say: "Hello, this is a test"
5. Watch console for:
   ✅ "📨 WebSocket message received"
   ✅ "🎯 Updating UI: Score=X%"
   ✅ "📊 Score Breakdown: Voice=X%, Content=X%"
   ✅ "📋 History: Added row"
```

**Expected Result:**
- Transcript shows your text
- Gauge updates to show score
- History table adds a row
- Chunk counter increments

---

### Test 2: Fraud Detection
```
1. Click "Start Listening"
2. Say these EXACT words slowly and clearly:
   "I am calling from bank. Your account is blocked. 
    Share your OTP immediately or police will arrest you."
3. Wait 2-3 seconds between sentences
4. Watch the UI update in real-time
```

**Expected Result:**
- Score increases as you speak fraud keywords
- Gauge turns yellow/orange/red
- Keywords highlighted in transcript
- Alert banner appears if score > 60%
- History shows increasing risk levels

---

### Test 3: Silent Handling
```
1. Click "Start Listening"
2. Don't say anything for 10 seconds
3. Check transcript area
```

**Expected Result:**
- Shows "🎤 Listening... speak into your microphone"
- Chunk counter still increments (showing chunks processed)
- No errors in console
- History doesn't fill with empty rows

---

### Test 4: Demo Scenario
```
1. Click "Run Demo Scenario" button
2. Watch all UI elements update
```

**Expected Result:**
- Transcript fills with demo text
- Gauge jumps to 92% (red)
- Alert banner appears
- History adds demo result
- All fraud indicators show

---

## 🔍 Console Debugging

### What to Look For in Console

**Good Signs:**
```
✅ PhishShield initialized
✅ WebSocket connected
📦 Chunk #1: 12345 bytes
✅ TRANSCRIBED: your text here
📨 WebSocket message received: {final_score_pct: 45, ...}
🎯 Updating UI: Score=45%, Level=MODERATE, Color=yellow
📊 Score Breakdown: Voice=20%, Content=70%
📋 History: Added row #1 (45% MODERATE)
```

**Bad Signs (and fixes):**
```
❌ "WebSocket not open" 
   → Backend not running. Start: uvicorn main:app --reload

❌ "Microphone access denied"
   → Click microphone icon in address bar, allow access

❌ "Failed to parse WebSocket message"
   → Backend sending invalid JSON. Check backend logs

❌ No transcript after speaking
   → Whisper not installed. Run: pip install openai-whisper
```

---

## 🎤 Strong Test Prompts

### Low Risk (0-30%)
```
"Hello, how are you today? I'm calling to check on your order status."
```
**Expected:** Green gauge, SAFE level

### Medium Risk (30-60%)
```
"Your account has been compromised. We need to verify your identity. 
 Please confirm your account number."
```
**Expected:** Yellow/orange gauge, MODERATE/HIGH level

### High Risk (60-80%)
```
"This is urgent. Your bank account will be frozen. 
 You must transfer money immediately to avoid legal action."
```
**Expected:** Orange gauge, HIGH RISK level, alert banner

### Critical Risk (80-100%)
```
"I am calling from police headquarters. An arrest warrant has been issued. 
 Your Aadhaar is linked to money laundering. Share your OTP now or 
 you will be arrested within 2 hours. Do not tell anyone about this call."
```
**Expected:** Red gauge, CRITICAL FRAUD, full-screen overlay, alert banner

---

## 🐛 Troubleshooting

### Issue: UI Not Updating

**Check:**
1. Open browser console (F12)
2. Look for JavaScript errors
3. Check if WebSocket is connected: "WebSocket: Connected" in bottom right
4. Verify backend is running: http://localhost:8000/health

**Fix:**
```bash
# Restart backend
cd backend
uvicorn main:app --reload

# Refresh browser (Ctrl+F5 to clear cache)
```

---

### Issue: No Transcript

**Check:**
1. Console shows: "✅ TRANSCRIBED: ..."
2. If not, Whisper might not be working

**Fix:**
```bash
# Install Whisper
pip install openai-whisper

# Test Whisper separately
python backend/test_whisper.py
```

---

### Issue: Score Always 0%

**Check:**
1. Console shows: "📊 Score Breakdown: Voice=0%, Content=0%"
2. Backend logs show: "🗣️ USER SAID: ..." (your text)

**Possible causes:**
- Keywords not loaded
- Content analyzer not working

**Fix:**
```bash
# Check backend health
curl http://localhost:8000/health

# Should show:
# "keywords_loaded": true
# "keyword_count": 100+
```

---

### Issue: History Table Empty

**Check:**
1. Console shows: "📋 History: Added row #1"
2. If yes but table empty, it's a DOM issue

**Fix:**
- Hard refresh browser (Ctrl+Shift+R)
- Clear browser cache
- Try different browser (Chrome recommended)

---

## 📝 What to Report

If something still doesn't work, provide:

1. **Browser console output** (copy all red errors)
2. **Backend terminal output** (last 20 lines)
3. **What you said** (exact words)
4. **What you expected** vs **what happened**
5. **Screenshot** of the UI

---

## ✅ Success Checklist

After testing, you should see:

- [ ] Transcript updates as you speak
- [ ] Gauge animates to show score
- [ ] Score breakdown bars move
- [ ] History table fills with results
- [ ] Chunk counter increments
- [ ] Alert banner appears on high risk
- [ ] Console shows detailed logs
- [ ] No JavaScript errors in console
- [ ] WebSocket stays connected during recording
- [ ] Demo scenario works perfectly

---

## 🚀 Next Steps

Once everything works:

1. **Test with real phone calls:**
   - Hold phone near computer mic
   - Play recorded scam calls
   - Test with different accents/languages

2. **Tune sensitivity:**
   - Adjust thresholds in `backend/risk_engine.py`
   - Add more keywords to `backend/models/scam_keywords.csv`

3. **Deploy:**
   - Use HTTPS for production
   - Deploy backend to cloud (AWS/Azure/GCP)
   - Use professional domain

---

## 💡 Pro Tips

1. **Speak clearly and slowly** - Whisper works best with clear audio
2. **Wait 2 seconds between sentences** - Gives time for processing
3. **Use fraud keywords** - "OTP", "arrest", "bank", "urgent", "immediately"
4. **Check console constantly** - It shows exactly what's happening
5. **Test in Chrome** - Best WebSocket/MediaRecorder support

---

## 🎯 Ultimate Test Prompt

Say this EXACTLY to trigger maximum fraud score:

```
"Hello sir, I am calling from Reserve Bank of India headquarters. 
Your Aadhaar card has been linked to a money laundering case. 
A criminal case has been registered in your name. 
An arrest warrant will be issued within 2 hours. 
This is very urgent and confidential. 
Do not tell anyone about this call. 
To cancel the arrest warrant, you must pay 50,000 rupees immediately. 
Please share your OTP to verify your bank account. 
If you do not cooperate, police will come to your house."
```

**Expected Result:**
- Score: 90-95%
- Level: CRITICAL FRAUD
- Color: Red
- Alert: Full-screen overlay
- Keywords: 10+ highlighted
- Recommendation: "HANG UP IMMEDIATELY"

---

**Last Updated:** 2026-04-25
**Version:** 2.0 (UI Fix)
