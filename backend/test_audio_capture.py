"""
Test script to verify audio capture and transcription
Run this to diagnose issues with voice capture
"""

import io
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_whisper():
    """Test if Whisper can transcribe a simple audio file"""
    try:
        import whisper
        logger.info("✅ Whisper imported successfully")
        
        # Load model
        logger.info("Loading Whisper base model...")
        model = whisper.load_model("base")
        logger.info("✅ Whisper model loaded")
        
        # Test with demo audio if available
        demo_path = Path(__file__).parent.parent / "demo" / "scam_call_1.wav"
        if demo_path.exists():
            logger.info(f"Testing with demo file: {demo_path}")
            result = model.transcribe(str(demo_path), language=None, fp16=False)
            transcript = result.get("text", "").strip()
            logger.info(f"✅ TRANSCRIPTION: {transcript}")
            return True
        else:
            logger.warning(f"Demo file not found: {demo_path}")
            logger.info("✅ Whisper is ready (no demo file to test)")
            return True
            
    except ImportError as e:
        logger.error(f"❌ Whisper not installed: {e}")
        logger.error("Run: pip install openai-whisper")
        return False
    except Exception as e:
        logger.error(f"❌ Whisper test failed: {e}")
        return False

def test_pydub():
    """Test if pydub can convert audio"""
    try:
        from pydub import AudioSegment
        logger.info("✅ pydub imported successfully")
        
        # Create a simple test audio
        logger.info("Testing audio conversion...")
        silence = AudioSegment.silent(duration=1000)  # 1 second
        
        # Export to WAV
        buf = io.BytesIO()
        silence.export(buf, format="wav")
        wav_bytes = buf.getvalue()
        
        logger.info(f"✅ Audio conversion works ({len(wav_bytes)} bytes)")
        return True
        
    except ImportError as e:
        logger.error(f"❌ pydub not installed: {e}")
        logger.error("Run: pip install pydub")
        return False
    except Exception as e:
        logger.error(f"❌ pydub test failed: {e}")
        return False

def test_backend_modules():
    """Test if backend modules load correctly"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from voice_analyzer import get_voice_analyzer
        from content_analyzer import get_content_analyzer
        from risk_engine import get_risk_engine
        
        logger.info("✅ voice_analyzer loaded")
        logger.info("✅ content_analyzer loaded")
        logger.info("✅ risk_engine loaded")
        
        # Test content analyzer
        content_analyzer = get_content_analyzer()
        test_text = "I am calling from police. Share your OTP immediately."
        result = content_analyzer.analyze(test_text)
        
        logger.info(f"✅ Content analysis works:")
        logger.info(f"   Score: {result['content_fraud_score']:.2%}")
        logger.info(f"   Keywords: {result['matched_keywords'][:3]}")
        logger.info(f"   Category: {result['category']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backend modules test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("PHISHSHIELD AUDIO CAPTURE TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Whisper Transcription", test_whisper),
        ("Audio Conversion (pydub)", test_pydub),
        ("Backend Modules", test_backend_modules),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n--- Testing: {name} ---")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {name}")
        if not success:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - System is ready!")
        logger.info("\nNext steps:")
        logger.info("1. Start backend: uvicorn main:app --reload")
        logger.info("2. Open frontend/dashboard.html")
        logger.info("3. Click 'Start Listening' and speak")
    else:
        logger.error("❌ SOME TESTS FAILED - Fix issues above")
        logger.error("\nCommon fixes:")
        logger.error("- pip install openai-whisper")
        logger.error("- pip install pydub")
        logger.error("- pip install -r requirements.txt")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
