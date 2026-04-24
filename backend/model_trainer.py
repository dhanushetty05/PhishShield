"""
model_trainer.py — PhishShield
Trains the fraud voice detection models:
  1. Random Forest Classifier (scikit-learn) — saved as fraud_voice_model.pkl
  2. LSTM Neural Network (TensorFlow/Keras) — saved as fraud_lstm_model.h5

Usage:
    python model_trainer.py
    python model_trainer.py /path/to/ASVspoof2019  (with real dataset)
"""

import os
import sys
import logging
import warnings
from pathlib import Path

import numpy as np
import joblib

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
MODELS_DIR = Path(__file__).parent / "models"
RF_MODEL_PATH = MODELS_DIR / "fraud_voice_model.pkl"
LSTM_MODEL_PATH = MODELS_DIR / "fraud_lstm_model.h5"


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray,
                        X_test: np.ndarray, y_test: np.ndarray):
    """
    Train a Random Forest classifier and evaluate on test set.

    Returns:
        Trained RandomForestClassifier model
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (accuracy_score, precision_score,
                                 recall_score, f1_score, confusion_matrix,
                                 classification_report)
    from sklearn.preprocessing import StandardScaler

    logger.info("\n" + "=" * 55)
    logger.info("TRAINING MODEL 1: Random Forest Classifier")
    logger.info("=" * 55)
    logger.info(f"Training samples : {len(X_train)}")
    logger.info(f"Test samples     : {len(X_test)}")
    logger.info(f"Feature dim      : {X_train.shape[1]}")

    # Scale features — important for SVM-like behavior inside RF
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest with 200 trees, max depth 20
    logger.info("\nFitting Random Forest (n_estimators=200, max_depth=20)...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",   # Handle imbalanced classes
        random_state=42,
        n_jobs=-1,                 # Use all CPU cores
        verbose=0
    )
    rf.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = rf.predict(X_test_scaled)
    y_prob = rf.predict_proba(X_test_scaled)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    logger.info("\n── Evaluation Results ──────────────────────────────")
    logger.info(f"Accuracy  : {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"Precision : {precision:.4f}")
    logger.info(f"Recall    : {recall:.4f}")
    logger.info(f"F1 Score  : {f1:.4f}")
    logger.info(f"\nConfusion Matrix:\n{cm}")
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred, target_names=["Real", "Spoof"]))

    # Feature importance (top 10)
    feature_importances = rf.feature_importances_
    top_idx = np.argsort(feature_importances)[::-1][:10]
    logger.info("\nTop 10 Most Important Features:")
    for rank, idx in enumerate(top_idx, 1):
        logger.info(f"  {rank}. feature_{idx}: {feature_importances[idx]:.4f}")

    # Bundle model + scaler together so we can use both at inference time
    model_bundle = {"model": rf, "scaler": scaler}
    return model_bundle


def train_lstm(X_train: np.ndarray, y_train: np.ndarray,
               X_test: np.ndarray, y_test: np.ndarray):
    """
    Train an LSTM neural network for sequential audio chunk analysis.
    The LSTM treats each feature vector as a time-step sequence.

    Returns:
        Trained Keras model
    """
    logger.info("\n" + "=" * 55)
    logger.info("TRAINING MODEL 2: LSTM Neural Network")
    logger.info("=" * 55)

    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import (LSTM, Dense, Dropout,
                                             BatchNormalization, Bidirectional)
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
        from tensorflow.keras.optimizers import Adam
        from sklearn.metrics import classification_report

        logger.info(f"TensorFlow version: {tf.__version__}")

        # Reshape for LSTM: (samples, timesteps, features)
        # Treat each 10-feature block as a "timestep" (98 features -> ~10 timesteps of ~10 features)
        feature_dim = X_train.shape[1]
        timesteps = 10
        lstm_features = feature_dim // timesteps
        remainder = feature_dim % timesteps

        # Pad features if not evenly divisible
        if remainder != 0:
            pad_len = timesteps - remainder
            X_train = np.pad(X_train, ((0, 0), (0, pad_len)))
            X_test = np.pad(X_test, ((0, 0), (0, pad_len)))
            lstm_features = X_train.shape[1] // timesteps

        X_train_lstm = X_train.reshape(-1, timesteps, lstm_features)
        X_test_lstm = X_test.reshape(-1, timesteps, lstm_features)

        logger.info(f"LSTM input shape : {X_train_lstm.shape}")

        # Build LSTM model
        model = Sequential([
            # Bidirectional LSTM captures patterns in both directions
            Bidirectional(LSTM(128, return_sequences=True),
                          input_shape=(timesteps, lstm_features)),
            BatchNormalization(),
            Dropout(0.3),

            Bidirectional(LSTM(64, return_sequences=False)),
            BatchNormalization(),
            Dropout(0.3),

            Dense(64, activation="relu"),
            Dropout(0.2),
            Dense(32, activation="relu"),

            # Binary output: real (0) vs spoof (1)
            Dense(1, activation="sigmoid")
        ])

        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy", tf.keras.metrics.AUC(name="auc")]
        )

        model.summary(print_fn=logger.info)

        # Callbacks
        early_stop = EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1
        )
        lr_reduce = ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1
        )

        logger.info("\nFitting LSTM model (up to 50 epochs)...")
        history = model.fit(
            X_train_lstm, y_train,
            validation_split=0.15,
            epochs=50,
            batch_size=32,
            callbacks=[early_stop, lr_reduce],
            verbose=1
        )

        # Evaluate
        y_prob_lstm = model.predict(X_test_lstm, verbose=0).flatten()
        y_pred_lstm = (y_prob_lstm > 0.5).astype(int)

        from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
        acc = accuracy_score(y_test, y_pred_lstm)
        f1 = f1_score(y_test, y_pred_lstm, zero_division=0)
        cm = confusion_matrix(y_test, y_pred_lstm)

        logger.info("\n── LSTM Evaluation Results ─────────────────────────")
        logger.info(f"Accuracy : {acc:.4f} ({acc*100:.2f}%)")
        logger.info(f"F1 Score : {f1:.4f}")
        logger.info(f"Confusion Matrix:\n{cm}")
        logger.info(classification_report(y_test, y_pred_lstm, target_names=["Real", "Spoof"]))

        # Save model metadata alongside (for reshaping at inference)
        model._lstm_timesteps = timesteps
        model._lstm_features = lstm_features
        model._original_feature_dim = feature_dim

        return model

    except ImportError as e:
        logger.warning(f"TensorFlow not available: {e}")
        logger.warning("Skipping LSTM training. Install tensorflow to enable.")
        return None


def main():
    """
    Main training pipeline:
    1. Load dataset (real or synthetic)
    2. Split train/test
    3. Train Random Forest
    4. Train LSTM
    5. Save both models
    """
    from sklearn.model_selection import train_test_split
    from dataset_loader import load_asvspoof_dataset, generate_synthetic_dataset

    # Create models directory
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load Dataset ──────────────────────────────────────────────────────────
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else None

    if dataset_path and Path(dataset_path).exists():
        logger.info(f"Loading ASVspoof dataset from: {dataset_path}")
        try:
            df = load_asvspoof_dataset(dataset_path, subset="train", max_files=5000)
        except Exception as e:
            logger.warning(f"Failed to load real dataset: {e}")
            logger.info("Falling back to synthetic dataset...")
            df = generate_synthetic_dataset(n_samples=3000)
    else:
        logger.info("No dataset path provided. Generating synthetic dataset for demo training...")
        logger.info("For production, download ASVspoof 2019 from:")
        logger.info("  https://datashare.ed.ac.uk/handle/10283/3336")
        logger.info("Then run: python model_trainer.py /path/to/ASVspoof2019\n")
        df = generate_synthetic_dataset(n_samples=3000)

    # ── Prepare features and labels ───────────────────────────────────────────
    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values.astype(np.int32)

    logger.info(f"\nTotal dataset: {len(X)} samples, {X.shape[1]} features")
    logger.info(f"Class distribution — Real: {(y==0).sum()}, Spoof: {(y==1).sum()}")

    # ── Train/Test Split: 80/20 ───────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # ── Train Random Forest ───────────────────────────────────────────────────
    rf_bundle = train_random_forest(X_train, y_train, X_test, y_test)

    # Save Random Forest + scaler bundle
    joblib.dump(rf_bundle, RF_MODEL_PATH)
    logger.info(f"\n✅ Random Forest saved → {RF_MODEL_PATH}")

    # ── Train LSTM ────────────────────────────────────────────────────────────
    lstm_model = train_lstm(X_train, y_train, X_test, y_test)

    if lstm_model is not None:
        # Save LSTM model metadata separately since custom attributes aren't saved in h5
        lstm_meta = {
            "timesteps": lstm_model._lstm_timesteps,
            "lstm_features": lstm_model._lstm_features,
            "original_feature_dim": lstm_model._original_feature_dim
        }
        joblib.dump(lstm_meta, MODELS_DIR / "lstm_meta.pkl")
        lstm_model.save(str(LSTM_MODEL_PATH))
        logger.info(f"✅ LSTM model saved → {LSTM_MODEL_PATH}")
    else:
        logger.info("⚠️  LSTM model not saved (TensorFlow unavailable)")

    # ── Final Summary ─────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 55)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 55)
    logger.info(f"Models saved in: {MODELS_DIR}")
    logger.info("Start the backend server:")
    logger.info("  uvicorn main:app --host 0.0.0.0 --port 8000")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
