"""
generate_keywords.py — PhishShield
Standalone script to generate (or regenerate) the scam_keywords.csv file
used by content_analyzer.py.

Run this to reset keywords to defaults, or use it as a template to add
your own custom phrases before starting the backend.

Usage:
    python generate_keywords.py
    python generate_keywords.py --output /custom/path/keywords.csv
"""

import csv
import sys
import argparse
from pathlib import Path

# ─── Complete scam keyword database ──────────────────────────────────────────
# Format: (phrase, risk_weight, category)
# risk_weight: 0.0 = no risk, 1.0 = definite fraud signal
#
# Weights are calibrated based on:
#  - How unique the phrase is to fraud contexts (vs legitimate use)
#  - How often the phrase appears in documented scam transcripts
#  - Severity of harm if phrase is part of a real scam
#
SCAM_KEYWORDS = [

    # ── OTP / Authentication fraud ─────────────────────────────────────────
    # These phrases have almost no legitimate use over the phone
    ("otp",                          0.95, "OTP Fraud"),
    ("one time password",            0.95, "OTP Fraud"),
    ("share your otp",               1.00, "OTP Fraud"),
    ("enter the otp",                0.95, "OTP Fraud"),
    ("otp received",                 0.90, "OTP Fraud"),
    ("otp expired",                  0.85, "OTP Fraud"),
    ("verification code",            0.80, "OTP Fraud"),
    ("confirm your otp",             0.95, "OTP Fraud"),
    ("do not share otp",             0.75, "OTP Fraud"),  # Scammer pretending to warn
    ("otp has been sent",            0.85, "OTP Fraud"),
    ("enter the code",               0.72, "OTP Fraud"),
    ("six digit code",               0.82, "OTP Fraud"),
    ("four digit code",              0.80, "OTP Fraud"),

    # ── UPI / Digital payment fraud ───────────────────────────────────────
    ("upi pin",                      0.95, "UPI Fraud"),
    ("upi id",                       0.75, "UPI Fraud"),
    ("google pay",                   0.60, "UPI Fraud"),
    ("phonepe",                      0.60, "UPI Fraud"),
    ("paytm",                        0.60, "UPI Fraud"),
    ("bhim upi",                     0.70, "UPI Fraud"),
    ("upi transaction",              0.70, "UPI Fraud"),
    ("collect request",              0.80, "UPI Fraud"),  # UPI collect scam
    ("approve the request",          0.82, "UPI Fraud"),
    ("scan the qr",                  0.78, "UPI Fraud"),
    ("scan this qr code",            0.82, "UPI Fraud"),

    # ── Banking fraud ─────────────────────────────────────────────────────
    ("bank account number",          0.85, "Banking Fraud"),
    ("account number",               0.75, "Banking Fraud"),
    ("ifsc code",                    0.80, "Banking Fraud"),
    ("net banking",                  0.75, "Banking Fraud"),
    ("internet banking",             0.75, "Banking Fraud"),
    ("transaction failed",           0.70, "Banking Fraud"),
    ("failed transaction",           0.70, "Banking Fraud"),
    ("refund process",               0.75, "Banking Fraud"),
    ("refund amount",                0.70, "Banking Fraud"),
    ("cvv",                          0.95, "Banking Fraud"),
    ("cvv number",                   0.98, "Banking Fraud"),
    ("card number",                  0.90, "Banking Fraud"),
    ("debit card",                   0.80, "Banking Fraud"),
    ("credit card details",          0.90, "Banking Fraud"),
    ("card expiry",                  0.85, "Banking Fraud"),
    ("card verification",            0.88, "Banking Fraud"),
    ("account blocked",              0.90, "Banking Fraud"),
    ("account suspended",            0.88, "Banking Fraud"),
    ("account frozen",               0.90, "Banking Fraud"),
    ("account will be closed",       0.88, "Banking Fraud"),
    ("account will be blocked",      0.90, "Banking Fraud"),
    ("minimum balance",              0.60, "Banking Fraud"),
    ("kyc update",                   0.85, "Banking Fraud"),
    ("kyc expired",                  0.88, "Banking Fraud"),
    ("kyc verification",             0.85, "Banking Fraud"),
    ("complete your kyc",            0.88, "Banking Fraud"),
    ("pending kyc",                  0.82, "Banking Fraud"),
    ("update your kyc",              0.85, "Banking Fraud"),
    ("re-kyc",                       0.80, "Banking Fraud"),

    # ── Aadhaar / Indian identity fraud ───────────────────────────────────
    ("aadhaar",                      0.75, "Identity Fraud"),
    ("aadhaar number",               0.85, "Identity Fraud"),
    ("aadhaar card",                 0.80, "Identity Fraud"),
    ("aadhaar linked",               0.82, "Identity Fraud"),
    ("aadhaar verification",         0.85, "Identity Fraud"),
    ("aadhaar otp",                  0.95, "Identity Fraud"),
    ("aadhaar blocked",              0.90, "Identity Fraud"),
    ("pan card",                     0.70, "Identity Fraud"),
    ("pan number",                   0.80, "Identity Fraud"),
    ("pan verification",             0.82, "Identity Fraud"),
    ("voter id",                     0.65, "Identity Fraud"),
    ("driving licence",              0.60, "Identity Fraud"),
    ("biometric",                    0.70, "Identity Fraud"),
    ("fingerprint verification",     0.72, "Identity Fraud"),

    # ── RBI / Government impersonation ────────────────────────────────────
    ("reserve bank of india",        0.88, "Government Impersonation"),
    ("rbi",                          0.80, "Government Impersonation"),
    ("rbi officer",                  0.92, "Government Impersonation"),
    ("rbi calling",                  0.95, "Government Impersonation"),
    ("rbi headquarters",             0.92, "Government Impersonation"),
    ("rbi notification",             0.88, "Government Impersonation"),
    ("income tax",                   0.75, "Government Impersonation"),
    ("income tax department",        0.80, "Government Impersonation"),
    ("income tax notice",            0.88, "Government Impersonation"),
    ("income tax officer",           0.90, "Government Impersonation"),
    ("tax evasion",                  0.85, "Government Impersonation"),
    ("it department",                0.80, "Government Impersonation"),
    ("tax refund",                   0.78, "Government Impersonation"),
    ("tds refund",                   0.78, "Government Impersonation"),
    ("enforcement directorate",      0.85, "Government Impersonation"),
    ("ed officer",                   0.88, "Government Impersonation"),
    ("cbi officer",                  0.90, "Government Impersonation"),
    ("cbi calling",                  0.92, "Government Impersonation"),
    ("central bureau",               0.88, "Government Impersonation"),
    ("cyber crime branch",           0.85, "Government Impersonation"),
    ("cybercrime police",            0.85, "Government Impersonation"),
    ("cyber cell",                   0.82, "Government Impersonation"),
    ("supreme court",                0.85, "Government Impersonation"),
    ("high court notice",            0.88, "Government Impersonation"),
    ("court order",                  0.85, "Government Impersonation"),
    ("government scheme",            0.70, "Government Impersonation"),
    ("pm scheme",                    0.72, "Government Impersonation"),
    ("ministry of finance",          0.82, "Government Impersonation"),
    ("trai",                         0.80, "Government Impersonation"),
    ("telecom regulatory",           0.78, "Government Impersonation"),
    ("your number will be blocked",  0.90, "Government Impersonation"),
    ("sim card blocked",             0.88, "Government Impersonation"),
    ("sim blocked",                  0.88, "Government Impersonation"),
    ("mobile number disconnected",   0.88, "Government Impersonation"),
    ("narcotics bureau",             0.88, "Government Impersonation"),
    ("interpol",                     0.85, "Government Impersonation"),

    # ── Password / PIN / Security ──────────────────────────────────────────
    ("password",                     0.80, "Credential Theft"),
    ("pin number",                   0.88, "Credential Theft"),
    ("atm pin",                      0.95, "Credential Theft"),
    ("share your pin",               0.98, "Credential Theft"),
    ("tell me your password",        0.98, "Credential Theft"),
    ("security code",                0.85, "Credential Theft"),
    ("authentication code",          0.85, "Credential Theft"),
    ("secret code",                  0.88, "Credential Theft"),
    ("passcode",                     0.82, "Credential Theft"),
    ("ipin",                         0.88, "Credential Theft"),
    ("mpin",                         0.90, "Credential Theft"),
    ("transaction password",         0.88, "Credential Theft"),
    ("login password",               0.88, "Credential Theft"),

    # ── Urgency language ──────────────────────────────────────────────────
    ("immediately",                  0.70, "Urgency Tactic"),
    ("urgent",                       0.68, "Urgency Tactic"),
    ("right now",                    0.65, "Urgency Tactic"),
    ("act now",                      0.72, "Urgency Tactic"),
    ("within 24 hours",              0.75, "Urgency Tactic"),
    ("within 2 hours",               0.80, "Urgency Tactic"),
    ("within an hour",               0.78, "Urgency Tactic"),
    ("within 30 minutes",            0.82, "Urgency Tactic"),
    ("last chance",                  0.72, "Urgency Tactic"),
    ("final warning",                0.80, "Urgency Tactic"),
    ("deadline today",               0.75, "Urgency Tactic"),
    ("time is running out",          0.70, "Urgency Tactic"),
    ("limited time",                 0.65, "Urgency Tactic"),
    ("do not delay",                 0.70, "Urgency Tactic"),
    ("without any delay",            0.72, "Urgency Tactic"),
    ("emergency",                    0.60, "Urgency Tactic"),
    ("critical alert",               0.72, "Urgency Tactic"),
    ("before it is too late",        0.75, "Urgency Tactic"),
    ("expire today",                 0.72, "Urgency Tactic"),
    ("expires in",                   0.65, "Urgency Tactic"),
    ("last opportunity",             0.70, "Urgency Tactic"),

    # ── Threat language ───────────────────────────────────────────────────
    ("arrest warrant",               0.95, "Threat Language"),
    ("fir registered",               0.90, "Threat Language"),
    ("fir filed",                    0.90, "Threat Language"),
    ("case filed against you",       0.92, "Threat Language"),
    ("you will be arrested",         0.95, "Threat Language"),
    ("police will come",             0.90, "Threat Language"),
    ("legal action",                 0.82, "Threat Language"),
    ("warrant issued",               0.92, "Threat Language"),
    ("criminal charges",             0.90, "Threat Language"),
    ("money laundering",             0.88, "Threat Language"),
    ("drug trafficking",             0.85, "Threat Language"),
    ("illegal activity",             0.82, "Threat Language"),
    ("narcotic",                     0.85, "Threat Language"),
    ("cocaine",                      0.85, "Threat Language"),
    ("your address is under surveillance", 0.92, "Threat Language"),
    ("your call is being monitored", 0.88, "Threat Language"),
    ("non bailable warrant",         0.95, "Threat Language"),
    ("lookout notice",               0.90, "Threat Language"),
    ("arrested tomorrow",            0.95, "Threat Language"),
    ("your name in fir",             0.92, "Threat Language"),

    # ── Prize / Lottery scams ─────────────────────────────────────────────
    ("you have won",                 0.90, "Lottery Scam"),
    ("congratulations you won",      0.92, "Lottery Scam"),
    ("lottery winner",               0.92, "Lottery Scam"),
    ("prize money",                  0.85, "Lottery Scam"),
    ("claim your prize",             0.88, "Lottery Scam"),
    ("free gift",                    0.70, "Lottery Scam"),
    ("lucky draw",                   0.82, "Lottery Scam"),
    ("bumper prize",                 0.85, "Lottery Scam"),
    ("you are selected",             0.80, "Lottery Scam"),
    ("lucky winner",                 0.85, "Lottery Scam"),
    ("reward points",                0.65, "Lottery Scam"),
    ("cashback offer",               0.60, "Lottery Scam"),
    ("gift voucher",                 0.65, "Lottery Scam"),
    ("amazon gift card",             0.80, "Lottery Scam"),
    ("flipkart winner",              0.85, "Lottery Scam"),
    ("jio prize",                    0.82, "Lottery Scam"),
    ("kbc winner",                   0.88, "Lottery Scam"),
    ("kaun banega crorepati",        0.88, "Lottery Scam"),
    ("jackpot winner",               0.90, "Lottery Scam"),
    ("ten lakh",                     0.78, "Lottery Scam"),
    ("fifty lakh",                   0.82, "Lottery Scam"),
    ("crore prize",                  0.88, "Lottery Scam"),

    # ── Remote access scams ───────────────────────────────────────────────
    ("anydesk",                      0.90, "Remote Access Scam"),
    ("teamviewer",                   0.85, "Remote Access Scam"),
    ("remote access",                0.82, "Remote Access Scam"),
    ("screen sharing",               0.78, "Remote Access Scam"),
    ("install this app",             0.80, "Remote Access Scam"),
    ("download this software",       0.80, "Remote Access Scam"),
    ("click on the link",            0.82, "Remote Access Scam"),
    ("follow the link",              0.80, "Remote Access Scam"),
    ("visit this website",           0.75, "Remote Access Scam"),
    ("install the apk",              0.88, "Remote Access Scam"),
    ("sideload",                     0.85, "Remote Access Scam"),
    ("allow access",                 0.75, "Remote Access Scam"),
    ("grant permission",             0.75, "Remote Access Scam"),
    ("i can see your screen",        0.92, "Remote Access Scam"),
    ("screen visible to me",         0.92, "Remote Access Scam"),
    ("quick support",                0.80, "Remote Access Scam"),
    ("ultraviewer",                  0.85, "Remote Access Scam"),
    ("airdroid",                     0.80, "Remote Access Scam"),

    # ── Money transfer requests ───────────────────────────────────────────
    ("send money",                   0.88, "Money Transfer Fraud"),
    ("transfer money",               0.88, "Money Transfer Fraud"),
    ("transfer amount",              0.85, "Money Transfer Fraud"),
    ("pay now",                      0.80, "Money Transfer Fraud"),
    ("payment required",             0.78, "Money Transfer Fraud"),
    ("processing fee",               0.80, "Money Transfer Fraud"),
    ("registration fee",             0.80, "Money Transfer Fraud"),
    ("security deposit",             0.78, "Money Transfer Fraud"),
    ("token amount",                 0.75, "Money Transfer Fraud"),
    ("advance payment",              0.78, "Money Transfer Fraud"),
    ("insurance amount",             0.75, "Money Transfer Fraud"),
    ("bail amount",                  0.90, "Money Transfer Fraud"),
    ("fine amount",                  0.80, "Money Transfer Fraud"),
    ("challan fee",                  0.78, "Money Transfer Fraud"),
    ("customs duty",                 0.75, "Money Transfer Fraud"),
    ("clearance fee",                0.78, "Money Transfer Fraud"),
    ("release fee",                  0.80, "Money Transfer Fraud"),
    ("send to this account",         0.88, "Money Transfer Fraud"),
    ("transfer to safe account",     0.92, "Money Transfer Fraud"),
    ("safe account",                 0.90, "Money Transfer Fraud"),
    ("government account",           0.88, "Money Transfer Fraud"),

    # ── Sensitive data requests ───────────────────────────────────────────
    ("date of birth",                0.60, "Data Theft"),
    ("mother's name",                0.65, "Data Theft"),
    ("residential address",          0.70, "Data Theft"),
    ("current address",              0.68, "Data Theft"),
    ("email address",                0.55, "Data Theft"),
    ("social security",              0.90, "Data Theft"),
    ("passport number",              0.80, "Data Theft"),
    ("confirm your details",         0.72, "Data Theft"),
    ("verify your identity",         0.70, "Data Theft"),
    ("identity proof",               0.70, "Data Theft"),
    ("photo id",                     0.65, "Data Theft"),
    ("form 16",                      0.72, "Data Theft"),
    ("salary slip",                  0.70, "Data Theft"),

    # ── Job / Investment scams ────────────────────────────────────────────
    ("work from home",               0.65, "Investment Fraud"),
    ("earn from home",               0.70, "Investment Fraud"),
    ("part time job",                0.65, "Investment Fraud"),
    ("data entry job",               0.68, "Investment Fraud"),
    ("earn daily",                   0.72, "Investment Fraud"),
    ("daily income",                 0.70, "Investment Fraud"),
    ("guaranteed returns",           0.82, "Investment Fraud"),
    ("double your money",            0.90, "Investment Fraud"),
    ("investment opportunity",       0.70, "Investment Fraud"),
    ("crypto investment",            0.72, "Investment Fraud"),
    ("bitcoin",                      0.65, "Investment Fraud"),
    ("high returns",                 0.72, "Investment Fraud"),
    ("no risk investment",           0.82, "Investment Fraud"),
    ("zero risk",                    0.80, "Investment Fraud"),
    ("300 percent return",           0.88, "Investment Fraud"),
    ("trading app",                  0.70, "Investment Fraud"),
    ("forex trading",                0.72, "Investment Fraud"),
    ("task based earning",           0.75, "Investment Fraud"),
    ("like and earn",                0.78, "Investment Fraud"),
    ("telegram group earning",       0.80, "Investment Fraud"),

    # ── Secrecy / isolation tactics ───────────────────────────────────────
    ("do not tell anyone",           0.88, "Secrecy Demand"),
    ("keep this call confidential",  0.90, "Secrecy Demand"),
    ("do not inform your family",    0.92, "Secrecy Demand"),
    ("keep it secret",               0.88, "Secrecy Demand"),
    ("this is confidential",         0.82, "Secrecy Demand"),
    ("between us",                   0.75, "Secrecy Demand"),
    ("do not tell your wife",        0.90, "Secrecy Demand"),
    ("do not tell your husband",     0.90, "Secrecy Demand"),
    ("do not discuss with anyone",   0.90, "Secrecy Demand"),
    ("private matter",               0.72, "Secrecy Demand"),
    ("do not go to police",          0.95, "Secrecy Demand"),
    ("do not contact bank",          0.92, "Secrecy Demand"),

    # ── Telecom / SIM fraud ───────────────────────────────────────────────
    ("your phone will be disconnected", 0.88, "Telecom Fraud"),
    ("number will be blocked",       0.85, "Telecom Fraud"),
    ("sim card will be cancelled",   0.88, "Telecom Fraud"),
    ("number linked to crime",       0.90, "Telecom Fraud"),
    ("your number used in fraud",    0.92, "Telecom Fraud"),
    ("trai regulation",              0.82, "Telecom Fraud"),
    ("dnd violation",                0.80, "Telecom Fraud"),
    ("telecom authority",            0.80, "Telecom Fraud"),
    ("mobile number blocked",        0.88, "Telecom Fraud"),
    ("number deactivated",           0.85, "Telecom Fraud"),
]


