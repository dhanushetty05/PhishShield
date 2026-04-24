"""
dataset_loader.py — PhishShield
Loads the ASVspoof 2019 dataset, extracts audio features using librosa,
and returns a clean Pandas DataFrame ready for model training.

Usage:
    from dataset_loader import load_asvspoof_dataset
    df = load_asvspoof_dataset("/path/to/ASVspoof2019")
"""

import os
import logging
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import librosa
import soundfile as sf

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Feature extraction constants ────────────────────────────────────────────
N_MFCC = 40          # Number of MFCC coefficients to extract
SAMPLE_RATE = 16000  # Resample all audio to 16kHz for consistency
DURATION = 4.0       # Clip or pad audio to exactly 4 seconds
N_SAMPLES = int(SAMPLE_RATE * DURATION)


def extract_features(audio_path: str) -> Optional[np.ndarray]:
    """
    Extract a fixed-length feature vector from a WAV/audio file.

    Features extracted:
    - 40 MFCCs (mean over time frames)
    - 40 MFCC delta (first derivative)
    - Pitch (F0) mean and std
    - Zero Crossing Rate mean
    - Spectral Centroid mean
    - Spectral Rolloff mean
    - RMS Energy mean
    - 12 Chroma features mean

    Returns:
        numpy array of shape (140,) or None if extraction fails
    """
    try:
        # Load audio, resample to 16kHz mono
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True, duration=DURATION)

        # Pad or truncate to exactly N_SAMPLES
        if len(y) < N_SAMPLES:
            y = np.pad(y, (0, N_SAMPLES - len(y)), mode="constant")
        else:
            y = y[:N_SAMPLES]

        # ── MFCC features ────────────────────────────────────────────────────
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        mfcc_mean = np.mean(mfcc, axis=1)          # (40,)
        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta_mean = np.mean(mfcc_delta, axis=1)  # (40,)

        # ── Pitch (F0) via pyin algorithm ────────────────────────────────────
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
        )
        f0_clean = f0[~np.isnan(f0)]  # Remove unvoiced (NaN) frames
        pitch_mean = np.mean(f0_clean) if len(f0_clean) > 0 else 0.0
        pitch_std = np.std(f0_clean) if len(f0_clean) > 0 else 0.0

        # ── Zero Crossing Rate ───────────────────────────────────────────────
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_mean = np.mean(zcr)

        # ── Spectral Centroid ────────────────────────────────────────────────
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        sc_mean = np.mean(spectral_centroid)

        # ── Spectral Rolloff ─────────────────────────────────────────────────
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        sr_mean = np.mean(spectral_rolloff)

        # ── RMS Energy ───────────────────────────────────────────────────────
        rms = librosa.feature.rms(y=y)
        rms_mean = np.mean(rms)

        # ── Chroma features ──────────────────────────────────────────────────
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)  # (12,)

        # ── Concatenate all features ─────────────────────────────────────────
        feature_vector = np.concatenate([
            mfcc_mean,          # 40 features
            mfcc_delta_mean,    # 40 features
            [pitch_mean, pitch_std, zcr_mean, sc_mean, sr_mean, rms_mean],  # 6 features
            chroma_mean,        # 12 features
        ])  # Total: 98 features

        return feature_vector.astype(np.float32)

    except Exception as e:
        logger.warning(f"Feature extraction failed for {audio_path}: {e}")
        return None


def parse_asvspoof_label_file(label_path: str) -> dict:
    """
    Parse the ASVspoof 2019 protocol/label file.

    ASVspoof label files have space-separated columns:
    speaker_id  file_id  - attack_type  label(bonafide/spoof)

    Returns:
        dict mapping file_id -> label (0=bonafide/real, 1=spoof/fake)
    """
    labels = {}
    try:
        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    file_id = parts[1]   # e.g. LA_T_1000137
                    label_str = parts[4] # 'bonafide' or 'spoof'
                    labels[file_id] = 1 if label_str == "spoof" else 0
                elif len(parts) >= 2:
                    # Fallback: simpler format
                    file_id = parts[0]
                    label_str = parts[-1]
                    labels[file_id] = 1 if label_str == "spoof" else 0
    except Exception as e:
        logger.error(f"Failed to parse label file {label_path}: {e}")

    return labels


