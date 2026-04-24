"""
test_pipeline.py — PhishShield
End-to-end test suite for the complete analysis pipeline.
Tests each module independently and then the full pipeline together.

Run with:
    python test_pipeline.py
    python test_pipeline.py --verbose
    python test_pipeline.py --module content   (run only content analyzer tests)
    python test_pipeline.py --module voice
    python test_pipeline.py --module risk
    python test_pipeline.py --module pipeline
"""

import sys
import io
import wave
import time
import struct
import argparse
import logging
from pathlib import Path

import numpy as np

# Silence verbose library output during tests
logging.basicConfig(level=logging.WARNING)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⚠️  SKIP"

results = []


def result(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    results.append((name, passed, detail))
    print(f"  {status}  {name}")
    if detail and (not passed or "--verbose" in sys.argv):
        print(f"          {detail}")


def section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ─── Helper: generate synthetic WAV bytes ─────────────────────────────────────

def make_wav_bytes(duration: float = 3.0, sr: int = 16000,
                   freq: float = 200.0, noise_level: float = 0.05,
                   flat_pitch: bool = False) -> bytes:
    """
    Generate a synthetic WAV audio clip as bytes.

    Args:
        duration:    Length in seconds
        sr:          Sample rate (Hz)
        freq:        Fundamental frequency (Hz)
        noise_level: Gaussian noise amplitude
        flat_pitch:  If True, generate robotic flat-pitch voice

    Returns:
        Raw WAV file bytes
    """
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    np.random.seed(0)

    if flat_pitch:
        # Robotic: perfectly constant pitch, low noise = AI voice signature
        signal = (
            0.5 * np.sin(2 * np.pi * freq * t) +
            0.25 * np.sin(2 * np.pi * 2 * freq * t) +
            0.12 * np.sin(2 * np.pi * 3 * freq * t)
        )
        signal += np.random.normal(0, 0.005, n)   # very low noise
    else:
        # Natural: varying pitch, more noise = human voice signature
        f_var = freq + 20 * np.sin(2 * np.pi * 0.5 * t) + 5 * np.random.randn(n).cumsum() * 0.002
        phase = 2 * np.pi * np.cumsum(f_var) / sr
        signal = (
            0.5 * np.sin(phase) +
            0.25 * np.sin(2 * phase) +
            0.12 * np.sin(3 * phase)
        )
        signal += np.random.normal(0, noise_level, n)

    # Normalize and convert to PCM
    signal /= np.max(np.abs(signal)) + 1e-9
    signal *= 0.7
    pcm = (signal * 32767).astype(np.int16)

    # Write to in-memory WAV
    buf = io.BytesIO()
    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


# ─── TEST: ContentAnalyzer ────────────────────────────────────────────────────

def test_content_analyzer(verbose: bool = False):
    section("CONTENT ANALYZER TESTS")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from content_analyzer import ContentAnalyzer
        analyzer = ContentAnalyzer()
    except ImportError as e:
        result("ContentAnalyzer import", False, str(e))
        return

    result("ContentAnalyzer import", True, f"{len(analyzer.keywords)} keywords loaded")

    # ── Test 1: Empty input ────────────────────────────────────────────────────
    res = analyzer.analyze("")
    result("Empty transcript → score 0.0",
           res["content_fraud_score"] == 0.0,
           f"score={res['content_fraud_score']}")

    result("Empty transcript → no keywords",
           len(res["matched_keywords"]) == 0,
           f"keywords={res['matched_keywords']}")

    # ── Test 2: Normal call ────────────────────────────────────────────────────
    normal_text = "Hi, I am calling to confirm your appointment tomorrow at 3 PM. Is that convenient for you?"
    res = analyzer.analyze(normal_text)
    result("Normal call → low score (<0.30)",
           res["content_fraud_score"] < 0.30,
           f"score={res['content_fraud_score']:.3f}")

    # ── Test 3: OTP fraud ─────────────────────────────────────────────────────
    otp_text = "Please share your OTP immediately. Your bank account will be blocked if you don't verify now."
    res = analyzer.analyze(otp_text)
    result("OTP fraud text → score >0.70",
           res["content_fraud_score"] > 0.70,
           f"score={res['content_fraud_score']:.3f}")

    result("OTP fraud → 'otp' in matched keywords",
           any("otp" in k.lower() for k in res["matched_keywords"]),
           f"matched={res['matched_keywords'][:5]}")

    # ── Test 4: RBI impersonation ──────────────────────────────────────────────
    rbi_text = "I am calling from RBI. Your Aadhaar number is linked to an illegal account. You will be arrested if you don't cooperate."
    res = analyzer.analyze(rbi_text)
    result("RBI impersonation → score >0.75",
           res["content_fraud_score"] > 0.75,
           f"score={res['content_fraud_score']:.3f}, category={res['category']}")

    result("RBI impersonation → authority_impersonation flag",
           "authority_impersonation" in res["flags"],
           f"flags={res['flags']}")

    # ── Test 5: Lottery scam ──────────────────────────────────────────────────
    lottery_text = "Congratulations! You have won a lucky draw prize of 10 lakh rupees. To claim your prize, pay a processing fee of 2000 rupees."
    res = analyzer.analyze(lottery_text)
    result("Lottery scam → score >0.70",
           res["content_fraud_score"] > 0.70,
           f"score={res['content_fraud_score']:.3f}")

    result("Lottery scam → correct category",
           "Lottery" in res["category"] or "Prize" in res["category"],
           f"category={res['category']}")

    # ── Test 6: Police impersonation with threat ───────────────────────────────
    threat_text = "This is CBI. An arrest warrant has been issued in your name for money laundering. You will be arrested within 2 hours. Do not tell anyone about this call. Pay the bail amount now."
    res = analyzer.analyze(threat_text)
    result("Police threat → score >0.85",
           res["content_fraud_score"] > 0.85,
           f"score={res['content_fraud_score']:.3f}")

    result("Police threat → multiple flags",
           len(res["flags"]) >= 2,
           f"flags={res['flags']}")

    # ── Test 7: UPI scam ──────────────────────────────────────────────────────
    upi_text = "Please approve the UPI collect request immediately. Enter your UPI PIN to receive your refund amount."
    res = analyzer.analyze(upi_text)
    result("UPI scam → score >0.65",
           res["content_fraud_score"] > 0.65,
           f"score={res['content_fraud_score']:.3f}")

    # ── Test 8: Keyword count ─────────────────────────────────────────────────
    result("Keywords count field is int",
           isinstance(res["keyword_count"], int),
           f"keyword_count={res['keyword_count']}")

    # ── Test 9: Score range validation ────────────────────────────────────────
    test_texts = [otp_text, rbi_text, lottery_text, threat_text, normal_text, ""]
    all_in_range = all(
        0.0 <= analyzer.analyze(t)["content_fraud_score"] <= 1.0
        for t in test_texts
    )
    result("All scores in [0.0, 1.0]", all_in_range)


# ─── TEST: VoiceAnalyzer ──────────────────────────────────────────────────────

def test_voice_analyzer(verbose: bool = False):
    section("VOICE ANALYZER TESTS")

    try:
        from voice_analyzer import VoiceAnalyzer
        analyzer = VoiceAnalyzer()
    except ImportError as e:
        result("VoiceAnalyzer import", False, str(e))
        return

    result("VoiceAnalyzer import", True,
           f"model_loaded={analyzer.model_loaded}")

    # ── Test 1: Silent audio → score near 0, is_silent flag ───────────────────
    silence = make_wav_bytes(duration=3.0, noise_level=0.0001, freq=0.1)
    res = analyzer.analyze(silence)
    result("Silent audio → is_silent=True",
           res.get("is_silent", False),
           f"score={res['voice_fraud_score']}, flags={res['flags']}")

    # ── Test 2: Natural voice → lower fraud score than flat voice ─────────────
    natural_wav = make_wav_bytes(duration=3.0, flat_pitch=False)
    flat_wav = make_wav_bytes(duration=3.0, flat_pitch=True, noise_level=0.005)

    res_natural = analyzer.analyze(natural_wav)
    res_flat = analyzer.analyze(flat_wav)

    result("Natural voice score < flat pitch score",
           res_natural["voice_fraud_score"] < res_flat["voice_fraud_score"],
           f"natural={res_natural['voice_fraud_score']:.3f}, flat={res_flat['voice_fraud_score']:.3f}")

    # ── Test 3: Flat pitch → triggers low_mfcc_variance or unnatural_pitch ────
    flat_flags = res_flat["flags"]
    result("Flat pitch audio → anomaly flags present",
           len(flat_flags) > 0,
           f"flags={flat_flags}")

    # ── Test 4: Score range ────────────────────────────────────────────────────
    for name, wav_bytes in [("natural", natural_wav), ("flat", flat_wav)]:
        res = analyzer.analyze(wav_bytes)
        in_range = 0.0 <= res["voice_fraud_score"] <= 1.0
        result(f"{name} voice score in [0.0, 1.0]", in_range,
               f"score={res['voice_fraud_score']}")

    # ── Test 5: Result dict has all required keys ──────────────────────────────
    required_keys = {"voice_fraud_score", "flags", "pitch_mean", "mfcc_variance", "is_silent"}
    res = analyzer.analyze(natural_wav)
    result("Result dict has all required keys",
           required_keys.issubset(res.keys()),
           f"keys={set(res.keys())}")

    # ── Test 6: Corrupt audio bytes ───────────────────────────────────────────
    corrupt_audio = b"NOT_AN_AUDIO_FILE" + b"\x00" * 100
    try:
        res = analyzer.analyze(corrupt_audio)
        result("Corrupt audio → returns dict (doesn't crash)",
               isinstance(res, dict),
               f"score={res.get('voice_fraud_score', 'N/A')}")
    except Exception as e:
        result("Corrupt audio → returns dict (doesn't crash)", False, str(e))

    # ── Test 7: Short audio (< 1 second) ─────────────────────────────────────
    short_wav = make_wav_bytes(duration=0.5)
    try:
        res = analyzer.analyze(short_wav)
        result("Short audio (0.5s) → returns dict",
               isinstance(res, dict) and "voice_fraud_score" in res,
               f"score={res.get('voice_fraud_score', 'N/A')}")
    except Exception as e:
        result("Short audio (0.5s) → returns dict", False, str(e))


# ─── TEST: RiskEngine ─────────────────────────────────────────────────────────

def test_risk_engine(verbose: bool = False):
    section("RISK ENGINE TESTS")

    try:
        from risk_engine import RiskEngine, RiskResult
        engine = RiskEngine()
    except ImportError as e:
        result("RiskEngine import", False, str(e))
        return

    result("RiskEngine import", True)

    def make_voice(score):
        return {"voice_fraud_score": score, "flags": [], "is_silent": False}

    def make_content(score, keywords=None, category="Unknown", patterns=None):
        return {
            "content_fraud_score": score,
            "matched_keywords": keywords or [],
            "category": category,
            "pattern_categories": patterns or [],
        }

    # ── Test 1: Low scores → SAFE ──────────────────────────────────────────────
    r = engine.compute(make_voice(0.05), make_content(0.10))
    result("Low scores → SAFE",
           r.risk_level == "SAFE" and r.color == "green",
           f"score={r.final_score_pct}%, level={r.risk_level}")

    # ── Test 2: Medium scores → SUSPICIOUS ────────────────────────────────────
    r = engine.compute(make_voice(0.45), make_content(0.50))
    result("Medium scores → SUSPICIOUS",
           r.risk_level == "SUSPICIOUS" and r.color == "yellow",
           f"score={r.final_score_pct}%, level={r.risk_level}")

    # ── Test 3: High scores → HIGH RISK ───────────────────────────────────────
    r = engine.compute(make_voice(0.70), make_content(0.75))
    result("High scores → HIGH RISK",
           r.risk_level == "HIGH RISK" and r.color == "orange",
           f"score={r.final_score_pct}%, level={r.risk_level}")

    # ── Test 4: Very high scores → CRITICAL FRAUD ─────────────────────────────
    r = engine.compute(make_voice(0.90), make_content(0.95))
    result("Very high scores → CRITICAL FRAUD",
           r.risk_level == "CRITICAL FRAUD" and r.color == "red",
           f"score={r.final_score_pct}%, level={r.risk_level}")

    # ── Test 5: Weighting — content has more influence (60%) ──────────────────
    r_voice_dominant = engine.compute(make_voice(0.90), make_content(0.10))
    r_content_dominant = engine.compute(make_voice(0.10), make_content(0.90))
    result("Content score (60%) outweighs voice score (40%)",
           r_content_dominant.final_score > r_voice_dominant.final_score,
           f"voice_dom={r_voice_dominant.final_score:.3f}, content_dom={r_content_dominant.final_score:.3f}")

    # ── Test 6: Both high → amplification boost ────────────────────────────────
    r_both = engine.compute(make_voice(0.80), make_content(0.80))
    r_weighted_only = 0.80 * 0.40 + 0.80 * 0.60   # = 0.80 without boost
    result("Both scores high → amplification applied",
           r_both.final_score > r_weighted_only,
           f"actual={r_both.final_score:.3f}, simple_weighted={r_weighted_only:.3f}")

    # ── Test 7: Score always in [0.0, 1.0] range ──────────────────────────────
    edge_cases = [(0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)]
    all_valid = all(
        0.0 <= engine.compute(make_voice(v), make_content(c)).final_score <= 1.0
        for v, c in edge_cases
    )
    result("Edge case scores always in [0.0, 1.0]", all_valid)

    # ── Test 8: Result serializable to dict ───────────────────────────────────
    r = engine.compute(make_voice(0.5), make_content(0.5), "test transcript", 500.0)
    d = r.to_dict()
    result("RiskResult.to_dict() returns dict",
           isinstance(d, dict) and "final_score" in d and "risk_level" in d,
           f"keys={list(d.keys())[:6]}...")

    # ── Test 9: Recommendation is non-empty string ─────────────────────────────
    result("Recommendation text is non-empty",
           isinstance(r.recommendation, str) and len(r.recommendation) > 10,
           f"len={len(r.recommendation)}")

    # ── Test 10: Silent audio → score suppressed ──────────────────────────────
    r_silent = engine.compute(
        {"voice_fraud_score": 0.0, "flags": [], "is_silent": True},
        make_content(0.30)
    )
    result("Silent audio flag → score suppressed",
           r_silent.final_score < 0.30,
           f"score={r_silent.final_score:.3f}")


# ─── TEST: Full Pipeline ──────────────────────────────────────────────────────

def test_full_pipeline(verbose: bool = False):
    section("FULL PIPELINE INTEGRATION TESTS")

    try:
        from voice_analyzer import VoiceAnalyzer
        from content_analyzer import ContentAnalyzer
        from risk_engine import RiskEngine

        voice_analyzer = VoiceAnalyzer()
        content_analyzer = ContentAnalyzer()
        risk_engine = RiskEngine()
    except ImportError as e:
        result("Module imports", False, str(e))
        return

    result("All three modules imported", True)

    # ── Test: Normal call — end to end ────────────────────────────────────────
    normal_wav = make_wav_bytes(duration=3.0, flat_pitch=False)
    normal_text = "Yes I will be available at 3 PM tomorrow. Thank you for calling."

    t0 = time.time()
    voice_result = voice_analyzer.analyze(normal_wav)
    content_result = content_analyzer.analyze(normal_text)
    risk_result = risk_engine.compute(
        voice_result, content_result, normal_text, (time.time()-t0)*1000
    )

    result("Normal call pipeline completes without error",
           isinstance(risk_result.final_score, float),
           f"score={risk_result.final_score_pct}%, level={risk_result.risk_level}")

    result("Normal call → SAFE or SUSPICIOUS",
           risk_result.risk_level in ("SAFE", "SUSPICIOUS"),
           f"level={risk_result.risk_level}, score={risk_result.final_score_pct}%")

    # ── Test: Scam call — end to end ──────────────────────────────────────────
    scam_wav = make_wav_bytes(duration=3.0, flat_pitch=True, noise_level=0.003)
    scam_text = (
        "I am calling from RBI. Your Aadhaar number is linked to illegal money laundering. "
        "An arrest warrant has been issued. You will be arrested in 2 hours. "
        "Do not tell your family. Pay 50,000 rupees bail amount now. Share your OTP immediately."
    )

    t0 = time.time()
    voice_result_scam = voice_analyzer.analyze(scam_wav)
    content_result_scam = content_analyzer.analyze(scam_text)
    risk_result_scam = risk_engine.compute(
        voice_result_scam, content_result_scam, scam_text, (time.time()-t0)*1000
    )

    result("Scam call pipeline completes without error",
           isinstance(risk_result_scam.final_score, float),
           f"score={risk_result_scam.final_score_pct}%, level={risk_result_scam.risk_level}")

    result("Scam call → HIGH RISK or CRITICAL FRAUD",
           risk_result_scam.risk_level in ("HIGH RISK", "CRITICAL FRAUD"),
           f"level={risk_result_scam.risk_level}, score={risk_result_scam.final_score_pct}%")

    # ── Test: Scam score > Normal score ───────────────────────────────────────
    result("Scam score > Normal score",
           risk_result_scam.final_score > risk_result.final_score,
           f"scam={risk_result_scam.final_score:.3f} > normal={risk_result.final_score:.3f}")

    # ── Test: Result has all required fields ───────────────────────────────────
    required = {
        "final_score", "final_score_pct", "risk_level", "color", "color_hex",
        "recommendation", "short_warning", "matched_keywords", "voice_flags",
        "category", "transcript", "processing_time_ms", "voice_model_used",
        "voice_fraud_score", "content_fraud_score",
    }
    result_dict = risk_result_scam.to_dict()
    missing = required - set(result_dict.keys())
    result("Result dict has all required fields",
           len(missing) == 0,
           f"missing={missing}" if missing else "all present")

    # ── Test: Processing time is measured ────────────────────────────────────
    result("Processing time > 0ms",
           risk_result_scam.processing_time_ms > 0,
           f"time={risk_result_scam.processing_time_ms:.0f}ms")

    # ── Test: Demo files are valid WAV ────────────────────────────────────────
    demo_dir = Path(__file__).parent.parent / "demo"
    for filename in ["scam_call_1.wav", "normal_call.wav"]:
        demo_path = demo_dir / filename
        if demo_path.exists():
            try:
                with wave.open(str(demo_path), "r") as wf:
                    frames = wf.getnframes()
                    sr = wf.getframerate()
                result(f"demo/{filename} is valid WAV",
                       frames > 0,
                       f"{frames/sr:.1f}s, {sr}Hz, {frames} frames")
            except Exception as e:
                result(f"demo/{filename} is valid WAV", False, str(e))
        else:
            result(f"demo/{filename} exists", False, f"File not found: {demo_path}")


# ─── TEST: Keyword CSV ────────────────────────────────────────────────────────

def test_keywords(verbose: bool = False):
    section("SCAM KEYWORDS CSV TESTS")

    csv_path = Path(__file__).parent / "models" / "scam_keywords.csv"

    result("scam_keywords.csv exists",
           csv_path.exists(),
           str(csv_path))

    if not csv_path.exists():
        return

    import csv as csv_mod

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv_mod.DictReader(f)
            rows = list(reader)
    except Exception as e:
        result("CSV readable", False, str(e))
        return

    result("CSV readable",
           len(rows) > 0,
           f"{len(rows)} rows")

    result("CSV has 200+ phrases",
           len(rows) >= 200,
           f"count={len(rows)}")

    result("CSV has required columns",
           all("phrase" in r and "risk_weight" in r for r in rows[:5]),
           f"columns={list(rows[0].keys()) if rows else []}")

    # Check weight validity
    valid_weights = all(
        0.0 <= float(r["risk_weight"]) <= 1.0
        for r in rows
        if r.get("risk_weight")
    )
    result("All risk_weights in [0.0, 1.0]", valid_weights)

    # Check for Indian scam keywords
    phrases = [r["phrase"].lower() for r in rows]
    indian_checks = [
        ("otp",        "otp" in phrases),
        ("aadhaar",    any("aadhaar" in p for p in phrases)),
        ("upi",        any("upi" in p for p in phrases)),
        ("rbi",        "rbi" in phrases),
        ("arrest warrant", "arrest warrant" in phrases),
    ]
    for kw, present in indian_checks:
        result(f"'{kw}' present in keywords", present)


# ─── Main runner ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PhishShield test suite")
    parser.add_argument("--verbose", action="store_true", help="Show details for passing tests too")
    parser.add_argument("--module", choices=["content", "voice", "risk", "pipeline", "keywords"],
                        help="Run only a specific test module")
    args = parser.parse_args()

    print("\n" + "═" * 55)
    print("  🛡️  PHISHSHIELD TEST SUITE")
    print("═" * 55)

    # Change to backend directory so imports work
    import os
    os.chdir(Path(__file__).parent)

    module = args.module
    verbose = args.verbose

    if module is None or module == "keywords":
        test_keywords(verbose)
    if module is None or module == "content":
        test_content_analyzer(verbose)
    if module is None or module == "voice":
        test_voice_analyzer(verbose)
    if module is None or module == "risk":
        test_risk_engine(verbose)
    if module is None or module == "pipeline":
        test_full_pipeline(verbose)

    # Summary
    print(f"\n{'═'*55}")
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed

    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  ·  {failed} failed")
        print(f"\n  Failed tests:")
        for name, p, detail in results:
            if not p:
                print(f"    ❌ {name}")
                if detail:
                    print(f"       {detail}")
    else:
        print("  · All tests passed! 🎉")

    print(f"{'═'*55}\n")

    # Return non-zero exit code if any tests failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
