# 🎲 AI Dungeon Master — Fully Local, Terminal-Native D&D

> *A complete D&D 5e adventure engine powered by Ollama + Mistral. Runs on your own hardware. No subscriptions. No cloud. No limits.*

```
  ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ███████╗ ██████╗
  ██╔══██╗██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗
  ██║  ██║██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██║   ██║
  ██║  ██║██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██║   ██║
  ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝███████╗╚██████╔╝
  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝

      ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗
      ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
      ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
      ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
      ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
      ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
```

**By [Icycereal477TCMG-v1](https://github.com/Icycereal477TCMG-v1)**  
*Free. Open source. Share it everywhere.*

---

## What This Is

A full terminal D&D experience where a local AI Dungeon Master runs your adventure in real time — on your own machine, with no cloud, no API keys, no subscriptions. The AI handles narration, NPC dialogue, combat, loot, level progression, notoriety, and story continuity across sessions. You play. It reacts. The story goes wherever you take it.

Built and battle-tested on a **Raspberry Pi 4 + Ollama** setup. Scales up to a Threadripper with a 70B model if you want the full cinematic experience.

---

## ✨ Features

### 🎭 Story Engine
- **Binary choice system** every scene — `[A]` bold/aggressive path, `[B]` subtle/cunning path, `[O]` type absolutely anything
- **Butterfly effect tracking** — your choices close and open future paths permanently across sessions
- **NPC color dialogue** — companions in cyan/magenta, enemies in bold red, neutral NPCs in white
- **Campaign persistence** — full state saves between sessions, resume exactly where you left off
- **Auto session summaries** — AI writes a campaign log entry at the end of every session
- **Tone & difficulty** — dark fantasy, high magic, grimdark; easy/normal/hard adjusts enemy lethality
- **Out-of-character notes** with `/ooc` — talk to the DM without affecting the story

### ⚔️ FF3-Style Combat Engine
Full action menu every round — no more "you attack the goblin":

```
  [A] Attack    [M] Magic    [S] Skills
  [I] Item      [D] Defend   [R] Run
```

- **Spell schools by class** — Warlock gets Void/Psychic/Curse, Wizard gets Fire/Ice/Lightning/Arcane, Cleric gets Holy/Death/Healing, Druid gets Nature/Poison/Shapeshifting, and more
- **25+ physical moves** by class and level: Cleave, Backstab, Charge, Rage, Whirlwind, Flurry of Blows, Garrote, Vanish, Maim, Ground Slam, Sneak Attack, Poison Strike, and more
- **Critical hits, conditions** — poisoned, stunned, bleeding, exhausted, charmed, frightened
- **Pact Magic** — Warlocks recover spell slots on short rest, not long rest
- **Companion AI** acts in combat based on personality
- **Launch anytime** — type `fight <enemy>`, `attack <enemy>`, or `kill <enemy>` mid-story

### 🌟 Talent Trees
- **4 fully built trees** with 4-tier specializations:
  - Warlock: Great Old One · Fiend · Archfey
  - Fighter: Champion · Battle Master · Eldritch Knight
  - Rogue: Assassin · Arcane Trickster · Thief
  - Barbarian: Berserker · Totem Warrior · Storm Herald
- 1 talent point at character creation, 1 per level up
- Press **T** anytime or use `/talents`

### 🎖️ Notoriety System
Your reputation shapes the world around you.

| Score | Title | Effect |
|-------|-------|--------|
| -1000 to -601 | **Villain** | Spoken of in fearful whispers |
| -600 to -301 | **Outlaw** | Wanted posters bear your face |
| -300 to -51 | **Scoundrel** | Folk eye you with suspicion |
| -50 to +50 | **Wanderer** | Your reputation is unwritten |
| +51 to +300 | **Goodfellow** | People remember your kindness |
| +301 to +600 | **Champion** | Bards sing of your deeds |
| +601 to +1000 | **Legend** | Your name alone inspires courage |

- **Infamous perks** — dark merchant 25% discount, thieves guild access, criminals respect you
- **Heralded perks** — temple 20% discount, city guard protection, nobles seek you out
- Attacking companions triggers an immediate notoriety penalty

### 🎒 Inventory & Economy
- Full inventory screen with **item condition tracking**: pristine → good → worn → damaged → broken
- `/merchant` — buy weapons, armor, potions; sell at half value (condition-adjusted); repair gear
- `/inn` — short rest (Warlock slot recovery), long rest (full HP + spell recovery), hear rumors, save
- `/trade <companion>` — give or take items and gold with party members
- Item conditions degrade with use and affect combat stats in real time

### 👥 Companions
- Up to 2 companions in solo mode, up to 8 players in multiplayer
- **6 archetypes** with distinct personalities and notoriety biases:
  - Gruff Veteran (Dwarf Fighter) — loyal but blunt, few words
  - Eager Scholar (Human Wizard) — brilliant under pressure, tends to overthink
  - Charming Rogue (Half-Elf) — morally flexible, quick with a joke and quicker with a knife
  - Zealous Cleric (Human) — heals without question, judges without mercy
  - Wild Ranger (Wood Elf) — talks to animals more than people, fiercely protective
  - Bitter Mercenary (Half-Orc Fighter) — only in it for coin, complains constantly, never deserts
- Name them, customize class/race, add personal notes at creation
- Companions **level up** alongside you
- **Permanent death** — one loot window, then they're gone forever

### 🎨 ASCII Art Library
Auto-fires based on what the DM narrates. Zero configuration needed.

**Combat banners:** FIGHT · AMBUSH · VICTORY · LEVEL UP · DEATH

**Character portraits (12 classes):**
Warlock · Fighter · Rogue · Wizard · Cleric · Ranger · Barbarian · Bard · Paladin · Druid · Monk · Sorcerer

**Enemy art (16 types):**
Orc · Skeleton · Giant Spider · Dragon · Dire Wolf · Goblin · Cave Troll · Lich · Bandit · Vampire · Fire Elemental · Cultist · Witch · Demon · Thug · Guard

**Location signs:** Tavern · Inn · Merchant · Dungeon · Graveyard · Forest · Warning · Wanted

**Scene art (20+ scenes):**
Camp · Ruins · Storm · Portal · Mystery Door · Town Gates · City · Mountain Pass · Cave · Ocean · Marketplace · Library · Throne Room · Bard Stage · Night Sky · Road Ambush · Ritual Circle · Prison Cell · Ghost · Level Up Flash · Darkness

**Live HUD** shown before every scene — HP bar with color, gold, equipped gear, spell slot pips, active conditions

---

## 📁 Files

| File | Purpose |
|------|---------|
| `solo_play.py` | Split-file solo campaign entry point |
| `server.py` | Split-file multiplayer TCP server |
| `client.py` | Split-file multiplayer client |
| `dnd_engine.py` | Unified v5 engine — solo, server, and client modes in one file |
| `combat.py` / `combat_screen.py` | Combat rules and terminal combat UI helpers |
| `art.py` / `dice.py` | ASCII art, HUDs, banners, and dice/challenge helpers |
| `setup.sh` | Raspberry Pi setup and file-copy bootstrap script |
| `requirements.txt` | Python dependencies |
| `.env.example` | Starter environment configuration you can copy to `.env` |

---

## 🖥️ Hardware

Runs on anything. Pick the model that fits your machine:

| Hardware | Recommended Model | Notes |
|----------|------------------|-------|
| Raspberry Pi 4 (4–8GB) | `phi3-mini` | Fast, lightweight — mistral crashes Pi4 |
| i7 + RTX 2080 | `mistral` | Great balance of speed and quality |
| Ryzen 9 + RTX 4060 | `mistral` | GPU-accelerated via CUDA, very smooth |
| Threadripper 32GB | `llama3:70b` | Full power, cinematic responses |

**Pro tip:** Run Ollama on your desktop, point the Pi at it via `.env`. Players SSH into the Pi, AI runs on your beefy machine.

```env
# On Pi — point to desktop
OPENAI_API_BASE=http://192.168.1.X:11434/v1
OPENAI_MODEL=llama3
```

---

## 🚀 Quick Start

### Option A — Raspberry Pi 4 (full auto setup)
```bash
bash setup.sh
cd ~/dnd_game && python3 solo_play.py
```

### Option B — Any Linux/Mac machine
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model
ollama pull mistral        # most machines
ollama pull phi3-mini      # Pi4 or low memory

# 3. Install Python deps
pip install -r requirements.txt

# 4. Configure
cp .env.example .env       # edit model name if needed

# 5. Play
python3 solo_play.py
```

### Option C — Unified v5 engine
```bash
cp .env.example .env
python3 dnd_engine.py
# or:
python3 dnd_engine.py --server
python3 dnd_engine.py --client localhost
```

### .env reference
```env
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
```

---

## 🎮 Controls

```
  A or [A]      Choose the bold/aggressive path
  B or [B]      Choose the subtle/cunning path
  O             Type any free action
  I             Open full inventory screen instantly
  T             Open talent tree instantly

  fight <name>  Launch FF3 combat directly
  attack <name>
  kill <name>
```

### Slash Commands
```
  /status          Full character sheet with all stats
  /spells          Spell list and remaining slots
  /inventory       Full inventory with item conditions
  /companions      Companion stats and conditions
  /trade <name>    Trade items or gold with a companion
  /merchant        Buy, sell, or repair gear
  /inn             Rest, recover spells, hear rumors, save
  /notoriety       Your reputation score and current tier
  /talents         Talent tree — spend your points
  /story           Read previous session summaries
  /difficulty      Change difficulty mid-campaign
  /ooc <message>   Out-of-character note to the DM
  /quit            Save and exit
```

---

## 🌐 Multiplayer

```bash
# Start the server (Pi or desktop)
cd ~/dnd_game && bash start_server.sh

# Each player connects from their SSH session
python3 client.py
```

The AI DM tracks all players simultaneously — individual character state, party dynamics, and a shared story that reacts to everyone's choices.

---

## 📖 Example Session

```
═══════════════════════════════════════════════════════════
  SESSION #1 — A SOLO JOURNEY
  Party: Lana with Gruff Veteran
═══════════════════════════════════════════════════════════

  🎸  ♪  ♫  THE STAGE IS YOURS  ♫  ♪  🎸

  The sun sets, painting Moros in an eerie glow. Lana's
  haunting melodies echo through the stone buildings as she
  stumbles into the town square. Fearful villagers gather.

  [MOROS ELDER]: "We cannot tolerate such abominations!"

  ╔══ [A] Confront the elder — appeal to reason
  ╠══ [B] Slip away — vanish into the crowd
  ╚══ [O] Other

You(A/B/O or type freely): B
  → Slip away — vanish into the crowd

  [Notoriety -25: dark deed]
```

---

## 🗺️ Roadmap

- [ ] Remaining talent trees: Cleric · Druid · Ranger · Paladin · Bard · Wizard · Sorcerer · Monk
- [ ] Full notoriety NPC reactions — guards hunt you, thieves respect you, peasants flee or help
- [ ] Inventory item icons (ASCII art per item type)
- [ ] Expanded spell catalogue — more schools, more edge cases, higher levels
- [ ] More fighting styles and combo moves per class
- [ ] Dungeon map generation — ASCII room layouts
- [ ] Web UI wrapper (optional, terminal stays primary)
- [ ] Import/export to Markdown and Obsidian

---

## 🤝 Contributing

PRs welcome. This started as a Pi4 weekend project and grew into something worth sharing. If you add a talent tree, a new enemy, a scene, or improve the model prompt — send it over.

---

## 📜 License

MIT — free forever. Use it, share it, build on it.

---

*Made with 🎲 and too much coffee by **Icycereal477TCMG-v1***  
*Powered by [Ollama](https://ollama.com) · Runs 100% locally · No cloud required*