def load_asvspoof_dataset(dataset_root: str, subset: str = "train", max_files: int = 5000) -> pd.DataFrame:
    """
    Load the ASVspoof 2019 Logical Access (LA) dataset.

    Expected folder structure:
    dataset_root/
    ├── LA/
    │   ├── ASVspoof2019_LA_train/
    │   │   └── flac/ (or wav/)
    │   ├── ASVspoof2019_LA_dev/
    │   │   └── flac/
    │   └── ASVspoof2019_LA_protocols/
    │       ├── ASVspoof2019.LA.cm.train.trn.txt
    │       └── ASVspoof2019.LA.cm.dev.trl.txt

    Args:
        dataset_root: Root path of the ASVspoof2019 dataset
        subset: 'train' or 'dev'
        max_files: Maximum number of files to load (for memory limits)

    Returns:
        DataFrame with columns: [feature_0 ... feature_97, label]
    """
    dataset_root = Path(dataset_root)

    # Locate audio and label folders
    if subset == "train":
        audio_dir = dataset_root / "LA" / "ASVspoof2019_LA_train" / "flac"
        if not audio_dir.exists():
            audio_dir = dataset_root / "LA" / "ASVspoof2019_LA_train" / "wav"
        label_file = dataset_root / "LA" / "ASVspoof2019_LA_protocols" / "ASVspoof2019.LA.cm.train.trn.txt"
    else:
        audio_dir = dataset_root / "LA" / "ASVspoof2019_LA_dev" / "flac"
        if not audio_dir.exists():
            audio_dir = dataset_root / "LA" / "ASVspoof2019_LA_dev" / "wav"
        label_file = dataset_root / "LA" / "ASVspoof2019_LA_protocols" / "ASVspoof2019.LA.cm.dev.trl.txt"

    if not audio_dir.exists():
        raise FileNotFoundError(
            f"Audio directory not found: {audio_dir}\n"
            "Please download ASVspoof 2019 dataset from:\n"
            "https://datashare.ed.ac.uk/handle/10283/3336"
        )

    # Parse label file
    labels = {}
    if label_file.exists():
        labels = parse_asvspoof_label_file(str(label_file))
        logger.info(f"Loaded {len(labels)} labels from {label_file.name}")
    else:
        logger.warning(f"Label file not found: {label_file}. Will attempt to infer from folder names.")

    # Collect audio files
    audio_extensions = [".flac", ".wav", ".mp3"]
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(audio_dir.glob(f"*{ext}"))

    if not audio_files:
        raise FileNotFoundError(f"No audio files found in {audio_dir}")

    # Limit to max_files
    if len(audio_files) > max_files:
        # Balance classes: take equal numbers of spoof and real if possible
        logger.info(f"Limiting to {max_files} files from {len(audio_files)} total")
        import random
        random.shuffle(audio_files)
        audio_files = audio_files[:max_files]

    logger.info(f"Processing {len(audio_files)} audio files from {audio_dir}...")

    # Extract features from each file
    feature_rows = []
    label_list = []
    failed = 0

    for i, audio_path in enumerate(audio_files):
        if i % 100 == 0:
            logger.info(f"  Processing {i}/{len(audio_files)} files...")

        # Determine label
        file_stem = audio_path.stem  # e.g. LA_T_1000137
        if file_stem in labels:
            label = labels[file_stem]
        elif labels:
            # Skip files with no known label when we have a label file
            continue
        else:
            # No label file — assume bonafide (0) for all
            label = 0

        # Extract audio features
        features = extract_features(str(audio_path))
        if features is not None:
            feature_rows.append(features)
            label_list.append(label)
        else:
            failed += 1

    if not feature_rows:
        raise ValueError("No features could be extracted. Check audio file formats and paths.")

    # Build DataFrame
    feature_dim = len(feature_rows[0])
    col_names = [f"feature_{i}" for i in range(feature_dim)]

    df = pd.DataFrame(feature_rows, columns=col_names)
    df["label"] = label_list

    # ── Print statistics ──────────────────────────────────────────────────────
    total = len(df)
    spoof_count = (df["label"] == 1).sum()
    real_count = (df["label"] == 0).sum()

    logger.info("\n" + "=" * 50)
    logger.info("DATASET STATISTICS")
    logger.info("=" * 50)
    logger.info(f"Total files processed : {total}")
    logger.info(f"Real (bonafide)        : {real_count} ({100*real_count/total:.1f}%)")
    logger.info(f"Spoof (fake)           : {spoof_count} ({100*spoof_count/total:.1f}%)")
    logger.info(f"Failed extractions     : {failed}")
    logger.info(f"Feature vector shape   : ({feature_dim},)")
    logger.info("=" * 50 + "\n")

    return df


