#!/bin/bash
# ================================================================
#  AI DUNGEON MASTER — Pi4 Setup Script
#  Run once on a fresh Pi4 with SSH access
#  Usage: bash setup.sh
# ================================================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC}  $1"; exit 1; }

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  AI DUNGEON MASTER — Raspberry Pi 4 Setup"
echo "  This will install: Python deps, Ollama, phi3-mini model"
echo "════════════════════════════════════════════════════════════════"
echo ""

# ── 1. System update ─────────────────────────────────────────
info "Updating system packages..."
sudo apt-get update -qq && sudo apt-get upgrade -y -qq
success "System updated."

# ── 2. Python ────────────────────────────────────────────────
info "Checking Python 3.10+..."
PYTHON=$(which python3)
PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
info "Found Python $PY_VERSION"

info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install --break-system-packages -r requirements.txt 2>/dev/null || \
        pip3 install -r requirements.txt
else
    pip3 install --break-system-packages openai python-dotenv 2>/dev/null || \
        pip3 install openai python-dotenv
fi
success "Python packages installed."

# ── 3. Ollama ────────────────────────────────────────────────
info "Installing Ollama..."
if command -v ollama &> /dev/null; then
    warn "Ollama already installed — skipping."
else
    curl -fsSL https://ollama.com/install.sh | sh
    success "Ollama installed."
fi

# Start Ollama service
info "Starting Ollama service..."
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama  2>/dev/null || true

# Wait for Ollama to be ready
info "Waiting for Ollama to be ready..."
for i in {1..15}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        success "Ollama is running."
        break
    fi
    sleep 2
    if [ $i -eq 15 ]; then
        error "Ollama did not start in time. Try: sudo systemctl start ollama"
    fi
done

# ── 4. Pull model ────────────────────────────────────────────
info "Pulling phi3-mini model (best for Pi4 — ~2.3GB download)..."
warn "This may take several minutes depending on your connection."
ollama pull phi3-mini
success "phi3-mini model ready."

# ── 5. Create project directory ──────────────────────────────
PROJECT_DIR="$HOME/dnd_game"
info "Setting up project at $PROJECT_DIR..."
mkdir -p "$PROJECT_DIR"

# Copy game files if running from same directory
PROJECT_FILES=(
    README.md
    requirements.txt
    .env.example
    server.py
    solo_play.py
    client.py
    combat.py
    art.py
    dice.py
    combat_screen.py
    dnd_engine.py
)
for f in "${PROJECT_FILES[@]}"; do
    if [ -f "$f" ]; then
        cp "$f" "$PROJECT_DIR/"
        success "Copied $f"
    else
        warn "$f not found in current directory — copy manually."
    fi
done

# ── 6. Create .env file ──────────────────────────────────────
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
        success ".env file created from .env.example at $ENV_FILE"
    else
        cat > "$ENV_FILE" << 'EOF'
OPENAI_API_KEY=ollama
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_MODEL=phi3-mini

DND_PORT=4000
MAX_PLAYERS=3
TURN_WAIT_SECONDS=60
MAX_TOKENS=400
TEMPERATURE=0.85

DM_PASSWORD=
DND_PASSWORD=
DND_SAVE_DIR=saves
EOF
        success ".env file created at $ENV_FILE"
    fi
else
    warn ".env already exists — not overwritten."
fi

# ── 7. Create tmux session helper ────────────────────────────
cat > "$PROJECT_DIR/start_server.sh" << 'EOF'
#!/bin/bash
# Start the DND server in a persistent tmux session
# Players can SSH in and run: python3 ~/dnd_game/client.py

SESSION="dnd_server"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Server already running. Attaching..."
    tmux attach -t "$SESSION"
else
    echo "Starting DND server in tmux session '$SESSION'..."
    tmux new-session -d -s "$SESSION" -c "$HOME/dnd_game" \
        "python3 server.py; bash"
    echo "Server started!"
    echo ""
    echo "Commands:"
    echo "  tmux attach -t $SESSION    — view server console"
    echo "  Ctrl+B then D              — detach (keep running)"
    echo "  tmux kill-session -t $SESSION — stop server"
fi
EOF
chmod +x "$PROJECT_DIR/start_server.sh"
success "start_server.sh created."

# ── 8. Install tmux ──────────────────────────────────────────
info "Installing tmux (keeps server running after SSH disconnect)..."
sudo apt-get install -y tmux -qq
success "tmux installed."

# ── 9. Optional: open firewall port ──────────────────────────
info "Opening port 4000 for game server..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 4000/tcp 2>/dev/null && success "Port 4000 opened." || warn "ufw rule may already exist."
else
    warn "ufw not found — if you have a firewall, manually open port 4000."
fi

# ── 10. Final instructions ────────────────────────────────────
PI_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}SETUP COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Your Pi4's IP address: $PI_IP"
echo ""
echo "  ── SOLO PLAY ─────────────────────────────────────────────"
echo "  cd ~/dnd_game && python3 solo_play.py"
echo ""
echo "  ── MULTIPLAYER SERVER ────────────────────────────────────"
echo "  Start server:    cd ~/dnd_game && bash start_server.sh"
echo "  Players connect: python3 client.py  (from their SSH session)"
echo ""
echo "  ── UPGRADING TO BIGGER HARDWARE ──────────────────────────"
echo "  Install Ollama on the other machine, then edit:"
echo "  $ENV_FILE"
echo "  Change OPENAI_API_BASE to http://<other-machine-ip>:11434/v1"
echo "  Change OPENAI_MODEL to llama3 or mistral for better responses"
echo ""
echo "  ── RECOMMENDED MODELS BY HARDWARE ───────────────────────"
echo "  Pi4 (4-8GB):        phi3-mini    (fast, lightweight)"
echo "  i7 + RTX 2080:      mistral      (great balance)"
echo "  Threadripper 32GB:  llama3:70b   (full power)"
echo ""
echo "════════════════════════════════════════════════════════════════"
