# 🎯 STRONG TEST PROMPTS FOR PHISHSHIELD

## Quick Test Phrases (Copy & Speak)

### 🟢 SAFE (0-30%) - Should Stay Green
```
"Hello, I'm calling to confirm your appointment for tomorrow at 3 PM. 
 Please let me know if you need to reschedule. Thank you."
```

---

### 🟡 SUSPICIOUS (30-50%) - Should Turn Yellow
```
"Your account has been compromised. We need to verify your identity. 
 Please confirm your account number for security purposes."
```

---

### 🟠 HIGH RISK (50-70%) - Should Turn Orange
```
"This is urgent. Your bank account will be frozen today. 
 You must transfer money immediately to avoid legal action. 
 Call this number back within 30 minutes."
```

---

### 🔴 CRITICAL FRAUD (70-100%) - Should Turn Red + Alert
```
"I am calling from police headquarters. An arrest warrant has been issued in your name. 
 Your Aadhaar card is linked to a money laundering case. 
 You will be arrested within 2 hours. 
 This is confidential - do not tell anyone about this call. 
 To cancel the warrant, you must pay 50,000 rupees bail immediately. 
 Share your OTP to verify your bank account."
```

---

## 🎯 Maximum Fraud Score Prompt (95%+)

**Say this SLOWLY and CLEARLY:**

```
"Hello sir, I am calling from Reserve Bank of India headquarters. 
Your Aadhaar card has been used for illegal money laundering activities. 
A criminal case has been registered at the cyber crime police station. 
An arrest warrant will be issued in your name within 2 hours. 
This matter is very urgent and highly confidential. 
Do not disconnect this call or tell anyone including your family. 
To cancel the arrest warrant and close the case, 
you must immediately transfer 50,000 rupees as bail amount. 
Please share your bank account OTP to verify your identity. 
If you do not cooperate, police officers will come to your house 
and arrest you in front of your neighbors."
```

**Expected Result:**
- Score: 92-98%
- Level: CRITICAL FRAUD
- Color: Red with pulsing animation
- Alert: Full-screen fraud overlay
- Banner: "🚨 CRITICAL FRAUD DETECTED"
- Keywords: 15+ highlighted (RBI, Aadhaar, arrest, money laundering, OTP, police, urgent, confidential, immediately, do not tell)
- Recommendation: "HANG UP IMMEDIATELY"

---

## 🔑 High-Impact Keywords

Use these words to trigger high scores:

### Authority Impersonation
- "police", "RBI", "Reserve Bank", "cyber crime", "government", "officer"

### Threat Language  
- "arrest warrant", "legal action", "criminal case", "jail", "court"

### Urgency Tactics
- "immediately", "urgent", "within 2 hours", "right now", "today"

### Secrecy Demands
- "do not tell anyone", "confidential", "secret", "do not disconnect"

### Money Requests
- "transfer money", "pay", "bail amount", "fine", "penalty"

### Information Phishing
- "OTP", "password", "PIN", "account number", "Aadhaar", "verify"

---

## 🧪 Testing Scenarios

### Scenario 1: Bank Fraud
```
"Your debit card has been blocked due to suspicious activity. 
 To unblock it, please share the OTP sent to your phone."
```
**Expected:** 60-70%, HIGH RISK, orange

---

### Scenario 2: Tech Support Scam
```
"Your computer has been infected with a virus. 
 We detected illegal activity from your IP address. 
 You must install our security software immediately 
 or your data will be deleted."
```
**Expected:** 50-65%, HIGH RISK, yellow/orange

---

### Scenario 3: Government Impersonation
```
"This is the Income Tax Department. 
 You have unpaid taxes and penalties. 
 An arrest warrant has been issued. 
 Pay immediately to avoid legal consequences."
```
**Expected:** 75-85%, CRITICAL FRAUD, red

---

### Scenario 4: Prize/Lottery Scam
```
"Congratulations! You have won 10 lakh rupees in a lottery. 
 To claim your prize, you must first pay 5000 rupees processing fee. 
 Share your bank details to receive the money."
```
**Expected:** 55-70%, HIGH RISK, orange

---

### Scenario 5: Family Emergency Scam
```
"Your son has been in a serious accident. 
 He is in the hospital and needs immediate surgery. 
 You must transfer 2 lakh rupees right now 
 or he will not survive. This is very urgent."
```
**Expected:** 65-80%, CRITICAL FRAUD, red

---

## 📊 Score Ranges Explained

| Score | Level | Color | UI Behavior |
|-------|-------|-------|-------------|
| 0-30% | SAFE | 🟢 Green | Normal display |
| 31-60% | MODERATE/HIGH | 🟡 Yellow | Warning indicators |
| 61-80% | HIGH RISK | 🟠 Orange | Alert banner slides down |
| 81-100% | CRITICAL FRAUD | 🔴 Red | Full-screen overlay + banner + pulse animation |

---

## 🎬 Demo Mode Test

Click "Run Demo Scenario" button to see:
- Pre-loaded fraud transcript
- 92% score
- All fraud indicators
- Full UI response

---

## 🔊 Audio Quality Tips

For best results:
1. **Speak clearly** - Enunciate each word
2. **Speak slowly** - Pause between sentences
3. **Use good microphone** - Built-in laptop mic works fine
4. **Reduce background noise** - Close windows, turn off fans
5. **Wait 2 seconds** - Between sentences for processing

---

## 🐛 If Score Stays at 0%

Try saying these HIGH-IMPACT phrases:

```
"Police arrest warrant OTP Aadhaar money laundering urgent immediately"
```

If still 0%, check:
- Backend is running (`uvicorn main:app --reload`)
- Keywords loaded (`curl http://localhost:8000/health`)
- Console shows transcription (`✅ TRANSCRIBED: ...`)

---

## 💡 Pro Testing Tips

1. **Start with demo button** - Verify UI works
2. **Test safe phrase first** - Should stay green
3. **Gradually increase risk** - Watch score climb
4. **Use maximum fraud prompt** - Should hit 90%+
5. **Check console logs** - See exactly what's detected

---

## 🎯 Quick Verification

Say: **"Police arrest OTP urgent"**

Should immediately show:
- Score jumps to 40-60%
- Color changes to yellow/orange
- Keywords highlighted
- History updates

---

## 📱 Real Phone Call Testing

1. **Play recorded scam call** near microphone
2. **Hold phone speaker** close to computer mic
3. **Use speakerphone** for clearer audio
4. **Test with different languages** (if supported)

---

## ✅ Success Indicators

You know it's working when:
- ✅ Transcript updates as you speak
- ✅ Score changes in real-time
- ✅ Gauge animates smoothly
- ✅ Keywords get highlighted
- ✅ History table fills up
- ✅ Alert appears on high risk
- ✅ Console shows detailed logs

---

**Remember:** The system analyzes ACCUMULATED text, so the more you speak, the more accurate the detection becomes!

---

**Last Updated:** 2026-04-25
**Version:** 2.0
