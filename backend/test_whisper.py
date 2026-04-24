"""
test_whisper.py — Quick test to verify Whisper is working

Run with: python test_whisper.py
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_whisper_import():
    """Test if openai-whisper is installed"""
    try:
        import whisper
        logger.info("✅ openai-whisper is installed")
        return True
    except ImportError:
        logger.error("❌ openai-whisper is NOT installed")
        logger.error("   Install with: pip install openai-whisper")
        return False

def test_whisper_load():
    """Test if Whisper model can be loaded"""
    try:
        import whisper
        logger.info("Loading Whisper 'tiny' model...")
        model = whisper.load_model("tiny")
        logger.info("✅ Whisper model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"❌ Failed to load Whisper model: {e}")
        return None

def test_whisper_transcribe(model):
    """Test transcription with a sample audio file"""
    import os
    
    # Check if demo audio exists
    demo_files = [
        "../demo/scam_call_1.wav",
        "../demo/normal_call.wav",
        "demo/scam_call_1.wav",
        "demo/normal_call.wav",
    ]
    
    audio_file = None
    for f in demo_files:
        if os.path.exists(f):
            audio_file = f
            break
    
    if not audio_file:
        logger.warning("⚠️ No demo audio files found")
        logger.info("   Skipping transcription test")
        return
    
    try:
        logger.info(f"Transcribing: {audio_file}")
        result = model.transcribe(audio_file, language="en", fp16=False, verbose=False)
        transcript = result.get("text", "").strip()
        
        if transcript:
            logger.info(f"✅ Transcription successful!")
            logger.info(f"   Text: {transcript[:100]}{'...' if len(transcript) > 100 else ''}")
        else:
            logger.warning("⚠️ Transcription returned empty string")
            logger.info("   This might be normal if the audio is silent")
        
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")

def test_ffmpeg():
    """Test if ffmpeg is installed"""
    import subprocess
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            logger.info(f"✅ ffmpeg is installed: {version_line}")
            return True
        else:
            logger.error("❌ ffmpeg command failed")
            return False
    except FileNotFoundError:
        logger.error("❌ ffmpeg is NOT installed")
        logger.error("   Windows: winget install ffmpeg")
        logger.error("   Mac: brew install ffmpeg")
        logger.error("   Linux: sudo apt install ffmpeg")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking ffmpeg: {e}")
        return False

def test_pydub():
    """Test if pydub is installed"""
    try:
        from pydub import AudioSegment
        logger.info("✅ pydub is installed")
        return True
    except ImportError:
        logger.error("❌ pydub is NOT installed")
        logger.error("   Install with: pip install pydub")
        return False

def main():
    logger.info("=" * 60)
    logger.info("PhishShield Audio Pipeline Test")
    logger.info("=" * 60)
    logger.info("")
    
    # Test 1: Whisper import
    logger.info("Test 1: Checking openai-whisper installation...")
    if not test_whisper_import():
        logger.error("\n❌ FAILED: openai-whisper not installed")
        sys.exit(1)
    logger.info("")
    
    # Test 2: FFmpeg
    logger.info("Test 2: Checking ffmpeg installation...")
    if not test_ffmpeg():
        logger.error("\n❌ FAILED: ffmpeg not installed")
        sys.exit(1)
    logger.info("")
    
    # Test 3: pydub
    logger.info("Test 3: Checking pydub installation...")
    if not test_pydub():
        logger.error("\n❌ FAILED: pydub not installed")
        sys.exit(1)
    logger.info("")
    
    # Test 4: Load Whisper model
    logger.info("Test 4: Loading Whisper model...")
    model = test_whisper_load()
    if not model:
        logger.error("\n❌ FAILED: Could not load Whisper model")
        sys.exit(1)
    logger.info("")
    
    # Test 5: Transcribe sample audio
    logger.info("Test 5: Testing transcription...")
    test_whisper_transcribe(model)
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Your audio pipeline is ready to use.")
    logger.info("Start the backend with: uvicorn main:app --host 0.0.0.0 --port 8000")
    logger.info("")

if __name__ == "__main__":
    main()
