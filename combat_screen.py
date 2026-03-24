"""
================================================================
  AI DUNGEON MASTER v4 — Cinematic Combat Screen
  combat_screen.py

  Side-by-side ASCII combat arena. Enemy portrait left,
  player stats right, FF3 menu below, damage floaters,
  condition banners, round history ticker.

  Co-created by Icycereal477TCMG-v1 & Claude (Anthropic)
================================================================
"""
import textwrap
import re

class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m"
    CYAN    = "\033[96m"; WHITE   = "\033[97m"
    YELLOW  = "\033[93m"; RED     = "\033[91m"
    GREEN   = "\033[92m"; MAGENTA = "\033[95m"
    BLUE    = "\033[94m"; ORANGE  = "\033[33m"
    GRAY    = "\033[90m"; DARK    = "\033[2m"
    CLEAR   = "\033[2J\033[H"

W  = 78   # total terminal width
LW = 28   # left panel width  (enemy)
RW = 46   # right panel width (player)

# ══════════════════════════════════════════════════════════════
#  ENEMY ASCII PORTRAITS  (28 chars wide)
# ══════════════════════════════════════════════════════════════

ENEMY_PORTRAITS = {

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
    "     ,--^^^^^--,    ",
    "    / >       < \\   ",
    "   | (  O   O ) |   ",
    "   |  \\  ~~~  / |   ",
    "    '--'-----'--'   ",
    "   /   ORC WARLORD \\ ",
    "  |  |   AXE   |   |",
    "   \\ |_________|  / ",
    "    '-'       '-'   ",
    "  💀 FOR THE HORDE  ",
],
"Wolf": [
    "        /\\    /\\    ",
    "       /  \\  /  \\   ",
    "      / ,--\\/--. \\  ",
    "     / /  (oo)  \\ \\ ",
    "    / /    \\/    \\ \\",
    "   / /  /|    |\\  \\ \\",
    "  /_/__/ |    | \\__\\_\\",
    "        /|    |\\      ",
    "       / |    | \\     ",
    "  🐺  DIRE WOLF  🐺  ",
],
"Bandit": [
    "       ,----.       ",
    "      / >  < \\      ",
    "     | (- -) |      ",
    "      \\ ~~~ /       ",
    "    .--'---'--.     ",
    "   /  WANTED!   \\   ",
    "  |  |KNIFE|    |   ",
    "   \\ |_____|   /    ",
    "    '-'   '-'       ",
    "  🗡  BANDIT  🗡    ",
],
"Vampire": [
    "      . *   *  .    ",
    "     ,--.___.--,    ",
    "    / /V|   |V\\ \\   ",
    "   | | (o) (o) | |  ",
    "   |  \\ ~~~~~ /  |  ",
    "    '--'-----'--'   ",
    "    /  ETERNAL   \\  ",
    "   | |  HUNGER  | | ",
    "    \\ |_______| /   ",
    "  🧛 VAMPIRE LORD 🧛",
],
"Lich": [
    "   * .  *  . *  .   ",
    "    ,--===--,       ",
    "   /  (X) (X) \\     ",
    "  |   |-----|  |    ",
    "  |   |LICH |  |    ",
    "   \\  |-----|  /    ",
    "  .-'---------'-.   ",
    " /  PHYLACTERY   \\  ",
    "|  ✦ UNDYING ✦   |  ",
    " 💀✦ LICH LORD ✦💀 ",
],
"Spider": [
    "   /\\         /\\    ",
    "  /  \\ .---. /  \\   ",
    " / .--| 8  8 |--. \\ ",
    "/  |  |  __  |  |  \\",
    "\\  '--|--\\/--|--'  /",
    " \\    '-----'    /  ",
    "  \\    |||||    /   ",
    "  -'---+++++---'-   ",
    "   |   |   |   |    ",
    "  🕷  GIANT SPIDER  🕷",
],
"Guard": [
    "       [HALT!]      ",
    "     ,-------.      ",
    "    /  [   ]  \\     ",
    "   | (  o o  ) |    ",
    "    \\  ~~~~~  /     ",
    "  .--'---------'-.  ",
    " /  |CITY  GUARD|  \\ ",
    "|   |___SPEAR___|   |",
    " \\  |___________|  /",
    "  ⚔  CITY GUARD  ⚔ ",
],
"Cultist": [
    "      ✛✛✛✛✛        ",
    "    ,---------.     ",
    "   / (o)   (o) \\    ",
    "  |   \\~~~~~/ |  |  ",
    "   '--'-^^^-'--'    ",
    "  /  PRAISE  THE  \\ ",
    " |   DARK   ONES   | ",
    "  \\ |_____________|/ ",
    "    '--'     '--'   ",
    "  🔮  CULTIST  🔮   ",
],
}

