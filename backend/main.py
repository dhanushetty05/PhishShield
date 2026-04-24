"""
main.py — PhishShield Backend
FastAPI application providing:
  - WebSocket /ws/analyze  → real-time audio stream analysis
  - POST /analyze          → one-shot file upload analysis
  - GET  /health           → service health check

Start with:
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import io
import time
import logging
import tempfile
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

# ─── Configure logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("phishshield")

# ─── Module-level singletons (loaded once at startup) ─────────────────────────
whisper_model = None
voice_analyzer = None
content_analyzer = None
risk_engine = None


def load_whisper():
    """Load Whisper tiny model for FAST speech-to-text."""
    global whisper_model
    try:
        import whisper
        logger.info("Loading Whisper 'tiny' model (FAST - 2-3 seconds per chunk)...")
        whisper_model = whisper.load_model("tiny")  # 🔥 TINY MODEL (10x faster!)
        logger.info("✅ Whisper model loaded successfully.")
    except ImportError:
        logger.warning(
            "openai-whisper not installed. Install with: pip install openai-whisper\n"
            "Transcription will return empty strings."
        )
    except Exception as e:
        logger.error(f"Failed to load Whisper: {e}")


def load_analyzers():
    """Load voice analyzer, content analyzer, and risk engine."""
    global voice_analyzer, content_analyzer, risk_engine
    from voice_analyzer import get_voice_analyzer
    from content_analyzer import get_content_analyzer
    from risk_engine import get_risk_engine

    voice_analyzer = get_voice_analyzer()
    content_analyzer = get_content_analyzer()
    risk_engine = get_risk_engine()
    logger.info("✅ Analysis modules loaded.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all models at startup, clean up at shutdown."""
    logger.info("=" * 50)
    logger.info("PhishShield backend starting up...")
    logger.info("=" * 50)
    load_whisper()
    load_analyzers()
    logger.info("🛡️  PhishShield ready. Listening on port 8000.")
    yield
    logger.info("PhishShield shutting down.")


# ─── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="PhishShield API",
    description="Real-time AI-powered fraud call detection",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow browser to connect from any origin (development + local file:// usage)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Serve frontend files ─────────────────────────────────────────────────────
# Serve dashboard.html at /dashboard
@app.get("/dashboard")
async def serve_dashboard():
    dashboard_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(dashboard_path)

# Serve index.html at root /
@app.get("/")
async def serve_index():
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index not found")
    return FileResponse(index_path)

# Serve CSS file
@app.get("/style.css")
async def serve_css():
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="CSS not found")
    return FileResponse(css_path, media_type="text/css")

# Serve JS file
@app.get("/app.js")
async def serve_js():
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="JS not found")
    return FileResponse(js_path, media_type="application/javascript")


