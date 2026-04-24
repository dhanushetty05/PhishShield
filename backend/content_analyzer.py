"""
content_analyzer.py — PhishShield
Analyzes transcribed call text for fraud indicators using:
  1. Weighted keyword matching (200+ scam phrases)
  2. Regex-based NLP pattern detection
  3. Fraud category classification

Covers Indian fraud patterns (UPI, Aadhaar, RBI, OTP) and global scam tactics.
"""

import re
import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to scam keyword CSV
KEYWORDS_CSV_PATH = Path(__file__).parent / "models" / "scam_keywords.csv"


# ─── Built-in scam keyword database ──────────────────────────────────────────
# Format: (phrase, risk_weight) — weight 0.0–1.0
# Higher weight = stronger indicator of fraud
SCAM_KEYWORDS_DEFAULT = [
    # ── OTP / Authentication fraud ────────────────────────────────────────────
    ("otp", 0.95), ("one time password", 0.95), ("share your otp", 1.0),
    ("enter the otp", 0.95), ("otp received", 0.90), ("otp expired", 0.85),
    ("verification code", 0.80), ("confirm your otp", 0.95),

    # ── Banking / UPI fraud ───────────────────────────────────────────────────
    ("upi", 0.70), ("upi pin", 0.95), ("upi id", 0.75), ("google pay", 0.60),
    ("phonepe", 0.60), ("paytm", 0.60), ("bhim upi", 0.70),
    ("bank account number", 0.85), ("account number", 0.75),
    ("ifsc code", 0.80), ("net banking", 0.75), ("internet banking", 0.75),
    ("transaction failed", 0.70), ("failed transaction", 0.70),
    ("refund process", 0.75), ("refund amount", 0.70),
    ("cvv", 0.95), ("cvv number", 0.98), ("card number", 0.90),
    ("debit card", 0.80), ("credit card details", 0.90),
    ("card expiry", 0.85), ("card verification", 0.88),
    ("account blocked", 0.90), ("account suspended", 0.88),
    ("account frozen", 0.90), ("account will be closed", 0.88),
    ("minimum balance", 0.60), ("kyc update", 0.85), ("kyc expired", 0.88),
    ("kyc verification", 0.85), ("complete your kyc", 0.88),

    # ── Aadhaar / Indian Identity fraud ──────────────────────────────────────
    ("aadhaar", 0.75), ("aadhaar number", 0.85), ("aadhaar card", 0.80),
    ("aadhaar linked", 0.82), ("aadhaar verification", 0.85),
    ("pan card", 0.70), ("pan number", 0.80), ("pan verification", 0.82),
    ("voter id", 0.65), ("driving licence", 0.60),
    ("biometric", 0.70), ("fingerprint verification", 0.72),

    # ── RBI / Government impersonation ───────────────────────────────────────
    ("reserve bank of india", 0.88), ("rbi", 0.80), ("rbi officer", 0.92),
    ("rbi calling", 0.95), ("rbi headquarters", 0.92),
    ("income tax", 0.75), ("income tax department", 0.80),
    ("income tax notice", 0.88), ("tax evasion", 0.85),
    ("it department", 0.80), ("tax refund", 0.78),
    ("enforcement directorate", 0.85), ("ed officer", 0.88),
    ("cbi officer", 0.90), ("cbi calling", 0.92),
    ("cyber crime branch", 0.85), ("cybercrime police", 0.85),
    ("supreme court", 0.85), ("high court notice", 0.88),
    ("government scheme", 0.70), ("pm scheme", 0.72),
    ("ministry of finance", 0.82), ("trai", 0.80),
    ("telecom regulatory", 0.78), ("your number will be blocked", 0.90),
    ("sim card blocked", 0.88), ("sim blocked", 0.88),

    # ── Password / PIN / Security ─────────────────────────────────────────────
    ("password", 0.80), ("pin number", 0.88), ("atm pin", 0.95),
    ("share your pin", 0.98), ("tell me your password", 0.98),
    ("security code", 0.85), ("authentication code", 0.85),
    ("secret code", 0.88), ("passcode", 0.82),

    # ── Urgency language ─────────────────────────────────────────────────────
    ("immediately", 0.70), ("urgent", 0.68), ("right now", 0.65),
    ("act now", 0.72), ("within 24 hours", 0.75), ("within an hour", 0.78),
    ("last chance", 0.72), ("final warning", 0.80), ("deadline today", 0.75),
    ("time is running out", 0.70), ("limited time", 0.65),
    ("do not delay", 0.70), ("without any delay", 0.72),
    ("as soon as possible", 0.55), ("asap", 0.55),
    ("emergency", 0.60), ("critical alert", 0.72),
    ("before it is too late", 0.75), ("expire today", 0.72),

    # ── Threat language ───────────────────────────────────────────────────────
    ("arrest warrant", 0.95), ("fir registered", 0.90), ("fir filed", 0.90),
    ("case filed against you", 0.92), ("you will be arrested", 0.95),
    ("police will come", 0.90), ("legal action", 0.82),
    ("court order", 0.85), ("warrant issued", 0.92),
    ("criminal charges", 0.90), ("money laundering", 0.88),
    ("drug trafficking", 0.85), ("illegal activity", 0.82),
    ("narcotic", 0.85), ("cocaine", 0.85),
    ("your address is under surveillance", 0.92),
    ("your call is being monitored", 0.88),

    # ── Prize / Lottery scams ─────────────────────────────────────────────────
    ("you have won", 0.90), ("congratulations you won", 0.92),
    ("lottery winner", 0.92), ("prize money", 0.85),
    ("claim your prize", 0.88), ("free gift", 0.70),
    ("lucky draw", 0.82), ("bumper prize", 0.85),
    ("you are selected", 0.80), ("lucky winner", 0.85),
    ("reward points", 0.65), ("cashback offer", 0.60),
    ("gift voucher", 0.65), ("amazon gift card", 0.80),

    # ── Remote access scams ───────────────────────────────────────────────────
    ("anydesk", 0.90), ("teamviewer", 0.85), ("remote access", 0.82),
    ("screen sharing", 0.78), ("install this app", 0.80),
    ("download this software", 0.80), ("click on the link", 0.82),
    ("follow the link", 0.80), ("visit this website", 0.75),
    ("install the apk", 0.88), ("sideload", 0.85),

    # ── Money transfer requests ───────────────────────────────────────────────
    ("send money", 0.88), ("transfer money", 0.88), ("transfer amount", 0.85),
    ("pay now", 0.80), ("payment required", 0.78),
    ("processing fee", 0.80), ("registration fee", 0.80),
    ("security deposit", 0.78), ("token amount", 0.75),
    ("advance payment", 0.78), ("insurance amount", 0.75),
    ("bail amount", 0.90), ("fine amount", 0.80),

    # ── Sensitive data requests ───────────────────────────────────────────────
    ("date of birth", 0.60), ("mother's name", 0.65),
    ("residential address", 0.70), ("current address", 0.68),
    ("full name", 0.50), ("email address", 0.55),
    ("social security", 0.90), ("passport number", 0.80),
    ("confirm your details", 0.72), ("verify your identity", 0.70),
    ("identity proof", 0.70), ("photo id", 0.65),

    # ── Job / Investment scams ────────────────────────────────────────────────
    ("work from home", 0.65), ("earn from home", 0.70),
    ("part time job", 0.65), ("data entry job", 0.68),
    ("earn daily", 0.72), ("daily income", 0.70),
    ("guaranteed returns", 0.82), ("double your money", 0.90),
    ("investment opportunity", 0.70), ("crypto investment", 0.72),
    ("bitcoin", 0.65), ("high returns", 0.72),
    ("no risk investment", 0.82), ("zero risk", 0.80),

    # ── Generic red flags ─────────────────────────────────────────────────────
    ("do not tell anyone", 0.88), ("keep this call confidential", 0.90),
    ("do not inform your family", 0.92), ("keep it secret", 0.88),
    ("this is confidential", 0.82), ("between us", 0.75),
    ("your phone will be disconnected", 0.88),
    ("number will be blocked", 0.85),
]


