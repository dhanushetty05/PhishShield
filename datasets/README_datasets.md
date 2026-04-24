# PhishShield — Dataset Guide

This document explains how to download and use the real-world audio datasets
that PhishShield's AI models are trained on.

---

## Dataset 1: ASVspoof 2019 (Primary — Required for Voice Model)

**Purpose**: Train the voice fraud classifier to detect AI-synthesized and cloned voices.

**Source**: University of Edinburgh DataShare  
**URL**: https://datashare.ed.ac.uk/handle/10283/3336  
**License**: Free for research use (requires registration)

### What It Contains

| Subset | Real Voices | Spoofed Voices | Total |
|---|---|---|---|
| Train | 2,580 | 22,800 | 25,380 |
| Dev   | 2,548 | 22,296 | 24,844 |
| Eval  | 7,355 | 63,882 | 71,237 |

- **Bonafide**: Real human speech recordings
- **Spoof**: AI-generated voices using 19 different attack algorithms (TTS, voice conversion, GAN-based)
- **Format**: FLAC audio files + protocol text files with labels

### Download Steps

1. Visit https://datashare.ed.ac.uk/handle/10283/3336
2. Click **"Login to download"** — create a free Edinburgh DataShare account
3. Download **ASVspoof2019_LA_train.zip** (~3.5 GB)
4. Download **ASVspoof2019_LA_dev.zip** (~3.5 GB)
5. Download **ASVspoof2019_LA_protocols.zip** (~small)
6. Extract all files into a single folder

### Required Folder Structure

```
/your/path/ASVspoof2019/
└── LA/
    ├── ASVspoof2019_LA_train/
    │   └── flac/
    │       ├── LA_T_1000137.flac
    │       ├── LA_T_1000723.flac
    │       └── ... (25,380 files)
    ├── ASVspoof2019_LA_dev/
    │   └── flac/
    │       └── ... (24,844 files)
    └── ASVspoof2019_LA_protocols/
        ├── ASVspoof2019.LA.cm.train.trn.txt
        ├── ASVspoof2019.LA.cm.dev.trl.txt
        └── ASVspoof2019.LA.cm.eval.trl.txt
```

### How to Use with PhishShield

```bash
# Train the model using the real dataset
cd backend
python model_trainer.py /your/path/ASVspoof2019
```

### Label File Format

Each line in the protocol file looks like:
```
LA_0069 LA_T_1000137 - - A07 spoof
LA_0069 LA_T_1000138 - - - bonafide
```
Fields: `speaker_id  file_id  environment  channel  attack_type  label`

- `bonafide` = real human voice (label 0 = safe)
- `spoof` = AI-generated voice (label 1 = fraud)

### Feature Extraction Details

For each FLAC file, PhishShield extracts a 98-dimensional feature vector:

| Feature | Dimensions | Description |
|---|---|---|
| MFCC (mean) | 40 | Mel-frequency cepstral coefficients — voice timbre |
| MFCC delta (mean) | 40 | First derivative of MFCCs — voice dynamics |
| Pitch mean | 1 | Fundamental frequency (Hz) |
| Pitch std | 1 | Pitch variability — flat pitch = synthetic voice |
| Zero Crossing Rate | 1 | Signal sign changes — noisiness measure |
| Spectral Centroid | 1 | Brightness of audio spectrum |
| Spectral Rolloff | 1 | Frequency distribution shape |
| RMS Energy | 1 | Loudness envelope |
| Chroma (mean) | 12 | Harmonic content per musical pitch class |
| **Total** | **98** | |

---

## Dataset 2: RAVDESS (Emotional Speech Detection)

**Purpose**: Detect emotional manipulation tactics — urgency, fear, anger — commonly used by scammers.

**URL**: https://zenodo.org/record/1188976  
**License**: CC BY-NA-SC 4.0 (free for non-commercial research)

### What It Contains

- 24 professional actors (12 male, 12 female)
- 8 emotions: neutral, calm, happy, sad, **angry, fearful, disgust, surprised**
- 1,440 audio files in WAV format
- Each actor reads two sentences at two intensity levels

### Download Steps