# ─── Helper: Audio transcription ──────────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using local Whisper model.

    Whisper accepts WAV files, so we write audio bytes to a temp file
    then read the transcription result.

    Returns:
        Transcribed text string, or "" if transcription fails/unavailable.
    """
    if whisper_model is None:
        logger.warning("Whisper model not loaded — skipping transcription.")
        return ""

    if len(audio_bytes) < 1000:
        logger.warning(f"Audio too small ({len(audio_bytes)} bytes) — skipping transcription.")
        return ""

    try:
        # Write bytes to a temporary file (Whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # 🔥 Run Whisper inference with ENGLISH FORCED
        result = whisper_model.transcribe(
            tmp_path,
            language="en",          # 🔥 FORCE ENGLISH (not auto-detect)
            task="transcribe",
            fp16=False,             # Use FP32 for CPU compatibility
            verbose=False,
            # 🔥 Lower temperature for more accurate transcription
            temperature=0.0,
            # 🔥 Suppress common hallucinations
            suppress_tokens="-1",
            # 🔥 No timestamps needed (faster)
            word_timestamps=False,
        )
        transcript = result.get("text", "").strip()
        
        # 🔥 LOG EVERY TRANSCRIPTION
        if transcript:
            logger.info(f"✅ TRANSCRIBED (English): {transcript}")
        else:
            logger.info("⚠️ No speech detected in this chunk")
            
        return transcript

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def convert_audio_to_wav(audio_bytes: bytes) -> bytes:
    """
    Convert WebM (MediaRecorder) audio to WAV (16kHz mono)
    Handles audio from both desktop and mobile devices
    """
    if not audio_bytes or len(audio_bytes) < 100:
        logger.warning("Audio bytes too small or empty")
        return b""
    
    try:
        from pydub import AudioSegment
        import io

        # 🔥 Try to load audio with better error handling
        audio = None
        
        # Try WebM first (most common from browser)
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
        except Exception as e1:
            # Try without format specification
            try:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            except Exception as e2:
                # Try as OGG (alternative browser format)
                try:
                    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="ogg")
                except Exception as e3:
                    logger.warning(f"All audio loading attempts failed. Last error: {e3}")
                    return b""

        if audio is None:
            logger.warning("Audio loading returned None")
            return b""

        # 🔥 Check if audio has actual content
        if len(audio) < 100:  # Less than 100ms
            logger.warning(f"Audio too short: {len(audio)}ms")
            return b""

        # 🔥 Standardize for Whisper (16kHz mono 16-bit)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

        # 🔥 Normalize volume (helps with quiet mobile audio)
        try:
            audio = audio.normalize()
        except Exception:
            pass  # Normalization not critical

        # 🔥 Export as WAV
        buf = io.BytesIO()
        audio.export(buf, format="wav")

        wav_bytes = buf.getvalue()
        logger.info(f"✅ Converted: {len(audio_bytes)} bytes → {len(wav_bytes)} bytes WAV ({len(audio)}ms)")

        return wav_bytes

    except ImportError:
        logger.error("pydub not installed. Run: pip install pydub")
        return b""
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e}")
        return b""

        
def run_full_analysis(audio_bytes: bytes) -> dict:
    """
    Complete analysis pipeline:
    1. Convert WebM → WAV
    2. Transcribe with Whisper
    3. Analyze voice (SKIPPED for speed)
    4. Analyze content (keywords + NLP)
    5. Compute risk score
    """
    t_start = time.monotonic()

    # ── Step 1: Convert audio ───────────────────────────────
    wav_bytes = convert_audio_to_wav(audio_bytes)
    logger.info(f"📦 Audio: {len(audio_bytes)} bytes → WAV: {len(wav_bytes)} bytes")

    # ── Step 2: Transcription (REAL WHISPER) ────────────────
    t_transcribe = time.monotonic()
    transcript = transcribe_audio(wav_bytes)
    transcribe_ms = (time.monotonic() - t_transcribe) * 1000
    logger.info(f"⏱️ Transcription: {transcribe_ms:.0f}ms")

    # 🔥 ALWAYS LOG TRANSCRIPT (even if empty)
    if transcript:
        logger.info(f"🗣️ USER SAID: \"{transcript}\"")
    else:
        logger.info("🔇 No speech detected in this chunk")

    # ── Step 3: Voice analysis (SKIPPED for demo speed) ─────
    voice_result = {
        "voice_fraud_score": 0.0,
        "flags": [],
        "is_silent": len(transcript) == 0
    }

    # ── Step 4: Content analysis (keywords + NLP) ───────────
    t_content = time.monotonic()
    content_result = content_analyzer.analyze(transcript)
    content_ms = (time.monotonic() - t_content) * 1000
    logger.info(f"⏱️ Content analysis: {content_ms:.0f}ms")

    # ── Step 5: Risk fusion ─────────────────────────────────
    total_ms = (time.monotonic() - t_start) * 1000

    risk_result = risk_engine.compute(
        voice_result=voice_result,
        content_result=content_result,
        transcript=transcript,
        processing_time_ms=total_ms,
    )

    logger.info(
        f"🎯 RESULT: {risk_result.risk_level} "
        f"({risk_result.final_score_pct}%) | "
        f"Keywords: {len(content_result.get('matched_keywords', []))} | "
        f"Time: {total_ms:.0f}ms"
    )

    return risk_result.to_dict()


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/health", summary="Health check")
async def health_check():
    """Check if the backend is running and models are loaded."""
    return JSONResponse({
        "status": "ok",
        "whisper_loaded": whisper_model is not None,
        "voice_model_loaded": (
            voice_analyzer is not None and voice_analyzer.model_loaded
        ),
        "content_analyzer_loaded": content_analyzer is not None,
        "keywords_loaded": (
            content_analyzer is not None and len(content_analyzer.keywords) > 0
        ),
        "keyword_count": len(content_analyzer.keywords) if content_analyzer else 0,
        "version": "1.0.0",
    })


@app.post("/analyze", summary="Analyze uploaded audio file")
async def analyze_file(file: UploadFile = File(...)):
    """
    Accept an uploaded WAV, MP3, or WebM audio file and return
    a complete fraud risk analysis as JSON.

    Example:
        curl -X POST http://localhost:8000/analyze -F "file=@scam_call.wav"
    """
    # Validate file type
    allowed_types = {
        "audio/wav", "audio/wave", "audio/x-wav",
        "audio/mpeg", "audio/mp3",
        "audio/webm", "audio/ogg",
        "application/octet-stream",  # Some browsers send this for audio
    }
    if file.content_type and file.content_type not in allowed_types:
        # Still proceed but log a warning (content_type is often wrong)
        logger.warning(f"Unexpected content type: {file.content_type}")

    # Read file bytes
    try:
        audio_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="File is too small or empty.")

    if len(audio_bytes) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit.")

    try:
        result = run_full_analysis(audio_bytes)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/analyze/text", summary="Analyze transcript text only")
async def analyze_text(body: dict):
    """
    Analyze a transcript text string without audio.
    Useful for testing content analysis in isolation.

    Body: {"transcript": "your call text here"}
    """
    transcript = body.get("transcript", "")
    if not transcript:
        raise HTTPException(status_code=400, detail="'transcript' field is required.")

    content_result = content_analyzer.analyze(transcript)

    # Use neutral voice score when no audio is provided
    neutral_voice = {
        "voice_fraud_score": 0.0,
        "flags": [],
        "is_silent": True,
    }

    risk_result = risk_engine.compute(
        voice_result=neutral_voice,
        content_result=content_result,
        transcript=transcript,
        processing_time_ms=0.0,
    )

    return JSONResponse(risk_result.to_dict())


# ─── WebSocket Endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    """
    Continuous real-time audio analysis WebSocket.
    
    Flow:
    1. Accept connection
    2. Loop forever (while True)
    3. Receive audio chunk
    4. Convert WebM → WAV
    5. Transcribe with Whisper
    6. Analyze for fraud
    7. Send JSON response
    8. Repeat (DO NOT close connection)
    """
    await websocket.accept()
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"✅ WebSocket connected from {client_ip}")

    chunk_count = 0
    accumulated_transcript = ""  # 🔥 Accumulate transcript across chunks

    try:
        # 🔥 INFINITE LOOP — Keep connection alive
        while True:
            # ── Receive audio chunk ────────────────────────────────────
            try:
                audio_bytes = await websocket.receive_bytes()
            except WebSocketDisconnect:
                logger.info(f"Client {client_ip} disconnected gracefully")
                break
            except Exception as e:
                logger.error(f"Error receiving data: {e}")
                break

            # 🔥 ALWAYS RESPOND - even for tiny chunks (send keepalive)
            if not audio_bytes or len(audio_bytes) < 100:
                logger.warning(f"Tiny/empty chunk ({len(audio_bytes) if audio_bytes else 0} bytes) - sending keepalive")
                
                # Send keepalive response to prevent timeout
                keepalive_response = {
                    "chunk_number": chunk_count,
                    "final_score": 0.0,
                    "final_score_pct": 0,
                    "risk_level": "SAFE",
                    "color": "green",
                    "voice_fraud_score": 0.0,
                    "content_fraud_score": 0.0,
                    "transcript": "",
                    "accumulated_transcript": accumulated_transcript,
                    "latest_chunk_text": "",
                    "matched_keywords": [],
                    "voice_flags": [],
                    "category": "Unknown",
                    "pattern_categories": [],
                    "recommendation": "Listening...",
                    "short_warning": "",
                    "processing_time_ms": 0,
                    "voice_model_used": False,
                    "is_keepalive": True
                }
                
                try:
                    await websocket.send_json(keepalive_response)
                    logger.info(f"   📤 Sent keepalive for chunk #{chunk_count}")
                except Exception:
                    pass
                
                continue

            chunk_count += 1
            logger.info(f"📦 Chunk #{chunk_count}: {len(audio_bytes)} bytes from {client_ip}")

            # ── Process chunk ──────────────────────────────────────────
            try:
                t_start = time.monotonic()

                # Step 1: Convert WebM → WAV
                t_convert = time.monotonic()
                wav_bytes = convert_audio_to_wav(audio_bytes)
                convert_ms = (time.monotonic() - t_convert) * 1000
                
                if not wav_bytes or len(wav_bytes) < 1000:
                    logger.warning(f"   ⚠️ Conversion failed or WAV too small ({len(wav_bytes) if wav_bytes else 0} bytes)")
                    logger.warning(f"   Original audio: {len(audio_bytes)} bytes")
                    
                    # Send response even for failed conversion
                    failed_response = {
                        "chunk_number": chunk_count,
                        "final_score": 0.0,
                        "final_score_pct": 0,
                        "risk_level": "SAFE",
                        "color": "green",
                        "voice_fraud_score": 0.0,
                        "content_fraud_score": 0.0,
                        "transcript": "",
                        "accumulated_transcript": accumulated_transcript,
                        "latest_chunk_text": "",
                        "matched_keywords": [],
                        "voice_flags": [],
                        "category": "Unknown",
                        "pattern_categories": [],
                        "recommendation": "Audio conversion failed - check microphone",
                        "short_warning": "",
                        "processing_time_ms": convert_ms,
                        "voice_model_used": False,
                        "is_keepalive": False
                    }
                    await websocket.send_json(failed_response)
                    continue
                
                logger.info(f"   ✅ Converted: {len(audio_bytes)} → {len(wav_bytes)} bytes ({convert_ms:.0f}ms)")

                # Step 2: Transcribe with Whisper
                t_transcribe = time.monotonic()
                transcript = ""
                
                # 🔥 Always try to transcribe if WAV is valid
                try:
                    transcript = transcribe_audio(wav_bytes)
                    transcribe_ms = (time.monotonic() - t_transcribe) * 1000
                    logger.info(f"   ⏱️ Transcription: {transcribe_ms:.0f}ms")
                    
                    if transcript and transcript.strip():
                        logger.info(f"   🗣️ TRANSCRIBED: \"{transcript}\"")
                    else:
                        logger.info(f"   🔇 No speech detected in chunk #{chunk_count}")
                except Exception as e:
                    logger.error(f"   ❌ Transcription error: {e}")
                    transcribe_ms = (time.monotonic() - t_transcribe) * 1000

                # 🔥 Accumulate transcript (don't replace)
                if transcript and transcript.strip():
                    if accumulated_transcript:
                        accumulated_transcript += " " + transcript.strip()
                    else:
                        accumulated_transcript = transcript.strip()
                    logger.info(f"   📝 ACCUMULATED: \"{accumulated_transcript[:100]}{'...' if len(accumulated_transcript) > 100 else ''}\"")
                    logger.info(f"   📊 Total length: {len(accumulated_transcript)} characters")

                # Step 3: Voice analysis (SKIPPED for speed)
                voice_result = {
                    "voice_fraud_score": 0.0,
                    "flags": [],
                    "is_silent": len(transcript) == 0
                }

                # Step 4: Content analysis on ACCUMULATED transcript
                t_content = time.monotonic()
                
                # 🔥 Always analyze, even if transcript is empty
                content_result = content_analyzer.analyze(accumulated_transcript if accumulated_transcript else "")
                content_ms = (time.monotonic() - t_content) * 1000
                logger.info(f"   ⏱️ Content: {content_ms:.0f}ms")

                # Step 5: Risk fusion
                total_ms = (time.monotonic() - t_start) * 1000

                risk_result = risk_engine.compute(
                    voice_result=voice_result,
                    content_result=content_result,
                    transcript=accumulated_transcript if accumulated_transcript else "",  # 🔥 Send full transcript
                    processing_time_ms=total_ms,
                )

                # Step 6: Build response JSON
                response = risk_result.to_dict()
                
                # 🔥 Add chunk-specific info
                response["chunk_number"] = chunk_count
                response["latest_chunk_text"] = transcript  # Just this chunk
                response["accumulated_transcript"] = accumulated_transcript  # Full text
                
                logger.info(
                    f"   🎯 Result: {response['risk_level']} "
                    f"({response['final_score_pct']}%) | "
                    f"Keywords: {len(response.get('matched_keywords', []))} | "
                    f"Time: {total_ms:.0f}ms"
                )

                # Step 7: Send response (DO NOT close connection)
                await websocket.send_json(response)

            except Exception as e:
                logger.error(f"❌ Analysis error on chunk #{chunk_count}: {e}", exc_info=True)
                
                # Send error response but KEEP CONNECTION ALIVE
                error_response = {
                    "error": str(e),
                    "chunk_number": chunk_count,
                    "final_score": 0.0,
                    "final_score_pct": 0,
                    "risk_level": "ERROR",
                    "transcript": accumulated_transcript,
                    "matched_keywords": [],
                    "voice_flags": []
                }
                
                try:
                    await websocket.send_json(error_response)
                except Exception:
                    logger.error("Failed to send error response, closing connection")
                    break

    except WebSocketDisconnect:
        logger.info(f"Client {client_ip} disconnected")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}", exc_info=True)
    finally:
        logger.info(f"Session ended: {chunk_count} chunks processed, {len(accumulated_transcript)} chars transcribed")
        # Connection closes automatically when function exits

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True,
    )