def generate_csv(output_path: str):
    """Write all keywords to a CSV file sorted by risk weight descending."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Sort by risk_weight descending, then alphabetically by phrase
    sorted_keywords = sorted(SCAM_KEYWORDS, key=lambda x: (-x[1], x[0]))

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phrase", "risk_weight", "category"])
        writer.writeheader()
        for phrase, weight, category in sorted_keywords:
            writer.writerow({
                "phrase": phrase,
                "risk_weight": weight,
                "category": category,
            })

    # Print statistics
    categories = {}
    for _, _, cat in SCAM_KEYWORDS:
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n✅ Keywords CSV written to: {path}")
    print(f"   Total phrases   : {len(SCAM_KEYWORDS)}")
    print(f"   Unique categories: {len(categories)}")
    print(f"\n   By category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"     {cat:<35} {count:>3} phrases")

    # Risk weight distribution
    weights = [w for _, w, _ in SCAM_KEYWORDS]
    critical  = sum(1 for w in weights if w >= 0.90)
    high      = sum(1 for w in weights if 0.75 <= w < 0.90)
    moderate  = sum(1 for w in weights if 0.60 <= w < 0.75)
    low       = sum(1 for w in weights if w < 0.60)

    print(f"\n   By risk weight:")
    print(f"     Critical  (≥0.90): {critical:>3} phrases")
    print(f"     High      (0.75–0.89): {high:>3} phrases")
    print(f"     Moderate  (0.60–0.74): {moderate:>3} phrases")
    print(f"     Low       (<0.60): {low:>3} phrases")


def main():
    parser = argparse.ArgumentParser(
        description="Generate PhishShield scam keywords CSV"
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "models" / "scam_keywords.csv"),
        help="Output CSV file path (default: backend/models/scam_keywords.csv)",
    )
    args = parser.parse_args()
    generate_csv(args.output)


if __name__ == "__main__":
    main()
