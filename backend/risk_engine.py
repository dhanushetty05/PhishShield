"""
risk_engine.py — PhishShield
Fuses voice fraud score (40%) and content fraud score (60%) into a final
risk score, maps it to a risk level, and generates user recommendations.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Risk level thresholds ────────────────────────────────────────────────────
SAFE_MAX = 0.30          # 0–30%  → SAFE
SUSPICIOUS_MAX = 0.60    # 31–60% → SUSPICIOUS
HIGH_RISK_MAX = 0.80     # 61–80% → HIGH RISK
# 81–100% → CRITICAL FRAUD

# ─── Weights for score fusion ─────────────────────────────────────────────────
VOICE_WEIGHT = 0.40
CONTENT_WEIGHT = 0.60


@dataclass
class RiskResult:
    """Complete fraud risk assessment result returned to the frontend."""

    # Core scores
    final_score: float          # 0.0–1.0 fused risk score
    final_score_pct: int        # 0–100 integer for display
    voice_fraud_score: float    # Raw voice analysis score
    content_fraud_score: float  # Raw content analysis score

    # Risk classification
    risk_level: str             # SAFE / SUSPICIOUS / HIGH RISK / CRITICAL FRAUD
    color: str                  # green / yellow / orange / red
    color_hex: str              # Hex color code for frontend gauge

    # User guidance
    recommendation: str         # Human-readable action recommendation
    short_warning: str          # Short banner text

    # Detail signals
    matched_keywords: list      # Scam keywords found in transcript
    voice_flags: list           # Voice anomaly flags
    category: str               # Fraud category classification
    pattern_categories: list    # NLP pattern categories triggered
    transcript: str             # The transcribed text

    # Metadata
    processing_time_ms: float   # Total analysis time in milliseconds
    voice_model_used: bool      # Whether ML model was used (vs rule-based only)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)


# ─── Risk level definitions ───────────────────────────────────────────────────
RISK_DEFINITIONS = {
    "SAFE": {
        "color": "green",
        "color_hex": "#22c55e",
        "short_warning": "No fraud detected",
        "recommendation": (
            "This call appears safe. Continue your conversation normally. "
            "Remain cautious — never share OTPs, PINs, or passwords with anyone."
        ),
    },
    "SUSPICIOUS": {
        "color": "yellow",
        "color_hex": "#eab308",
        "short_warning": "Suspicious patterns detected — stay alert",
        "recommendation": (
            "Some suspicious patterns have been detected. Be careful about sharing "
            "personal information. Do not share OTPs, bank details, or passwords. "
            "If you feel uncomfortable, it's OK to hang up and call back on the official number."
        ),
    },
    "HIGH RISK": {
        "color": "orange",
        "color_hex": "#f97316",
        "short_warning": "⚠️ HIGH RISK — Do not share any personal information",
        "recommendation": (
            "This call shows strong fraud indicators. DO NOT share OTPs, Aadhaar, "
            "account details, or make any payments. Legitimate banks and government "
            "agencies NEVER ask for OTPs or passwords over the phone. "
            "Consider ending the call immediately."
        ),
    },
    "CRITICAL FRAUD": {
        "color": "red",
        "color_hex": "#ef4444",
        "short_warning": "🚨 CRITICAL FRAUD DETECTED — HANG UP NOW",
        "recommendation": (
            "HANG UP IMMEDIATELY. This call has all the hallmarks of a fraud/scam call. "
            "Do NOT share any information, make any payments, or follow any instructions. "
            "Report this number to the National Cyber Crime Helpline: 1930 "
            "or visit cybercrime.gov.in. Never call back this number."
        ),
    },
}


def _classify_risk(score: float) -> str:
    """Map a 0.0–1.0 score to a risk level string."""
    if score <= SAFE_MAX:
        return "SAFE"
    elif score <= SUSPICIOUS_MAX:
        return "SUSPICIOUS"
    elif score <= HIGH_RISK_MAX:
        return "HIGH RISK"
    else:
        return "CRITICAL FRAUD"


class RiskEngine:
    """
    Combines voice and content analysis results into a unified risk assessment.

    Score fusion formula:
        final_score = (voice_score × 0.40) + (content_score × 0.60)

    Content score is weighted higher (60%) because keyword/pattern analysis
    is generally more precise than voice model predictions on short audio clips.
    When both signals are high, the combined score is boosted via amplification.
    """

    def compute(
        self,
        voice_result: dict,
        content_result: dict,
        transcript: str = "",
        processing_time_ms: float = 0.0,
    ) -> RiskResult:
        """
        Fuse voice and content scores into a final risk assessment.

        Args:
            voice_result:  Output dict from VoiceAnalyzer.analyze()
            content_result: Output dict from ContentAnalyzer.analyze()
            transcript:    Transcribed text (for passing through to frontend)
            processing_time_ms: Total pipeline time (for performance logging)

        Returns:
            RiskResult dataclass with complete assessment
        """
        # ── Extract raw scores ─────────────────────────────────────────────────
        voice_score = float(voice_result.get("voice_fraud_score", 0.0))
        content_score = float(content_result.get("content_fraud_score", 0.0))

        # ── Clamp to [0, 1] ────────────────────────────────────────────────────
        voice_score = max(0.0, min(1.0, voice_score))
        content_score = max(0.0, min(1.0, content_score))

        # ── Weighted fusion ────────────────────────────────────────────────────
        base_score = (voice_score * VOICE_WEIGHT) + (content_score * CONTENT_WEIGHT)

        # ── Signal amplification (when both detectors agree on fraud) ──────────
        # If both voice and content scores are high, the combined probability
        # is higher than a simple weighted average suggests.
        # Amplification only kicks in when BOTH scores are above 0.5.
        if voice_score > 0.5 and content_score > 0.5:
            # Joint probability model: P(fraud) gets a boost
            agreement_boost = (voice_score - 0.5) * (content_score - 0.5) * 0.4
            base_score = base_score + agreement_boost

        # If silent audio, suppress voice contribution
        if voice_result.get("is_silent", False):
            base_score = content_score * CONTENT_WEIGHT + 0.1

        final_score = float(max(0.0, min(1.0, base_score)))

        # ── Classify risk ──────────────────────────────────────────────────────
        risk_level = _classify_risk(final_score)
        risk_def = RISK_DEFINITIONS[risk_level]

        # ── Build result ───────────────────────────────────────────────────────
        result = RiskResult(
            # Scores
            final_score=round(final_score, 4),
            final_score_pct=int(round(final_score * 100)),
            voice_fraud_score=round(voice_score, 4),
            content_fraud_score=round(content_score, 4),
            # Risk classification
            risk_level=risk_level,
            color=risk_def["color"],
            color_hex=risk_def["color_hex"],
            # User guidance
            recommendation=risk_def["recommendation"],
            short_warning=risk_def["short_warning"],
            # Signals
            matched_keywords=content_result.get("matched_keywords", []),
            voice_flags=voice_result.get("flags", []),
            category=content_result.get("category", "Unknown"),
            pattern_categories=content_result.get("pattern_categories", []),
            transcript=transcript,
            # Metadata
            processing_time_ms=round(processing_time_ms, 1),
            voice_model_used=not voice_result.get("flags", []) == ["analysis_failed"],
        )

        logger.info(
            f"RiskEngine → score={final_score:.2%} [{risk_level}] "
            f"voice={voice_score:.2%} content={content_score:.2%} "
            f"time={processing_time_ms:.0f}ms"
        )

        return result


# ─── Singleton instance ───────────────────────────────────────────────────────
_engine_instance: Optional[RiskEngine] = None


def get_risk_engine() -> RiskEngine:
    """Return a singleton RiskEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RiskEngine()
    return _engine_instance


