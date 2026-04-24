#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — PhishShield startup script
# Checks dependencies, optionally trains model, then starts the backend.
#
# Usage:
#   ./start.sh              → Start backend (skip training if model exists)
#   ./start.sh --train      → Force re-train model before starting
#   ./start.sh --train /path/to/ASVspoof2019  → Train with real dataset
#   ./start.sh --test       → Run test suite before starting
# ─────────────────────────────────────────────────────────────────────────────

set -e

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/backend" && pwd)"
MODEL_PATH="$BACKEND_DIR/models/fraud_voice_model.pkl"
PORT=8000

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗███████╗██╗  ██╗██╗███████╗██╗     ██████╗"
echo "  ██╔══██╗██║  ██║██║██╔════╝██║  ██║██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗"
echo "  ██████╔╝███████║██║███████╗███████║███████╗███████║██║█████╗  ██║     ██║  ██║"
echo "  ██╔═══╝ ██╔══██║██║╚════██║██╔══██║╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║"
echo "  ██║     ██║  ██║██║███████║██║  ██║███████║██║  ██║██║███████╗███████╗██████╔╝"
echo "  ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝"
echo -e "${NC}"
echo -e "  ${BOLD}Live AI-Powered Fraud Call Detection${NC}"
echo ""

# ─── Parse arguments ─────────────────────────────────────────────────────────
DO_TRAIN=false
DO_TEST=false
DATASET_PATH=""

for arg in "$@"; do
    case "$arg" in
        --train)    DO_TRAIN=true ;;
        --test)     DO_TEST=true ;;
        --help|-h)
            echo "Usage: ./start.sh [OPTIONS] [DATASET_PATH]"
            echo ""
            echo "  --train [PATH]  Train models before starting"
            echo "                  PATH = path to ASVspoof2019 dataset (optional)"
            echo "  --test          Run test suite before starting"
            echo "  --help          Show this help message"
            echo ""
            exit 0
            ;;
        /*)         DATASET_PATH="$arg" ;;
        *)          ;;
    esac
done

# ─── Check Python ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[1/5] Checking Python environment...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ python3 not found. Install Python 3.10+${NC}"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "     ${GREEN}✅ Python $PY_VERSION found${NC}"

# ─── Check pip dependencies ───────────────────────────────────────────────────
echo -e "${BOLD}[2/5] Checking required packages...${NC}"

MISSING_PACKAGES=()
check_pkg() {
    python3 -c "import $1" 2>/dev/null || MISSING_PACKAGES+=("$2")
}

check_pkg fastapi fastapi
check_pkg uvicorn uvicorn
check_pkg numpy numpy
check_pkg sklearn scikit-learn
check_pkg joblib joblib

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "     ${YELLOW}⚠️  Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    echo -e "     Installing..."
    pip install -r "$BACKEND_DIR/requirements.txt" --quiet
    echo -e "     ${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "     ${GREEN}✅ Core packages available${NC}"
fi

# Check optional packages
OPTIONAL_MISSING=()
check_optional() {
    python3 -c "import $1" 2>/dev/null || OPTIONAL_MISSING+=("$1")
}
check_optional whisper
check_optional librosa

if [ ${#OPTIONAL_MISSING[@]} -gt 0 ]; then
    echo -e "     ${YELLOW}⚠️  Optional packages missing: ${OPTIONAL_MISSING[*]}${NC}"
    echo -e "     ${YELLOW}   Voice analysis will use rule-based fallback${NC}"
    echo -e "     ${YELLOW}   Install with: pip install openai-whisper librosa${NC}"
fi

# ─── Check ffmpeg ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[3/5] Checking system dependencies...${NC}"
if command -v ffmpeg &>/dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
    echo -e "     ${GREEN}✅ ffmpeg $FFMPEG_VERSION found${NC}"
else
    echo -e "     ${YELLOW}⚠️  ffmpeg not found${NC}"
    echo -e "     ${YELLOW}   Audio format conversion may fail${NC}"
    echo -e "     ${YELLOW}   macOS:  brew install ffmpeg${NC}"
    echo -e "     ${YELLOW}   Ubuntu: sudo apt install ffmpeg${NC}"
fi

# ─── Train model if needed ────────────────────────────────────────────────────
echo -e "${BOLD}[4/5] Checking AI models...${NC}"

if [ "$DO_TRAIN" = true ] || [ ! -f "$MODEL_PATH" ]; then
    if [ "$DO_TRAIN" = true ]; then
        echo -e "     Training models (--train flag set)..."
    else
        echo -e "     ${YELLOW}Model not found. Training with synthetic data...${NC}"
    fi

    if [ -n "$DATASET_PATH" ] && [ -d "$DATASET_PATH" ]; then
        echo -e "     Using real dataset: $DATASET_PATH"
        python3 "$BACKEND_DIR/model_trainer.py" "$DATASET_PATH"
    else
        echo -e "     Using synthetic dataset (run --train /path/to/ASVspoof2019 for better accuracy)"
        python3 "$BACKEND_DIR/model_trainer.py"
    fi
    echo -e "     ${GREEN}✅ Models trained and saved${NC}"
else
    echo -e "     ${GREEN}✅ Model found: $MODEL_PATH${NC}"
fi

# Ensure keywords CSV exists
KEYWORDS_CSV="$BACKEND_DIR/models/scam_keywords.csv"
if [ ! -f "$KEYWORDS_CSV" ]; then
    echo -e "     Generating scam keywords CSV..."
    python3 "$BACKEND_DIR/generate_keywords.py"
fi
echo -e "     ${GREEN}✅ Keywords CSV ready${NC}"

# ─── Run tests if requested ───────────────────────────────────────────────────
if [ "$DO_TEST" = true ]; then
    echo -e "${BOLD}[4b] Running test suite...${NC}"
    python3 "$BACKEND_DIR/test_pipeline.py" --module keywords --module content --module risk
    echo -e "     ${GREEN}✅ Tests passed${NC}"
fi

# ─── Start backend ────────────────────────────────────────────────────────────
echo -e "${BOLD}[5/5] Starting PhishShield backend...${NC}"
echo ""
echo -e "  ${CYAN}Backend URL : http://localhost:$PORT${NC}"
echo -e "  ${CYAN}WebSocket   : ws://localhost:$PORT/ws/analyze${NC}"
echo -e "  ${CYAN}Health check: http://localhost:$PORT/health${NC}"
echo -e "  ${CYAN}API docs    : http://localhost:$PORT/docs${NC}"
echo ""
echo -e "  ${YELLOW}Open frontend/index.html in Chrome to start detection${NC}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${NC} to stop"
echo ""
echo "═══════════════════════════════════════════════════════"
echo ""

cd "$BACKEND_DIR"
exec python3 -m uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --reload \
    --reload-dir "$BACKEND_DIR" \
    --log-level info