# ─── NLP Pattern definitions ──────────────────────────────────────────────────
NLP_PATTERNS = [
    # Authority impersonation
    {
        "pattern": r"\b(i am|this is|calling from|officer from|official from)\b.{0,30}\b(rbi|reserve bank|income tax|cbi|police|court|government|ministry|enforcement|trai|telecom|cyber crime)\b",
        "weight": 0.90,
        "category": "Authority Impersonation",
        "flag": "authority_impersonation"
    },
    # Sensitive data request sentence
    {
        "pattern": r"\b(share|tell|give|provide|send|confirm|enter|type)\b.{0,20}\b(otp|pin|password|cvv|account number|card number|aadhaar|pan)\b",
        "weight": 0.95,
        "category": "Sensitive Data Request",
        "flag": "sensitive_data_request"
    },
    # Threat + arrest language
    {
        "pattern": r"\b(arrest|jail|prison|fir|warrant|case|charges|legal action|sue)\b.{0,30}\b(you|your name|your account|against you)\b",
        "weight": 0.92,
        "category": "Threat / Legal Intimidation",
        "flag": "threat_language"
    },
    # Prize / lottery claim
    {
        "pattern": r"\b(won|winner|selected|prize|lottery|reward|gift)\b.{0,30}\b(claim|collect|receive|get|redeem)\b",
        "weight": 0.88,
        "category": "Lottery / Prize Scam",
        "flag": "lottery_scam"
    },
    # Urgency + action command
    {
        "pattern": r"\b(immediately|right now|within|today|urgent|quickly|fast)\b.{0,20}\b(pay|transfer|send|deposit|click|call|verify|update)\b",
        "weight": 0.80,
        "category": "Urgency Tactic",
        "flag": "urgency_tactic"
    },
    # Remote access instruction
    {
        "pattern": r"\b(install|download|open|launch|click)\b.{0,20}\b(anydesk|teamviewer|app|link|apk|software|remote)\b",
        "weight": 0.88,
        "category": "Remote Access Scam",
        "flag": "remote_access"
    },
    # Secrecy instruction
    {
        "pattern": r"\b(do not|don't|never|avoid)\b.{0,20}\b(tell|inform|share|mention|discuss)\b.{0,20}\b(anyone|family|wife|husband|friends|police|bank)\b",
        "weight": 0.92,
        "category": "Secrecy Demand",
        "flag": "secrecy_demand"
    },
    # Money transfer instruction
    {
        "pattern": r"\b(transfer|send|deposit|pay)\b.{0,20}\b(rupees|rs|inr|amount|money|funds|lakh|thousand|crore)\b",
        "weight": 0.85,
        "category": "Money Transfer Request",
        "flag": "money_transfer"
    },
    # KYC / verification deadline
    {
        "pattern": r"\b(kyc|verification|update|renew)\b.{0,20}\b(expire|expired|deadline|today|hours|immediately|block|suspend)\b",
        "weight": 0.88,
        "category": "KYC Expiry Threat",
        "flag": "kyc_threat"
    },
    # SIM / number blocking threat
    {
        "pattern": r"\b(sim|number|mobile|phone)\b.{0,20}\b(block|disconnect|suspend|cancel|deactivate)\b",
        "weight": 0.85,
        "category": "SIM Block Threat",
        "flag": "sim_threat"
    },
]