if __name__ == "__main__":
    # Demo: test risk engine with various score combinations
    engine = RiskEngine()

    test_cases = [
        {
            "label": "Safe Call",
            "voice": {"voice_fraud_score": 0.10, "flags": [], "is_silent": False},
            "content": {"content_fraud_score": 0.05, "matched_keywords": [], "category": "Unknown", "pattern_categories": []},
            "transcript": "Yes I will be home tomorrow afternoon, thanks for calling."
        },
        {
            "label": "Suspicious Call",
            "voice": {"voice_fraud_score": 0.45, "flags": ["low_mfcc_variance"], "is_silent": False},
            "content": {"content_fraud_score": 0.55, "matched_keywords": ["otp", "urgent"], "category": "Banking Fraud", "pattern_categories": ["Urgency Tactic"]},
            "transcript": "Please share your OTP urgently to complete the verification."
        },
        {
            "label": "High Risk",
            "voice": {"voice_fraud_score": 0.70, "flags": ["unnatural_pitch", "low_mfcc_variance"], "is_silent": False},
            "content": {"content_fraud_score": 0.78, "matched_keywords": ["rbi", "account blocked", "otp", "immediately"], "category": "Authority Impersonation", "pattern_categories": ["Authority Impersonation", "Urgency Tactic"]},
            "transcript": "I am calling from RBI. Your account is blocked. Share your OTP immediately."
        },
        {
            "label": "Critical Fraud",
            "voice": {"voice_fraud_score": 0.88, "flags": ["unnatural_pitch", "low_mfcc_variance", "voice_switching_detected"], "is_silent": False},
            "content": {"content_fraud_score": 0.95, "matched_keywords": ["arrest warrant", "cbi", "do not tell anyone", "pay now", "otp", "account blocked", "immediately"], "category": "Police / Government Impersonation", "pattern_categories": ["Authority Impersonation", "Threat / Legal Intimidation", "Secrecy Demand", "Money Transfer Request"]},
            "transcript": "This is CBI. Arrest warrant issued. Pay bail amount now. Do not tell anyone."
        },
    ]

    print("\n" + "=" * 65)
    print("RISK ENGINE TEST")
    print("=" * 65)

    for case in test_cases:
        result = engine.compute(case["voice"], case["content"], case["transcript"], processing_time_ms=750.0)
        print(f"\n[{case['label']}]")
        print(f"  Final Score  : {result.final_score_pct}% — {result.risk_level}")
        print(f"  Color        : {result.color}")
        print(f"  Voice Score  : {result.voice_fraud_score:.2%}")
        print(f"  Content Score: {result.content_fraud_score:.2%}")
        print(f"  Category     : {result.category}")
        print(f"  Warning      : {result.short_warning}")