1. Visit https://zenodo.org/record/1188976
2. Click **"Download"** button
3. Download `Audio_Speech_Actors_01-24.zip` (~215 MB)
4. Extract to `datasets/RAVDESS/`

### Folder Structure

```
datasets/RAVDESS/
├── Actor_01/
│   ├── 03-01-01-01-01-01-01.wav  (neutral)
│   ├── 03-01-05-01-01-01-01.wav  (angry)
│   └── ...
├── Actor_02/
│   └── ...
└── ...
```

### RAVDESS Filename Encoding

Filename: `03-01-05-02-01-01-01.wav`
- Position 3: Emotion (01=neutral, 02=calm, 03=happy, 04=sad, **05=angry, 06=fearful**, 07=disgust, 08=surprised)
- Position 4: Intensity (01=normal, **02=strong**)

### How PhishShield Uses This

Scammers often speak with artificially amplified emotions:
- **Fearful tone** → "Your account will be arrested in 2 hours!"
- **Angry urgency** → "Pay immediately or face legal action!"
- **Surprised delivery** → "You've WON the lottery!"

RAVDESS teaches the pitch/tone analyzer to distinguish natural emotional speech from scripted emotional manipulation.

```python
# Example usage in voice_analyzer.py
# High pitch variance + fearful tone patterns → boost fraud score
```

---

## Dataset 3: Mozilla Common Voice (Normal Speech Baseline)

**Purpose**: Provide thousands of examples of normal, safe human speech so the model learns what legitimate calls look like.

**URL**: https://commonvoice.mozilla.org/en/datasets  
**License**: CC0 (public domain — completely free)

### What It Contains

- **27,000+ hours** of recorded speech
- Millions of audio clips from real volunteers worldwide
- Multiple languages (use English subset for PhishShield)
- TSV metadata files with transcriptions

### Download Steps

1. Visit https://commonvoice.mozilla.org/en/datasets
2. Select **English** language
3. Click **"Download Dataset"** (requires free Mozilla account)
4. Download the latest version (Common Voice 17.0 or later)
5. Extract to `datasets/CommonVoice/`

### Folder Structure

```
datasets/CommonVoice/
├── clips/
│   ├── common_voice_en_00001.mp3
│   ├── common_voice_en_00002.mp3
│   └── ... (millions of files)
├── train.tsv
├── test.tsv
└── validated.tsv
```

### TSV Format

```
client_id  path            sentence         up_votes  down_votes  age  gender  ...
abc123     clips/xxx.mp3   "Hello world"    5         0           20s  male    ...
```

### How to Use as "Safe" Training Data

Common Voice clips are labeled as `bonafide` (label 0) and mixed with the ASVspoof training data to prevent the model from becoming too sensitive and flagging all calls as fraud.

```python
# In dataset_loader.py, use Common Voice clips as "real" examples
# alongside ASVspoof bonafide recordings
```

---

## Dataset 4: FoR Dataset (Fake or Real)

**Purpose**: Deepfake audio detection — GAN-generated synthetic speech vs real human speech.

**URL**: https://bil.eecs.yorku.ca/datasets/  
**License**: Research use

### What It Contains

- **87,000+ audio clips**
- Real: Recordings from various speakers
- Fake: GAN-generated speech (WaveGAN, WaveNet, Tacotron)
- Format: WAV files organized in real/ and fake/ folders
- Binary classification: real (0) vs fake (1)

### Download Steps

1. Visit https://bil.eecs.yorku.ca/datasets/
2. Find "FoR — Fake or Real" dataset
3. Download the WAV version (recommended)
4. Extract to `datasets/FoR/`

### Folder Structure

```
datasets/FoR/
├── training/
│   ├── real/
│   │   ├── real_001.wav
│   │   └── ...
│   └── fake/
│       ├── fake_001.wav
│       └── ...
├── validation/
│   ├── real/
│   └── fake/
└── testing/
    ├── real/
    └── fake/
```

### How PhishShield Uses FoR

The FoR dataset specifically targets **GAN-generated** speech, which is becoming common in scam calls where scammers use AI to clone the voice of a family member ("grandparent scam") or authority figure.