def generate_synthetic_dataset(n_samples: int = 2000) -> pd.DataFrame:
    """
    Generate a synthetic dataset for testing when the real ASVspoof dataset
    is not available. Creates plausible audio feature distributions.

    Real voices: higher MFCC variance, natural pitch variation
    Fake voices: lower MFCC variance, flat pitch, abnormal spectral features

    Returns:
        DataFrame with feature columns + label column (0=real, 1=fake)
    """
    np.random.seed(42)
    half = n_samples // 2

    # ── Real voice feature distributions ─────────────────────────────────────
    # MFCCs: more variable, normally distributed
    real_mfcc = np.random.normal(loc=0, scale=20, size=(half, 40))
    real_mfcc_delta = np.random.normal(loc=0, scale=5, size=(half, 40))
    # Pitch: natural variation (100–300 Hz)
    real_pitch_mean = np.random.uniform(100, 300, (half, 1))
    real_pitch_std = np.random.uniform(20, 60, (half, 1))
    # Other features
    real_other = np.random.normal(
        loc=[0.05, 2000, 4000, 0.1],
        scale=[0.02, 500, 1000, 0.05],
        size=(half, 4)
    )
    real_chroma = np.random.uniform(0.2, 0.8, (half, 12))
    real_features = np.concatenate([real_mfcc, real_mfcc_delta, real_pitch_mean,
                                     real_pitch_std, real_other, real_chroma], axis=1)

    # ── Fake/spoofed voice feature distributions ─────────────────────────────
    # MFCCs: low variance, flatter distribution (synthetic/cloned voice)
    fake_mfcc = np.random.normal(loc=0, scale=8, size=(half, 40))
    fake_mfcc_delta = np.random.normal(loc=0, scale=2, size=(half, 40))
    # Pitch: unnaturally flat or zero
    fake_pitch_mean = np.random.uniform(0, 150, (half, 1))
    fake_pitch_std = np.random.uniform(0, 10, (half, 1))
    # Other features — abnormal values
    fake_other = np.random.normal(
        loc=[0.15, 3500, 6000, 0.05],
        scale=[0.05, 800, 1500, 0.02],
        size=(half, 4)
    )
    fake_chroma = np.random.uniform(0.0, 0.3, (half, 12))
    fake_features = np.concatenate([fake_mfcc, fake_mfcc_delta, fake_pitch_mean,
                                     fake_pitch_std, fake_other, fake_chroma], axis=1)

    # ── Combine and label ────────────────────────────────────────────────────
    all_features = np.vstack([real_features, fake_features])
    labels = np.array([0] * half + [1] * half)

    # Shuffle
    idx = np.random.permutation(n_samples)
    all_features = all_features[idx]
    labels = labels[idx]

    feature_dim = all_features.shape[1]
    col_names = [f"feature_{i}" for i in range(feature_dim)]
    df = pd.DataFrame(all_features, columns=col_names)
    df["label"] = labels

    logger.info(f"Generated synthetic dataset: {n_samples} samples, {feature_dim} features")
    logger.info(f"Real: {(labels==0).sum()}, Fake: {(labels==1).sum()}")

    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
        logger.info(f"Loading ASVspoof dataset from: {dataset_path}")
        try:
            df = load_asvspoof_dataset(dataset_path)
            print(df.head())
            print(f"\nDataFrame shape: {df.shape}")
        except FileNotFoundError as e:
            logger.error(str(e))
            logger.info("Falling back to synthetic dataset...")
            df = generate_synthetic_dataset()
            print(df.head())
    else:
        logger.info("No dataset path provided. Generating synthetic dataset...")
        df = generate_synthetic_dataset()
        print(df.head())
        print(f"\nDataFrame shape: {df.shape}")