# Default silhouette for unknown enemies
DEFAULT_ENEMY = [
    "     ,-------,      ",
    "    / ?       \\     ",
    "   | (?) (?) |  |   ",
    "   |   \\~~~/ |  |   ",
    "    '--'---'--'      ",
    "   /   UNKNOWN   \\  ",
    "  |   CREATURE   |  ",
    "   \\ |_________| /  ",
    "    '-'       '-'   ",
    "  ☠  BEWARE  ☠      ",
]

def get_enemy_portrait(enemy_name: str) -> list:
    """Return portrait lines for named enemy, fuzzy match."""
    name = enemy_name.strip().title()
    if name in ENEMY_PORTRAITS:
        return ENEMY_PORTRAITS[name]
    for key in ENEMY_PORTRAITS:
        if key.lower() in enemy_name.lower() or enemy_name.lower() in key.lower():
            return ENEMY_PORTRAITS[key]
    return DEFAULT_ENEMY

# ══════════════════════════════════════════════════════════════
#  HP / STATUS BARS
# ══════════════════════════════════════════════════════════════

def hp_bar(current, maximum, width=20) -> tuple:
    """Returns (bar_str, color)."""
    pct = current / maximum if maximum else 0
    col = C.GREEN if pct > 0.5 else C.ORANGE if pct > 0.25 else C.RED
    filled = int(pct * width)
    bar = f"{col}{'█' * filled}{C.GRAY}{'░' * (width - filled)}{C.RESET}"
    return bar, col

def spell_pips(current, maximum) -> str:
    if maximum == 0: return ""
    pips = f"{C.MAGENTA}{'◆' * current}{C.DARK}{'◇' * (maximum - current)}{C.RESET}"
    return pips

def condition_icons(conditions: list) -> str:
    icons = {
        "poisoned":   f"{C.GREEN}☠PSN{C.RESET}",
        "bleeding":   f"{C.RED}🩸BLD{C.RESET}",
        "burning":    f"{C.ORANGE}🔥BRN{C.RESET}",
        "stunned":    f"{C.YELLOW}⚡STN{C.RESET}",
        "paralyzed":  f"{C.GRAY}⛓PAR{C.RESET}",
        "defending":  f"{C.BLUE}🛡DEF{C.RESET}",
        "charmed":    f"{C.MAGENTA}💜CHR{C.RESET}",
        "frightened": f"{C.YELLOW}😱FRT{C.RESET}",
        "blinded":    f"{C.GRAY}👁BLD{C.RESET}",
    }
    return "  ".join(icons.get(c.lower(), f"{C.ORANGE}⚠{c.upper()}{C.RESET}")
                     for c in conditions)

# ══════════════════════════════════════════════════════════════
#  MAIN COMBAT SCREEN
# ══════════════════════════════════════════════════════════════