The model learns to detect:
- Unnaturally smooth spectral transitions (GAN artifact)
- Missing natural breath sounds
- Abnormally consistent pitch contours

---

## Dataset 5: Custom Scam Keyword Dataset (Auto-Generated)

**Purpose**: Content-based fraud scoring using weighted keyword patterns.

**Generated by**: `content_analyzer.py` automatically on first run

### What It Contains

- 200+ scam phrases with risk weights (0.0–1.0)
- Organized by fraud category:
  - Indian Banking: OTP, UPI PIN, Aadhaar, CVV
  - Government Impersonation: RBI, CBI, income tax, TRAI
  - Urgency language: immediately, within 24 hours, act now
  - Threat language: arrest warrant, FIR, legal action
  - Prize scams: lottery winner, claim your prize
  - Remote access: AnyDesk, TeamViewer, install app

### File Location

```
backend/models/scam_keywords.csv
```

Auto-generated on first run if not present. You can edit this CSV to add custom keywords.

### CSV Format

```csv
phrase,risk_weight
otp,0.95
arrest warrant,0.95
aadhaar number,0.85
you have won,0.90
anydesk,0.90
rbi officer,0.92
...
```

### Adding Custom Keywords

1. Open `backend/models/scam_keywords.csv` in any text editor or spreadsheet app
2. Add new rows: `your phrase,0.85`
3. Restart the backend — changes are loaded automatically
4. Higher weight (closer to 1.0) = stronger fraud signal

---

## Quick Setup for Demo (No Dataset Download Required)

If you want to test PhishShield without downloading the large datasets,
the system will automatically generate a synthetic training dataset:

```bash
cd backend
python model_trainer.py
# No arguments = uses synthetic data
```

The synthetic dataset generates:
- 1,500 "real voice" samples with natural MFCC distributions
- 1,500 "fake voice" samples with flat/robotic MFCC distributions
- Trains the Random Forest in ~30 seconds on CPU
- Achieves ~85% accuracy on synthetic test set

**Note**: The synthetic model will be less accurate on real calls than a model trained on ASVspoof 2019. Download the real datasets for production use.

---

## Storage Requirements

| Dataset | Size | Training Time (CPU) |
|---|---|---|
| ASVspoof 2019 (LA train+dev) | ~7 GB | 15–30 min |
| RAVDESS | ~215 MB | 1–2 min |
| Common Voice (English) | ~70 GB | Several hours |
| FoR Dataset | ~4 GB | 10–20 min |
| Synthetic (built-in) | 0 GB | ~30 sec |

**Recommendation**: Start with ASVspoof 2019 + synthetic data. That combination gives the best accuracy-to-effort ratio.

---

## Pre-processing Pipeline

All datasets go through the same pre-processing pipeline before training:

```
Raw Audio File
     │
     ▼
Resample to 16kHz mono
     │
     ▼
Clip/pad to exactly 4 seconds
     │
     ▼
Extract 98 features:
  ├── 40 MFCC (mean)
  ├── 40 MFCC delta (mean)
  ├── pitch mean + std
  ├── ZCR, spectral centroid, rolloff, RMS
  └── 12 chroma features
     │
     ▼
Save to DataFrame row: [feature_0 ... feature_97, label]
     │
     ▼
80/20 train/test split
     │
     ▼
Train Random Forest + LSTM
```

---

## Troubleshooting Dataset Loading

**Error: `FileNotFoundError: Audio directory not found`**
→ Check that folder structure matches exactly as shown above

**Error: `librosa.load failed`**  
→ Install ffmpeg: `brew install ffmpeg` or `apt install ffmpeg`  
→ FLAC files require ffmpeg for librosa to read them

**Error: `No features could be extracted`**  
→ Audio files may be corrupt; try re-downloading the dataset

**Training too slow**  
→ Set `max_files=1000` in `dataset_loader.py` to train on a smaller subset  
→ Or use `n_jobs=-1` in Random Forest (already set) to use all CPU cores

**Out of memory during training**  
→ Reduce `max_files` in `dataset_loader.py` to 2000 or less  
→ Reduce `batch_size` in LSTM training to 16
