"""
voice_analyzer.py — PhishShield
Extracts acoustic features from raw audio bytes and predicts the
probability that the voice is fraudulent (fake/spoofed/AI-cloned).

Uses:
  - librosa for feature extraction
  - Trained Random Forest model (fraud_voice_model.pkl) for classification
  - Rule-based anomaly detection for additional voice fraud signals
"""

import io
import logging
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import joblib
import librosa
import soundfile as sf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = Path(__file__).parent / "models"
RF_MODEL_PATH = MODELS_DIR / "fraud_voice_model.pkl"

# Feature extraction constants (must match dataset_loader.py)
N_MFCC = 40
SAMPLE_RATE = 16000
DURATION = 4.0
N_SAMPLES = int(SAMPLE_RATE * DURATION)

# Thresholds for rule-based anomaly detection
MFCC_VARIANCE_THRESHOLD = 50.0     # Below this = suspiciously flat MFCC (AI voice)
PITCH_STD_THRESHOLD = 10.0         # Below this = unnaturally constant pitch
RMS_THRESHOLD = 0.001              # Below this = near-silent / dead audio
PITCH_MEAN_LOW = 50.0              # Below this = robotic/very low fundamental
PITCH_MEAN_HIGH = 350.0            # Above this = suspiciously high pitch