def draw_combat_screen(
    player: dict,
    enemy_name: str,
    enemy_hp: int,
    enemy_max_hp: int,
    round_num: int,
    round_log: list = None,
    flash_msg: str = "",
    flash_col: str = "",
):
    """
    Draw the full cinematic combat screen.
    Left panel: enemy portrait + HP
    Right panel: player stats + conditions
    Bottom: round log + menu hint
    """
    from combat import _simple_max_hp

    # ── Gather player data ─────────────────────────────────────
    php   = player.get("hp", 1)
    pmhp  = _simple_max_hp(player)
    pname = player.get("name", "Hero")
    pcls  = player.get("class", "Fighter")
    plvl  = player.get("level", 1)
    pac   = player.get("ac", 10)
    patk  = player.get("attack_bonus", 0)
    pslots= player.get("spell_slots_current", 0)
    pmslt = player.get("spell_slots_max", 0)
    pconds= player.get("conditions", [])
    gold  = player.get("gold", 0)

    phbar, phcol = hp_bar(php, pmhp, 18)
    ehbar, ehcol = hp_bar(enemy_hp, enemy_max_hp, 18)

    portrait = get_enemy_portrait(enemy_name)

    # ── Print header ───────────────────────────────────────────
    print()
    print(f"  {C.BOLD}{C.RED}╔{'═'*74}╗{C.RESET}")
    round_title = f"  ⚔  COMBAT  —  Round {round_num}  ⚔  "
    print(f"  {C.BOLD}{C.RED}║{round_title:^74}║{C.RESET}")
    print(f"  {C.BOLD}{C.RED}╠{'═'*34}╦{'═'*39}╣{C.RESET}")

    # ── Portrait rows (left) + stats rows (right) ─────────────
    # Build left lines (enemy portrait + HP)
    left_lines = []
    # enemy name banner
    en_banner = enemy_name.upper().center(30)
    left_lines.append(f"{C.BOLD}{C.RED}{en_banner}{C.RESET}")
    for p_line in portrait:
        left_lines.append(f"{C.RED}{p_line:<28}{C.RESET}")
    # enemy HP
    epct_str = f"{ehcol}{enemy_hp}{C.RESET}/{C.GRAY}{enemy_max_hp}{C.RESET}"
    left_lines.append(f"  HP [{ehbar}] {epct_str}")
    left_lines.append("")

    # Build right lines (player stats)
    right_lines = []
    right_lines.append(f"{C.BOLD}{C.CYAN}{pname}{C.RESET}  {C.GRAY}Lvl {plvl} {pcls}{C.RESET}")
    right_lines.append(f"HP  [{phbar}] {phcol}{php}{C.RESET}/{C.GRAY}{pmhp}{C.RESET}")
    right_lines.append(f"AC: {C.BOLD}{C.BLUE}{pac}{C.RESET}   ATK: {C.BOLD}{C.YELLOW}{patk:+d}{C.RESET}   💰{C.YELLOW}{gold}gp{C.RESET}")
    if pmslt > 0:
        right_lines.append(f"Slots: {spell_pips(pslots, pmslt)}  {C.GRAY}({pslots}/{pmslt}){C.RESET}")
    if pconds:
        right_lines.append(f"⚠ {condition_icons(pconds)}")

    # equipped
    eq = player.get("equipped", {})
    wpn = eq.get("weapon", "Fist") or "Fist"
    arm = eq.get("armor",  "—")   or "—"
    right_lines.append(f"⚔ {C.YELLOW}{wpn}{C.RESET}")
    right_lines.append(f"🛡 {C.BLUE}{arm}{C.RESET}")

    # stats block
    stats = player.get("stats", {})
    def sm(k): v=stats.get(k,10); m=(v-10)//2; return f"{C.GRAY}{k}:{C.RESET}{C.WHITE}{v}{C.RESET}{C.GRAY}({m:+d}){C.RESET}"
    right_lines.append(f"{sm('STR')} {sm('DEX')} {sm('CON')}")
    right_lines.append(f"{sm('INT')} {sm('WIS')} {sm('CHA')}")

    # pad to same height
    max_rows = max(len(left_lines), len(right_lines))
    while len(left_lines)  < max_rows: left_lines.append("")
    while len(right_lines) < max_rows: right_lines.append("")

    for i in range(max_rows):
        # strip ANSI for width measurement
        ansi_re = re.compile(r'\033\[[0-9;]*m')
        l_clean = ansi_re.sub('', left_lines[i])
        r_clean = ansi_re.sub('', right_lines[i])
        l_pad   = 34 - len(l_clean)
        r_pad   = 39 - len(r_clean)
        print(f"  {C.GRAY}║{C.RESET} {left_lines[i]}{' '*max(0,l_pad)}{C.GRAY}║{C.RESET} {right_lines[i]}{' '*max(0,r_pad)}{C.GRAY}║{C.RESET}")

    print(f"  {C.BOLD}{C.RED}╠{'═'*34}╩{'═'*39}╣{C.RESET}")

    # ── Flash message (damage / crit / miss) ──────────────────
    if flash_msg:
        fc = flash_col or C.WHITE
        msg_line = f" {fc}{C.BOLD}{flash_msg}{C.RESET} "
        ansi_re  = re.compile(r'\033\[[0-9;]*m')
        clean    = ansi_re.sub('', msg_line)
        pad      = max(0, 74 - len(clean))
        print(f"  {C.RED}║{C.RESET}{msg_line}{' '*pad}{C.RED}║{C.RESET}")
        print(f"  {C.RED}╠{'═'*74}╣{C.RESET}")

    # ── Round log (last 3 events) ──────────────────────────────
    if round_log:
        for entry in round_log[-3:]:
            ansi_re = re.compile(r'\033\[[0-9;]*m')
            clean   = ansi_re.sub('', entry)
            pad     = max(0, 73 - len(clean))
            print(f"  {C.GRAY}║ {entry}{' '*pad}║{C.RESET}")
        print(f"  {C.GRAY}╠{'═'*74}╣{C.RESET}")

    # ── Action menu ───────────────────────────────────────────
    print(f"  {C.GRAY}║{C.RESET}  {C.BOLD}YOUR TURN:{C.RESET}  "
          f"{C.YELLOW}[A]{C.RESET}ttack  "
          f"{C.MAGENTA}[M]{C.RESET}agic  "
          f"{C.CYAN}[S]{C.RESET}kills  "
          f"{C.GREEN}[I]{C.RESET}tem  "
          f"{C.ORANGE}[D]{C.RESET}efend  "
          f"{C.RED}[R]{C.RESET}un"
          f"{'':>14}{C.GRAY}║{C.RESET}")
    print(f"  {C.BOLD}{C.RED}╚{'═'*74}╝{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  DAMAGE FLOATER  (big ASCII hit number)
# ══════════════════════════════════════════════════════════════

BIG_NUMS = {
    "0":["┌─┐","│ │","└─┘"],
    "1":["  ╷","  │","  ╵"],
    "2":["╶─┐"," ─┤","└─╴"],
    "3":["╶─┐"," ─┤","╶─┘"],
    "4":["╷ ╷","└─┤","  ╵"],
    "5":["┌─╴","└─┐","╶─┘"],
    "6":["┌─╴","├─┐","└─┘"],
    "7":["╶─┐","  │","  ╵"],
    "8":["┌─┐","├─┤","└─┘"],
    "9":["┌─┐","└─┤","╶─┘"],
    "!":["  │","  │","  ·"],
    "-":["   ","───","   "],
    " ":["   ","   ","   "],
}

def _big_number(text: str) -> list:
    rows = ["","",""]
    for ch in str(text):
        glyph = BIG_NUMS.get(ch, BIG_NUMS[" "])
        for r in range(3):
            rows[r] += glyph[r] + " "
    return rows

def damage_floater(amount: int, dtype: str = "physical",
                   is_crit: bool = False, is_miss: bool = False,
                   is_heal: bool = False):
    """Print a big ASCII damage number."""
    if is_miss:
        color = C.GRAY
        label = "  M I S S ! "
        nums  = _big_number("---")
    elif is_heal:
        color = C.GREEN
        label = f"  + {amount} HP  "
        nums  = _big_number(str(amount))
    else:
        dtype_colors = {
            "fire":C.ORANGE,"ice":C.CYAN,"lightning":C.YELLOW,
            "void":C.MAGENTA,"holy":C.YELLOW,"poison":C.GREEN,
            "physical":C.WHITE,"weapon":C.WHITE,"magic":C.MAGENTA,
        }
        color = dtype_colors.get(dtype.lower(), C.WHITE)
        if is_crit: color = C.MAGENTA
        label = f"  {'✦ CRITICAL! ' if is_crit else ''}{dtype.upper()} DAMAGE  "
        nums  = _big_number(str(amount))

    print()
    for row in nums:
        print(f"    {color}{C.BOLD}{row}{C.RESET}")
    print(f"  {color}{label}{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  ENEMY DEATH SCREEN
# ══════════════════════════════════════════════════════════════

def enemy_death_screen(enemy_name: str, xp: int = 0, loot: list = None):
    portrait = get_enemy_portrait(enemy_name)
    print()
    print(f"  {C.BOLD}{C.GREEN}╔{'═'*74}╗{C.RESET}")
    title = f"  ✓  {enemy_name.upper()}  DEFEATED!  "
    print(f"  {C.BOLD}{C.GREEN}║{title:^74}║{C.RESET}")
    print(f"  {C.BOLD}{C.GREEN}╠{'═'*74}╣{C.RESET}")

    # Portrait — greyed out (dead)
    for line in portrait:
        ansi_re = re.compile(r'\033\[[0-9;]*m')
        clean   = ansi_re.sub('', line)
        pad     = max(0, 74 - len(clean))
        print(f"  {C.GRAY}║ {line}{' '*pad}║{C.RESET}")

    print(f"  {C.BOLD}{C.GREEN}╠{'═'*74}╣{C.RESET}")
    if xp:
        xp_line = f"  ★  +{xp} XP  ★  "
        print(f"  {C.BOLD}{C.YELLOW}║{xp_line:^74}║{C.RESET}")
    if loot:
        for item in loot:
            loot_line = f"  💰  Found: {item}  "
            print(f"  {C.BOLD}{C.YELLOW}║{loot_line:^74}║{C.RESET}")
    print(f"  {C.BOLD}{C.GREEN}╚{'═'*74}╝{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  PLAYER DEATH SCREEN
# ══════════════════════════════════════════════════════════════

def player_death_screen(player: dict, enemy_name: str):
    name = player.get("name", "Hero")
    cls  = player.get("class", "Adventurer")
    lvl  = player.get("level", 1)
    print()
    print(f"  {C.BOLD}{C.RED}╔{'═'*74}╗{C.RESET}")
    print(f"  {C.BOLD}{C.RED}║{'  ☠  Y O U   H A V E   F A L L E N  ☠  ':^74}║{C.RESET}")
    print(f"  {C.BOLD}{C.RED}╠{'═'*74}╣{C.RESET}")

    skull_art = [
        "           .-.  .-.",
        "          | (o)(o) |",
        "          |  ----  |",
        "           \\      /",
        "           /`----'\\",
        "          /  |  |  \\",
        "          |  |  |  |",
        "           \\_|  |_/",
        "             |  |",
        "             '--'",
    ]
    for line in skull_art:
        pad = max(0, 74 - len(line))
        print(f"  {C.RED}║ {line}{' '*pad}║{C.RESET}")

    print(f"  {C.BOLD}{C.RED}╠{'═'*74}╣{C.RESET}")
    epitaph = f"  Here fell {name}, Lvl {lvl} {cls} — slain by {enemy_name}.  "
    print(f"  {C.BOLD}{C.GRAY}║{epitaph:^74}║{C.RESET}")
    print(f"  {C.BOLD}{C.RED}╚{'═'*74}╝{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  COMBAT INTRO SCREEN  (shown before round 1)
# ══════════════════════════════════════════════════════════════

def combat_intro(player: dict, enemy_name: str,
                 enemy_hp: int, enemy_max_hp: int,
                 p_init: int, e_init: int):
    """Cinematic intro before combat begins."""
    from combat import _simple_max_hp
    portrait = get_enemy_portrait(enemy_name)

    print()
    print(f"  {C.BOLD}{C.RED}╔{'═'*74}╗{C.RESET}")
    print(f"  {C.BOLD}{C.RED}║{'  ⚔  COMBAT BEGINS  ⚔  ':^74}║{C.RESET}")
    print(f"  {C.BOLD}{C.RED}╠{'═'*34}╦{'═'*39}╣{C.RESET}")

    # Enemy side
    left = [f"{C.BOLD}{C.RED}{enemy_name.upper().center(30)}{C.RESET}"]
    for line in portrait:
        left.append(f"{C.RED}{line:<28}{C.RESET}")
    ehbar, ehcol = hp_bar(enemy_hp, enemy_max_hp, 18)
    left.append(f"  HP [{ehbar}] {ehcol}{enemy_hp}/{enemy_max_hp}{C.RESET}")

    # Player side
    pmhp = _simple_max_hp(player)
    php  = player.get("hp", pmhp)
    phbar, phcol = hp_bar(php, pmhp, 18)
    right = [
        f"{C.BOLD}{C.CYAN}{player['name']}{C.RESET}  {C.GRAY}Lvl {player.get('level',1)} {player.get('class','?')}{C.RESET}",
        f"HP  [{phbar}] {phcol}{php}/{pmhp}{C.RESET}",
        "",
        f"  {C.BOLD}INITIATIVE{C.RESET}",
        f"  {C.GREEN}You:   {p_init:>2}{C.RESET}",
        f"  {C.RED}Enemy: {e_init:>2}{C.RESET}",
        "",
    ]
    if p_init >= e_init:
        right.append(f"  {C.BOLD}{C.GREEN}✓ YOU act FIRST!{C.RESET}")
    else:
        right.append(f"  {C.BOLD}{C.RED}✗ ENEMY acts first!{C.RESET}")

    max_rows = max(len(left), len(right))
    while len(left)  < max_rows: left.append("")
    while len(right) < max_rows: right.append("")

    ansi_re = re.compile(r'\033\[[0-9;]*m')
    for i in range(max_rows):
        l_clean = ansi_re.sub('', left[i]);  l_pad = 34 - len(l_clean)
        r_clean = ansi_re.sub('', right[i]); r_pad = 39 - len(r_clean)
        print(f"  {C.GRAY}║{C.RESET} {left[i]}{' '*max(0,l_pad)}{C.GRAY}║{C.RESET} {right[i]}{' '*max(0,r_pad)}{C.GRAY}║{C.RESET}")

    print(f"  {C.BOLD}{C.RED}╚{'═'*34}╩{'═'*39}╝{C.RESET}")
    print()
    input(f"  {C.GRAY}[ Press Enter to begin... ]{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  ROUND NARRATION BOX
# ══════════════════════════════════════════════════════════════

def narration_box(text: str, color: str = None):
    """Print DM narration in a styled box."""
    color = color or C.CYAN
    print(f"\n  {color}╔{'═'*74}╗{C.RESET}")
    for line in textwrap.wrap(text, 72):
        ansi_re = re.compile(r'\033\[[0-9;]*m')
        pad     = max(0, 72 - len(ansi_re.sub('', line)))
        print(f"  {color}║{C.RESET} {C.WHITE}{line}{' '*pad} {color}║{C.RESET}")
    print(f"  {color}╚{'═'*74}╝{C.RESET}\n")