class ContentAnalyzer:
    """
    Analyzes call transcript text for fraud patterns.
    Combines keyword scoring with NLP pattern detection.
    """

    def __init__(self):
        self.keywords: dict[str, float] = {}
        self._load_keywords()

    def _load_keywords(self):
        """
        Load keywords from CSV file (if available) or use built-in defaults.
        CSV format: phrase,risk_weight
        """
        if KEYWORDS_CSV_PATH.exists():
            try:
                with open(KEYWORDS_CSV_PATH, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        phrase = row.get("phrase", "").strip().lower()
                        try:
                            weight = float(row.get("risk_weight", 0.5))
                        except ValueError:
                            weight = 0.5
                        if phrase:
                            self.keywords[phrase] = weight
                logger.info(f"Loaded {len(self.keywords)} keywords from {KEYWORDS_CSV_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load keyword CSV: {e}. Using built-in defaults.")
                self._use_defaults()
        else:
            logger.info("Keyword CSV not found. Using built-in keyword database.")
            self._use_defaults()
            # Save the defaults to CSV for future reference / editing
            self._save_keywords_csv()

    def _use_defaults(self):
        """Load the built-in keyword dictionary."""
        self.keywords = {phrase.lower(): weight for phrase, weight in SCAM_KEYWORDS_DEFAULT}

    def _save_keywords_csv(self):
        """Save the built-in keywords to a CSV file for easy editing."""
        try:
            KEYWORDS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(KEYWORDS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["phrase", "risk_weight"])
                writer.writeheader()
                for phrase, weight in sorted(SCAM_KEYWORDS_DEFAULT, key=lambda x: -x[1]):
                    writer.writerow({"phrase": phrase, "risk_weight": weight})
            logger.info(f"Saved {len(SCAM_KEYWORDS_DEFAULT)} keywords to {KEYWORDS_CSV_PATH}")
        except Exception as e:
            logger.warning(f"Could not save keywords CSV: {e}")

    def _keyword_score(self, text_lower: str) -> tuple[float, list[str]]:
        """
        Scan text for known scam keywords and compute a weighted score.

        Strategy: Use the maximum-weight matched keyword as the base,
        then add diminishing bonuses for each additional match.
        This prevents a single word from being gamed while rewarding
        texts with many diverse fraud signals.

        Returns:
            (score 0.0–1.0, list of matched keyword strings)
        """
        matched = []
        matched_weights = []

        for phrase, weight in self.keywords.items():
            if phrase in text_lower:
                matched.append(phrase)
                matched_weights.append(weight)

        if not matched:
            return 0.0, []

        # Sort by weight descending
        pairs = sorted(zip(matched_weights, matched), reverse=True)
        matched_weights_sorted = [w for w, _ in pairs]
        matched_sorted = [p for _, p in pairs]

        # Base score = highest single keyword weight
        base = matched_weights_sorted[0]

        # Additional matches add diminishing bonuses (20% of remaining gap)
        score = base
        for w in matched_weights_sorted[1:]:
            score = score + (1.0 - score) * 0.20 * w

        score = min(score, 1.0)
        return round(score, 4), matched_sorted[:15]  # Return top 15 matches

    def _pattern_score(self, text_lower: str) -> tuple[float, list[str], list[str], str]:
        """
        Apply regex NLP patterns to detect complex fraud sentence structures.

        Returns:
            (score 0.0–1.0, list of flags, list of pattern categories, primary category)
        """
        flags = []
        categories = []
        weights = []

        for pattern_def in NLP_PATTERNS:
            try:
                if re.search(pattern_def["pattern"], text_lower, re.IGNORECASE):
                    flags.append(pattern_def["flag"])
                    categories.append(pattern_def["category"])
                    weights.append(pattern_def["weight"])
            except re.error as e:
                logger.warning(f"Regex error in pattern '{pattern_def['pattern']}': {e}")

        if not weights:
            return 0.0, [], [], "Unknown"

        # Combine pattern scores with diminishing returns
        weights_sorted = sorted(weights, reverse=True)
        score = weights_sorted[0]
        for w in weights_sorted[1:]:
            score = score + (1.0 - score) * 0.25 * w
        score = min(score, 1.0)

        # Primary category = highest-weight pattern's category
        primary_idx = weights.index(max(weights))
        primary_category = categories[primary_idx]

        return round(score, 4), flags, categories, primary_category

    def _determine_fraud_category(self, matched_keywords: list[str],
                                  pattern_categories: list[str],
                                  text_lower: str) -> str:
        """
        Classify the call into a specific fraud category based on signals.
        Used for user-facing display ("Banking Fraud", "KYC Scam", etc.)
        """
        # Priority order of categories
        if "authority_impersonation" in pattern_categories or any(
            k in text_lower for k in ["cbi", "rbi officer", "income tax officer", "cyber crime"]
        ):
            if any(k in text_lower for k in ["arrest", "warrant", "fir", "case"]):
                return "Police / Government Impersonation"
            return "Authority Impersonation"

        if any(k in matched_keywords for k in ["otp", "cvv", "atm pin", "upi pin"]):
            return "Banking / OTP Fraud"

        if any(k in matched_keywords for k in ["aadhaar", "pan card", "kyc", "kyc update"]):
            return "KYC / Identity Fraud"

        if any(k in matched_keywords for k in ["lottery winner", "you have won", "prize money", "lucky draw"]):
            return "Lottery / Prize Scam"

        if any(k in matched_keywords for k in ["anydesk", "teamviewer", "install this app", "remote access"]):
            return "Remote Access Scam"

        if any(k in matched_keywords for k in ["income tax notice", "tax evasion", "tax refund"]):
            return "Income Tax Scam"

        if any(k in matched_keywords for k in ["send money", "transfer money", "pay now", "bail amount"]):
            return "Money Transfer Fraud"

        if any(k in matched_keywords for k in ["sim card blocked", "number will be blocked", "trai"]):
            return "SIM / Telecom Fraud"

        if any(k in matched_keywords for k in ["guaranteed returns", "double your money", "investment opportunity"]):
            return "Investment Fraud"

        if pattern_categories:
            return pattern_categories[0]

        return "General Fraud"

    def analyze(self, transcript: str) -> dict:
        """
        Main analysis function. Takes a call transcript and returns
        a complete content fraud analysis result.

        Args:
            transcript: Transcribed call text (from Whisper or any STT)

        Returns:
            dict with keys:
              - content_fraud_score (float 0.0–1.0)
              - matched_keywords (list of str)
              - flags (list of str)
              - category (str fraud category)
              - pattern_categories (list of str)
              - keyword_count (int)
        """
        if not transcript or not transcript.strip():
            return {
                "content_fraud_score": 0.0,
                "matched_keywords": [],
                "flags": [],
                "category": "Unknown",
                "pattern_categories": [],
                "keyword_count": 0,
            }

        text_lower = transcript.lower().strip()

        # ── Keyword scoring ───────────────────────────────────────────────────
        kw_score, matched_keywords = self._keyword_score(text_lower)

        # ── Pattern scoring ───────────────────────────────────────────────────
        pat_score, flags, pattern_categories, primary_category = self._pattern_score(text_lower)

        # ── Combine scores ────────────────────────────────────────────────────
        # Keywords are a strong signal (60%), patterns are more precise (40%)
        if kw_score > 0 or pat_score > 0:
            combined = (kw_score * 0.60) + (pat_score * 0.40)
        else:
            combined = 0.0

        # Determine fraud category
        category = self._determine_fraud_category(matched_keywords, pattern_categories, text_lower)

        return {
            "content_fraud_score": round(float(combined), 4),
            "matched_keywords": matched_keywords,
            "flags": flags,
            "category": category,
            "pattern_categories": pattern_categories,
            "keyword_count": len(matched_keywords),
        }


# ── Singleton instance ────────────────────────────────────────────────────────
_analyzer_instance: Optional[ContentAnalyzer] = None


def get_content_analyzer() -> ContentAnalyzer:
    """Return a singleton ContentAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ContentAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # Test with sample transcripts
    analyzer = ContentAnalyzer()

    test_cases = [
        {
            "label": "Banking OTP Scam",
            "text": "Hello sir, I am calling from RBI. Your Aadhaar card is linked with an illegal account. Please share your OTP immediately to verify your identity or your account will be blocked within 24 hours."
        },
        {
            "label": "Lottery Scam",
            "text": "Congratulations! You have won the lucky draw prize of 5 lakh rupees. To claim your prize, please provide your bank account number and pay a processing fee of 2000 rupees."
        },
        {
            "label": "Normal Call",
            "text": "Hi, I am calling to confirm the delivery of your order. It will arrive tomorrow between 10 AM and 2 PM. Is there anything else you need?"
        },
        {
            "label": "Police Impersonation",
            "text": "This is the cyber crime branch. A case has been filed against you for money laundering. You will be arrested within 2 hours unless you pay the bail amount. Do not tell anyone about this call."
        },
    ]

    print("\n" + "=" * 60)
    print("CONTENT ANALYZER TEST")
    print("=" * 60)

    for case in test_cases:
        result = analyzer.analyze(case["text"])
        print(f"\n[{case['label']}]")
        print(f"  Score    : {result['content_fraud_score']:.2%}")
        print(f"  Category : {result['category']}")
        print(f"  Keywords : {result['matched_keywords'][:5]}")
        print(f"  Flags    : {result['flags']}")