class VoiceAnalyzer:
    """
    Analyzes raw audio to detect voice fraud characteristics.

    Combines ML model predictions with rule-based anomaly detection
    to produce a voice_fraud_score between 0.0 (safe) and 1.0 (fraud).
    """

    def __init__(self):
        self.model_bundle = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """Load the trained Random Forest model from disk."""
        if RF_MODEL_PATH.exists():
            try:
                self.model_bundle = joblib.load(RF_MODEL_PATH)
                self.model_loaded = True
                logger.info(f"✅ Voice fraud model loaded from {RF_MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load voice model: {e}")
                logger.warning("VoiceAnalyzer will use rule-based detection only.")
        else:
            logger.warning(
                f"Voice model not found at {RF_MODEL_PATH}. "
                "Run python model_trainer.py to train the model. "
                "Using rule-based detection only."
            )

    def _load_audio_from_bytes(self, audio_bytes: bytes) -> Optional[np.ndarray]:
        """
        Convert raw audio bytes to a numpy float32 waveform array.
        Handles WAV, WebM, OGG, and other formats via soundfile/librosa.

        Returns:
            Waveform array at SAMPLE_RATE, or None if loading fails
        """
        # First, try loading directly via soundfile
        try:
            buf = io.BytesIO(audio_bytes)
            y, sr = sf.read(buf, dtype="float32")
            if y.ndim > 1:
                y = y.mean(axis=1)  # Convert stereo to mono
            if sr != SAMPLE_RATE:
                y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
            return y
        except Exception:
            pass

        # Fallback: try librosa which uses pydub/ffmpeg under the hood
        try:
            buf = io.BytesIO(audio_bytes)
            y, sr = librosa.load(buf, sr=SAMPLE_RATE, mono=True, duration=DURATION)
            return y
        except Exception:
            pass

        # Last resort: try pydub to convert WebM/OGG to WAV then load
        try:
            from pydub import AudioSegment
            buf = io.BytesIO(audio_bytes)
            # Try common browser formats
            for fmt in ["webm", "ogg", "mp3", "wav"]:
                try:
                    buf.seek(0)
                    segment = AudioSegment.from_file(buf, format=fmt)
                    segment = segment.set_frame_rate(SAMPLE_RATE).set_channels(1)
                    wav_buf = io.BytesIO()
                    segment.export(wav_buf, format="wav")
                    wav_buf.seek(0)
                    y, _ = sf.read(wav_buf, dtype="float32")
                    return y
                except Exception:
                    continue
        except ImportError:
            pass

        logger.warning("All audio loading attempts failed.")
        return None

    def _extract_features(self, y: np.ndarray) -> np.ndarray:
        """
        Extract the same feature vector used during model training.
        Feature order must exactly match dataset_loader.py.

        Returns:
            numpy array of shape (98,)
        """
        # Pad or truncate to exact length
        if len(y) < N_SAMPLES:
            y = np.pad(y, (0, N_SAMPLES - len(y)), mode="constant")
        else:
            y = y[:N_SAMPLES]

        # ── MFCCs ──────────────────────────────────────────────────────────────
        mfcc = librosa.feature.mfcc(y=y, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta_mean = np.mean(mfcc_delta, axis=1)

        # ── Pitch via pyin ──────────────────────────────────────────────────────
        try:
            f0, _, _ = librosa.pyin(
                y,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=SAMPLE_RATE
            )
            f0_clean = f0[~np.isnan(f0)]
            pitch_mean = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
            pitch_std = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0
        except Exception:
            pitch_mean, pitch_std = 0.0, 0.0

        # ── Other spectral features ─────────────────────────────────────────────
        zcr_mean = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        sc_mean = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=SAMPLE_RATE)))
        sr_mean = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=SAMPLE_RATE)))
        rms_mean = float(np.mean(librosa.feature.rms(y=y)))

        # ── Chroma ─────────────────────────────────────────────────────────────
        chroma = librosa.feature.chroma_stft(y=y, sr=SAMPLE_RATE)
        chroma_mean = np.mean(chroma, axis=1)

        # Concatenate in same order as training
        feature_vector = np.concatenate([
            mfcc_mean,
            mfcc_delta_mean,
            [pitch_mean, pitch_std, zcr_mean, sc_mean, sr_mean, rms_mean],
            chroma_mean,
        ]).astype(np.float32)

        return feature_vector

    def _detect_anomalies(self, y: np.ndarray, features: np.ndarray) -> list[str]:
        """
        Rule-based checks for specific voice fraud indicators.
        These run independently of the ML model and catch patterns
        that the model may miss.

        Returns:
            List of flag strings identifying detected anomalies
        """
        flags = []

        # Extract individual feature values for rule checking
        mfcc_values = features[:N_MFCC]
        mfcc_variance = float(np.var(mfcc_values))

        pitch_mean = float(features[80])   # Index 40+40+0
        pitch_std = float(features[81])    # Index 40+40+1
        zcr_mean = float(features[82])
        rms_mean = float(features[85])

        # ── Flag: Low MFCC variance (AI-synthesized voice signature) ──────────
        # Real human voices produce variable MFCCs. AI voices are unnaturally consistent.
        if mfcc_variance < MFCC_VARIANCE_THRESHOLD:
            flags.append("low_mfcc_variance")

        # ── Flag: Unnaturally constant pitch (robotic voice) ──────────────────
        if 0 < pitch_std < PITCH_STD_THRESHOLD and pitch_mean > 0:
            flags.append("unnatural_pitch")

        # ── Flag: Near-silent audio (possible dead air / muted call) ──────────
        if rms_mean < RMS_THRESHOLD:
            flags.append("near_silent_audio")

        # ── Flag: Out-of-range pitch (robotic low or artificially high) ───────
        if pitch_mean > 0 and (pitch_mean < PITCH_MEAN_LOW or pitch_mean > PITCH_MEAN_HIGH):
            flags.append("abnormal_pitch_range")

        # ── Flag: High ZCR (excessive noise / robotic audio artifact) ─────────
        if zcr_mean > 0.25:
            flags.append("high_zero_crossing_rate")

        # ── Flag: Sudden voice switching (detect using segment analysis) ───────
        # Compare MFCC frames in first half vs second half of audio
        mfcc_full = librosa.feature.mfcc(y=y, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        if mfcc_full.shape[1] > 10:
            half = mfcc_full.shape[1] // 2
            first_half_mean = np.mean(mfcc_full[:, :half], axis=1)
            second_half_mean = np.mean(mfcc_full[:, half:], axis=1)
            voice_switch_delta = np.linalg.norm(first_half_mean - second_half_mean)
            if voice_switch_delta > 80:
                flags.append("voice_switching_detected")

        return flags

    def analyze(self, audio_bytes: bytes) -> dict:
        """
        Main analysis function. Takes raw audio bytes and returns
        a complete voice fraud analysis result.

        Args:
            audio_bytes: Raw audio data (WAV, WebM, OGG, MP3)

        Returns:
            dict with keys:
              - voice_fraud_score (float 0.0–1.0)
              - flags (list of detected anomaly strings)
              - pitch_mean (float)
              - mfcc_variance (float)
              - is_silent (bool)
        """
        # Default result in case of failure
        default_result = {
            "voice_fraud_score": 0.5,
            "flags": ["analysis_failed"],
            "pitch_mean": 0.0,
            "mfcc_variance": 0.0,
            "is_silent": False,
        }

        # ── Load and validate audio ───────────────────────────────────────────
        y = self._load_audio_from_bytes(audio_bytes)
        if y is None:
            logger.warning("Could not load audio bytes.")
            return default_result

        # Check if audio is essentially silent
        rms = float(np.sqrt(np.mean(y ** 2)))
        if rms < 0.0005:
            return {
                "voice_fraud_score": 0.0,
                "flags": ["silent_audio"],
                "pitch_mean": 0.0,
                "mfcc_variance": 0.0,
                "is_silent": True,
            }

        # ── Extract features ──────────────────────────────────────────────────
        try:
            features = self._extract_features(y)
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return default_result

        # ── ML model prediction ───────────────────────────────────────────────
        ml_score = 0.5  # Neutral default if model not available
        if self.model_loaded and self.model_bundle is not None:
            try:
                scaler = self.model_bundle["scaler"]
                model = self.model_bundle["model"]
                features_scaled = scaler.transform(features.reshape(1, -1))
                # predict_proba returns [P(real), P(spoof)]
                proba = model.predict_proba(features_scaled)[0]
                ml_score = float(proba[1])  # Probability of being spoof/fraud
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}. Using rule-based score only.")
                ml_score = 0.5

        # ── Rule-based anomaly detection ──────────────────────────────────────
        flags = self._detect_anomalies(y, features)

        # ── Combine ML score with flag-based penalty ──────────────────────────
        # Each flag adds a penalty to push score toward fraud
        flag_penalties = {
            "low_mfcc_variance": 0.15,
            "unnatural_pitch": 0.12,
            "abnormal_pitch_range": 0.10,
            "voice_switching_detected": 0.20,
            "high_zero_crossing_rate": 0.08,
            "near_silent_audio": 0.05,
        }
        flag_score = sum(flag_penalties.get(f, 0.05) for f in flags)

        # Blend ML prediction (70%) + flag-based score (30%)
        if self.model_loaded:
            final_score = (ml_score * 0.70) + (min(flag_score, 1.0) * 0.30)
        else:
            # No model: use flags + neutral baseline
            final_score = 0.3 + min(flag_score, 0.7)

        final_score = float(np.clip(final_score, 0.0, 1.0))

        # ── Return result ─────────────────────────────────────────────────────
        mfcc_full = librosa.feature.mfcc(y=y[:N_SAMPLES], sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        mfcc_variance = float(np.var(np.mean(mfcc_full, axis=1)))

        pitch_mean_value = float(features[80]) if len(features) > 80 else 0.0

        return {
            "voice_fraud_score": round(final_score, 4),
            "flags": flags,
            "pitch_mean": round(pitch_mean_value, 2),
            "mfcc_variance": round(mfcc_variance, 4),
            "is_silent": False,
        }


# ── Singleton instance (loaded once when module is imported) ─────────────────
_analyzer_instance: Optional[VoiceAnalyzer] = None


def get_voice_analyzer() -> VoiceAnalyzer:
    """Return a singleton VoiceAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = VoiceAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # Quick test with a dummy silent audio (for smoke testing)
    import sys

    analyzer = VoiceAnalyzer()

    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        logger.info(f"Analyzing: {audio_path}")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        result = analyzer.analyze(audio_bytes)
        print("\nVoice Analysis Result:")
        for key, val in result.items():
            print(f"  {key}: {val}")
    else:
        # Generate 3 seconds of silent audio for testing
        sample_rate = 16000
        silence = np.zeros(sample_rate * 3, dtype=np.float32)
        buf = io.BytesIO()
        sf.write(buf, silence, sample_rate, format="WAV")
        audio_bytes = buf.getvalue()

        result = analyzer.analyze(audio_bytes)
        print("\nTest result (silent audio):")
        for key, val in result.items():
            print(f"  {key}: {val}")
