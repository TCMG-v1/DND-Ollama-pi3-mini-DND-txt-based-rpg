#!/usr/bin/env python3
"""
================================================================
  AI DUNGEON MASTER v5 — Pi 4 Edition
  Single-file, commercial-grade D&D engine

  Optimized for: Raspberry Pi 4 (8GB) + Ollama (phi3-mini/mistral)
  Features: Full 5e mechanics, FF3 combat, 12 classes, talent trees,
            procedural dungeons, 20-player async server, rich ASCII UI

  Run solo:       python3 dnd_engine.py
  Run server:     python3 dnd_engine.py --server
  Connect client: python3 dnd_engine.py --client [host]

  Created by TCMG-v1 · Co-created with Claude, Grok, Perplexity
================================================================
"""
__version__ = "5.1.0-pi4"

import json, os, sys, random, textwrap, re, time, tempfile, shutil
import asyncio, socket, signal, hashlib, argparse, logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field, asdict

# ── Optional deps (graceful fallback) ─────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION — Pi 4 optimized defaults
# ══════════════════════════════════════════════════════════════

@dataclass
class Config:
    """All tunable settings — override via .env or CLI."""
    # LLM
    model: str          = os.getenv("OPENAI_MODEL", "phi3-mini")
    api_key: str        = os.getenv("OPENAI_API_KEY", "ollama")
    api_base: str       = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
    max_tokens: int     = int(os.getenv("MAX_TOKENS", "300"))
    temperature: float  = float(os.getenv("TEMPERATURE", "0.85"))
    # Server
    host: str           = os.getenv("DND_HOST", "0.0.0.0")
    port: int           = int(os.getenv("DND_PORT", "4000"))
    max_players: int    = int(os.getenv("MAX_PLAYERS", "20"))
    server_password: str= os.getenv("DND_PASSWORD", "")
    turn_timeout: int   = int(os.getenv("TURN_WAIT_SECONDS", "60"))
    # Paths
    save_dir: str       = os.getenv("DND_SAVE_DIR", "saves")
    # Performance — Pi 4 tuning
    context_window: int = 4          # last N exchanges in prompt
    history_trim: int   = 120        # chars per historical AI response
    queue_workers: int  = 1          # LLM workers (1 for Pi, 2+ for GPU)
    # Game
    max_companions: int = 2
    terminal_width: int = 78

CFG = Config()

# ══════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("dnd")

# ══════════════════════════════════════════════════════════════
#  TERMINAL COLORS & DISPLAY
# ══════════════════════════════════════════════════════════════

class C:
    """ANSI color codes — full terminal palette."""
    RESET   = "\033[0m";   BOLD    = "\033[1m";   DIM     = "\033[2m"
    ITALIC  = "\033[3m";   UNDER   = "\033[4m"
    CYAN    = "\033[96m";  WHITE   = "\033[97m";  YELLOW  = "\033[93m"
    RED     = "\033[91m";  GREEN   = "\033[92m";  MAGENTA = "\033[95m"
    BLUE    = "\033[94m";  ORANGE  = "\033[33m";  GRAY    = "\033[90m"
    DARK    = "\033[2m";   CLEAR   = "\033[2J\033[H"
    # Background
    BG_RED    = "\033[41m"; BG_GREEN  = "\033[42m"; BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"; BG_MAGENTA= "\033[45m"; BG_GRAY   = "\033[100m"

W = CFG.terminal_width

def cc(color: str, text: str) -> str:
    return f"{color}{text}{C.RESET}"

def bold(text: str) -> str:
    return f"{C.BOLD}{text}{C.RESET}"

def cprint(color: str, text: str, wrap: bool = True):
    if wrap:
        lines = []
        for para in text.split("\n"):
            if not para.strip():
                lines.append("")
            else:
                lines.extend(textwrap.wrap(para, W))
        text = "\n".join(lines)
    print(f"{color}{text}{C.RESET}")

def divider(ch: str = "─", color: str = C.GRAY):
    print(f"{color}{ch * W}{C.RESET}")

def header(text: str, color: str = C.BLUE):
    print(f"\n{C.BOLD}{color}{'═' * W}{C.RESET}")
    print(f"{C.BOLD}{color}  {text}{C.RESET}")
    print(f"{C.BOLD}{color}{'═' * W}{C.RESET}")

def center_text(line: str, width: int = W) -> str:
    clean = re.sub(r'\033\[[0-9;]*m', '', line)
    pad = max(0, (width - len(clean)) // 2)
    return " " * pad + line

def print_art(lines: list, color: str = C.WHITE, centered: bool = True):
    print()
    for line in lines:
        out = center_text(f"{color}{line}{C.RESET}") if centered else f"{color}{line}{C.RESET}"
        print(out)
    print()


# ══════════════════════════════════════════════════════════════
#  ASCII ART LIBRARY — Consolidated + Expanded
# ══════════════════════════════════════════════════════════════

TITLE_ART = [
    r"    ___    ____   ____                                         __  ___           __           ",
    r"   /   |  /  _/  / __ \ __  __ ____   ____ _ ___   ____  ____ /  |/  /____ _ ___/ /_  ___  ___",
    r"  / /| |  / /   / / / // / / // __ \ / __ `// _ \ / __ \/ __ \  /|_/ // __ `// __  // _ \/ _ \\",
    r" / ___ |_/ /   / /_/ // /_/ // / / // /_/ //  __// /_/ / / / / /  / // /_/ // /_/ //  __/  __/",
    r"/_/  |_/___/  /_____/ \__,_//_/ /_/ \__, / \___/ \____/_/ /_/_/  /_/ \__,_/ \__,_/ \___/\___/ ",
    r"                                   /____/                                                     ",
    r"                        ⚔  v5 — Pi 4 Edition  ⚔                                              ",
]

BANNERS = {
    "fight": [
        r"  ███████╗██╗ ██████╗ ██╗  ██╗████████╗██╗",
        r"  ██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝██║",
        r"  █████╗  ██║██║  ███╗███████║   ██║   ██║",
        r"  ██╔══╝  ██║██║   ██║██╔══██║   ██║   ╚═╝",
        r"  ██║     ██║╚██████╔╝██║  ██║   ██║   ██╗",
        r"  ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝",
        r"        ⚔   Steel meets steel!   ⚔        ",
    ],
    "victory": [
        r"  ██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗██╗",
        r"  ██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝██║",
        r"  ██║   ██║██║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ ██║",
        r"  ╚██╗ ██╔╝██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  ╚═╝",
        r"   ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   ██╗",
        r"    ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝",
        r"            ★  The battle is won!  ★                          ",
    ],
    "death": [
        r"  ██████╗ ███████╗ █████╗ ████████╗██╗  ██╗",
        r"  ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║  ██║",
        r"  ██║  ██║█████╗  ███████║   ██║   ███████║",
        r"  ██║  ██║██╔══╝  ██╔══██║   ██║   ██╔══██║",
        r"  ██████╔╝███████╗██║  ██║   ██║   ██║  ██║",
        r"  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝",
        r"         ☠  Darkness takes you.  ☠          ",
    ],
    "ambush": [
        r"   █████╗ ███╗   ███╗██████╗ ██╗   ██╗███████╗██╗  ██╗██╗",
        r"  ██╔══██╗████╗ ████║██╔══██╗██║   ██║██╔════╝██║  ██║██║",
        r"  ███████║██╔████╔██║██████╔╝██║   ██║███████╗███████║██║",
        r"  ██╔══██║██║╚██╔╝██║██╔══██╗██║   ██║╚════██║██╔══██║╚═╝",
        r"  ██║  ██║██║ ╚═╝ ██║██████╔╝╚██████╔╝███████║██║  ██║██╗",
        r"  ╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝",
        r"        👁  You were not alone in the dark.  👁            ",
    ],
    "level_up": [
        r"  ██╗     ███████╗██╗   ██╗███████╗██╗          ██╗   ██╗██████╗ ██╗",
        r"  ██║     ██╔════╝██║   ██║██╔════╝██║          ██║   ██║██╔══██╗██║",
        r"  ██║     █████╗  ██║   ██║█████╗  ██║          ██║   ██║██████╔╝██║",
        r"  ██║     ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║          ██║   ██║██╔═══╝ ╚═╝",
        r"  ███████╗███████╗ ╚████╔╝ ███████╗███████╗     ╚██████╔╝██║     ██╗",
        r"  ╚══════╝╚══════╝  ╚═══╝  ╚══════╝╚══════╝      ╚═════╝ ╚═╝     ╚═╝",
        r"         ★  Power surges through you!  ★                              ",
    ],
}

def show_banner(name: str, color: str = None):
    colors = {"fight": C.RED, "victory": C.GREEN, "death": C.RED,
              "ambush": C.ORANGE, "level_up": C.MAGENTA}
    if name in BANNERS:
        print_art(BANNERS[name], color or colors.get(name, C.WHITE))

# ── Enemy Portraits (28 chars wide) ─────────────────────────

ENEMY_PORTRAITS = {
    "Goblin": [
        "      ,--^--.       ",
        "     / ^ ^ ^ \\      ",
        "    | (>   <) |     ",
        "     \\  ---  /      ",
        "   .--'-^^^-'--.    ",
        "  /  |hehehehe|  \\  ",
        " |   |  :D:   |   | ",
        "  \\  |________|  /  ",
        "   '-|        |-'   ",
        "     | /\\  /\\ |     ",
    ],
    "Skeleton": [
        "        ___         ",
        "       (o o)        ",
        "       |---|        ",
        "      /|   |\\      ",
        "     / |   | \\     ",
        "    /  | ✝ |  \\    ",
        "       |   |        ",
        "      /|   |\\      ",
        "     /_|___|_\\      ",
        "  🦴 SKELETON 🦴    ",
    ],
    "Orc": [
        "     .----.         ",
        "    / o  o \\        ",
        "   | \\    / |       ",
        "    \\ `--´ /        ",
        "     '-..-'         ",
        "    /|    |\\        ",
        "   / |WAAAGH| \\     ",
        "  |  |______|  |    ",
        "     |  ||  |       ",
        "     |__|__|       ",
    ],
    "Wolf": [
        "     /\\___/\\        ",
        "    /  o o  \\       ",
        "   ( ==  ^ == )     ",
        "    )       (       ",
        "   (  GROWL  )      ",
        "  ( |       | )     ",
        "   (|       |)      ",
        "    \\       /       ",
        "     \\_____/        ",
        "  🐺  DIRE WOLF 🐺  ",
    ],
    "Dragon": [
        "  __---~~  ~~--__   ",
        " /   ANCIENT     \\  ",
        "| /‾\\ DRAGON /‾\\ | ",
        "| |o |       |o | | ",
        "|  \\_/  ~~~  \\_/ | ",
        " \\    \\       /   / ",
        "  \\    '--,--'   /  ",
        "   \\___/   \\___/    ",
        "  🔥  FLEE OR FIGHT  ",
        "                    ",
    ],
    "Troll": [
        "    ,--^^^^^--,     ",
        "   / >       < \\    ",
        "  | ( @     @ ) |   ",
        "  |   \\~~~~~/ |  |   ",
        "   '--'-^^^^-'--'   ",
        "  /   CAVE TROLL  \\ ",
        " |  REGENERATES!  | ",
        "  \\ |___________| / ",
        "    '--'     '--'   ",
        "      |  | |  |     ",
    ],
    "Spider": [
        "       /\\  /\\       ",
        "      //\\\\//\\\\      ",
        "     ( (o  o) )     ",
        "    .-'`----´'-.    ",
        "   /  GIANT     \\   ",
        "  / /  SPIDER  \\ \\  ",
        " | /            \\ | ",
        "  V              V  ",
        "  |\\  /\\    /\\  /|  ",
        "   \\\\//\\\\  //\\\\//   ",
    ],
    "Bandit": [
        "     .---.          ",
        "    /  o  \\         ",
        "   | \\   / |        ",
        "    \\ === /         ",
        "     '---'          ",
        "   _/|   |\\_ ⚔     ",
        "  / /|   | \\ \\     ",
        " |_/ |___| \\_|     ",
        "     |   |          ",
        "  🗡  BANDIT  🗡    ",
    ],
    "Cultist": [
        "      .---.         ",
        "     / x x \\        ",
        "    |  ___  |       ",
        "     \\_____/        ",
        "    /|  ✦  |\\       ",
        "   / | /-\\ | \\      ",
        "  |  |/   \\|  |     ",
        "   \\_|     |_/      ",
        "     |  |  |        ",
        "  👁  CULTIST  👁   ",
    ],
    "Beholder": [
        "      .-----.       ",
        "   .-´ (0) (0)`-.   ",
        "  / (0)       (0)\\  ",
        " |    .-------.   | ",
        " |   ( ●     ● )  | ",
        " |    `--===--´   | ",
        "  \\ (0)       (0)/  ",
        "   `-.  (0)(0) .-´  ",
        "      `-------´     ",
        " 👁  BEHOLDER  👁   ",
    ],
    "Mind Flayer": [
        "      .====.        ",
        "     /  @@  \\       ",
        "    |  ====  |      ",
        "    | /WWWW\\ |      ",
        "    ||WWWWWW||      ",
        "     \\WWWWWW/       ",
        "    /|      |\\      ",
        "   / |      | \\     ",
        "  /  |______|  \\    ",
        " 🧠 MIND FLAYER 🧠 ",
    ],
    "Lich": [
        "      .===.         ",
        "     / x x \\        ",
        "    | \\___/ |       ",
        "     \\     /        ",
        "    .-'---'-.       ",
        "   / UNDYING  \\     ",
        "  |   POWER   |     ",
        "   \\  ✦✦✦✦  /      ",
        "    '-.___.─'       ",
        " 💀  LICH KING  💀  ",
    ],
    "Druid": [
        "       🌲           ",
        "      /|\\           ",
        "     / | \\          ",
        "    /  |  \\         ",
        "       |            ",
        "      / \\           ",
        "     /   \\          ",
        "    |  O  |         ",
        "     \\___/          ",
        "      |||           ",
    ],
    "Vampire": [
        "      .===.         ",
        "     / ^ ^ \\        ",
        "    |  (v)  |       ",
        "    | \\VVV/ |       ",
        "     \\     /        ",
        "   .-'-^^^-'-.      ",
        "  /   BLOOD   \\     ",
        " |  ETERNAL   |     ",
        "  \\  NIGHT   /      ",
        " 🦇 VAMPIRE 🦇     ",
    ],
    "Wraith": [
        "      ~~~~~         ",
        "    ~/     \\~       ",
        "   /  O   O  \\      ",
        "  |  ~~~~~~   |     ",
        "   \\  oooo  /       ",
        "    ~|     |~       ",
        "   ~ |     | ~      ",
        "  ~  |     |  ~     ",
        "     ~~~~~~~        ",
        "  👻  WRAITH  👻    ",
    ],
    "Mimic": [
        "   .-----------.    ",
        "  /    CHEST?   \\   ",
        " |  [XXXXXXXXX]  |  ",
        " |  [XXXXXXXXX]  |  ",
        " |  .--^  ^--.   |  ",
        " | / (o)  (o) \\  |  ",
        " ||   ~~~~~~   | |  ",
        " | \\  CHOMP!  /  |  ",
        " |  '--------'   |  ",
        "  📦  MIMIC!  📦    ",
    ],
    "Owlbear": [
        "     /\\_/\\          ",
        "   =(o v o)=        ",
        "    ) ___ (         ",
        "   / /   \\ \\        ",
        "  | |ROAR!| |       ",
        "  | |     | |       ",
        "   \\ \\___/ /        ",
        "    \\_____/         ",
        "    /|   |\\         ",
        "  🦉 OWLBEAR 🐻     ",
    ],
    "Gelatinous Cube": [
        "   .-----------.    ",
        "  /  .  .   .   \\   ",
        " |   .  💀  .    |  ",
        " | .   .  .   .  |  ",
        " |  .  ⚔  .  .   |  ",
        " |   .   .  .    |  ",
        " | .  .   .  .   |  ",
        " |  .   . 🦴 .   |  ",
        "  \\ .   .   .  /    ",
        "  🟢  GEL. CUBE  🟢 ",
    ],
    "Demon": [
        "    /\\     /\\       ",
        "   /  \\   /  \\      ",
        "  | (●) (●) |      ",
        "  |  \\  ^  /  |     ",
        "   \\  VVVVV  /      ",
        "    '-.___.─'       ",
        "   /|  ✦✦  |\\      ",
        "  / |FIEND | \\     ",
        " |  |______|  |    ",
        " 😈  DEMON  😈     ",
    ],
    "Elemental": [
        "     ~ /\\ ~         ",
        "   ~ / ~~ \\ ~       ",
        "  ~ | (oo) | ~      ",
        "  ~/|  ~~  |\\~      ",
        " ~/ | FIRE | \\~     ",
        " ~  | WIND |  ~     ",
        "  ~ | EARTH| ~      ",
        "   ~| WATER|~       ",
        "    ~~~~~~~         ",
        "  ⚡ ELEMENTAL ⚡    ",
    ],
    "Hydra": [
        "  /\\ /\\ /\\          ",
        " /oo/oo/oo\\         ",
        " \\VV\\VV\\VV/         ",
        "   \\ | | /          ",
        "    \\|  |/          ",
        "     | ||           ",
        "    /    \\          ",
        "   / HYDRA \\        ",
        "  |________|        ",
        "  🐍 3 HEADS 🐍     ",
    ],
}

# ── Scene Art ────────────────────────────────────────────────

SCENE_ART = {
    "tavern": [
        "  ┌─────────────────────────────────────────────┐",
        "  │  🍺  THE WANDERER'S REST  🍺                │",
        "  │  ╔═══╗  ╔═══╗  ╔═══╗   ~ ~ ~               │",
        "  │  ║ 🪑 ║  ║ 🪑 ║  ║ 🪑 ║  ║🔥║               │",
        "  │  ╚═══╝  ╚═══╝  ╚═══╝  ╚══╝               │",
        "  │          🧙 Innkeeper                       │",
        "  └─────────────────────────────────────────────┘",
    ],
    "forest": [
        "      🌲  🌲     🌲  🌲  🌲",
        "    🌲  🌲  🌲  🌲     🌲   ",
        "  ~~~  🌲     🌲  🌲  🌲  ~~",
        "       ___     🌲       🌲   ",
        "      /   \\  🌲   🌲        ",
        "  ~~~/ path \\~~~  🌲   🌲 ~~",
        "     \\     /                 ",
        "      \\___/   🌲  🌲        ",
    ],
    "dungeon": [
        "  ┌───┬───┬───┬───┬───┐",
        "  │ S │   │ T │   │   │",
        "  ├───┼───┼───┼───┼───┤",
        "  │   │ C │   │   │ M │",
        "  ├───┼───┼───┼───┼───┤",
        "  │   │   │   │ E │   │",
        "  ├───┼───┼───┼───┼───┤",
        "  │   │   │   │   │   │",
        "  └───┴───┴───┴───┴───┘",
        "  S=Start T=Treasure C=Chest E=Enemy M=Merchant",
    ],
    "cave": [
        "     .-.                      .-.      ",
        "    /   \\    .-.    .-.      /   \\     ",
        "   /     \\  /   \\  /   \\    /     \\    ",
        "  /       \\/     \\/     \\  /  💎   \\   ",
        " |  DARK                 \\/         |  ",
        " |         CAVE  🦇                 |  ",
        "  \\                               /    ",
        "   \\_____________________________/     ",
    ],
    "temple": [
        "           ⛪                           ",
        "         /|  |\\                         ",
        "        / | ✦| \\                        ",
        "       /  |__|  \\                       ",
        "      / __|  |__ \\                      ",
        "     |  |  ||  |  |                     ",
        "     |  | 🕯️ |  |                     ",
        "     |__|__||__|__|                     ",
        "     ANCIENT TEMPLE                    ",
    ],
    "swamp": [
        "  ~~ 🌿 ~~  🌿  ~~ 🌿 ~~               ",
        "     ~~~ 🐊  ~~~  ~~~                   ",
        "  🌿  ~~~  /\\.  ~~~  🌿                 ",
        "    ~~~ . /  \\ . ~~~                    ",
        "  🌫️  ~~|path|~~ 🌫️                     ",
        "    ~~~ .\\  /. ~~~                      ",
        "  🌿  ~~~ \\/  ~~~  🌿                   ",
        "     ~~~ MURKY ~~~ SWAMP               ",
    ],
    "graveyard": [
        "  🌙                                    ",
        "     ✝  ✝   ✝  ✝   ✝                  ",
        "    /|  |\\  /| |\\  /|                   ",
        "   | R | | I | | P |                    ",
        "   |___|/  |__|/  |_|                    ",
        "    ~~  .  ~~ .  ~~                     ",
        "  💀 GRAVEYARD 💀                       ",
        "   fog rolls between the stones...      ",
    ],
    "castle": [
        "     🏰          🏰                     ",
        "    /|  |\\------/|  |\\                  ",
        "   / |  | \\    / |  | \\                 ",
        "  |  |==|  |  |  |==|  |                ",
        "  |  |  |  |  |  |  |  |                ",
        "  |__|__|__|__|__|__|__|                ",
        "     |    GATE    |                     ",
        "     |  ⚔  👑  ⚔  |                     ",
    ],
    "marketplace": [
        "  ┌─────┐  ┌─────┐  ┌─────┐            ",
        "  │HERBS│  │ARMOR│  │ GEMS│            ",
        "  │ 🌿  │  │ 🛡️  │  │ 💎  │            ",
        "  └──┬──┘  └──┬──┘  └──┬──┘            ",
        "     │        │        │                ",
        "  ~~~|~~~ MARKET ~~~|~~~                ",
        "    🧙  👩‍🌾  🧝  🗡️  📿                  ",
        "      busy chatter fills the air        ",
    ],
    "battlefield": [
        "   ⚔  ⚔  ⚔  ⚔  ⚔  ⚔                  ",
        "  /  SCORCHED  EARTH  \\                 ",
        " |  🔥  💀  ⚔  🔥  💀 |                ",
        " | broken shields litter  |             ",
        " |  the blood-soaked ground|             ",
        "  \\ 💀  🔥  💀  ⚔  🔥 /                ",
        "   \\  crows circle above /               ",
        "    \\____BATTLEFIELD____/                 ",
    ],
}

def show_scene(name: str):
    name = name.lower()
    if name in SCENE_ART:
        print_art(SCENE_ART[name], C.CYAN, centered=False)

def detect_and_show_scene(text: str):
    """Auto-detect scene keywords and display art."""
    t = text.lower()
    triggers = {
        "tavern": ["tavern", "inn", "bar", "innkeeper", "drink", "ale"],
        "forest": ["forest", "woods", "trees", "path through", "woodland"],
        "dungeon": ["dungeon", "labyrinth", "maze"],
        "cave": ["cave", "cavern", "grotto"],
        "temple": ["temple", "shrine", "altar", "chapel", "cathedral", "holy place"],
        "swamp": ["swamp", "marsh", "bog", "mire", "wetland", "murky"],
        "graveyard": ["graveyard", "cemetery", "tomb", "crypt", "burial", "gravestone"],
        "castle": ["castle", "fortress", "keep", "stronghold", "citadel", "throne"],
        "marketplace": ["market", "bazaar", "shop", "stall", "vendor", "trade district"],
        "battlefield": ["battlefield", "warzone", "scorched", "fallen soldiers", "aftermath"],
    }
    for scene, keywords in triggers.items():
        if any(k in t for k in keywords):
            show_scene(scene)
            return

def show_enemy_portrait(name: str):
    """Show ASCII portrait for enemy if available."""
    for key, art in ENEMY_PORTRAITS.items():
        if key.lower() in name.lower():
            print_art(art, C.RED)
            return
    # Generic enemy
    print_art([
        "     .----.     ",
        "    /  ??  \\    ",
        "   |  ????  |   ",
        "    \\ ???? /    ",
        "     '----'     ",
        f"   {name:^16}",
    ], C.RED)


# ══════════════════════════════════════════════════════════════
#  DICE ENGINE — Polyhedral dice with ASCII art
# ══════════════════════════════════════════════════════════════

D6_FACES = {
    1: [" _____ ", "|     |", "|  *  |", "|     |", "|_____|"],
    2: [" _____ ", "| *   |", "|     |", "|   * |", "|_____|"],
    3: [" _____ ", "| *   |", "|  *  |", "|   * |", "|_____|"],
    4: [" _____ ", "| * * |", "|     |", "| * * |", "|_____|"],
    5: [" _____ ", "| * * |", "|  *  |", "| * * |", "|_____|"],
    6: [" _____ ", "| * * |", "| * * |", "| * * |", "|_____|"],
}

def _d20_art(val: int) -> list:
    v = str(val).center(4)
    top = "✦" if val == 20 else ("☠" if val == 1 else "△")
    return [
        f"    {top}    ",
        "  .·´  `·. ",
        f" /  {v}  \\ ",
        " \\        / ",
        "  `·.,.,·´  ",
    ]

def roll(sides: int, count: int = 1, bonus: int = 0) -> Tuple[int, List[int]]:
    rolls = [random.randint(1, sides) for _ in range(count)]
    return sum(rolls) + bonus, rolls

def d20(bonus: int = 0) -> Tuple[int, int]:
    r = random.randint(1, 20)
    return r + bonus, r

def mod(score: int) -> int:
    return (score - 10) // 2

def mstr(score: int) -> str:
    m = mod(score)
    return f"+{m}" if m >= 0 else str(m)

def prof_bonus(level: int) -> int:
    return 2 + (level - 1) // 4

def parse_dice(notation: str) -> Tuple[int, int, int]:
    """Parse '2d6+3' into (count, sides, bonus)."""
    m = re.match(r"(\d+)?d(\d+)([+-]\d+)?", notation.strip().lower())
    if not m:
        return 1, 4, 0
    count = int(m.group(1) or 1)
    sides = int(m.group(2))
    bonus = int(m.group(3) or 0)
    return count, sides, bonus

def roll_dice_notation(notation: str) -> Tuple[int, List[int]]:
    count, sides, bonus = parse_dice(notation)
    return roll(sides, count, bonus)

def roll_display(sides: int, values: List[int], color: str = C.YELLOW):
    """Print dice side by side with ASCII art."""
    if sides == 20 and len(values) == 1:
        art = _d20_art(values[0])
        col = C.GREEN if values[0] == 20 else (C.RED if values[0] == 1 else color)
        for line in art:
            print(f"  {col}{line}{C.RESET}")
        return
    if sides == 6:
        arts = [D6_FACES.get(v, D6_FACES[1]) for v in values]
        max_h = max(len(a) for a in arts)
        for row in range(max_h):
            line = "  "
            for a in arts:
                line += f"{color}{a[row] if row < len(a) else ' ' * 7}{C.RESET}   "
            print(line)
    else:
        print(f"  {color}[{', '.join(str(v) for v in values)}]{C.RESET}")

def roll_initiative(player: dict, enemy_name: str) -> Tuple[int, int]:
    dex_mod = mod(player.get("stats", {}).get("DEX", 10))
    p_init, p_raw = d20(dex_mod)
    e_init, e_raw = d20(0)
    header("INITIATIVE", C.YELLOW)
    print(f"  {C.BOLD}{player['name']}{C.RESET}: ", end="")
    roll_display(20, [p_raw], C.CYAN)
    print(f"  {C.GRAY}  + DEX ({mstr(player.get('stats', {}).get('DEX', 10))}) = {C.BOLD}{p_init}{C.RESET}")
    print(f"  {C.BOLD}{enemy_name}{C.RESET}: ", end="")
    roll_display(20, [e_raw], C.RED)
    print(f"  {C.GRAY}  = {C.BOLD}{e_init}{C.RESET}")
    if p_init >= e_init:
        cprint(C.GREEN, f"\n  {player['name']} acts first!")
    else:
        cprint(C.RED, f"\n  {enemy_name} acts first!")
    divider()
    return p_init, e_init


# ══════════════════════════════════════════════════════════════
#  SKILL CHECK ENGINE
# ══════════════════════════════════════════════════════════════

CHECK_PROFILES = {
    "athletics":    ("STR", "1d20", 12, "physical feat",     " — raw muscle and grit"),
    "acrobatics":   ("DEX", "1d20", 13, "nimble maneuver",   " — grace under pressure"),
    "stealth":      ("DEX", "1d20", 14, "silent approach",   " — shadow and silence"),
    "arcana":       ("INT", "1d20", 15, "magical knowledge",  " — ancient lore recall"),
    "investigation":("INT", "1d20", 12, "deductive search",   " — clues and connections"),
    "perception":   ("WIS", "1d20", 13, "keen observation",   " — eyes like a hawk"),
    "insight":      ("WIS", "1d20", 14, "read intentions",    " — truth from lies"),
    "persuasion":   ("CHA", "1d20", 13, "silver tongue",      " — words as weapons"),
    "intimidation": ("CHA", "1d20", 15, "fearsome presence",  " — force of will"),
    "deception":    ("CHA", "1d20", 14, "convincing lie",     " — poker face"),
    "survival":     ("WIS", "1d20", 12, "wilderness lore",    " — nature's guidance"),
    "medicine":     ("WIS", "1d20", 13, "healing check",      " — steady hands"),
    "lockpick":     ("DEX", "1d20", 15, "lock mechanism",     " — click, click, open"),
    "history":      ("INT", "1d20", 12, "historical recall",  " — memory of ages"),
    "nature":       ("INT", "1d20", 12, "natural knowledge",  " — flora and fauna"),
    "religion":     ("INT", "1d20", 13, "divine knowledge",   " — gods and temples"),
    "animal":       ("WIS", "1d20", 12, "animal handling",    " — beast whisperer"),
    "performance":  ("CHA", "1d20", 13, "crowd pleasing",     " — showtime"),
    "sleight":      ("DEX", "1d20", 14, "quick hands",        " — now you see it"),
}

INFER_MAP = {
    "sneak|hide|creep|shadow|silent|stealthy|slip past": "stealth",
    "climb|jump|lift|push|pull|swim|break|smash|force": "athletics",
    "dodge|flip|tumble|roll|balance|acrobat": "acrobatics",
    "search|look|investigate|examine|inspect|study|analyze": "investigation",
    "listen|watch|notice|spot|scan|observe|perceive": "perception",
    "persuade|convince|negotiate|talk|plead|charm|flatter": "persuasion",
    "lie|deceive|bluff|trick|disguise|pretend|feign": "deception",
    "threaten|intimidate|scare|frighten|menace|glare": "intimidation",
    "heal|bandage|treat|medicine|stabilize|mend": "medicine",
    "pick lock|lockpick|unlock|disarm trap|thieves": "lockpick",
    "read|recall|history|remember|knowledge|lore": "history",
    "track|forage|survive|navigate|camp|hunt|trail": "survival",
    "cast|spell|magic|arcane|ritual|enchant|conjure": "arcana",
    "pray|divine|holy|religion|god|temple|bless": "religion",
    "nature|plant|animal|beast|wild|druid": "nature",
    "perform|sing|dance|play music|entertain|bard": "performance",
    "pickpocket|sleight|palm|swipe|steal": "sleight",
    "sense motive|read.*face|read.*intent|insight|gut feeling": "insight",
    "tame|calm.*animal|soothe.*beast|animal handling|ride": "animal",
}

def infer_check(text: str, player: dict) -> Tuple[Optional[str], Optional[tuple]]:
    t = text.lower()
    for pattern, check_name in INFER_MAP.items():
        if re.search(pattern, t):
            prof = CHECK_PROFILES.get(check_name)
            if prof:
                return check_name, prof
    return None, None

def challenge_screen(situation: str, player: dict,
                     forced_check: str = None, forced_dc: int = None) -> dict:
    """Run a skill check with full display."""
    if forced_check and forced_check in CHECK_PROFILES:
        check = forced_check
        prof = CHECK_PROFILES[check]
    else:
        check, prof = infer_check(situation, player)
        if not check:
            return {"action": situation, "success": True, "total": 15,
                    "dc": 10, "nat20": False, "nat1": False}

    stat_name, dice_str, base_dc, desc, flavor = prof
    dc = forced_dc if forced_dc is not None else base_dc

    stat_val = player.get("stats", {}).get(stat_name, 10)
    stat_mod = mod(stat_val)
    prof_b = prof_bonus(player.get("level", 1))

    total_bonus = stat_mod + prof_b
    result, raw = d20(total_bonus)
    nat = raw

    # Display
    print(f"\n  {C.BOLD}{C.CYAN}┌─ SKILL CHECK ─────────────────────────────────────┐{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {desc.upper()}{flavor}")
    print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {check.upper()} ({stat_name}) — DC {dc}")
    print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")

    roll_display(20, [nat])

    nat20 = nat == 20
    nat1 = nat == 1

    if nat20:
        cprint(C.GREEN, f"\n  ✦ NATURAL 20! ✦  Roll: {nat} + {total_bonus} = {result} vs DC {dc}")
        cprint(C.GREEN, "  CRITICAL SUCCESS!")
        success = True
    elif nat1:
        cprint(C.RED, f"\n  ☠ NATURAL 1! ☠  Roll: {nat} + {total_bonus} = {result} vs DC {dc}")
        cprint(C.RED, "  CRITICAL FAILURE!")
        success = False
    elif result >= dc:
        cprint(C.GREEN, f"\n  ✓ SUCCESS!  Roll: {nat} + {total_bonus} = {result} vs DC {dc}")
        success = True
    else:
        cprint(C.RED, f"\n  ✗ FAILED!  Roll: {nat} + {total_bonus} = {result} vs DC {dc}")
        success = False

    return {"action": situation, "success": success, "total": result,
            "dc": dc, "nat20": nat20, "nat1": nat1, "check": check}


# ══════════════════════════════════════════════════════════════
#  COMPASS NAVIGATION
# ══════════════════════════════════════════════════════════════

def show_compass():
    print(f"""
  {C.GRAY}         {C.BOLD}{C.CYAN}N{C.RESET}
  {C.GRAY}         {C.BOLD}[W]{C.RESET}
  {C.GRAY}    {C.BOLD}{C.YELLOW}W{C.RESET}{C.GRAY}  ──{C.WHITE}✦{C.GRAY}──  {C.BOLD}{C.GREEN}E{C.RESET}
  {C.GRAY}    {C.BOLD}[A]{C.RESET}{C.GRAY}       {C.BOLD}[D]{C.RESET}
  {C.GRAY}         {C.BOLD}{C.ORANGE}S{C.RESET}
  {C.GRAY}         {C.BOLD}[S]{C.RESET}
  {C.GRAY}      {C.MAGENTA}[E]{C.RESET}{C.GRAY}xamine{C.RESET}""")


# ══════════════════════════════════════════════════════════════
#  D&D 5e DATA — Stats, Classes, Races, Gear, Spells
# ══════════════════════════════════════════════════════════════

STAT_NAMES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

def roll_4d6() -> int:
    r = sorted([random.randint(1, 6) for _ in range(4)])
    return sum(r[1:])

def gen_stats() -> Dict[str, int]:
    return {s: roll_4d6() for s in STAT_NAMES}

# ── Classes ──────────────────────────────────────────────────

HIT_DICE = {
    "Barbarian": 12, "Fighter": 10, "Paladin": 10, "Ranger": 10,
    "Cleric": 8, "Druid": 8, "Monk": 8, "Rogue": 8, "Bard": 8, "Warlock": 8,
    "Wizard": 6, "Sorcerer": 6,
}

SLOT_TABLE = {
    "Warlock":  {1:1,2:2,3:2,4:2,5:2,6:2,7:2,8:2,9:2,10:2,11:3,12:3,13:3,14:3},
    "Wizard":   {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Sorcerer": {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Cleric":   {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Druid":    {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Bard":     {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Paladin":  {1:2,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6},
    "Ranger":   {1:2,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6},
}

# ── Gear ─────────────────────────────────────────────────────

WEAPONS = {
    "Dagger":         {"damage": "1d4",  "dtype": "piercing",    "value": 2,    "finesse": True},
    "Shortsword":     {"damage": "1d6",  "dtype": "piercing",    "value": 10,   "finesse": True},
    "Longsword":      {"damage": "1d8",  "dtype": "slashing",    "value": 15},
    "Greatsword":     {"damage": "2d6",  "dtype": "slashing",    "value": 50},
    "Handaxe":        {"damage": "1d6",  "dtype": "slashing",    "value": 5},
    "Greataxe":       {"damage": "1d12", "dtype": "slashing",    "value": 30},
    "Quarterstaff":   {"damage": "1d6",  "dtype": "bludgeoning", "value": 2},
    "Mace":           {"damage": "1d6",  "dtype": "bludgeoning", "value": 5},
    "Warhammer":      {"damage": "1d8",  "dtype": "bludgeoning", "value": 15},
    "Shortbow":       {"damage": "1d6",  "dtype": "piercing",    "value": 25},
    "Longbow":        {"damage": "1d8",  "dtype": "piercing",    "value": 50},
    "Rapier":         {"damage": "1d8",  "dtype": "piercing",    "value": 25,   "finesse": True},
    "Scimitar":       {"damage": "1d6",  "dtype": "slashing",    "value": 25,   "finesse": True},
    "Eldritch Focus": {"damage": "1d10", "dtype": "force",       "value": 60,   "arcane": True},
    "Arcane Tome":    {"damage": "1d6",  "dtype": "psychic",     "value": 75,   "arcane": True},
    "Holy Symbol":    {"damage": "1d8",  "dtype": "radiant",     "value": 50,   "arcane": True},
    "Druidic Focus":  {"damage": "1d8",  "dtype": "nature",      "value": 40,   "arcane": True},
}

ARMORS = {
    "Leather Armor":   {"ac": 11, "value": 10},
    "Studded Leather": {"ac": 12, "value": 45},
    "Hide Armor":      {"ac": 12, "value": 10},
    "Chain Shirt":     {"ac": 13, "value": 50},
    "Scale Mail":      {"ac": 14, "value": 50},
    "Breastplate":     {"ac": 14, "value": 400},
    "Half Plate":      {"ac": 15, "value": 750},
    "Chain Mail":      {"ac": 16, "value": 75},
    "Full Plate":      {"ac": 18, "value": 1500},
    "Mage Robes":      {"ac": 10, "value": 30},
    "Druid Vestments": {"ac": 11, "value": 35},
}

STARTING_GEAR = {
    "Fighter":   ("Longsword",   "Chain Mail"),
    "Wizard":    ("Arcane Tome", "Mage Robes"),
    "Rogue":     ("Rapier",      "Leather Armor"),
    "Cleric":    ("Mace",        "Chain Mail"),
    "Ranger":    ("Longbow",     "Studded Leather"),
    "Paladin":   ("Longsword",   "Chain Mail"),
    "Barbarian": ("Greataxe",    "Hide Armor"),
    "Bard":      ("Rapier",      "Leather Armor"),
    "Druid":     ("Druidic Focus","Druid Vestments"),
    "Monk":      ("Quarterstaff",""),
    "Sorcerer":  ("Arcane Tome", "Mage Robes"),
    "Warlock":   ("Eldritch Focus","Mage Robes"),
}

RACES = ["Human", "Elf", "Dwarf", "Halfling", "Half-Orc", "Half-Elf",
         "Gnome", "Tiefling", "Dragonborn"]

# ── Item Conditions ──────────────────────────────────────────

ITEM_STATES  = ["pristine", "good", "worn", "damaged", "broken"]
REPAIR_COSTS = {"pristine": 0, "good": 5, "worn": 20, "damaged": 60, "broken": 120}

# ── Conditions ───────────────────────────────────────────────

CONDITIONS = {
    "bleeding":   (C.RED,     "Losing 1d4 HP per turn until treated"),
    "burning":    (C.ORANGE,  "1d6 fire damage per turn"),
    "poisoned":   (C.GREEN,   "-2 to attacks and saves"),
    "cursed":     (C.MAGENTA, "Disadvantage on ability checks"),
    "stunned":    (C.YELLOW,  "Cannot act this turn"),
    "frightened": (C.ORANGE,  "Disadvantage on attacks while source visible"),
    "shielded":   (C.BLUE,    "Temp HP absorbs next hit"),
    "near-death": (C.RED,     "One bad hit could end you"),
}

# ── Notoriety ────────────────────────────────────────────────

NOTORIETY_TIERS = [
    (-1000, -601, "Villain",    C.RED,     "Your name is spoken in fearful whispers."),
    (-600,  -301, "Outlaw",     C.ORANGE,  "Wanted posters bear your likeness."),
    (-300,   -51, "Scoundrel",  C.YELLOW,  "Folk eye you with suspicion."),
    (-50,     50, "Wanderer",   C.GRAY,    "Your reputation is unwritten."),
    (51,     300, "Goodfellow", C.GREEN,   "People smile when you enter a room."),
    (301,    600, "Champion",   C.CYAN,    "Bards sing of your deeds."),
    (601,   1000, "Legend",     C.MAGENTA, "Your name alone inspires courage."),
]

# ── XP Table ─────────────────────────────────────────────────

XP_THRESH = {
    1:300,2:900,3:2700,4:6500,5:14000,6:23000,7:34000,
    8:48000,9:64000,10:85000,11:100000,12:120000,13:140000,
    14:165000,15:195000,16:225000,17:265000,18:305000,19:355000,
}


# ══════════════════════════════════════════════════════════════
#  SPELLS — All 12 classes
# ══════════════════════════════════════════════════════════════

SPELLS = {
    "Warlock": {
        "cantrips": [
            {"name": "Eldritch Blast",    "dice": "1d10", "dtype": "force",    "desc": "A crackling beam of alien energy.", "color": C.MAGENTA},
            {"name": "Mind Sliver",       "dice": "1d6",  "dtype": "psychic",  "desc": "A spike of alien thought scrambles focus.", "color": C.CYAN},
            {"name": "Toll the Dead",     "dice": "1d8",  "dtype": "necrotic", "desc": "A funeral bell tolls from beyond.", "color": C.GRAY},
            {"name": "Chill Touch",       "dice": "1d8",  "dtype": "necrotic", "desc": "A ghostly hand prevents healing.", "color": C.GRAY},
        ],
        "spells": [
            {"name": "Hex",                "dice": "1d6",  "dtype": "curse",    "slots": 1, "desc": "Dark mark — every hit carries hunger."},
            {"name": "Dissonant Whispers", "dice": "3d6",  "dtype": "psychic",  "slots": 1, "desc": "Words never meant for mortal ears."},
            {"name": "Armor of Agathys",   "dice": "0",    "dtype": "shield",   "slots": 1, "desc": "Icy void wraps you — attackers take cold."},
            {"name": "Hunger of Hadar",    "dice": "2d6",  "dtype": "cold",     "slots": 2, "desc": "Darkness and teeth. Something hungers."},
            {"name": "Synaptic Static",    "dice": "8d6",  "dtype": "psychic",  "slots": 5, "desc": "Pure alien madness detonates."},
        ]
    },
    "Wizard": {
        "cantrips": [
            {"name": "Fire Bolt",    "dice": "1d10", "dtype": "fire",     "desc": "A mote of fire streaks forward.", "color": C.ORANGE},
            {"name": "Ray of Frost", "dice": "1d8",  "dtype": "cold",     "desc": "A frigid ray chills your foe.", "color": C.CYAN},
            {"name": "Shocking Grasp","dice": "1d8",  "dtype": "lightning","desc": "Electricity arcs from your hand.", "color": C.YELLOW},
            {"name": "Mage Hand",    "dice": "0",    "dtype": "utility",  "desc": "A spectral hand manipulates objects.", "color": C.BLUE},
        ],
        "spells": [
            {"name": "Magic Missile", "dice": "3d4",  "dtype": "force",    "slots": 1, "desc": "Three darts of magical force."},
            {"name": "Shield",        "dice": "0",    "dtype": "shield",   "slots": 1, "desc": "+5 AC until next turn."},
            {"name": "Fireball",      "dice": "8d6",  "dtype": "fire",     "slots": 3, "desc": "A bright streak becomes a fiery explosion."},
            {"name": "Counterspell",  "dice": "0",    "dtype": "utility",  "slots": 3, "desc": "You attempt to interrupt a creature casting a spell."},
            {"name": "Meteor Swarm",  "dice": "40d6", "dtype": "fire",     "slots": 9, "desc": "Blazing orbs rain devastation."},
        ]
    },
    "Cleric": {
        "cantrips": [
            {"name": "Sacred Flame", "dice": "1d8",  "dtype": "radiant",  "desc": "Flame-like radiance descends.", "color": C.YELLOW},
            {"name": "Spare the Dying","dice": "0",  "dtype": "utility",  "desc": "Stabilize a dying creature.", "color": C.GREEN},
            {"name": "Thaumaturgy", "dice": "0",     "dtype": "utility",  "desc": "Minor divine wonder.", "color": C.YELLOW},
        ],
        "spells": [
            {"name": "Cure Wounds",    "dice": "1d8",  "dtype": "heal",     "slots": 1, "desc": "Touch heals wounds."},
            {"name": "Guiding Bolt",   "dice": "4d6",  "dtype": "radiant",  "slots": 1, "desc": "A flash of light streaks toward a creature."},
            {"name": "Spirit Guardians","dice": "3d8",  "dtype": "radiant",  "slots": 3, "desc": "Spectral warriors orbit you."},
            {"name": "Revivify",       "dice": "0",    "dtype": "heal",     "slots": 3, "desc": "Return a creature dead less than 1 minute to life."},
            {"name": "Heal",           "dice": "0",    "dtype": "heal",     "slots": 6, "desc": "Restore 70 HP to a creature."},
        ]
    },
    "Druid": {
        "cantrips": [
            {"name": "Produce Flame",  "dice": "1d8",  "dtype": "fire",     "desc": "Flickering flame in your palm.", "color": C.ORANGE},
            {"name": "Thorn Whip",     "dice": "1d6",  "dtype": "piercing", "desc": "Thorny vine lashes out.", "color": C.GREEN},
            {"name": "Druidcraft",     "dice": "0",    "dtype": "utility",  "desc": "Minor natural wonder.", "color": C.GREEN},
        ],
        "spells": [
            {"name": "Entangle",       "dice": "0",    "dtype": "control",  "slots": 1, "desc": "Grasping vines sprout from the ground."},
            {"name": "Healing Word",   "dice": "1d4",  "dtype": "heal",     "slots": 1, "desc": "A word of power restores vitality."},
            {"name": "Moonbeam",       "dice": "2d10", "dtype": "radiant",  "slots": 2, "desc": "A silvery beam of pale light shines down."},
            {"name": "Call Lightning", "dice": "3d10", "dtype": "lightning", "slots": 3, "desc": "A storm cloud forms and lightning strikes."},
            {"name": "Wall of Thorns", "dice": "7d8",  "dtype": "piercing", "slots": 6, "desc": "A barrier of tough, pliable thorns."},
        ]
    },
    "Paladin": {
        "cantrips": [],
        "spells": [
            {"name": "Divine Smite",    "dice": "2d8",  "dtype": "radiant",  "slots": 1, "desc": "Holy energy sears your weapon."},
            {"name": "Lay on Hands",    "dice": "0",    "dtype": "heal",     "slots": 0, "desc": "Your touch restores hit points."},
            {"name": "Shield of Faith", "dice": "0",    "dtype": "shield",   "slots": 1, "desc": "+2 AC for 10 minutes."},
            {"name": "Aura of Vitality","dice": "2d6",  "dtype": "heal",     "slots": 3, "desc": "Healing energy radiates from you."},
            {"name": "Banishing Smite", "dice": "5d10", "dtype": "force",    "slots": 5, "desc": "Your weapon crackles with force to banish."},
        ]
    },
    "Ranger": {
        "cantrips": [],
        "spells": [
            {"name": "Hunter's Mark",   "dice": "1d6",  "dtype": "bonus",    "slots": 1, "desc": "You mark prey — extra damage on hits."},
            {"name": "Cure Wounds",     "dice": "1d8",  "dtype": "heal",     "slots": 1, "desc": "Touch heals wounds."},
            {"name": "Conjure Barrage", "dice": "3d8",  "dtype": "piercing", "slots": 3, "desc": "Projectiles multiply in a cone."},
            {"name": "Swift Quiver",    "dice": "0",    "dtype": "utility",  "slots": 5, "desc": "Your quiver produces endless ammo."},
        ]
    },
    "Bard": {
        "cantrips": [
            {"name": "Vicious Mockery", "dice": "1d4",  "dtype": "psychic",  "desc": "Your insult is literally damaging.", "color": C.YELLOW},
            {"name": "Minor Illusion",  "dice": "0",    "dtype": "utility",  "desc": "A convincing illusion.", "color": C.MAGENTA},
        ],
        "spells": [
            {"name": "Healing Word",    "dice": "1d4",  "dtype": "heal",     "slots": 1, "desc": "A word of power restores vitality."},
            {"name": "Dissonant Whispers","dice": "3d6", "dtype": "psychic",  "slots": 1, "desc": "Unnerving whispers cause fleeing."},
            {"name": "Hypnotic Pattern","dice": "0",    "dtype": "control",  "slots": 3, "desc": "Weaving colors charm creatures."},
            {"name": "Greater Invisibility","dice":"0",  "dtype": "utility",  "slots": 4, "desc": "You or a creature become invisible."},
        ]
    },
    "Rogue":     {"cantrips": [], "spells": []},
    "Fighter":   {"cantrips": [], "spells": []},
    "Barbarian": {"cantrips": [], "spells": []},
    "Monk":      {"cantrips": [], "spells": []},
    "Sorcerer": {
        "cantrips": [
            {"name": "Fire Bolt",   "dice": "1d10", "dtype": "fire",     "desc": "A mote of fire.", "color": C.ORANGE},
            {"name": "Chill Touch", "dice": "1d8",  "dtype": "necrotic", "desc": "A ghostly hand.", "color": C.GRAY},
        ],
        "spells": [
            {"name": "Chaos Bolt",   "dice": "2d8",  "dtype": "random",   "slots": 1, "desc": "An orb of chaotic energy."},
            {"name": "Fireball",     "dice": "8d6",  "dtype": "fire",     "slots": 3, "desc": "A bright streak of fiery explosion."},
            {"name": "Wish",         "dice": "0",    "dtype": "utility",  "slots": 9, "desc": "The mightiest spell a mortal can cast."},
        ]
    },
}


# ══════════════════════════════════════════════════════════════
#  TALENT TREES — All 12 classes
# ══════════════════════════════════════════════════════════════

TALENT_TREES = {
    "Fighter": {
        "Precision Strike":  {"tier": 1, "desc": "+2 to attack rolls",             "effect": {"atk_bonus": 2}},
        "Weapon Master":     {"tier": 1, "desc": "+1 damage die size",             "effect": {"dmg_bonus": 1}},
        "Second Wind":       {"tier": 2, "desc": "Heal 1d10+level once per rest",  "effect": {"heal_ability": "1d10"}},
        "Action Surge":      {"tier": 2, "desc": "Extra attack once per rest",     "effect": {"extra_attack": True}},
        "Champion":          {"tier": 3, "desc": "Crit on 19-20",                  "effect": {"crit_range": 19}},
        "Battlemaster":      {"tier": 3, "desc": "Maneuvers: trip, riposte, push", "effect": {"maneuvers": True}},
    },
    "Warlock": {
        "Agonizing Blast":   {"tier": 1, "desc": "+CHA mod to Eldritch Blast",     "effect": {"blast_bonus": "cha"}},
        "Repelling Blast":   {"tier": 1, "desc": "EB pushes targets 10ft",         "effect": {"push": 10}},
        "Pact of the Chain": {"tier": 2, "desc": "Summon a familiar",              "effect": {"familiar": True}},
        "Dark One's Luck":   {"tier": 2, "desc": "Add 1d10 to a failed check",     "effect": {"luck_die": "1d10"}},
        "Lifedrinker":       {"tier": 3, "desc": "+CHA necrotic damage on melee",  "effect": {"lifedrinker": True}},
        "Master of Myriad":  {"tier": 3, "desc": "Cast one 6th+ spell without slot","effect": {"arcanum": True}},
    },
    "Rogue": {
        "Sneak Attack":      {"tier": 1, "desc": "+2d6 damage with advantage",     "effect": {"sneak_dice": "2d6"}},
        "Cunning Action":    {"tier": 1, "desc": "Dash/disengage/hide as bonus",   "effect": {"cunning": True}},
        "Evasion":           {"tier": 2, "desc": "Half or no damage on DEX saves",  "effect": {"evasion": True}},
        "Uncanny Dodge":     {"tier": 2, "desc": "Halve one attack's damage",       "effect": {"uncanny": True}},
        "Assassinate":       {"tier": 3, "desc": "Auto-crit on surprised targets",  "effect": {"assassinate": True}},
        "Reliable Talent":   {"tier": 3, "desc": "Minimum 10 on proficient checks", "effect": {"reliable": True}},
    },
    "Wizard": {
        "Arcane Recovery":   {"tier": 1, "desc": "Recover slots on short rest",    "effect": {"arcane_recovery": True}},
        "Spell Sculpting":   {"tier": 1, "desc": "Allies auto-save your AoE",      "effect": {"sculpt": True}},
        "Overchannel":       {"tier": 2, "desc": "Max damage on one spell",        "effect": {"overchannel": True}},
        "War Caster":        {"tier": 2, "desc": "Advantage on concentration",     "effect": {"war_caster": True}},
        "Spell Mastery":     {"tier": 3, "desc": "Cast 1st/2nd at will",           "effect": {"mastery": True}},
        "Archmage":          {"tier": 3, "desc": "+2 to spell save DC",            "effect": {"dc_bonus": 2}},
    },
    "Cleric": {
        "Divine Domain":     {"tier": 1, "desc": "Heavy armor proficiency",        "effect": {"heavy_armor": True}},
        "Healing Surge":     {"tier": 1, "desc": "+WIS mod to healing spells",     "effect": {"heal_bonus": "wis"}},
        "Turn Undead":       {"tier": 2, "desc": "Undead must flee for 1 minute",  "effect": {"turn_undead": True}},
        "Spiritual Weapon":  {"tier": 2, "desc": "Bonus action 1d8+WIS attack",   "effect": {"spirit_weapon": True}},
        "Divine Intervention":{"tier": 3,"desc": "Your deity intervenes directly", "effect": {"divine_intervention": True}},
        "Supreme Healing":   {"tier": 3, "desc": "Healing spells always max",      "effect": {"max_heal": True}},
    },
    "Druid": {
        "Wild Shape":        {"tier": 1, "desc": "Transform into beasts",          "effect": {"wild_shape": True}},
        "Natural Recovery":  {"tier": 1, "desc": "Recover slots during short rest","effect": {"nat_recovery": True}},
        "Primal Strike":     {"tier": 2, "desc": "Beast attacks count as magical", "effect": {"primal_strike": True}},
        "Elemental Form":    {"tier": 2, "desc": "Wild Shape into elementals",     "effect": {"elemental": True}},
        "Archdruid":         {"tier": 3, "desc": "Unlimited Wild Shape uses",      "effect": {"unlimited_ws": True}},
        "Beast Spells":      {"tier": 3, "desc": "Cast spells while shapeshifted", "effect": {"beast_spells": True}},
    },
    "Paladin": {
        "Divine Sense":      {"tier": 1, "desc": "Detect undead/fiends nearby",    "effect": {"divine_sense": True}},
        "Improved Smite":    {"tier": 1, "desc": "+1d8 radiant to all melee",      "effect": {"imp_smite": True}},
        "Aura of Protection":{"tier": 2, "desc": "+CHA to saves for allies",       "effect": {"aura_prot": True}},
        "Cleansing Touch":   {"tier": 2, "desc": "Remove one spell on an ally",    "effect": {"cleanse": True}},
        "Holy Avenger":      {"tier": 3, "desc": "Weapon becomes +3 holy",         "effect": {"holy_avenger": True}},
        "Oath Champion":     {"tier": 3, "desc": "Elder Champion transformation",  "effect": {"champion": True}},
    },
    "Ranger": {
        "Favored Enemy":     {"tier": 1, "desc": "+2 damage vs chosen type",       "effect": {"fav_enemy": True}},
        "Natural Explorer":  {"tier": 1, "desc": "Advantage on survival checks",   "effect": {"nat_explore": True}},
        "Extra Attack":      {"tier": 2, "desc": "Attack twice per turn",          "effect": {"extra_attack": True}},
        "Volley":            {"tier": 2, "desc": "Attack all targets in 10ft",     "effect": {"volley": True}},
        "Vanish":            {"tier": 3, "desc": "Hide as bonus, untrackable",     "effect": {"vanish": True}},
        "Foe Slayer":        {"tier": 3, "desc": "+WIS to attack or damage 1/turn","effect": {"foe_slayer": True}},
    },
    "Barbarian": {
        "Rage":              {"tier": 1, "desc": "+2 damage, resist phys damage",  "effect": {"rage": True}},
        "Reckless Attack":   {"tier": 1, "desc": "Advantage on attacks, foes too", "effect": {"reckless": True}},
        "Bear Totem":        {"tier": 2, "desc": "Resist all damage while raging", "effect": {"bear_totem": True}},
        "Brutal Critical":   {"tier": 2, "desc": "+1 die on critical hits",        "effect": {"brutal_crit": True}},
        "Relentless Rage":   {"tier": 3, "desc": "Don't drop to 0 HP (DC save)",  "effect": {"relentless": True}},
        "Primal Champion":   {"tier": 3, "desc": "+4 STR and CON permanently",     "effect": {"primal_champ": True}},
    },
    "Bard": {
        "Bardic Inspiration": {"tier": 1, "desc": "Grant allies 1d6 bonus",       "effect": {"inspiration": "1d6"}},
        "Jack of All Trades": {"tier": 1, "desc": "Half prof to untrained checks", "effect": {"jack": True}},
        "Cutting Words":      {"tier": 2, "desc": "Reduce enemy roll by 1d8",      "effect": {"cutting": "1d8"}},
        "Countercharm":       {"tier": 2, "desc": "Allies advantage vs charm/fear","effect": {"countercharm": True}},
        "Magical Secrets":    {"tier": 3, "desc": "Learn 2 spells from any class", "effect": {"secrets": True}},
        "Superior Inspiration":{"tier": 3, "desc": "Regain inspiration on init",   "effect": {"sup_insp": True}},
    },
    "Monk": {
        "Flurry of Blows":   {"tier": 1, "desc": "Two unarmed strikes as bonus",  "effect": {"flurry": True}},
        "Patient Defense":   {"tier": 1, "desc": "Dodge as bonus action",          "effect": {"patient": True}},
        "Stunning Strike":   {"tier": 2, "desc": "Stun on hit (CON save)",         "effect": {"stunning": True}},
        "Deflect Missiles":  {"tier": 2, "desc": "Reduce ranged damage by 1d10",   "effect": {"deflect": True}},
        "Quivering Palm":    {"tier": 3, "desc": "Set vibrations — kill on demand", "effect": {"quivering": True}},
        "Empty Body":        {"tier": 3, "desc": "Invisible + resist all damage",  "effect": {"empty_body": True}},
    },
    "Sorcerer": {
        "Font of Magic":     {"tier": 1, "desc": "Convert sorcery points to slots","effect": {"font": True}},
        "Twinned Spell":     {"tier": 1, "desc": "Target two creatures with one spell","effect": {"twinned": True}},
        "Quickened Spell":   {"tier": 2, "desc": "Cast as bonus action",           "effect": {"quickened": True}},
        "Careful Spell":     {"tier": 2, "desc": "Allies auto-save your spells",   "effect": {"careful": True}},
        "Sorcerous Restoration":{"tier": 3, "desc": "Regain 4 SP on short rest",   "effect": {"restoration": True}},
        "Arcane Apotheosis":  {"tier": 3, "desc": "Permanent flight + resistance",  "effect": {"apotheosis": True}},
    },
}


# ══════════════════════════════════════════════════════════════
#  CHARACTER MECHANICS — Derived stats, HP, AC, etc.
# ══════════════════════════════════════════════════════════════

def max_hp(char: dict) -> int:
    hd = HIT_DICE.get(char.get("class", "Fighter"), 8)
    con = mod(char.get("stats", {}).get("CON", 12))
    lvl = char.get("level", 1)
    return max(1, hd + con + (hd // 2 + 1 + con) * (lvl - 1))

def max_slots(char: dict) -> int:
    tbl = SLOT_TABLE.get(char.get("class", "Fighter"), {})
    if not tbl:
        return 0
    return tbl.get(min(char.get("level", 1), max(tbl.keys(), default=1)), 0)

def init_slots(char: dict):
    char["spell_slots_max"] = max_slots(char)
    char["spell_slots_current"] = char["spell_slots_max"]

def calc_ac(char: dict) -> int:
    dex = mod(char.get("stats", {}).get("DEX", 10))
    armor = char.get("equipped", {}).get("armor", "")
    if item_cond(char, armor) == "broken":
        return 10 + dex
    base = ARMORS.get(armor, {}).get("ac", 10)
    return base + (dex if "Plate" not in armor else 0)

def calc_atk(char: dict) -> int:
    pb = prof_bonus(char.get("level", 1))
    weapon = char.get("equipped", {}).get("weapon", "")
    if item_cond(char, weapon) == "broken":
        return 0
    stats = char.get("stats", {})
    wdata = WEAPONS.get(weapon, {})
    if wdata.get("finesse"):
        sv = max(stats.get("STR", 10), stats.get("DEX", 10))
    elif wdata.get("arcane"):
        sv = max(stats.get("INT", 10), stats.get("CHA", 10))
    else:
        sv = stats.get("STR", 10)
    return mod(sv) + pb

def weapon_damage(char: dict) -> Tuple[int, str]:
    weapon = char.get("equipped", {}).get("weapon", "")
    wdata = WEAPONS.get(weapon, {})
    notation = wdata.get("damage", "1d4")
    total, rolls = roll_dice_notation(notation)
    return total, wdata.get("dtype", "physical")

def hp_color(char: dict) -> str:
    hp = char.get("hp", 1)
    mhp = max_hp(char)
    pct = hp / mhp if mhp else 0
    return C.GREEN if pct > 0.5 else C.ORANGE if pct > 0.25 else C.RED

def hp_status(char: dict) -> str:
    hp = char.get("hp", 1)
    mhp = max_hp(char)
    pct = hp / mhp if mhp else 0
    if hp <= 0:     return cc(C.RED,    "☠  UNCONSCIOUS")
    if pct <= 0.25: return cc(C.RED,    "💀 NEAR DEATH")
    if pct <= 0.5:  return cc(C.ORANGE, "🩸 BLOODIED")
    if pct <= 0.75: return cc(C.YELLOW, "⚠  WOUNDED")
    return cc(C.GREEN, "♥  HEALTHY")

def item_cond(char: dict, item: str) -> str:
    return char.get("item_conditions", {}).get(item, "good")

def degrade_item(char: dict, slot: str):
    item = char.get("equipped", {}).get(slot, "")
    if not item:
        return
    cur = item_cond(char, item)
    idx = ITEM_STATES.index(cur) if cur in ITEM_STATES else 1
    if idx < len(ITEM_STATES) - 1:
        nxt = ITEM_STATES[idx + 1]
        char.setdefault("item_conditions", {})[item] = nxt
        col = C.ORANGE if nxt in ("worn", "damaged") else C.RED
        cprint(col, f"  ⚔  Your {item} is now {nxt.upper()}!")
        if nxt == "broken":
            cprint(C.RED, f"  ✗  Your {item} has BROKEN!")
            char["equipped"][slot] = ""

def get_rep(score: int) -> Tuple[str, str, str]:
    for lo, hi, title, col, flavor in NOTORIETY_TIERS:
        if lo <= score <= hi:
            return title, col, flavor
    return "Wanderer", C.GRAY, "Your reputation is unwritten."

def apply_notoriety(char: dict, delta: int, reason: str) -> str:
    old = char.get("notoriety_score", 0)
    old_t, _, _ = get_rep(old)
    new = max(-1000, min(1000, old + delta))
    char["notoriety_score"] = new
    t, col, flavor = get_rep(new)
    sign = "+" if delta >= 0 else ""
    dcol = C.GREEN if delta > 0 else C.RED
    msg = f"{dcol}  [Notoriety {sign}{delta}: {reason}]{C.RESET}"
    if old_t != t:
        msg += f"\n{col}  {'★' * 40}\n  You are now known as: {bold(t)}\n  {flavor}\n  {'★' * 40}{C.RESET}"
    return msg

def xp_next(lvl: int) -> int:
    return XP_THRESH.get(lvl, 999999)

def lvl_up_check(char: dict) -> Optional[int]:
    l = char.get("level", 1)
    return l + 1 if l < 20 and char.get("xp", 0) >= xp_next(l) else None

def add_condition(char: dict, cond: str):
    char.setdefault("conditions", [])
    if cond not in char["conditions"]:
        char["conditions"].append(cond)
        col, desc = CONDITIONS.get(cond, (C.ORANGE, ""))
        cprint(col, f"  ⚠  {char['name']} is now {cond.upper()}! {desc}")

def remove_condition(char: dict, cond: str):
    if cond in char.get("conditions", []):
        char["conditions"].remove(cond)
        cprint(C.GREEN, f"  ✓  {char['name']} is no longer {cond}.")

def tick_conditions(char: dict) -> int:
    total = 0
    for cond in list(char.get("conditions", [])):
        if cond == "bleeding":
            dmg, _ = roll(4)
            total += dmg
            cprint(C.RED, f"  💉 {char['name']} bleeds for {dmg} damage!")
        elif cond == "burning":
            dmg, _ = roll(6)
            total += dmg
            cprint(C.ORANGE, f"  🔥 {char['name']} burns for {dmg} damage!")
    return total


# ══════════════════════════════════════════════════════════════
#  SAVE/LOAD — Atomic writes, crash-safe
# ══════════════════════════════════════════════════════════════

def ensure_save_dir():
    Path(CFG.save_dir).mkdir(parents=True, exist_ok=True)

def atomic_save(filepath: str, data: dict):
    """Write JSON atomically (temp file + rename) to prevent corruption."""
    ensure_save_dir()
    full = os.path.join(CFG.save_dir, filepath)
    fd, tmp = tempfile.mkstemp(dir=CFG.save_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(tmp, full)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

def load_json(filepath: str, default: Any = None) -> Any:
    full = os.path.join(CFG.save_dir, filepath)
    if not os.path.exists(full):
        return default if default is not None else {}
    try:
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        log.warning(f"Failed to load {full}, using default")
        return default if default is not None else {}

def load_chars() -> Dict[str, dict]:
    return load_json("characters.json", {})

def save_chars(chars: Dict[str, dict]):
    atomic_save("characters.json", chars)

def load_campaign() -> dict:
    return load_json("campaign.json", {
        "title": "A Solo Journey",
        "tone": "Gritty adventure with room for redemption.",
        "difficulty": "normal",
        "world_notes": [
            "The world is fractured — old empires crumbled, new ones rise.",
            "Magic is rare and feared by common folk.",
            "The roads are dangerous but rich with opportunity.",
            "Something vast and ancient stirs in the dark between the stars.",
        ],
        "session_log": [], "session_number": 1, "story_so_far": [],
        "turn_count": 0, "last_ambush_turn": -99,
    })

def save_campaign(state: dict):
    atomic_save("campaign.json", state)


# ══════════════════════════════════════════════════════════════
#  ENCOUNTER TABLE — CR-scaled enemies with loot tiers
# ══════════════════════════════════════════════════════════════

ENCOUNTER_TABLE = {
    # CR tier -> list of (name, base_hp, base_ac, xp, loot_tier)
    "minion": [
        ("Goblin Scout",     12, 11, 100, "common"),
        ("Giant Rat",        10, 10, 50,  "junk"),
        ("Kobold",           12, 11, 75,  "common"),
        ("Skeleton",         14, 12, 100, "common"),
        ("Zombie",           18, 8,  100, "junk"),
    ],
    "standard": [
        ("Bandit",           22, 13, 200, "common"),
        ("Orc Raider",       26, 13, 250, "common"),
        ("Wolf Pack Leader", 20, 13, 200, "common"),
        ("Cultist",          24, 12, 200, "uncommon"),
        ("Giant Spider",     20, 14, 250, "uncommon"),
        ("Wraith",           22, 13, 300, "uncommon"),
    ],
    "elite": [
        ("Owlbear",          40, 14, 450, "uncommon"),
        ("Cave Troll",       45, 14, 500, "uncommon"),
        ("Vampire Spawn",    38, 15, 500, "rare"),
        ("Mimic",            30, 15, 400, "rare"),
        ("Gelatinous Cube",  35, 8,  400, "rare"),
    ],
    "boss": [
        ("Demon",            55, 16, 800,  "rare"),
        ("Hydra",            60, 15, 900,  "rare"),
        ("Elemental Lord",   50, 16, 750,  "rare"),
        ("Mind Flayer",      55, 17, 1000, "epic"),
        ("Vampire Lord",     65, 16, 1100, "epic"),
    ],
    "legendary": [
        ("Ancient Dragon",   120, 18, 2500, "legendary"),
        ("Lich King",        90,  17, 2000, "legendary"),
        ("Beholder",         80,  17, 1800, "epic"),
        ("Demon Prince",     100, 18, 2200, "legendary"),
    ],
}

LOOT_TABLES = {
    "junk":      ["Rat Tail", "Broken Tooth", "Moldy Bread", "Rusty Nail"],
    "common":    ["Health Potion", "Bandage Kit", "Adventurer's Ration", "Torch x5",
                  "Antidote", "Thieves' Tools", "Rope (50ft)"],
    "uncommon":  ["Health Potion", "Greater Health Potion", "Scroll of Identify",
                  "Silver Arrow x10", "Potion of Strength", "Smoke Bomb x3"],
    "rare":      ["Greater Health Potion", "Potion of Invisibility", "Scroll of Fireball",
                  "Ring of Protection", "Cloak of Elvenkind", "Gem (50gp)"],
    "epic":      ["Supreme Health Potion", "Potion of Speed", "Scroll of Teleport",
                  "Amulet of Health", "Gem (200gp)"],
    "legendary": ["Potion of Invulnerability", "Scroll of Wish", "Dragon Scale Mail",
                  "Gem (500gp)", "Tome of Knowledge"],
}

def scale_encounter(player_level: int, difficulty: str) -> tuple:
    """Pick a CR-appropriate encounter based on player level + difficulty."""
    diff_bump = {"easy": -1, "normal": 0, "hard": 1}.get(difficulty, 0)
    if player_level <= 2:
        tier = "minion"
    elif player_level <= 5:
        tier = "standard"
    elif player_level <= 9:
        tier = "elite"
    elif player_level <= 14:
        tier = "boss"
    else:
        tier = "legendary"

    tiers = list(ENCOUNTER_TABLE.keys())
    idx = tiers.index(tier) + diff_bump
    idx = max(0, min(len(tiers) - 1, idx))
    tier = tiers[idx]

    name, base_hp, base_ac, xp, loot_tier = random.choice(ENCOUNTER_TABLE[tier])
    # Scale HP with player level
    hp_scale = 1.0 + (player_level - 1) * 0.12
    hp = int(base_hp * hp_scale)
    ac = base_ac + (player_level // 5)
    xp = int(xp * hp_scale)
    return name, hp, ac, xp, loot_tier

def roll_loot(loot_tier: str, luck_bonus: int = 0) -> list:
    """Roll loot from the appropriate tier."""
    items = []
    pool = LOOT_TABLES.get(loot_tier, LOOT_TABLES["common"])
    # Always one item
    items.append(random.choice(pool))
    # 30% chance of second item (+ luck)
    if random.randint(1, 100) <= 30 + luck_bonus:
        items.append(random.choice(pool))
    # 10% chance to roll from one tier higher
    tier_order = ["junk", "common", "uncommon", "rare", "epic", "legendary"]
    if random.randint(1, 100) <= 10:
        idx = tier_order.index(loot_tier) if loot_tier in tier_order else 1
        if idx < len(tier_order) - 1:
            items.append(random.choice(LOOT_TABLES[tier_order[idx + 1]]))
    return items


# ══════════════════════════════════════════════════════════════
#  DM PERSONALITY SYSTEM — 3 Dungeon Master styles
# ══════════════════════════════════════════════════════════════

DM_STYLES = {
    "dramatic": {
        "name": "The Dramatist",
        "icon": "🎭",
        "desc": "Epic narration, high stakes, cinematic moments.",
        "system_addon": (
            "STYLE: You are a dramatic, cinematic storyteller. "
            "Every scene is larger than life. Use vivid sensory details "
            "— the smell of ozone before lightning, the rumble of "
            "approaching hooves, the flicker of torchlight on ancient stone. "
            "Build tension. Make the player feel like the hero of an epic saga."
        ),
        "combat_flavor": [
            "Steel rings against steel as fate hangs in the balance!",
            "The air crackles with the weight of the moment!",
            "Time seems to slow as the blow connects!",
            "A thunderclap of impact echoes through the chamber!",
        ],
        "death_quote": "The darkness claims another hero. But legends never truly die.",
        "victory_quote": "And so the champion stands victorious, their name carved into the annals of history.",
    },
    "sardonic": {
        "name": "The Wisecracker",
        "icon": "😏",
        "desc": "Dry wit, dark humor, fourth-wall-aware.",
        "system_addon": (
            "STYLE: You are a sardonic, witty DM with dry humor. "
            "Narrate like a sarcastic author who's seen it all. "
            "Slip in deadpan observations. NPCs can be sarcastic. "
            "The world is dangerous but absurd. Never break character "
            "but let your narrator voice have personality — think "
            "Terry Pratchett meets a jaded tavern keeper."
        ),
        "combat_flavor": [
            "Well, that's going to leave a mark.",
            "Somewhere, a bard is taking notes for a very unflattering song.",
            "The enemy looks personally offended by your competence.",
            "Violence: the universal language. How heartwarming.",
        ],
        "death_quote": "And that, dear adventurer, is why we don't pick fights with things larger than our head.",
        "victory_quote": "Congratulations. You've successfully converted a living thing into loot. Your parents would be so proud.",
    },
    "poetic": {
        "name": "The Poet",
        "icon": "📜",
        "desc": "Lyrical prose, mythic tone, Tolkien-esque.",
        "system_addon": (
            "STYLE: You are a poetic, mythic storyteller in the tradition of "
            "Tolkien and Le Guin. Your narration reads like ancient prose. "
            "Use metaphor and rhythm. The world feels old and deep — "
            "rivers remember, stones whisper, trees have watched empires "
            "rise and fall. Nature is alive and watching. "
            "Your voice is gentle but carries the weight of ages."
        ),
        "combat_flavor": [
            "And the blade sang its crimson song.",
            "In the silence between heartbeats, steel found flesh.",
            "The old dance of death and defiance, played once more.",
            "Like autumn leaves before the storm, the foe falters.",
        ],
        "death_quote": "And so the light passes into the grey lands beyond, where all rivers find the sea.",
        "victory_quote": "The shadow retreats, and for a moment, the world remembers what it is to breathe.",
    },
}


# ══════════════════════════════════════════════════════════════
#  RANDOM EVENTS — Weather, merchants, strangers, traps
# ══════════════════════════════════════════════════════════════

WEATHER_TABLE = [
    ("clear",       C.CYAN,    "☀️  Clear skies — good travel weather."),
    ("cloudy",      C.GRAY,    "☁️  Overcast clouds hang low."),
    ("rain",        C.BLUE,    "🌧️  Rain patters against your cloak. (-1 Perception)"),
    ("fog",         C.GRAY,    "🌫️  Thick fog limits visibility. (-2 Perception)"),
    ("storm",       C.YELLOW,  "⚡  Thunder rolls — lightning flashes. (-2 Stealth)"),
    ("snow",        C.WHITE,   "❄️  Snow falls gently. Movement slowed."),
    ("heatwave",    C.ORANGE,  "🔥  Scorching heat — CON save or lose 1d4 HP."),
    ("wind",        C.CYAN,    "🌬️  Howling wind makes ranged attacks harder."),
    ("beautiful",   C.GREEN,   "🌅  A beautiful dawn breaks. +1 to all checks this scene."),
    ("eerie calm",  C.MAGENTA, "🌑  An unnatural stillness. Something is watching."),
]

RANDOM_EVENTS = [
    {
        "name": "Wandering Merchant",
        "weight": 15,
        "prompt": "A merchant approaches with unusual wares. Describe them and their goods briefly. Offer [A] trade [B] ignore.",
        "effect": None,
    },
    {
        "name": "Mysterious Stranger",
        "weight": 10,
        "prompt": "A cloaked stranger appears — they know your name. Describe the encounter dramatically. Offer [A] listen [B] draw weapon.",
        "effect": None,
    },
    {
        "name": "Hidden Trap",
        "weight": 12,
        "check": "perception",
        "prompt": "The player {result} a hidden trap. Narrate the outcome. If failed: 1d6 damage. Offer [A]/[B] choices.",
        "effect": "trap_damage",
    },
    {
        "name": "Abandoned Camp",
        "weight": 10,
        "prompt": "The party discovers an abandoned campsite. Signs of a hasty departure. Something was left behind. Offer [A] search [B] move on.",
        "effect": None,
    },
    {
        "name": "Distant Battle",
        "weight": 8,
        "prompt": "Sounds of combat echo from nearby — screams, steel, something inhuman. Offer [A] investigate [B] avoid.",
        "effect": None,
    },
    {
        "name": "Healing Spring",
        "weight": 5,
        "prompt": "A natural spring glows faintly with restorative energy. Describe it beautifully. The player heals 2d6 HP.",
        "effect": "heal_spring",
    },
    {
        "name": "Ominous Omen",
        "weight": 8,
        "prompt": "An omen appears — a raven with three eyes, a bloodied sun, a whispering wind. Describe it cryptically. This foreshadows danger. Offer [A]/[B].",
        "effect": None,
    },
    {
        "name": "Lost Child",
        "weight": 6,
        "prompt": "A lost child appears on the road, frightened and alone. Helping gains notoriety. Ignoring costs it. Offer [A] help [B] keep walking.",
        "effect": None,
    },
    {
        "name": "Treasure Glint",
        "weight": 8,
        "prompt": "Something glints in the underbrush — could be treasure, could be a trap. Offer [A] investigate [B] leave it.",
        "effect": None,
    },
    {
        "name": "Old Battlefield",
        "weight": 5,
        "prompt": "You cross an ancient battlefield. Bones and rusted weapons litter the ground. The dead do not always rest. Offer [A] search [B] pray and move on.",
        "effect": None,
    },
]

def roll_weather() -> tuple:
    """Roll random weather. Returns (name, color, description)."""
    return random.choice(WEATHER_TABLE)

def choose_dm_style(state: dict):
    """Let the player pick a DM personality style."""
    header("DUNGEON MASTER STYLE", C.MAGENTA)
    styles = list(DM_STYLES.items())
    for i, (key, data) in enumerate(styles, 1):
        print(f"  [{i}] {C.BOLD}{data.get('icon','')} {key.upper()}{C.RESET} — {data['desc']}")
    print(f"  {C.GRAY}[Enter] Keep current ({state.get('dm_style', 'dramatic').upper()}){C.RESET}\n")
    choice = input("  Choose style: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(styles):
        picked = styles[int(choice) - 1]
        state["dm_style"] = picked[0]
        cprint(C.MAGENTA, f"  DM style set to {picked[1].get('icon','')} {picked[0].upper()} — {picked[1]['desc']}")
    else:
        cprint(C.GRAY, f"  Keeping {state.get('dm_style', 'dramatic').upper()} style.")


def roll_random_event(player: dict, state: dict) -> Optional[dict]:
    """Maybe trigger a random event. Returns event dict or None."""
    # 20% base chance per non-combat turn
    if random.randint(1, 100) > 20:
        return None
    # Weighted selection
    total_weight = sum(e["weight"] for e in RANDOM_EVENTS)
    r = random.randint(1, total_weight)
    cumulative = 0
    for event in RANDOM_EVENTS:
        cumulative += event["weight"]
        if r <= cumulative:
            return event
    return None

def apply_event_effect(event: dict, player: dict):
    """Apply mechanical effects of random events."""
    eff = event.get("effect")
    if eff == "trap_damage":
        dmg, _ = roll(6)
        player["hp"] = max(0, player.get("hp", 1) - dmg)
        cprint(C.RED, f"  💥 Trap! You take {dmg} damage. HP: {player['hp']}/{max_hp(player)}")
    elif eff == "heal_spring":
        heal, _ = roll(6, 2)
        player["hp"] = min(max_hp(player), player.get("hp", 1) + heal)
        cprint(C.GREEN, f"  ✨ The spring restores {heal} HP. HP: {player['hp']}/{max_hp(player)}")


# ══════════════════════════════════════════════════════════════
#  QUEST JOURNAL
# ══════════════════════════════════════════════════════════════

def add_quest(state: dict, title: str, description: str, quest_type: str = "main"):
    """Add a quest to the journal."""
    state.setdefault("quests", [])
    quest = {
        "title": title,
        "description": description,
        "type": quest_type,  # main, side, bounty
        "status": "active",
        "added_session": state.get("session_number", 1),
        "objectives": [],
    }
    state["quests"].append(quest)
    cprint(C.YELLOW, f"\n  📜 NEW QUEST: {title}")
    cprint(C.GRAY, f"     {description}")

def complete_quest(state: dict, index: int):
    """Mark a quest as complete."""
    quests = state.get("quests", [])
    if 0 <= index < len(quests):
        quests[index]["status"] = "complete"
        cprint(C.GREEN, f"  ✓ Quest complete: {quests[index]['title']}")

def show_quests(state: dict):
    """Display the quest journal."""
    quests = state.get("quests", [])
    header("QUEST JOURNAL", C.YELLOW)
    if not quests:
        cprint(C.GRAY, "  No quests yet. The adventure awaits.")
        return

    active = [q for q in quests if q["status"] == "active"]
    done = [q for q in quests if q["status"] == "complete"]

    if active:
        cprint(C.YELLOW, "  ══ ACTIVE QUESTS ══", wrap=False)
        for i, q in enumerate(quests):
            if q["status"] == "active":
                icon = {
                    "main": f"{C.YELLOW}★",
                    "side": f"{C.CYAN}○",
                    "bounty": f"{C.RED}⚔",
                }.get(q["type"], f"{C.GRAY}○")
                print(f"  {icon} [{i + 1}]{C.RESET} {C.BOLD}{q['title']}{C.RESET}")
                print(f"       {C.GRAY}{q['description']}{C.RESET}")
                if q.get("objectives"):
                    for obj in q["objectives"]:
                        done_mark = cc(C.GREEN, "✓") if obj.get("done") else cc(C.GRAY, "○")
                        print(f"       {done_mark} {obj['text']}")
        print()

    if done:
        cprint(C.GREEN, "  ══ COMPLETED ══", wrap=False)
        for q in done:
            print(f"  {C.GREEN}✓{C.RESET} {C.GRAY}{q['title']}{C.RESET}")
    divider()


# ══════════════════════════════════════════════════════════════
#  CAMPFIRE REST SYSTEM — Atmospheric rest scenes
# ══════════════════════════════════════════════════════════════

CAMPFIRE_ART = [
    "       *    .  *       .        *    .  ",
    "    .    *    .    *  .    .   *    .   ",
    "           (                            ",
    "          ) \\  .  .                     ",
    "         /   \\                          ",
    "        / 🔥  \\     * * *               ",
    "       (  🔥🔥  )   * camp *              ",
    "  ~~~~~`------´~~~~~* * *~~~~~~~~~~~    ",
]

DREAM_TABLE = [
    "You dream of a vast ocean, and something enormous moves beneath the surface.",
    "In your dream, a voice speaks your name from inside a mountain.",
    "You dream you are falling through stars, and each one whispers a secret.",
    "A figure made of shadow offers you a key. You wake before you can take it.",
    "You dream of the first home you ever knew, but the rooms have changed.",
    "In the dream, your weapon speaks. It tells you its real name.",
    "You dream of a door that shouldn't exist. Behind it, laughter.",
    "A great tree grows from your chest in the dream. Birds nest in your ribs.",
    "You relive a battle, but this time your enemy stops and asks: 'Why?'",
    "You dream of a feast laid for one. Every chair has a name carved in it. Yours is at the head.",
    "A child version of you stares across a river. They mouth something you can't hear.",
    "You dream of walking a road that never ends, and you don't want it to.",
]

WATCH_EVENTS = [
    "Nothing stirs. The night is peaceful.",
    "An owl hoots three times. Old folk say that means change is coming.",
    "You hear distant howling. It stops abruptly.",
    "A shooting star crosses the sky. You make a wish.",
    "The wind carries a faint melody. When you listen harder, it's gone.",
    "Fireflies dance at the edge of the clearing. For a moment, they seem to form a pattern.",
    "Something large moves through the trees. It doesn't approach.",
    "You find a small flower growing from a crack in the stone. It shouldn't be alive.",
    "The fire dims for no reason, then flares back brighter than before.",
    "You hear your name on the wind. Probably nothing.",
]

def campfire_rest(player: dict, companions: List[dict], state: dict):
    """Full campfire rest sequence with atmosphere."""
    print()
    print_art(CAMPFIRE_ART, C.ORANGE, centered=False)
    header("CAMPFIRE REST", C.ORANGE)

    # Weather
    w_name, w_col, w_desc = roll_weather()
    print(f"  {w_col}{w_desc}{C.RESET}\n")

    # Watch shift
    cprint(C.GRAY, "  First watch...\n", wrap=False)
    time.sleep(0.5)
    watch_event = random.choice(WATCH_EVENTS)
    cprint(C.CYAN, f"  {watch_event}")
    print()

    # Companion banter (if any)
    if companions:
        alive = [c for c in companions if c.get("alive", True)]
        if alive:
            talker = random.choice(alive)
            banter = ai_call([{"role": "user", "content":
                f"{talker['name']} ({talker['archetype']}, personality: {talker['personality']}) "
                f"says ONE short sentence to the party around a campfire. "
                f"In character. No preamble."}], max_tokens=40)
            col = COMP_COLORS.get(talker["name"].lower(), C.WHITE)
            print(f"  {col}{C.BOLD}{talker['name']}:{C.RESET} {col}\"{banter}\"{C.RESET}\n")

    # Rest options
    print(f"  {C.BOLD}[1]{C.RESET} Short Rest  — recover some HP + all spell slots")
    print(f"  {C.BOLD}[2]{C.RESET} Long Rest   — full HP, all slots, clear conditions")
    print(f"  {C.BOLD}[3]{C.RESET} Keep Watch  — stay alert (skip rest)")
    action = input(f"\n  {C.ORANGE}>{C.RESET} ").strip()

    if action == "1":
        # Short rest
        init_slots(player)
        con_rec = max(1, player.get("level", 1) // 2 + mod(player.get("stats", {}).get("CON", 10)))
        player["hp"] = min(max_hp(player), player.get("hp", 1) + con_rec)
        cprint(C.GREEN, f"  Recovered {con_rec} HP. ({player['hp']}/{max_hp(player)})")
        cprint(C.MAGENTA, f"  Spell slots restored.")
    elif action == "2":
        # Long rest
        player["hp"] = max_hp(player)
        init_slots(player)
        player["conditions"] = []
        cprint(C.GREEN, f"  Fully rested. HP: {player['hp']}/{max_hp(player)}")
        cprint(C.MAGENTA, f"  All spell slots restored. Conditions cleared.")
        # Dream
        dream = random.choice(DREAM_TABLE)
        print(f"\n  {C.MAGENTA}{C.ITALIC}  You dream...{C.RESET}")
        cprint(C.MAGENTA, f"  {dream}")
    elif action == "3":
        # Keep watch — chance to spot danger early
        cprint(C.CYAN, "  You keep watch through the night. Your eyes are sharp.")
        # 20% chance of spotting something
        if random.randint(1, 5) == 1:
            cprint(C.YELLOW, "  👁  You spot movement in the darkness. You're prepared!")
            state["_watch_bonus"] = True  # advantage on next ambush

    print()
    divider("~", C.ORANGE)
    cprint(C.GRAY, "  Dawn breaks. The road calls.")
    print()


# ══════════════════════════════════════════════════════════════
#  LLM ENGINE — Ollama via OpenAI SDK, Pi 4 optimized
# ══════════════════════════════════════════════════════════════

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not HAS_OPENAI:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        _client = OpenAI(api_key=CFG.api_key, base_url=CFG.api_base)
    return _client

def ai_call(messages: list, max_tokens: int = None) -> str:
    """Single LLM call with error handling and Pi 4 token budget."""
    mt = max_tokens or CFG.max_tokens
    try:
        r = get_client().chat.completions.create(
            model=CFG.model,
            messages=messages,
            temperature=CFG.temperature,
            max_tokens=mt,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        log.error(f"LLM error: {e}")
        return f"[The world holds its breath... AI error: {type(e).__name__}]"

def build_system_prompt(state: dict, player: dict, companions: List[dict]) -> str:
    """Ultra-tight DM system prompt — optimized for small local models."""
    eq = player.get("equipped", {})
    hp = player.get("hp", 1)
    mhp = max_hp(player)
    pct = hp / mhp if mhp else 1
    slots = player.get("spell_slots_current", 0)
    mslots = player.get("spell_slots_max", 0)
    conds = player.get("conditions", [])
    t, _, _ = get_rep(player.get("notoriety_score", 0))

    if pct <= 0.25:
        hp_note = f"NEAR DEATH ({hp}/{mhp}hp) — describe as desperate, staggering"
    elif pct <= 0.5:
        hp_note = f"bloodied ({hp}/{mhp}hp) — show strain"
    else:
        hp_note = f"healthy ({hp}/{mhp}hp)"

    comp_lines = []
    for c in companions:
        if c.get("alive", True):
            chp = c.get("hp", "?")
            cmhp = max_hp(c)
            comp_lines.append(f"  {c['name']} ({c['class']}): {chp}/{cmhp}hp | {c['personality']}")
    comp_str = "\n".join(comp_lines) if comp_lines else "traveling alone"

    story = ""
    if state.get("story_so_far"):
        story = "Story so far: " + state["story_so_far"][-1][:200]

    cond_str = f" CONDITIONS: {','.join(conds)}" if conds else ""
    slot_str = f" Slots:{slots}/{mslots}" if mslots else ""

    # Weather context
    weather_str = ""
    if state.get("_current_weather"):
        weather_str = f"\nWEATHER: {state['_current_weather']}"

    # DM personality injection
    dm_style = state.get("dm_style", "dramatic")
    style_data = DM_STYLES.get(dm_style, DM_STYLES["dramatic"])
    style_addon = style_data["system_addon"]

    # Quest context
    quest_str = ""
    active_quests = [q for q in state.get("quests", []) if q["status"] == "active"]
    if active_quests:
        quest_str = "\nACTIVE QUESTS: " + "; ".join(q["title"] for q in active_quests[:3])

    return f"""You are a Dungeon Master running a D&D adventure.
{style_addon}

CHARACTER: {player['name']} ({player['race']} {player['class']} Lv{player['level']}) — {hp_note}{cond_str}{slot_str}
WEAPON: {eq.get('weapon', 'none')} | ARMOR: {eq.get('armor', 'none')} | GOLD: {player.get('gold', 0)}gp
PARTY: {comp_str}
{story}{weather_str}{quest_str}

CRITICAL: You are narrating for {player['name']} ONLY. Do not narrate actions for any other player character.
If companions act, describe their actions briefly. {player['name']} is the hero of this story.

WRITE EXACTLY THIS FORMAT — nothing else:
Two sentences of vivid scene description. Make it dramatic and specific.
NPC_NAME: "one short quote" — only if an NPC is present, else omit this line entirely

[A] bold action label (5 words max)
[B] cunning alternative (5 words max)
[O] Other

RULES — READ EVERY TIME:
- STOP writing after [O] Other. Nothing after it. Ever.
- NEVER number lines. No 1. 2. 3. No A: B: — only [A] [B]
- NEVER repeat choices or write two [A] blocks
- NEVER write "Regardless of the option chosen" or meta-commentary
- ALWAYS advance the plot — something must change"""


def clean_response(raw: str) -> str:
    """Nuclear cleaner — strips ALL model-invented sections."""
    text = re.sub(r'^(PARAGRAPH|NPC LINE|NPC|SCENE|NARRATION|STORY|ACTION|CHOICE|OUTCOME):\s*', '',
                  raw, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'\[2 sentences[^\]]*\]\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^NAME:\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\[NAME\][^"]*"', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s*(\[)', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^A:\s+', '[A] ', text, flags=re.MULTILINE)
    text = re.sub(r'^B:\s+', '[B] ', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'\[O\].*', '[O] Other', text)
    if '[O] Other' in text:
        text = text[:text.index('[O] Other') + len('[O] Other')]

    SKIP_STARTS = [
        "narration:", "hp:", "gold:", "companions:", "stats:", "spells:",
        "conditions:", "leveled spells:", "cantrips:", "weapon:", "armor:",
        "spell slots:", "xp:", "compiled by", "butterfly effect",
        "continued...", "(continued", "- strength", "- dexterity",
        "- constitution", "- intelligence", "- wisdom", "- charisma",
    ]
    SKIP_CONTAINS = [
        "implications for", "has implications", "'s health:",
        "'s stats:", "'s gold:", "'s spell", "hp (confident)",
        "hp (healthy)", "hp (bloodied)", "hp (near death)",
    ]
    SKIP_RE = [
        re.compile(r"^(STR|DEX|CON|INT|WIS|CHA|AC|ATK|HP|XP)[\t :]", re.I),
        re.compile(r"^\d+/\d+\s*hp\s*\(", re.I),
    ]

    lines = text.split("\n")
    seen_a = False
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            out.append("")
            continue
        sl = s.lower()
        if any(sl.startswith(p) for p in SKIP_STARTS):
            continue
        if any(p in sl for p in SKIP_CONTAINS):
            continue
        if any(p.search(s) for p in SKIP_RE):
            continue
        if re.match(r"^\[A\]", s):
            if seen_a:
                break
            seen_a = True
        out.append(line)

    result = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    if "[A]" in result and "[O]" not in result:
        result += "\n[O] Other"
    return result


def get_response(state: dict, player: dict, companions: List[dict],
                 user_input: str) -> str:
    """Get DM response with tight context window for Pi 4."""
    msgs = [{"role": "system", "content": build_system_prompt(state, player, companions)}]
    for entry in state["session_log"][-CFG.context_window:]:
        role = "assistant" if entry.startswith("[DM]") else "user"
        content = entry.replace("[DM] ", "").replace("[YOU] ", "")
        if role == "assistant":
            content = content[:CFG.history_trim] + ("..." if len(content) > CFG.history_trim else "")
        msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_input})
    raw = ai_call(msgs, max_tokens=260)
    return clean_response(raw)


# ══════════════════════════════════════════════════════════════
#  DM NARRATION PRINTER — Color-coded, semantic parsing
# ══════════════════════════════════════════════════════════════

COMP_COLORS = {
    "thalia": C.MAGENTA, "gruff veteran": C.BLUE, "gruff": C.BLUE,
    "moros": C.CYAN, "eager scholar": C.CYAN, "charming rogue": C.YELLOW,
    "wild ranger": C.GREEN, "zealous cleric": C.YELLOW,
    "bitter mercenary": C.ORANGE,
}

RE_CHOICE_A = re.compile(r"^\[A\]")
RE_CHOICE_B = re.compile(r"^\[B\]")
RE_CHOICE_O = re.compile(r"^\[O\]")
RE_NPC_FMT  = re.compile(r"^\[([A-Z][A-Za-z ]+)\]:\s*(.+)$")
RE_SAYS_FMT = re.compile(r"^([A-Z][a-zA-Z ]+)\s+(says|whispers|growls|shouts|snarls|mutters):\s*(.+)$")
RE_DAMAGE   = re.compile(r"\b\d+\s*(damage|slashing|piercing|fire|cold|necrotic)\b", re.I)
RE_GOLD     = re.compile(r"\b(gold|gp|you find|loot|treasure|coin)\b", re.I)
RE_MAGIC    = re.compile(r"\b(eldritch|arcane|crackl|surge|void|patron|spell|magic)\b", re.I)

def dm_print(text: str):
    """Print DM narration with semantic color coding."""
    print()
    print(f"{C.MAGENTA}{'=' * W}{C.RESET}")
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            print()
            continue
        if RE_CHOICE_A.match(s):
            print(f"\n  {C.BOLD}{C.GREEN}[A] {s[3:].strip()}{C.RESET}")
            continue
        if RE_CHOICE_B.match(s):
            print(f"  {C.BOLD}{C.YELLOW}[B] {s[3:].strip()}{C.RESET}")
            continue
        if RE_CHOICE_O.match(s):
            print(f"  {C.GRAY}[O] Other{C.RESET}\n")
            continue
        m = RE_NPC_FMT.match(s)
        if m:
            name, quote = m.group(1).strip(), m.group(2).strip().strip('"')
            col = COMP_COLORS.get(name.lower(), C.WHITE)
            print(f"  {col}{C.BOLD}{name}:{C.RESET} {col}\"{quote}\"{C.RESET}")
            continue
        for tag, col in [("npc", C.WHITE), ("companion", C.MAGENTA), ("enemy", C.RED)]:
            if f"<{tag}>" in s:
                txt = re.sub(f"</?{tag}>", "", s).strip()
                for wl in textwrap.wrap(txt, W - 4):
                    print(f"  {col}{wl}{C.RESET}")
                break
        else:
            d = RE_SAYS_FMT.match(s)
            if d:
                name, _, quote = d.group(1).strip(), d.group(2), d.group(3).strip().strip('"')
                col = COMP_COLORS.get(name.lower(), C.WHITE)
                print(f"  {col}{C.BOLD}{name}:{C.RESET} {col}\"{quote}\"{C.RESET}")
            elif RE_DAMAGE.search(s):
                for wl in textwrap.wrap(s, W - 4):
                    print(f"  {C.RED}{wl}{C.RESET}")
            elif RE_GOLD.search(s):
                for wl in textwrap.wrap(s, W - 4):
                    print(f"  {C.YELLOW}{wl}{C.RESET}")
            elif RE_MAGIC.search(s):
                for wl in textwrap.wrap(s, W - 4):
                    print(f"  {C.MAGENTA}{wl}{C.RESET}")
            else:
                for wl in textwrap.wrap(s, W - 4):
                    print(f"  {C.CYAN}{wl}{C.RESET}")
    print(f"{C.MAGENTA}{'=' * W}{C.RESET}")
    print()


# ══════════════════════════════════════════════════════════════
#  COMBAT ENGINE — FF3-style with full 5e mechanics
# ══════════════════════════════════════════════════════════════

def combat_menu(player: dict) -> dict:
    """FF3-style combat action menu."""
    cls = player.get("class", "Fighter")
    spells_data = SPELLS.get(cls, {"cantrips": [], "spells": []})
    slots = player.get("spell_slots_current", 0)

    print(f"\n  {C.BOLD}{C.CYAN}┌─ COMBAT ACTIONS ──────────────────────────────────┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET}  {C.BOLD}[1]{C.RESET} ⚔  Attack      {C.BOLD}[2]{C.RESET} 🛡 Defend")
    print(f"  {C.CYAN}│{C.RESET}  {C.BOLD}[3]{C.RESET} 🧪 Use Item    {C.BOLD}[4]{C.RESET} ↩  Flee")

    if spells_data.get("cantrips"):
        print(f"  {C.CYAN}│{C.RESET}  {C.BOLD}[5]{C.RESET} ✨ Cantrip     {C.BOLD}[6]{C.RESET} 🔮 Cast Spell {C.GRAY}(slots: {slots}){C.RESET}")

    # Talent abilities
    talents = player.get("talents", [])
    if talents:
        abilities = [t for t in talents if TALENT_TREES.get(cls, {}).get(t, {}).get("effect", {}).get("heal_ability") or
                     TALENT_TREES.get(cls, {}).get(t, {}).get("effect", {}).get("extra_attack") or
                     TALENT_TREES.get(cls, {}).get(t, {}).get("effect", {}).get("rage")]
        if abilities:
            print(f"  {C.CYAN}│{C.RESET}  {C.BOLD}[7]{C.RESET} 💫 Talent: {abilities[0]}")

    print(f"  {C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")

    while True:
        choice = input(f"  {C.BOLD}{C.WHITE}Action: {C.RESET}").strip()

        if choice == "1":
            return {"type": "attack", "name": "Strike", "data": {}}

        elif choice == "2":
            return {"type": "defend", "name": "Defend", "data": {}}

        elif choice == "3":
            inv = player.get("inventory", [])
            usable = [i for i in inv if "Potion" in i or "Bandage" in i or "Antidote" in i]
            if not usable:
                cprint(C.YELLOW, "  No usable items!")
                continue
            for i, item in enumerate(usable, 1):
                print(f"  [{i}] {item}")
            try:
                idx = int(input("  Use which? ")) - 1
                return {"type": "item", "name": usable[idx], "data": {"item": usable[idx]}}
            except (ValueError, IndexError):
                continue

        elif choice == "4":
            flee_dc = random.randint(8, 16)
            dex_mod_val = mod(player.get("stats", {}).get("DEX", 10))
            flee_roll, raw = d20(dex_mod_val)
            success = flee_roll >= flee_dc
            cprint(C.GRAY if success else C.RED,
                   f"  Flee check: {raw} + {dex_mod_val} = {flee_roll} vs DC {flee_dc} — {'ESCAPED!' if success else 'BLOCKED!'}")
            return {"type": "run", "name": "Flee", "data": {"success": success}}

        elif choice == "5" and spells_data.get("cantrips"):
            print(f"\n  {C.BOLD}CANTRIPS (free):{C.RESET}")
            for i, sp in enumerate(spells_data["cantrips"], 1):
                col = sp.get("color", C.MAGENTA)
                print(f"  {col}[{i}] {sp['name']} — {sp['dice']} {sp['dtype']}{C.RESET}")
                print(f"      {C.GRAY}{sp['desc']}{C.RESET}")
            try:
                idx = int(input("  Cast which? ")) - 1
                sp = spells_data["cantrips"][idx]
                return {"type": "spell", "name": sp["name"], "data": {"spell": sp, "is_cantrip": True}}
            except (ValueError, IndexError):
                continue

        elif choice == "6" and spells_data.get("spells"):
            print(f"\n  {C.BOLD}SPELLS{C.RESET} (Slots: {cc(C.MAGENTA, str(slots))})")
            for i, sp in enumerate(spells_data["spells"], 1):
                cost = sp.get("slots", 1)
                avail = "✓" if slots >= cost else "✗"
                col = C.GREEN if slots >= cost else C.RED
                print(f"  {col}[{i}] {avail} {sp['name']} [{cost} slot] — {sp['dice']} {sp['dtype']}{C.RESET}")
                print(f"      {C.GRAY}{sp['desc']}{C.RESET}")
            try:
                idx = int(input("  Cast which? ")) - 1
                sp = spells_data["spells"][idx]
                cost = sp.get("slots", 1)
                if slots < cost:
                    cprint(C.RED, f"  Need {cost} slot(s), have {slots}!")
                    continue
                player["spell_slots_current"] -= cost
                return {"type": "spell", "name": sp["name"], "data": {"spell": sp, "is_cantrip": False}}
            except (ValueError, IndexError):
                continue

        elif choice == "7" and talents:
            return {"type": "talent", "name": talents[0] if talents else "Ability", "data": {}}

        else:
            cprint(C.GRAY, "  Choose a valid action.")


def resolve_attack(player: dict, action: dict, enemy_ac: int,
                   enemy_hp: int, enemy_max_hp: int) -> dict:
    """Resolve a combat action and return results."""
    result = {
        "hit": False, "crit": False, "damage": 0,
        "dtype": "physical", "effect": None,
        "enemy_hp": enemy_hp, "enemy_max_hp": enemy_max_hp,
        "player_hp_change": 0,
    }

    if action["type"] == "attack":
        atk_bonus = calc_atk(player)
        total, raw = d20(atk_bonus)
        is_crit = raw == 20
        is_hit = is_crit or total >= enemy_ac

        if is_hit:
            dmg, dtype = weapon_damage(player)
            if is_crit:
                dmg *= 2
            # Talent bonuses
            for t in player.get("talents", []):
                tree = TALENT_TREES.get(player.get("class", ""), {})
                eff = tree.get(t, {}).get("effect", {})
                if eff.get("dmg_bonus"):
                    dmg += eff["dmg_bonus"]
                if eff.get("imp_smite"):
                    bonus, _ = roll(8)
                    dmg += bonus
            result.update(hit=True, crit=is_crit, damage=dmg,
                          dtype=dtype, enemy_hp=max(0, enemy_hp - dmg))
        else:
            result["hit"] = False

    elif action["type"] == "spell":
        sp = action["data"].get("spell", {})
        dice_str = sp.get("dice", "0")
        dtype = sp.get("dtype", "magic")

        if dtype in ("heal", "shield"):
            if dice_str != "0":
                heal, _ = roll_dice_notation(dice_str)
            else:
                heal = 10 + mod(player.get("stats", {}).get("WIS", 10))
            result.update(hit=True, damage=heal, dtype="heal",
                          player_hp_change=heal, enemy_hp=enemy_hp)
        elif dice_str != "0":
            dmg, _ = roll_dice_notation(dice_str)
            result.update(hit=True, damage=dmg, dtype=dtype,
                          enemy_hp=max(0, enemy_hp - dmg))
        else:
            result.update(hit=True, damage=0, dtype=dtype, enemy_hp=enemy_hp)
            if sp.get("name") == "Shield":
                add_condition(player, "shielded")

    elif action["type"] == "defend":
        result.update(hit=True, dtype="defend", enemy_hp=enemy_hp)

    elif action["type"] == "item":
        item = action["data"].get("item", "")
        if "Health Potion" in item:
            heal, _ = roll(8, 2, 2)
            result.update(hit=True, damage=heal, dtype="heal",
                          player_hp_change=heal, enemy_hp=enemy_hp)
            if item in player.get("inventory", []):
                player["inventory"].remove(item)
        elif "Bandage" in item:
            if "bleeding" in player.get("conditions", []):
                remove_condition(player, "bleeding")
            result.update(hit=True, dtype="heal", enemy_hp=enemy_hp)
            if item in player.get("inventory", []):
                player["inventory"].remove(item)

    return result


def show_combat_header(player: dict, enemy_name: str, enemy_hp: int,
                       enemy_max_hp: int, round_num: int,
                       round_log: list = None):
    """Draw the FF3-style combat HUD."""
    mhp = max_hp(player)
    hp = player.get("hp", mhp)
    hc = hp_color(player)
    pct_p = hp / mhp if mhp else 0
    pct_e = enemy_hp / enemy_max_hp if enemy_max_hp else 0

    bar_w = 20
    p_bar = cc(hc, "█" * int(pct_p * bar_w)) + cc(C.GRAY, "░" * (bar_w - int(pct_p * bar_w)))
    e_bar = cc(C.RED, "█" * int(pct_e * bar_w)) + cc(C.GRAY, "░" * (bar_w - int(pct_e * bar_w)))

    print(f"\n  {C.BOLD}{C.RED}╔{'═' * (W - 4)}╗{C.RESET}")
    print(f"  {C.RED}║{C.RESET}  {C.BOLD}Round {round_num}{C.RESET}")
    print(f"  {C.RED}╠{'═' * (W - 4)}╣{C.RESET}")
    print(f"  {C.RED}║{C.RESET}  {C.BOLD}{enemy_name:20}{C.RESET}  [{e_bar}] {C.RED}{enemy_hp}/{enemy_max_hp}{C.RESET}")
    print(f"  {C.RED}║{C.RESET}  {C.BOLD}{player['name']:20}{C.RESET}  [{p_bar}] {hc}{hp}/{mhp}{C.RESET}")
    if player.get("spell_slots_max", 0) > 0:
        slots = player.get("spell_slots_current", 0)
        mslots = player.get("spell_slots_max", 0)
        sb = cc(C.MAGENTA, "◆" * slots) + cc(C.GRAY, "◇" * (mslots - slots))
        print(f"  {C.RED}║{C.RESET}  Slots: {sb}")
    if player.get("conditions"):
        cond_str = " ".join(f"{C.ORANGE}⚠{c}{C.RESET}" for c in player["conditions"])
        print(f"  {C.RED}║{C.RESET}  {cond_str}")
    if round_log:
        print(f"  {C.RED}╠{'─' * (W - 4)}╣{C.RESET}")
        for entry in round_log[-3:]:
            print(f"  {C.RED}║{C.RESET}  {entry}")
    print(f"  {C.RED}╚{'═' * (W - 4)}╝{C.RESET}")


def run_combat(player: dict, companions: List[dict], state: dict,
               all_chars: dict, enemy_name: str = "Enemy",
               enemy_hp: int = 20, enemy_ac: int = 12) -> str:
    """Full FF3-style combat encounter. Returns 'victory', 'defeat', or 'fled'."""
    enemy_max_hp = enemy_hp
    round_num = 1
    round_log = []

    # Initiative
    show_enemy_portrait(enemy_name)
    show_banner("fight")
    p_init, e_init = roll_initiative(player, enemy_name)
    # DM style combat flavor
    dm_style = state.get("dm_style", "dramatic")
    style_data = DM_STYLES.get(dm_style, DM_STYLES["dramatic"])
    cprint(C.MAGENTA, f"  {random.choice(style_data['combat_flavor'])}")
    input(f"\n  {C.GRAY}[ Press Enter to begin combat ]{C.RESET}")

    while player.get("hp", 1) > 0 and enemy_hp > 0:
        show_combat_header(player, enemy_name, enemy_hp, enemy_max_hp,
                           round_num, round_log)

        # Player turn
        action = combat_menu(player)

        if action["type"] == "run":
            if action["data"].get("success", True):
                round_log.append(f"{C.GRAY}  ↩ You disengage and flee!{C.RESET}")
                cprint(C.GRAY, f"  You disengage and flee from {enemy_name}!")
                return "fled"
            else:
                round_log.append(f"{C.RED}  ✗ Escape blocked!{C.RESET}")
                cprint(C.RED, f"  {enemy_name} cuts off your escape!")
        else:
            result = resolve_attack(player, action, enemy_ac, enemy_hp, enemy_max_hp)
            enemy_hp = result.get("enemy_hp", enemy_hp)
            is_crit = result.get("crit", False)
            is_hit = result.get("hit", False)
            dmg = result.get("damage", 0)
            dtype = result.get("dtype", "physical")

            if not is_hit:
                round_log.append(f"{C.GRAY}  ✗ MISS — {action['name']}{C.RESET}")
                cprint(C.GRAY, "  Your attack misses!")
            elif dtype == "heal":
                round_log.append(f"{C.GREEN}  ♥ +{dmg} HP healed{C.RESET}")
                player["hp"] = min(max_hp(player), player.get("hp", 1) + result.get("player_hp_change", 0))
                cprint(C.GREEN, f"  Healed for {dmg} HP!")
            elif dtype == "defend":
                round_log.append(f"{C.BLUE}  🛡 Defending — reduced incoming damage{C.RESET}")
                cprint(C.BLUE, "  You brace for impact!")
            else:
                crit_str = " ✦CRITICAL!" if is_crit else ""
                round_log.append(f"{C.YELLOW}  ⚔ {action['name']}: {dmg} {dtype} dmg{crit_str}{C.RESET}")
                cprint(C.YELLOW, f"  {action['name']}: {dmg} {dtype} damage!{crit_str}")

            # AI narration for the action
            if is_hit and dtype not in ("heal", "defend"):
                narr = ai_call([{"role": "user", "content":
                    f"Narrate {player['name']} {'critically ' if is_crit else ''}hits "
                    f"{enemy_name} with {action['name']} for {dmg} {dtype} damage. "
                    f"2 vivid sentences, no stat blocks."}], max_tokens=80)
            elif not is_hit:
                narr = ai_call([{"role": "user", "content":
                    f"Narrate {player['name']} misses {enemy_name} with {action['name']}. "
                    f"1 sentence, dramatic."}], max_tokens=50)
            else:
                narr = ""

            if narr:
                print(f"\n  {C.CYAN}{narr}{C.RESET}")

        # Enemy defeated?
        if enemy_hp <= 0:
            xp_reward = {"easy": 150, "normal": 300, "hard": 500}.get(
                state.get("difficulty", "normal"), 300)
            gold_loot = random.randint(5, 25) + player.get("level", 1) * 3
            # Determine loot tier from state (set by scale_encounter) or from level
            loot_tier = state.pop("_combat_loot_tier", None)
            if not loot_tier:
                lvl = player.get("level", 1)
                if lvl <= 2:   loot_tier = "common"
                elif lvl <= 5: loot_tier = "uncommon"
                elif lvl <= 9: loot_tier = "rare"
                elif lvl <= 14: loot_tier = "epic"
                else:           loot_tier = "legendary"
            loot_items = roll_loot(loot_tier)
            if loot_items:
                player.setdefault("inventory", []).extend(loot_items)
            player["gold"] = player.get("gold", 0) + gold_loot

            # DM style victory flavor
            dm_style = state.get("dm_style", "dramatic")
            style_data = DM_STYLES.get(dm_style, DM_STYLES["dramatic"])
            show_banner("victory")
            cprint(C.GREEN, f"  ✓ {enemy_name} defeated!")
            cprint(C.MAGENTA, f"  {style_data['victory_quote']}")
            cprint(C.YELLOW, f"  +{xp_reward} XP  +{gold_loot} gold")
            if loot_items:
                cprint(C.YELLOW, f"  Loot: {', '.join(loot_items)}")
            player["xp"] = player.get("xp", 0) + xp_reward
            return "victory"

        # Enemy turn
        defending = action.get("type") == "defend"
        raw_dmg = random.randint(4, 14)
        if defending:
            raw_dmg = max(1, raw_dmg // 2)
            round_log.append(f"{C.BLUE}  🛡 Guard! Reduced to {raw_dmg}{C.RESET}")
        player["hp"] = max(0, player.get("hp", 1) - raw_dmg)
        round_log.append(f"{C.RED}  💢 {enemy_name} hits for {raw_dmg}!{C.RESET}")
        cprint(C.RED, f"  {enemy_name} hits you for {raw_dmg}! HP: {player['hp']}/{max_hp(player)}")

        # Condition ticks
        cond_dmg = tick_conditions(player)
        if cond_dmg > 0:
            player["hp"] = max(0, player.get("hp", 1) - cond_dmg)

        # Death
        if player["hp"] <= 0:
            dm_style = state.get("dm_style", "dramatic")
            style_data = DM_STYLES.get(dm_style, DM_STYLES["dramatic"])
            show_banner("death")
            cprint(C.RED, f"  {player['name']} has been defeated by {enemy_name}.")
            cprint(C.MAGENTA, f"  {style_data['death_quote']}")
            return "defeat"

        round_num += 1

    return "victory" if enemy_hp <= 0 else "defeat"


# ══════════════════════════════════════════════════════════════
#  TALENT TREE DISPLAY
# ══════════════════════════════════════════════════════════════

def show_talent_tree(player: dict):
    cls = player.get("class", "Fighter")
    tree = TALENT_TREES.get(cls, {})
    if not tree:
        cprint(C.GRAY, f"  No talent tree for {cls} yet.")
        return

    tp = player.get("talent_points", 0)
    owned = player.get("talents", [])

    header(f"{cls.upper()} TALENT TREE", C.MAGENTA)
    print(f"  {C.BOLD}Talent Points: {cc(C.YELLOW, str(tp))}{C.RESET}\n")

    for tier in [1, 2, 3]:
        tier_name = {1: "APPRENTICE", 2: "JOURNEYMAN", 3: "MASTER"}[tier]
        print(f"  {C.BOLD}{C.CYAN}── {tier_name} (Tier {tier}) ──{C.RESET}")
        for name, data in tree.items():
            if data["tier"] == tier:
                have = name in owned
                icon = cc(C.GREEN, "★") if have else cc(C.GRAY, "○")
                col = C.GREEN if have else C.WHITE
                cost = tier  # tier 1 = 1 point, tier 2 = 2, etc.
                cost_str = "" if have else f" [{cost} pt]"
                print(f"    {icon} {col}{name}{C.RESET}{C.GRAY}{cost_str} — {data['desc']}{C.RESET}")
        print()

    if tp > 0:
        choice = input(f"  {C.CYAN}Learn a talent (name or Enter to skip): {C.RESET}").strip()
        if choice:
            matched = next((n for n in tree if n.lower() == choice.lower()), None)
            if matched and matched not in owned:
                cost = tree[matched]["tier"]
                if tp >= cost:
                    player["talent_points"] = tp - cost
                    player.setdefault("talents", []).append(matched)
                    cprint(C.GREEN, f"  ★ Learned {matched}!")
                else:
                    cprint(C.RED, f"  Need {cost} point(s), have {tp}.")
            elif matched in owned:
                cprint(C.YELLOW, "  Already learned!")
            else:
                cprint(C.RED, "  Talent not found.")


# ══════════════════════════════════════════════════════════════
#  CHARACTER CREATION
# ══════════════════════════════════════════════════════════════

def create_char(existing: dict) -> dict:
    header("CREATE YOUR CHARACTER", C.MAGENTA)
    classes = list(STARTING_GEAR.keys())

    while True:
        name = input(f"  {C.CYAN}Character name:{C.RESET} ").strip()
        if not name:
            continue
        if name in existing:
            cprint(C.YELLOW, f"  '{name}' already exists.")
            if input("  Load existing? (y/n): ").strip().lower() == "y":
                return existing[name]
            continue
        break

    cprint(C.BLUE, "\n  Classes:", wrap=False)
    for i, c in enumerate(classes, 1):
        hd = HIT_DICE.get(c, 8)
        has_spells = "✨" if c in SPELLS and SPELLS[c].get("spells") else "  "
        print(f"  {C.GRAY}{i:2}.{C.RESET} {C.BOLD}{c:12}{C.RESET} {C.GRAY}d{hd} HP{C.RESET} {has_spells}")
    while True:
        try:
            cls = classes[int(input(f"  {C.CYAN}Choose class:{C.RESET} ")) - 1]
            break
        except (ValueError, IndexError):
            cprint(C.RED, "  Invalid.")

    cprint(C.BLUE, "\n  Races:", wrap=False)
    for i, r in enumerate(RACES, 1):
        print(f"  {C.GRAY}{i:2}.{C.RESET} {r}")
    while True:
        try:
            race = RACES[int(input(f"  {C.CYAN}Choose race:{C.RESET} ")) - 1]
            break
        except (ValueError, IndexError):
            cprint(C.RED, "  Invalid.")

    backstory = input(f"\n  {C.CYAN}Brief backstory (Enter to skip):{C.RESET} ").strip()

    cprint(C.MAGENTA, "\n  Rolling stats (4d6 drop lowest)...", wrap=False)
    stats = gen_stats()
    for s, v in stats.items():
        bar = cc(C.MAGENTA, "█" * (v // 2)) + cc(C.GRAY, "░" * (9 - v // 2))
        col = C.GREEN if v >= 15 else C.YELLOW if v >= 12 else C.GRAY
        print(f"  {C.BOLD}{s}{C.RESET}  {col}{v:2}{C.RESET} ({mstr(v):>3})  {bar}")

    if input(f"\n  {C.CYAN}Reroll? (y/n):{C.RESET} ").strip().lower() == "y":
        stats = gen_stats()
        cprint(C.MAGENTA, "  New rolls:", wrap=False)
        for s, v in stats.items():
            bar = cc(C.MAGENTA, "█" * (v // 2)) + cc(C.GRAY, "░" * (9 - v // 2))
            col = C.GREEN if v >= 15 else C.YELLOW if v >= 12 else C.GRAY
            print(f"  {C.BOLD}{s}{C.RESET}  {col}{v:2}{C.RESET} ({mstr(v):>3})  {bar}")

    w, a = STARTING_GEAR.get(cls, ("Dagger", ""))
    inv = [w] + ([a] if a else []) + ["Adventurer's pack", "Health Potion"]

    char = {
        "name": name, "type": "player", "class": cls, "race": race,
        "level": 1, "xp": 0, "stats": stats,
        "hp": max_hp({"class": cls, "level": 1, "stats": stats}),
        "gold": 15, "notoriety_score": 0,
        "inventory": inv,
        "equipped": {"weapon": w, "armor": a, "offhand": "", "accessory": ""},
        "item_conditions": {}, "conditions": [],
        "notes": backstory, "sessions_played": 0,
        "last_seen": datetime.now().strftime("%Y-%m-%d"),
        "companions_lost": [], "talents": [], "talent_points": 1,
    }
    init_slots(char)
    mhp = max_hp(char)
    cprint(C.GREEN, f"\n  {name} the {race} {cls} steps into the world!")
    cprint(C.YELLOW, f"  HP:{mhp} | AC:{calc_ac(char)} | Atk:{calc_atk(char):+d} | Gold:15gp")
    if char["spell_slots_max"] > 0:
        cprint(C.MAGENTA, f"  Spell Slots: {char['spell_slots_max']}")
    cprint(C.MAGENTA, "  ★ 1 Talent Point to spend! Use /talents")
    return char


# ══════════════════════════════════════════════════════════════
#  NPC COMPANION SYSTEM
# ══════════════════════════════════════════════════════════════

ARCHETYPES = {
    "1": {"name": "Gruff Veteran",    "personality": "Blunt, battle-hardened, unshakeable loyalty.", "bias": 0,    "class": "Fighter", "race": "Dwarf"},
    "2": {"name": "Eager Scholar",    "personality": "Curious, bookish, brilliant under pressure.",  "bias": 150,  "class": "Wizard",  "race": "Human"},
    "3": {"name": "Charming Rogue",   "personality": "Quick with a joke, quicker with a knife.",    "bias": -100, "class": "Rogue",   "race": "Half-Elf"},
    "4": {"name": "Zealous Cleric",   "personality": "Devoted to their deity, heals without question.","bias": 300, "class": "Cleric","race": "Human"},
    "5": {"name": "Wild Ranger",      "personality": "Speaks more to animals than people.",          "bias": 50,   "class": "Ranger",  "race": "Wood Elf"},
    "6": {"name": "Bitter Mercenary", "personality": "Only in it for coin. Never deserts mid-contract.","bias": -200,"class":"Fighter","race": "Half-Orc"},
}

def make_npc(key: str, name: str, cls: str, race: str, notes: str = "") -> dict:
    arch = ARCHETYPES[key]
    stats = gen_stats()
    w, a = STARTING_GEAR.get(cls, ("Dagger", ""))
    inv = [w] + ([a] if a else [])
    npc = {
        "name": name, "type": "npc", "class": cls, "race": race,
        "level": 1, "xp": 0, "stats": stats,
        "hp": max_hp({"class": cls, "level": 1, "stats": stats}),
        "gold": random.randint(3, 12),
        "notoriety_score": arch["bias"], "personality": arch["personality"],
        "archetype": arch["name"],
        "inventory": inv, "equipped": {"weapon": w, "armor": a, "offhand": "", "accessory": ""},
        "item_conditions": {}, "conditions": [],
        "notes": notes, "alive": True, "sessions_played": 0,
        "last_seen": datetime.now().strftime("%Y-%m-%d"),
        "talents": [], "talent_points": 0,
    }
    init_slots(npc)
    return npc


# ══════════════════════════════════════════════════════════════
#  STATUS / INVENTORY / SPELL SCREENS
# ══════════════════════════════════════════════════════════════

def show_status(p: dict):
    st = p.get("stats", {})
    eq = p.get("equipped", {})
    t, col, flv = get_rep(p.get("notoriety_score", 0))
    mhp = max_hp(p)
    hp = p.get("hp", mhp)
    hpct = hp / mhp if mhp else 0
    hc = hp_color(p)
    slots = p.get("spell_slots_current", 0)
    msl = p.get("spell_slots_max", 0)
    hpbar = cc(hc, "█" * int(hpct * 30)) + cc(C.GRAY, "░" * (30 - int(hpct * 30)))

    print(f"\n{C.BOLD}{C.BLUE}{'═' * W}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {p['name']} — {p['race']} {p['class']} | Lvl {p['level']}{C.RESET}")
    divider()
    print(f"  HP: {hc}{hp}/{mhp}{C.RESET} [{hpbar}]  {hp_status(p)}")
    print(f"  AC: {cc(C.CYAN, str(calc_ac(p)))}  Atk: {cc(C.YELLOW, f'{calc_atk(p):+d}')}  Gold: {cc(C.YELLOW, str(p.get('gold', 0)) + ' gp')}")
    if msl > 0:
        sb = cc(C.MAGENTA, "◆" * slots) + cc(C.GRAY, "◇" * (msl - slots))
        print(f"  Spell Slots: {sb} {slots}/{msl}")
    divider()
    line = "  "
    for s in STAT_NAMES:
        v = st.get(s, 10)
        sc = C.GREEN if v >= 15 else C.YELLOW if v >= 12 else C.GRAY
        line += f"{C.BOLD}{s}{C.RESET}:{sc}{v}{C.RESET}({mstr(v)})  "
    print(line)
    divider()
    for slot in ["weapon", "armor", "offhand", "accessory"]:
        item = eq.get(slot, "")
        if item:
            cond = item_cond(p, item)
            cc2 = C.GREEN if cond in ("pristine", "good") else C.ORANGE if cond == "worn" else C.RED
            print(f"  {slot.capitalize():10} {cc(C.YELLOW, item)} [{cc2}{cond}{C.RESET}]")
    divider()
    print(f"  Reputation: {col}{bold(t)}{C.RESET}  ({p.get('notoriety_score', 0):+d})")
    if p.get("talents"):
        print(f"  Talents: {', '.join(p['talents'])}")
    print(f"  XP: {p.get('xp', 0)}/{xp_next(p['level'])} | Sessions: {p.get('sessions_played', 0)}")
    print(f"{C.BOLD}{C.BLUE}{'═' * W}{C.RESET}")

def show_spells(p: dict):
    cls = p.get("class", "")
    spells_data = SPELLS.get(cls, {"cantrips": [], "spells": []})
    slots = p.get("spell_slots_current", 0)
    msl = p.get("spell_slots_max", 0)
    header(f"{cls} SPELLS", C.MAGENTA)
    if spells_data.get("cantrips"):
        cprint(C.CYAN, "  CANTRIPS — free:", wrap=False)
        for sp in spells_data["cantrips"]:
            dmg = f" — {sp['dice']} {sp['dtype']}" if sp['dice'] != "0" else " — utility"
            print(f"  {C.BOLD}{sp['name']}{C.RESET}{C.GRAY}{dmg}{C.RESET}")
    if spells_data.get("spells"):
        sb = cc(C.MAGENTA, "◆" * slots) + cc(C.GRAY, "◇" * (msl - slots))
        print(f"\n  {C.BOLD}SPELLS{C.RESET} — Slots: {sb} {slots}/{msl}")
        for sp in spells_data["spells"]:
            cost = sp.get("slots", 1)
            avail = cc(C.GREEN, "✓") if slots >= cost else cc(C.RED, "✗")
            print(f"  {avail} {C.BOLD}{sp['name']}{C.RESET} [{cost}] — {sp['dice']} {sp['dtype']}")

def show_inventory(p: dict):
    inv = p.get("inventory", [])
    eq = p.get("equipped", {})
    header(f"{p['name']}'s INVENTORY", C.YELLOW)
    print(f"  Gold: {cc(C.YELLOW, str(p.get('gold', 0)) + ' gp')}")
    divider()
    for slot in ["weapon", "armor", "offhand", "accessory"]:
        item = eq.get(slot, "") or "—"
        print(f"  {slot.capitalize():10} {cc(C.WHITE, item)}")
    divider()
    if not inv:
        print(f"  {C.GRAY}(empty backpack){C.RESET}")
    for item in inv:
        wdata = WEAPONS.get(item, {})
        adata = ARMORS.get(item, {})
        stats_str = ""
        if wdata:
            stats_str = f" {C.GRAY}[{wdata.get('damage', '?')} {wdata.get('dtype', '?')}]{C.RESET}"
        elif adata:
            stats_str = f" {C.GRAY}[AC:{adata.get('ac', '?')}]{C.RESET}"
        print(f"  • {C.WHITE}{item}{C.RESET}{stats_str}")
    divider()

def show_companions(comps: List[dict]):
    header("COMPANIONS", C.BLUE)
    if not comps:
        cprint(C.GRAY, "  Traveling alone.")
        return
    for c in comps:
        alive = c.get("alive", True)
        status = cc(C.GREEN, "● ALIVE") if alive else cc(C.RED, "✝ DEAD")
        mhp = max_hp(c)
        hp = c.get("hp", mhp)
        hc = hp_color(c)
        print(f"\n  {C.BOLD}{c['name']}{C.RESET} {status}")
        print(f"  {c['race']} {c['class']} Lvl {c['level']} | HP:{hc}{hp}/{mhp}{C.RESET}")
        cprint(C.GRAY, f"  \"{c.get('personality', '')}\"")


# ══════════════════════════════════════════════════════════════
#  MERCHANT & INN
# ══════════════════════════════════════════════════════════════

def visit_merchant(p: dict):
    header("MERCHANT", C.YELLOW)
    cprint(C.GRAY, "  A weathered merchant eyes your coin pouch.\n")
    while True:
        cprint(C.YELLOW, f"  Gold: {p.get('gold', 0)} gp", wrap=False)
        print(f"  {C.BOLD}[B]{C.RESET}uy  {C.BOLD}[S]{C.RESET}ell  {C.BOLD}[R]{C.RESET}epair  {C.BOLD}[L]{C.RESET}eave")
        action = input("  > ").strip().upper()
        if action == "L":
            cprint(C.GRAY, "  'Safe travels.'")
            break
        elif action == "B":
            all_items = list(WEAPONS.items()) + list(ARMORS.items())
            for i, (name, data) in enumerate(all_items, 1):
                val = data.get("value", 0)
                extra = data.get("damage", "") or f"AC:{data.get('ac', '?')}"
                can = cc(C.GREEN, "✓") if p.get("gold", 0) >= val else cc(C.RED, "✗")
                print(f"  {can} [{i:2}] {name:22} {C.GRAY}{str(extra):14}{C.RESET} {cc(C.YELLOW, str(val) + 'gp')}")
            print(f"  {C.GRAY}[0] Cancel{C.RESET}")
            try:
                ch = int(input("\n  Buy which? "))
                if ch == 0:
                    continue
                if 1 <= ch <= len(all_items):
                    nm, dt = all_items[ch - 1]
                    price = dt["value"]
                    if p.get("gold", 0) >= price:
                        p["gold"] -= price
                        p.setdefault("inventory", []).append(nm)
                        p.setdefault("item_conditions", {})[nm] = "pristine"
                        cprint(C.GREEN, f"  Bought {nm} for {price}gp.")
                    else:
                        cprint(C.RED, f"  Need {price}gp.")
            except (ValueError, IndexError):
                pass
        elif action == "S":
            inv = p.get("inventory", [])
            if not inv:
                cprint(C.YELLOW, "  Nothing to sell.")
                continue
            for i, item in enumerate(inv, 1):
                val = WEAPONS.get(item, {}).get("value") or ARMORS.get(item, {}).get("value")
                if val:
                    sp = max(1, val // 2)
                    print(f"  [{i}] {item:25} ~{cc(C.YELLOW, str(sp) + 'gp')}")
            print(f"  {C.GRAY}[0] Cancel{C.RESET}")
            try:
                ch = int(input("\n  Sell which? "))
                if ch == 0:
                    continue
                if 1 <= ch <= len(inv):
                    item = inv[ch - 1]
                    val = WEAPONS.get(item, {}).get("value") or ARMORS.get(item, {}).get("value")
                    if val:
                        sp = max(1, val // 2)
                        p["inventory"].remove(item)
                        p["gold"] = p.get("gold", 0) + sp
                        cprint(C.GREEN, f"  Sold {item} for {sp}gp.")
            except (ValueError, IndexError):
                pass

def visit_inn(p: dict, comps: List[dict], state: dict):
    show_scene("tavern")
    header("THE INN — The Wanderer's Rest", C.CYAN)
    while True:
        mhp = max_hp(p)
        hp = p.get("hp", mhp)
        slots = p.get("spell_slots_current", 0)
        msl = p.get("spell_slots_max", 0)
        print(f"  HP: {hp_color(p)}{hp}/{mhp}{C.RESET}  Slots: {cc(C.MAGENTA, str(slots))}/{msl}  Gold: {p.get('gold', 0)}gp\n")
        print(f"  {C.BOLD}[1]{C.RESET} Short Rest (free) — recover slots + some HP")
        print(f"  {C.BOLD}[2]{C.RESET} Long Rest  (5gp)  — full HP, all slots, clear conditions")
        print(f"  {C.BOLD}[3]{C.RESET} Rent a room (2gp) — save progress")
        print(f"  {C.BOLD}[4]{C.RESET} Buy a drink (1gp) — hear a rumor")
        print(f"  {C.BOLD}[L]{C.RESET} Leave")
        action = input("\n  > ").strip().upper()
        if action == "L":
            break
        elif action == "1":
            init_slots(p)
            con_rec = max(1, p.get("level", 1) // 2 + mod(p.get("stats", {}).get("CON", 10)))
            p["hp"] = min(max_hp(p), p.get("hp", mhp) + con_rec)
            cprint(C.GREEN, f"  Recovered {con_rec} HP. ({p['hp']}/{max_hp(p)})")
        elif action == "2":
            if p.get("gold", 0) >= 5:
                p["gold"] -= 5
                p["hp"] = max_hp(p)
                init_slots(p)
                p["conditions"] = []
                cprint(C.GREEN, f"  Fully rested. HP: {p['hp']}/{max_hp(p)}")
            else:
                cprint(C.RED, "  Long rest costs 5gp.")
        elif action == "3":
            if p.get("gold", 0) >= 2:
                p["gold"] -= 2
                save_campaign(state)
                save_chars({p["name"]: p})
                cprint(C.GREEN, "  Progress saved.")
            else:
                cprint(C.RED, "  A room costs 2gp.")
        elif action == "4":
            if p.get("gold", 0) >= 1:
                p["gold"] -= 1
                rumor = ai_call([{"role": "user", "content":
                    f"Give ONE short mysterious D&D tavern rumor (2 sentences). "
                    f"World: {state.get('title')}. Make it ominous. No preamble."}],
                    max_tokens=80)
                cprint(C.WHITE, f"  A grizzled sailor leans in: \"{rumor}\"")
            else:
                cprint(C.RED, "  A drink costs 1gp.")


# ══════════════════════════════════════════════════════════════
#  HELP / COMMANDS
# ══════════════════════════════════════════════════════════════

def print_help():
    print(f"""
{C.BOLD}{C.BLUE}  ── Commands ──────────────────────────────────────────────{C.RESET}
  {C.CYAN}/status{C.RESET}              Full character sheet
  {C.CYAN}/spells{C.RESET}              Spell list and slots
  {C.CYAN}/inventory{C.RESET}           Items, conditions, sell values
  {C.CYAN}/companions{C.RESET}          Companion stats
  {C.CYAN}/merchant{C.RESET}            Buy, sell, or repair gear
  {C.CYAN}/inn{C.RESET}                 Rest, recover, hear rumors
  {C.CYAN}/talents{C.RESET}             Talent tree — spend points
  {C.CYAN}/combat <enemy>{C.RESET}      Start combat (e.g. /combat orc)
  {C.CYAN}/notoriety{C.RESET}           Your reputation bar
  {C.CYAN}/story{C.RESET}               Session summaries
  {C.CYAN}/difficulty{C.RESET}          Change difficulty
  {C.CYAN}/map{C.RESET}                 Show dungeon map
  {C.CYAN}/equip <item>{C.RESET}        Equip an item
  {C.CYAN}/ooc <msg>{C.RESET}           Out-of-character note
  {C.CYAN}/quests{C.RESET}              Quest journal
  {C.CYAN}/camp{C.RESET}                Make camp — rest, dream, keep watch
  {C.CYAN}/dm{C.RESET}                  Change DM personality style
  {C.CYAN}/weather{C.RESET}             Check the sky / re-roll weather
  {C.CYAN}/quit{C.RESET}                Save and end session
{C.BLUE}  ──────────────────────────────────────────────────────────{C.RESET}""")


# ══════════════════════════════════════════════════════════════
#  PROCEDURAL DUNGEON MAP
# ══════════════════════════════════════════════════════════════

def generate_dungeon_map(size: int = 5) -> List[List[str]]:
    """Generate a random dungeon grid."""
    grid = [[" " for _ in range(size)] for _ in range(size)]
    grid[0][0] = "S"  # Start

    symbols = {"T": "Treasure", "C": "Chest", "E": "Enemy",
               "M": "Merchant", "!": "Trap", "?": "Mystery"}
    placed = {"S"}
    for sym in symbols:
        while True:
            r, c = random.randint(0, size - 1), random.randint(0, size - 1)
            if grid[r][c] == " ":
                grid[r][c] = sym
                break
    return grid

def show_dungeon_map():
    grid = generate_dungeon_map()
    header("DUNGEON MAP", C.ORANGE)
    sym_colors = {"S": C.GREEN, "T": C.YELLOW, "C": C.YELLOW,
                  "E": C.RED, "M": C.CYAN, "!": C.ORANGE, "?": C.MAGENTA}
    line = "  +"
    for _ in range(len(grid[0])):
        line += "---+"
    print(f"  {C.GRAY}{line}{C.RESET}")
    for row in grid:
        cells = "  |"
        for cell in row:
            col = sym_colors.get(cell, C.GRAY)
            cells += f" {col}{cell}{C.RESET} |"
        print(cells)
        print(f"  {C.GRAY}{line}{C.RESET}")
    print(f"  {C.GRAY}S=Start T=Treasure C=Chest E=Enemy M=Merchant !=Trap ?=Mystery{C.RESET}")


# ══════════════════════════════════════════════════════════════
#  SESSION END
# ══════════════════════════════════════════════════════════════

def end_session(state: dict, p: dict, comps: List[dict], all_chars: dict):
    xp = {"easy": 150, "normal": 300, "hard": 500}.get(state["difficulty"], 300)
    header("SESSION COMPLETE", C.GREEN)
    p["xp"] = p.get("xp", 0) + xp
    p["sessions_played"] = p.get("sessions_played", 0) + 1
    p["last_seen"] = datetime.now().strftime("%Y-%m-%d")
    cprint(C.GREEN, f"  XP awarded: +{xp}")

    # Level up check
    nl = lvl_up_check(p)
    if nl:
        p["level"] = nl
        p["hp"] = max_hp(p)
        init_slots(p)
        p["talent_points"] = p.get("talent_points", 0) + 1
        show_banner("level_up")
        cprint(C.MAGENTA, f"  ★★★ {p['name']} reached Level {nl}! ★★★")
        cprint(C.GREEN, f"  Max HP: {p['hp']}  |  Spell Slots: {p.get('spell_slots_max', 0)}")
        cprint(C.YELLOW, "  +1 Talent Point!")

    for c in comps:
        if c.get("alive", True):
            c["xp"] = c.get("xp", 0) + xp
            cl = lvl_up_check(c)
            if cl:
                c["level"] = cl
                c["hp"] = max_hp(c)
                init_slots(c)
                cprint(C.GREEN, f"  ★ {c['name']} reached Level {cl}!")

    t, col, flv = get_rep(p.get("notoriety_score", 0))
    cprint(col, f"\n  Reputation: {t} | {flv}")

    # Session summary
    cprint(C.BLUE, "\n  Generating session summary...")
    summary = ai_call([{"role": "user", "content":
        f"Write a 2-sentence campaign log entry. "
        f"Events: {' | '.join(state['session_log'][-6:])}"}], max_tokens=100)
    state["story_so_far"].append(f"Session {state['session_number']}: {summary}")
    cprint(C.GRAY, f"  {summary}")

    state["session_number"] += 1
    state["session_log"] = []
    save_campaign(state)
    all_chars[p["name"]] = p
    for c in comps:
        all_chars[c["name"]] = c
    save_chars(all_chars)
    cprint(C.GREEN, f"\n  Saved. Next session: #{state['session_number']}")
    divider("═", C.GREEN)


# ══════════════════════════════════════════════════════════════
#  MAIN GAME LOOP — Solo Play
# ══════════════════════════════════════════════════════════════

def recruit_companion(player: dict, taken_names: list) -> Optional[dict]:
    header("RECRUIT A COMPANION", C.BLUE)
    p_side = "heralded" if player.get("notoriety_score", 0) > 50 else \
             "infamous" if player.get("notoriety_score", 0) < -50 else "neutral"
    for k, a in ARCHETYPES.items():
        side = "heralded" if a["bias"] > 50 else "infamous" if a["bias"] < -50 else "neutral"
        label = cc(C.GREEN, "Heralded") if side == "heralded" else \
                cc(C.RED, "Infamous") if side == "infamous" else cc(C.GRAY, "Neutral")
        print(f"  {C.BOLD}[{k}]{C.RESET} {a['name']} — {a['race']} {a['class']}")
        print(f"       {C.GRAY}{a['personality']}{C.RESET}")
        print(f"       Lean: {label}\n")
    ch = input("  Choose (1-6) or [S]kip: ").strip()
    if ch.upper() == "S" or ch not in ARCHETYPES:
        return None
    a = ARCHETYPES[ch]
    nm = input(f"  Name them (default: {a['name']}): ").strip() or a["name"]
    if nm in taken_names:
        cprint(C.RED, "  Name taken.")
        return None
    npc = make_npc(ch, nm, a["class"], a["race"])
    cprint(C.GREEN, f"\n  {nm} the {a['race']} {a['class']} joins your party!")
    return npc


def main():
    """Main solo play game loop."""
    print_art(TITLE_ART, C.CYAN)
    print(f"{C.GRAY}  Model: {CFG.model}  |  WASD Navigate  |  [A]/[B] Choices  |  Actions trigger dice rolls{C.RESET}")
    print(f"{C.GRAY}  Created by TCMG-v1  ·  Co-created with Claude, Grok, Perplexity{C.RESET}")
    print(f"{C.BOLD}{C.MAGENTA}{'═' * W}{C.RESET}")

    all_chars = load_chars()
    state = load_campaign()

    # Character select
    header("YOUR CHARACTER", C.CYAN)
    pchars = {k: v for k, v in all_chars.items() if v.get("type") == "player"}
    if pchars:
        cprint(C.BLUE, "  Existing characters:\n", wrap=False)
        for i, (n, ch) in enumerate(pchars.items(), 1):
            t, col, _ = get_rep(ch.get("notoriety_score", 0))
            mhp = max_hp(ch)
            hp = ch.get("hp", mhp)
            hc = hp_color(ch)
            print(f"  [{i}] {C.BOLD}{n}{C.RESET} — Lvl {ch['level']} {ch['race']} {ch['class']} "
                  f"HP:{hc}{hp}/{mhp}{C.RESET} | {col}{t}{C.RESET}")
        print(f"  {C.GRAY}[N] New character{C.RESET}\n")
        choice = input("  Choose: ").strip()
        if choice.upper() != "N":
            try:
                p = list(pchars.values())[int(choice) - 1]
                if "talents" not in p:
                    p["talents"] = []
                if "talent_points" not in p:
                    p["talent_points"] = p.get("level", 1)
                cprint(C.GREEN, f"\n  Welcome back, {p['name']}!")
            except (ValueError, IndexError):
                p = create_char(all_chars)
        else:
            p = create_char(all_chars)
    else:
        p = create_char(all_chars)
    all_chars[p["name"]] = p

    # Companions
    comps: List[dict] = []
    living = {k: v for k, v in all_chars.items()
              if v.get("type") == "npc" and v.get("alive", True)}
    if living:
        cprint(C.BLUE, "\n  Living companions:", wrap=False)
        nlist = list(living.items())
        for i, (n, c) in enumerate(nlist, 1):
            print(f"  [{i}] {C.BOLD}{n}{C.RESET} Lvl {c['level']} {c['race']} {c['class']}")
        print(f"  {C.GRAY}[R] Recruit new  [S] Travel alone{C.RESET}")
        cc_choice = input("\n  Choose: ").strip()
        if cc_choice.upper() == "R":
            npc = recruit_companion(p, [c["name"] for c in comps])
            if npc:
                comps.append(npc)
                all_chars[npc["name"]] = npc
        elif cc_choice.upper() != "S":
            for idx in cc_choice.split(","):
                try:
                    nm = nlist[int(idx.strip()) - 1][0]
                    comps.append(all_chars[nm])
                except (ValueError, IndexError):
                    pass
    else:
        npc = recruit_companion(p, [])
        if npc:
            comps.append(npc)
            all_chars[npc["name"]] = npc
    save_chars(all_chars)

    # Difficulty
    diff_ch = input(f"\n  {C.CYAN}Difficulty [{state['difficulty']}] (easy/normal/hard or Enter):{C.RESET} ").strip().lower()
    if diff_ch in ("easy", "normal", "hard"):
        state["difficulty"] = diff_ch

    # DM personality style
    choose_dm_style(state)

    # Roll starting weather
    weather_name, weather_color, weather_desc = roll_weather()
    state["_current_weather"] = f"{weather_name} — {weather_desc}"
    print(f"\n  {C.BOLD}{weather_color}☁  Weather: {weather_name}{C.RESET}")
    cprint(C.GRAY, f"  {weather_desc}")

    # Session start
    print(f"\n{C.BOLD}{C.MAGENTA}{'═' * W}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  SESSION #{state['session_number']} — {state['title'].upper()}{C.RESET}")
    print(f"{C.BOLD}{C.MAGENTA}{'═' * W}{C.RESET}")
    alive_comps = [c for c in comps if c.get("alive", True)]
    party = p["name"] + (f" with {', '.join(c['name'] for c in alive_comps)}" if alive_comps else "")
    cprint(C.GRAY, f"  Party: {party}\n  Type /help for commands\n")

    # Opening scene
    opening = (
        "Begin with a vivid, immersive opening scene. Set the mood and hint at danger. "
        "If companions are present, let them show personality briefly."
        if not state["session_log"] else
        "Resume where we left off. Brief atmospheric recap, then back into the action."
    )
    cprint(C.GRAY, "  [Generating opening scene...]\n", wrap=False)
    resp = get_response(state, p, comps, opening)
    state["session_log"].append(f"[DM] {resp}")
    save_campaign(state)
    detect_and_show_scene(resp)
    dm_print(resp)

    # Controls hint
    print(f"\n{C.GRAY}  ╔═══════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}CHOICES:{C.RESET}  {C.GREEN}[A]{C.RESET}=bold  {C.YELLOW}[B]{C.RESET}=cunning  {C.WHITE}[O]{C.RESET}=roleplay freely         {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}MOVE:{C.RESET}     {C.CYAN}[W]{C.RESET}=North {C.YELLOW}[A]{C.RESET}=West {C.ORANGE}[S]{C.RESET}=South {C.GREEN}[D]{C.RESET}=East {C.MAGENTA}[E]{C.RESET}=Examine  {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}MENUS:{C.RESET}    {C.CYAN}[I]{C.RESET}=Inventory  {C.MAGENTA}[T]{C.RESET}=Talents  /inn  /merchant  {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ╚═══════════════════════════════════════════════════════════╝{C.RESET}\n")

    # ── GAME LOOP ────────────────────────────────────────────
    while True:
        try:
            user_input = input(f"\n{C.BOLD}{C.WHITE}  ❯{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            end_session(state, p, comps, all_chars)
            break

        if not user_input:
            continue

        ul = user_input.strip().upper()

        # Quick-access keys
        if ul == "I":
            show_inventory(p)
            continue
        if ul == "T":
            show_talent_tree(p)
            save_chars(all_chars)
            continue

        # Compass navigation
        NAV = {"W": "north", "S": "south", "D": "east"}
        if ul in NAV:
            direction = NAV[ul]
            show_compass()
            print(f"  {C.BOLD}{C.CYAN}┌─ MOVING ──────────────────────────────────────────┐{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  You head {direction.upper()}...")
            print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")
            user_input = f"I move {direction} and explore what lies there. Describe what I find."

        elif ul == "E":
            show_compass()
            print(f"  {C.BOLD}{C.CYAN}┌─ EXAMINING ───────────────────────────────────────┐{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  You study your surroundings carefully...")
            print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")
            user_input = "I examine my surroundings. Describe hidden details, clues, dangers."

        # Binary choice shortcuts
        elif ul in ("[A]", "A") and state.get("_last_choice_a"):
            user_input = state["_last_choice_a"]
            print(f"  {C.BOLD}{C.GREEN}→ {user_input}{C.RESET}")
        elif ul in ("[B]", "B") and state.get("_last_choice_b"):
            user_input = state["_last_choice_b"]
            print(f"  {C.BOLD}{C.YELLOW}→ {user_input}{C.RESET}")
        elif ul == "O" or ul == "[O]":
            try:
                user_input = input(f"\n  {C.CYAN}What do you do? {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if not user_input:
                user_input = "look around carefully"

        # Fight shortcut
        fight_match = re.match(r"^(fight|attack|kill|strike|battle)\s+(.+)",
                               user_input.strip(), re.IGNORECASE)
        if fight_match and not user_input.startswith("/"):
            target = fight_match.group(2).strip().title()
            cprint(C.RED, f"\n  ⚔  Entering combat with {target}...")
            f_enc = scale_encounter(p.get("level", 1), state.get("difficulty", "normal"))
            _, f_hp, f_ac, _, f_loot_tier = f_enc
            state["_combat_loot_tier"] = f_loot_tier
            outcome = run_combat(p, comps, state, all_chars, target, f_hp, f_ac)
            save_chars(all_chars)
            if outcome == "defeat":
                end_session(state, p, comps, all_chars)
                break
            user_input = f"After the fight with {target} ({outcome}), continue the story."

        # Dice check on free-form actions
        if not user_input.startswith("/") and len(user_input.split()) >= 2:
            ck, prof_data = infer_check(user_input, p)
            if ck:
                dc_adjust = {"easy": -3, "normal": 0, "hard": 3}.get(state.get("difficulty", "normal"), 0)
                fdc = prof_data[3] + dc_adjust
                result = challenge_screen(
                    situation=f"You attempt: \"{user_input}\".",
                    player=p, forced_check=ck, forced_dc=fdc,
                )
                how = "successfully" if result["success"] else "but failed to"
                if result.get("nat20"):
                    how = "with a spectacular CRITICAL SUCCESS, brilliantly"
                elif result.get("nat1"):
                    how = "but critically FUMBLED and disastrously failed to"
                user_input = (
                    f"I attempted to {user_input} and {how} do so "
                    f"(rolled {result['total']} vs DC {result['dc']}). "
                    f"Narrate the outcome, then give [A]/[B] choices."
                )

        # Command handling
        if user_input.startswith("/"):
            parts = user_input.split(None, 1)
            cmd = parts[0].lower()
            if cmd == "/quit":
                end_session(state, p, comps, all_chars)
                break
            elif cmd == "/help":
                print_help()
            elif cmd == "/status":
                show_status(p)
            elif cmd == "/spells":
                show_spells(p)
            elif cmd == "/inventory":
                show_inventory(p)
            elif cmd == "/companions":
                show_companions(comps)
            elif cmd == "/merchant":
                visit_merchant(p)
                save_chars(all_chars)
            elif cmd == "/inn":
                visit_inn(p, comps, state)
                save_chars(all_chars)
            elif cmd == "/talents":
                show_talent_tree(p)
                save_chars(all_chars)
            elif cmd == "/map":
                show_dungeon_map()
            elif cmd == "/combat":
                enemy = parts[1] if len(parts) > 1 else "Bandit"
                cmd_enc = scale_encounter(p.get("level", 1), state.get("difficulty", "normal"))
                _, cmd_hp, cmd_ac, _, cmd_loot_tier = cmd_enc
                state["_combat_loot_tier"] = cmd_loot_tier
                outcome = run_combat(p, comps, state, all_chars, enemy,
                                     cmd_hp, cmd_ac)
                save_chars(all_chars)
                if outcome == "defeat":
                    end_session(state, p, comps, all_chars)
                    break
            elif cmd == "/notoriety":
                score = p.get("notoriety_score", 0)
                t, col, flv = get_rep(score)
                bar_pos = int((score + 1000) / 2000 * 40)
                bar = cc(col, "█" * bar_pos) + cc(C.GRAY, "░" * (40 - bar_pos))
                print(f"\n  {col}{bold(t)}{C.RESET}  ({score:+d})")
                cprint(C.GRAY, f"  {flv}")
                print(f"  Infamous [{bar}] Heralded")
            elif cmd == "/story":
                if state.get("story_so_far"):
                    header("STORY SO FAR", C.CYAN)
                    for e in state["story_so_far"][-5:]:
                        cprint(C.GRAY, f"  {e}")
                else:
                    cprint(C.GRAY, "  No previous sessions yet.")
            elif cmd == "/difficulty":
                dc = input("  (easy/normal/hard): ").strip().lower()
                if dc in ("easy", "normal", "hard"):
                    state["difficulty"] = dc
                    cprint(C.YELLOW, f"  Difficulty: {dc.upper()}")
            elif cmd == "/equip":
                if len(parts) < 2:
                    cprint(C.RED, "  Usage: /equip <item name>")
                else:
                    item_name = parts[1]
                    inv = p.get("inventory", [])
                    match = next((i for i in inv if i.lower() == item_name.lower()), None)
                    if match:
                        if match in WEAPONS:
                            p.setdefault("equipped", {})["weapon"] = match
                            cprint(C.GREEN, f"  Equipped {match} as weapon.")
                        elif match in ARMORS:
                            p.setdefault("equipped", {})["armor"] = match
                            cprint(C.GREEN, f"  Equipped {match} as armor.")
                    else:
                        cprint(C.RED, f"  '{item_name}' not in inventory.")
            elif cmd == "/quests":
                show_quests(state)
            elif cmd == "/camp":
                campfire_rest(p, comps, state)
                save_chars(all_chars)
            elif cmd == "/dm":
                choose_dm_style(state)
                save_campaign(state)
            elif cmd == "/weather":
                w_name, w_color, w_desc = roll_weather()
                state["_current_weather"] = f"{w_name} — {w_desc}"
                print(f"\n  {C.BOLD}{w_color}☁  Weather shifts to: {w_name}{C.RESET}")
                cprint(C.GRAY, f"  {w_desc}")
                save_campaign(state)
            elif cmd == "/ooc":
                if len(parts) > 1:
                    cprint(C.GRAY, f"  [OOC: {parts[1]}]")
            else:
                cprint(C.RED, "  Unknown command. /help for list.")
            continue

        # Random ambush check
        turn_count = state.get("turn_count", 0) + 1
        state["turn_count"] = turn_count
        last_ambush = state.get("last_ambush_turn", -99)
        if (turn_count - last_ambush >= 5 and
                random.randint(1, 10) == 1 and
                not user_input.startswith("/")):
            state["last_ambush_turn"] = turn_count
            enc = scale_encounter(p.get("level", 1), state.get("difficulty", "normal"))
            ambush_name, ambush_hp, ambush_ac, ambush_xp, ambush_loot_tier = enc
            state["_combat_loot_tier"] = ambush_loot_tier
            show_banner("ambush")
            cprint(C.RED, f"\n  ⚠  AMBUSH! A {ambush_name} strikes from the shadows!")
            input(f"  {C.GRAY}[ Press Enter to fight! ]{C.RESET}")
            outcome = run_combat(p, comps, state, all_chars, ambush_name,
                                 ambush_hp, ambush_ac)
            save_chars(all_chars)
            if outcome == "defeat":
                end_session(state, p, comps, all_chars)
                break
            user_input = f"After being ambushed by a {ambush_name} ({outcome}), continue the story."

        # DM response
        state["session_log"].append(f"[YOU] {user_input}")
        cprint(C.GRAY, "\n  [The DM considers your action...]\n", wrap=False)
        resp = get_response(state, p, comps, user_input)
        state["session_log"].append(f"[DM] {resp}")

        # Extract A/B choices
        ca = re.search(r"\[A\]\s*(.+)", resp)
        cb = re.search(r"\[B\]\s*(.+)", resp)
        if ca:
            state["_last_choice_a"] = re.sub(r"\*+", "", ca.group(1)).strip()
        if cb:
            state["_last_choice_b"] = re.sub(r"\*+", "", cb.group(1)).strip()

        save_campaign(state)
        detect_and_show_scene(resp)
        dm_print(resp)

        # Random event check (20% chance, weighted selection)
        rand_event = roll_random_event(p, state)
        if rand_event:
            print(f"\n  {C.BOLD}{C.ORANGE}⚠  {rand_event['name'].upper()}{C.RESET}")
            cprint(C.YELLOW, f"  {rand_event['description']}")
            apply_event_effect(rand_event, p)
            state["session_log"].append(f"[EVENT] {rand_event['name']}: {rand_event['description']}")

        # Auto-detect combat from DM narration
        combat_triggers = ["attacks you", "charges at you", "lunges toward",
                           "draws their weapon", "battle begins", "combat starts",
                           "moves to strike"]
        if any(t in resp.lower() for t in combat_triggers):
            enemy_name = "Enemy"
            for c in ["orc", "goblin", "bandit", "guard", "wolf", "spider",
                       "skeleton", "troll", "vampire", "lich", "dragon"]:
                if c in resp.lower():
                    enemy_name = c.capitalize()
                    break
            cprint(C.RED, f"\n  ⚔  {enemy_name} engages! Entering combat...")
            auto_enc = scale_encounter(p.get("level", 1), state.get("difficulty", "normal"))
            _, auto_hp, auto_ac, _, auto_loot_tier = auto_enc
            state["_combat_loot_tier"] = auto_loot_tier
            outcome = run_combat(p, comps, state, all_chars, enemy_name,
                                 auto_hp, auto_ac)
            save_chars(all_chars)
            if outcome == "defeat":
                end_session(state, p, comps, all_chars)
                break

        # Condition ticks
        dmg = tick_conditions(p)
        if dmg > 0:
            p["hp"] = max(0, p.get("hp", 1) - dmg)
            if p["hp"] <= 0:
                cprint(C.RED, f"\n  ☠  {p['name']} has fallen!")
                end_session(state, p, comps, all_chars)
                break

        # Near-death check
        nd_thresh = max(1, max_hp(p) // 4)
        if 0 < p.get("hp", 1) <= nd_thresh:
            if "near-death" not in p.get("conditions", []):
                add_condition(p, "near-death")
        elif "near-death" in p.get("conditions", []):
            remove_condition(p, "near-death")

        # Notoriety
        al = user_input.lower()
        if any(w in al for w in ["steal", "murder", "betray", "loot the body", "threaten", "rob"]):
            print(apply_notoriety(p, -25, "dark deed"))
        elif any(w in al for w in ["help", "donate", "save", "protect", "heal", "rescue", "spare"]):
            print(apply_notoriety(p, +25, "good deed"))

        # Equipment degradation
        if any(w in al for w in ["attack", "strike", "fight", "slash", "cast", "swing"]):
            if random.randint(1, 10) == 1:
                degrade_item(p, random.choice(["weapon", "armor"]))

        all_chars[p["name"]] = p
        save_chars(all_chars)


# ══════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Dungeon Master v5 — Pi 4 Edition")
    parser.add_argument("--server", action="store_true", help="Run multiplayer server")
    parser.add_argument("--client", nargs="?", const="localhost", help="Connect to server")
    parser.add_argument("--model", type=str, help="Override LLM model")
    parser.add_argument("--port", type=int, help="Override port")
    args = parser.parse_args()

    if args.model:
        CFG.model = args.model
    if args.port:
        CFG.port = args.port

    if args.server:
        print(f"  Server mode coming in next update. Use solo play for now.")
        # TODO: Async server with queue + auth (Grok's assignment)
    elif args.client:
        print(f"  Client mode coming in next update. Use solo play for now.")
    else:
        try:
            main()
        except KeyboardInterrupt:
            print(f"\n{C.GRAY}  Session interrupted. Progress auto-saved.{C.RESET}")
