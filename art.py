"""
================================================================
  AI DUNGEON MASTER v3 — ASCII Art Library
  art.py — import and call show(key) to display any art
================================================================
"""

# ── Colors ────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m"
    CYAN    = "\033[96m"; WHITE   = "\033[97m"
    YELLOW  = "\033[93m"; RED     = "\033[91m"
    GREEN   = "\033[92m"; MAGENTA = "\033[95m"
    BLUE    = "\033[94m"; ORANGE  = "\033[33m"
    GRAY    = "\033[90m"; DARK    = "\033[2m"

def cc(color, text): return f"{color}{text}{C.RESET}"
def bold(text):      return f"{C.BOLD}{text}{C.RESET}"

W = 78

def _center(line, width=W):
    """Center a line accounting for ANSI escape codes."""
    import re
    clean = re.sub(r'\033\[[0-9;]*m', '', line)
    pad   = max(0, (width - len(clean)) // 2)
    return " " * pad + line

def _print_art(lines, color=C.WHITE, center=True):
    print()
    for line in lines:
        if center:
            print(_center(f"{color}{line}{C.RESET}"))
        else:
            print(f"{color}{line}{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  COMBAT BANNERS
# ══════════════════════════════════════════════════════════════

def banner_fight():
    lines = [
        r"  ███████╗██╗ ██████╗ ██╗  ██╗████████╗██╗",
        r"  ██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝██║",
        r"  █████╗  ██║██║  ███╗███████║   ██║   ██║",
        r"  ██╔══╝  ██║██║   ██║██╔══██║   ██║   ╚═╝",
        r"  ██║     ██║╚██████╔╝██║  ██║   ██║   ██╗",
        r"  ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝",
        r"        ⚔   Steel meets steel!   ⚔        ",
    ]
    _print_art(lines, C.RED)

def banner_ambush():
    lines = [
        r"   ██████╗ ███╗   ███╗██████╗ ██╗   ██╗███████╗██╗  ██╗██╗",
        r"  ██╔══██╗████╗ ████║██╔══██╗██║   ██║██╔════╝██║  ██║██║",
        r"  ███████║██╔████╔██║██████╔╝██║   ██║███████╗███████║██║",
        r"  ██╔══██║██║╚██╔╝██║██╔══██╗██║   ██║╚════██║██╔══██║╚═╝",
        r"  ██║  ██║██║ ╚═╝ ██║██████╔╝╚██████╔╝███████║██║  ██║██╗",
        r"  ╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝",
        r"        👁  You were not alone in the dark.  👁            ",
    ]
    _print_art(lines, C.ORANGE)

def banner_victory():
    lines = [
        r"  ██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗██╗",
        r"  ██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝██║",
        r"  ██║   ██║██║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ ██║",
        r"  ╚██╗ ██╔╝██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  ╚═╝",
        r"   ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   ██╗",
        r"    ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝",
        r"            ★  The battle is won!  ★                          ",
    ]
    _print_art(lines, C.GREEN)

def banner_level_up():
    lines = [
        r"  ██╗     ███████╗██╗   ██╗███████╗██╗         ██╗   ██╗██████╗ ██╗",
        r"  ██║     ██╔════╝██║   ██║██╔════╝██║         ██║   ██║██╔══██╗██║",
        r"  ██║     █████╗  ██║   ██║█████╗  ██║         ██║   ██║██████╔╝██║",
        r"  ██║     ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║         ██║   ██║██╔═══╝ ╚═╝",
        r"  ███████╗███████╗ ╚████╔╝ ███████╗███████╗    ╚██████╔╝██║     ██╗",
        r"  ╚══════╝╚══════╝  ╚═══╝  ╚══════╝╚══════╝     ╚═════╝ ╚═╝     ╚═╝",
        r"              ✦ ✦ ✦  Power grows within you.  ✦ ✦ ✦               ",
    ]
    _print_art(lines, C.MAGENTA)

def banner_death():
    lines = [
        r"  ██╗   ██╗ ██████╗ ██╗   ██╗    ██╗  ██╗ █████╗ ██╗   ██╗███████╗",
        r"  ╚██╗ ██╔╝██╔═══██╗██║   ██║    ██║  ██║██╔══██╗██║   ██║██╔════╝",
        r"   ╚████╔╝ ██║   ██║██║   ██║    ███████║███████║██║   ██║█████╗  ",
        r"    ╚██╔╝  ██║   ██║██║   ██║    ██╔══██║██╔══██║╚██╗ ██╔╝██╔══╝  ",
        r"     ██║   ╚██████╔╝╚██████╔╝    ██║  ██║██║  ██║ ╚████╔╝ ███████╗",
        r"     ╚═╝    ╚═════╝  ╚═════╝     ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝",
        r"                  ☠   The darkness takes you.   ☠                  ",
    ]
    _print_art(lines, C.RED)

# ══════════════════════════════════════════════════════════════
#  CHARACTER CLASS PORTRAITS
# ══════════════════════════════════════════════════════════════

def portrait_warlock():
    lines = [
        r"          .  *  .   *    .  *",
        r"      *  /|\\  *   .   /|\\  *",
        "        / | \\\\      * / | \\\\",
        r"  *   .-'~~~'-.   .-'~~~'-.",
        r"     ( o     o ) *         *",
        r"      \  ~~~  /    ~  *  ~",
        r"    *  '-----'   *",
        "      /|||||\\\\",
        r"     / ||||| \\   ✦ The Void watches ✦",
        r"    '~~~~~~~~~~~'",
        r"   ~~~~~~~~~~~~~~~~~",
    ]
    print()
    for line in lines:
        print(_center(f"{C.MAGENTA}{line}{C.RESET}"))
    print(_center(f"{C.GRAY}~ Great Old One Warlock ~{C.RESET}"))
    print()

def portrait_fighter():
    lines = [
        r"         _______",
        r"        |  [_]  |",
        r"        |_______|",
        "       /|  | |  |\\\\",
        "      / |  | |  | \\\\",
        "     /__|__|_|__|__\\\\",
        r"        |  | |  |",
        "       /|  | |  |\\\\",
        "      /_|__|_|__|_\\\\",
        r"        |__|_|__|",
        r"       ⚔  Fighter  ⚔",
    ]
    _print_art(lines, C.BLUE)

def portrait_rogue():
    lines = [
        r"        ,---.",
        "       /     \\\\",
        r"      | (. .) |",
        r"       \  ^  /",
        r"    .---'---'---..",
        "   /  ,-.   ,-.  \\\\",
        r"  |  /   \ /   \  |",
        r"   \ \   / \   / /",
        r"    '-'   '-'",
        r"   ≈ Shadow and silence ≈",
    ]
    _print_art(lines, C.GRAY)

def portrait_wizard():
    lines = [
        r"       *  .  *  .",
        r"      .  ,---.  *",
        r"     *  / ^ ^ \  .",
        r"       | (o o) |",
        r"      * \ ~~~ / *",
        r"      .-'-----'-.",
        "     /  |  *  |  \\\\",
        r"    |   | *** |   |",
        r"     \  |_____|  /",
        r"      '---   ---'",
        r"      ✦ Arcane Mastery ✦",
    ]
    _print_art(lines, C.CYAN)

def portrait_cleric():
    lines = [
        r"          ✛",
        r"        ,--+--.",
        "       /   |   \\\\",
        r"      | (+ + +) |",
        r"       \  ~~~  /",
        r"      .-'-----'-.",
        "     /  |+   +|  \\\\",
        r"    |   | ✛✛✛ |   |",
        r"     \  |_____|  /",
        r"      '---   ---'",
        r"    ✛ Blessed by the Divine ✛",
    ]
    _print_art(lines, C.YELLOW)

def portrait_ranger():
    lines = [
        r"       )))  (((",
        "      /   \\/   \\\\",
        r"     | (.)(.) |",
        r"      \  /\  /",
        r"    ---'----'---",
        "   /   /    \\   \\\\",
        r"  |   / bow  \   |",
        r"   \ /________\ /",
        r"    |    ||    |",
        "   /\\\\   ||   /\\\\",
        r"  🏹  Ranger of the Wild  🏹",
    ]
    _print_art(lines, C.GREEN)

def portrait_barbarian():
    lines = [
        r"       ,---.    AXE",
        r"      /     \    |",
        r"     | >   < |   |",
        r"      \ ~~~ / ,--+",
        r"    .--'---'-'",
        "   /  GRRRR   \\\\",
        r"  |  |     |   |",
        r"   \ |_____|  /",
        "   /\\       /\\\\",
        "  /  \\_____/  \\\\",
        r"  💢 RAGE IS POWER 💢",
    ]
    _print_art(lines, C.RED)

def portrait_bard():
    lines = [
        r"     ♪  ♫  ♪  ♫",
        r"       ,---.",
        "      / ♪ ♫ \\\\",
        r"     | (♪ ♪) |",
        r"      \ ~~~ /",
        r"    .--'---'--..",
        "   /  /lute\\   \\\\",
        r"  |  |_____|    |",
        r"   \ |_____| __/",
        r"    '--'  '--'",
        r"  ♫ Tales told, hearts stolen ♫",
    ]
    _print_art(lines, C.YELLOW)

def portrait_paladin():
    lines = [
        r"         ✛✛✛",
        r"       ,-----.",
        "      /  [ ] \\\\",
        r"     | (+ + +)|",
        r"      \ ~~~~~ /",
        r"    .--'-----'--..",
        "   / |HOLY|HOLY| \\\\",
        r"  |  |===|+|===|  |",
        r"   \ |___|_|___| /",
        r"    '---'   '---'",
        r"  ⚔✛ Oath sworn, blade blessed ✛⚔",
    ]
    _print_art(lines, C.CYAN)

CLASS_PORTRAITS = {
    "Warlock":   portrait_warlock,
    "Fighter":   portrait_fighter,
    "Rogue":     portrait_rogue,
    "Wizard":    portrait_wizard,
    "Cleric":    portrait_cleric,
    "Ranger":    portrait_ranger,
    "Barbarian": portrait_barbarian,
    "Bard":      portrait_bard,
    "Paladin":   portrait_paladin,
}

# ══════════════════════════════════════════════════════════════
#  ENEMY PORTRAITS
# ══════════════════════════════════════════════════════════════

def enemy_orc():
    lines = [
        r"       ,--^--.",
        "      / >   < \\\\",
        r"     | (  O  ) |",
        r"      \  ~~~  /",
        r"    .--'-----'--.",
        "   /  ( HULK )   \\\\",
        r"  |   |     |    |",
        r"   \  | AXE |   /",
        r"    '-|_____|--'",
        r"       |   |",
        r"  💀  ORC WARRIOR  💀",
    ]
    _print_art(lines, C.GREEN)

def enemy_skeleton():
    lines = [
        r"        ___",
        r"       (o o)",
        r"       |---|",
        "      /|   |\\\\",
        "     / |   | \\\\",
        "    /  | ✝ |  \\\\",
        r"       |   |",
        "      /|   |\\\\",
        "     /_|___|_\\\\",
        r"      |   |",
        r"  🦴  SKELETON  🦴",
    ]
    _print_art(lines, C.GRAY)

def enemy_spider():
    lines = [
        "   /\\   /\\\\",
        "  /  \\./  \\\\",
        " / .-----. \\\\",
        "/  | 8  8 |  \\\\",
        r"\  |  __  |  /",
        r" \ '-----' /",
        r"  \  |||  /",
        r"---'--+--'---",
        r" |    |    |",
        r" |    |    |",
        r"  🕷  GIANT SPIDER  🕷",
    ]
    _print_art(lines, C.ORANGE)

def enemy_dragon():
    lines = [
        r"                          __---~~  ~~--__",
        r"                    _--~~              ~~-_",
        "                  /                        \\\\",
        r"     __          |   /-\    DRAGON    /-\   |",
        r"    /  \\  __    |  |o o|             |o o|  |",
        r"   | >< | \\ \\   |   \-/     ~~~     \-/   |",
        r"   |____|  | |  |       \\           /      |",
        r"   /      // /   \       \\---------/      /",
        r"  | fangs // /    \__                   __/",
        r"   \     // /        ~--___________---~~",
        r"  🔥  ANCIENT DRAGON  🔥  FLEE OR FIGHT  🔥",
    ]
    _print_art(lines, C.RED)

def enemy_wolf():
    lines = [
        "          /\\    /\\\\",
        "         /  \\  /  \\\\",
        "        / ,--\\/--. \\\\",
        "       / /  (oo)  \\ \\\\",
        "      / /    \\/    \\ \\\\",
        "     / /  /|    |\\  \\ \\\\",
        "    /_/__/_|____|_\\__\\_\\\\",
        "          /|    |\\\\",
        "         / |    | \\\\",
        "        /__|____|__\\\\",
        r"  🐺  DIRE WOLF  🐺",
    ]
    _print_art(lines, C.GRAY)

def enemy_goblin():
    lines = [
        r"       ,--^.",
        "      / ^ ^ \\\\",
        r"     | (>_<) |",
        r"      \ --- /",
        r"    .--'---'-.",
        "   /  |hehe|  \\\\",
        r"  |   |:D: |   |",
        r"   \  |____|  /",
        r"    '-|    |-'",
        r"      | /\ |",
        r"  😈  GOBLIN  😈",
    ]
    _print_art(lines, C.GREEN)

def enemy_troll():
    lines = [
        r"      ,----^----.",
        "     / >       < \\\\",
        r"    | (  @   @  ) |",
        r"    |  \  ~~~  /  |",
        r"     '--'-----'--'",
        "   /  REGENERATES  \\\\",
        r"  |   |  FLESH  |   |",
        r"   \  |_________|  /",
        r"    '--'       '--'",
        r"      |  | |  |",
        r"  👹  CAVE TROLL  👹",
    ]
    _print_art(lines, C.GREEN)

def enemy_lich():
    lines = [
        r"     * .  *  . *  .",
        r"      ,--===--.",
        "     /  (X) (X) \\\\",
        r"    |   |-----|  |",
        r"    |   |LICH |  |",
        r"     \  |-----|  /",
        r"    .-'---------'-.",
        "   /  PHYLACTERY   \\\\",
        r"  |  ✦ UNDYING ✦   |",
        r"   \_______________/",
        r"  💀✦  LICH LORD  ✦💀",
    ]
    _print_art(lines, C.MAGENTA)

def enemy_bandit():
    lines = [
        r"       ,----.",
        "      / >  < \\\\",
        r"     | (- -) |",
        r"      \ ~~~ /",
        r"    .--'---'--..",
        "   /  WANTED!   \\\\",
        r"  |  |KNIFE|    |",
        r"   \ |_____|   /",
        r"    '-'   '-'",
        r"      |   |",
        r"  🗡  BANDIT  🗡",
    ]
    _print_art(lines, C.YELLOW)

def enemy_guard():
    lines = [
        r"         [HALT]",
        r"       ,-------.",
        "      /  [   ]  \\\\",
        r"     | (  o o  ) |",
        r"      \  ~~~~~  /",
        r"    .--'-------'-.",
        "   /  |CITY GUARD| \\\\",
        r"  |   |_SPEAR____|  |",
        r"   \  |_________|  /",
        r"    '-'         '-'",
        r"  ⚔  CITY GUARD  ⚔",
    ]
    _print_art(lines, C.BLUE)

def enemy_vampire():
    lines = [
        r"       . *   *  .",
        r"      ,--.___.--.",
        "     / /V|   |V\\ \\\\",
        r"    | | (o) (o) | |",
        r"    |  \ ~~~~~ /  |",
        r"     '--'-----'--'",
        "     /  ETERNAL   \\\\",
        r"    | |  HUNGER  | |",
        r"     \ |_______| /",
        r"      '---   ---'",
        r"  🧛  VAMPIRE LORD  🧛",
    ]
    _print_art(lines, C.RED)

def enemy_elemental_fire():
    lines = [
        r"       ,--~--.",
        "      / ~   ~ \\\\",
        "     /~ FIRE  ~\\\\",
        "    / ~~ | | ~~ \\\\",
        "   /  ~ /||\\\\ ~  \\\\",
        r"  | ~ //||||\\~ ~ |",
        r"  |~ //||||||\\~ ~|",
        r"  | ~|||||||||~ ~ |",
        r"   \\~||||||||| ~ /",
        r"    '~---------~'",
        r"  🔥  FIRE ELEMENTAL  🔥",
    ]
    _print_art(lines, C.ORANGE)

ENEMY_ART = {
    "orc":       enemy_orc,
    "skeleton":  enemy_skeleton,
    "spider":    enemy_spider,
    "dragon":    enemy_dragon,
    "wolf":      enemy_wolf,
    "goblin":    enemy_goblin,
    "troll":     enemy_troll,
    "lich":      enemy_lich,
    "bandit":    enemy_bandit,
    "guard":     enemy_guard,
    "vampire":   enemy_vampire,
    "elemental": enemy_elemental_fire,
    "fire":      enemy_elemental_fire,
}

# ══════════════════════════════════════════════════════════════
#  WORLD SIGNS & LOCATIONS
# ══════════════════════════════════════════════════════════════

def sign_tavern():
    lines = [
        r"     ___________________________",
        r"    |   ~~~~~~~~~~~~~~~~~~~~~~  |",
        r"    |                           |",
        r"    |    🍺  THE  TAVERN  🍺    |",
        r"    |                           |",
        r"    |   Ale  •  Rooms  •  Tales |",
        r"    |   ~~~~~~~~~~~~~~~~~~~~~~  |",
        r"    |___________________________|",
        r"              | |",
        r"              | |",
        r"           ~~~   ~~~",
    ]
    _print_art(lines, C.YELLOW)

def sign_warning():
    lines = [
        "      /\\/\\/\\/\\/\\/\\/\\/\\/\\/\\\\",
        "     /                    \\\\",
        "    /    ⚠  WARNING  ⚠    \\\\",
        r"    \                      /",
        r"     \   TRESPASSERS WILL  /",
        r"      \    BE FED TO THE  /",
        r"       \     WOLVES      /",
        r"        \               /",
        r"         \/\/\/\/\/\/\/",
        r"               |",
        r"          ____/ \\____",
    ]
    _print_art(lines, C.RED)

def sign_wanted():
    lines = [
        r"    .========================.",
        r"    |   W A N T E D   D E A D|",
        r"    |      or  A L I V E     |",
        r"    |   .---------------.    |",
        r"    |   |   (portrait)  |    |",
        r"    |   |   (  ???  )   |    |",
        r"    |   '---------------'    |",
        r"    |                        |",
        r"    |  REWARD: 500 GOLD GP   |",
        r"    |  Contact City Guard    |",
        r"    '========================'",
    ]
    _print_art(lines, C.ORANGE)

def sign_inn():
    lines = [
        r"    .============================.",
        r"    |                            |",
        r"    |   🌙 THE WANDERER'S REST 🌙 |",
        r"    |                            |",
        r"    |  Rooms • Meals • Hot Baths |",
        r"    |  Short Rest  •  Long Rest  |",
        r"    |                            |",
        r"    |   ~ Safe harbor awaits ~   |",
        r"    |____________________________|",
        r"            |        |",
        r"         ~~~          ~~~",
    ]
    _print_art(lines, C.CYAN)

def sign_merchant():
    lines = [
        r"    .---------------------------.",
        r"    |                           |",
        r"    |  💰  TRADER & SMITH  💰   |",
        r"    |                           |",
        r"    | Weapons • Armor • Repairs |",
        r"    |                           |",
        r"    |  'A fair deal for all!'   |",
        r"    |___________________________|",
        r"            |       |",
        r"        ~~~~         ~~~~",
    ]
    _print_art(lines, C.YELLOW)

def sign_dungeon():
    lines = [
        r"     _______________________________",
        r"    |  ⚠  DANGER BELOW  ⚠          |",
        r"    |                               |",
        r"    |   Here there be monsters.     |",
        r"    |   Many have entered.          |",
        r"    |   Few have returned.          |",
        r"    |                               |",
        r"    |   You have been warned.       |",
        r"    |_______________________________|",
        r"              ||",
        r"          ____||____",
    ]
    _print_art(lines, C.RED)

def sign_graveyard():
    lines = [
        r"        ✛         ✛        ✛",
        r"       _|_       _|_      _|_",
        r"      |   |     |   |    |   |",
        r"   ---|---|-----|---|----| R. |---",
        r"      |   |  ~~|   |~~  | I. |",
        r"    ~~|   |~~~~|   |~~~~| P. |~~",
        r"  ~~~~|___|~~~~|___|~~~~|_____|~~~~",
        r"  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        r"   🌑  THE GRAVEYARD  🌑",
        r"     Silence lives here.",
    ]
    _print_art(lines, C.GRAY)

def sign_forest():
    lines = [
        r"    🌲      🌲  🌲     🌲   🌲",
        "   /|\\    /|\\\\  /|\\\\   /|\\\\  /|\\\\",
        "  / | \\  / | \\/ | \\ / | \\/ | \\\\",
        " /  |  \\/  |  |  | /  |  |  |  \\\\",
        r"    |      |  |  |    |  |  |",
        r"   ~~~  THE DEEP FOREST  ~~~",
        r"  Something watches from the dark.",
        r"    🌲      🌲  🌲     🌲   🌲",
        "   /|\\\\    /|\\\\ /|\\\\   /|\\\\ /|\\\\",
        "  / | \\  / | / | \\ / | / | \\\\",
    ]
    _print_art(lines, C.GREEN)

def treasure_chest():
    lines = [
        r"     .------======------.",
        "    /  .--          --. \\\\",
        "   /  /   =========   \\  \\\\",
        r"  |  | ( G O L D ! ) |  |",
        r"  |  |   =========   |  |",
        r"   \  \  '--      --'  / /",
        r"    \  '--============--' /",
        r"     '----====[]====----'",
        r"          [  LOOT  ]",
        r"    💰  Treasure Found!  💰",
    ]
    _print_art(lines, C.YELLOW)

def skull():
    lines = [
        r"       .-.  .-.",
        r"      | (o)(o) |",
        r"      |  ----  |",
        r"       \      /",
        "       /`----'\\\\",
        "      /  |  |  \\\\",
        r"      |  |  |  |",
        r"       \_|  |_/",
        r"         |  |",
        r"         '--'",
        r"  ☠   DEATH AWAITS   ☠",
    ]
    _print_art(lines, C.RED)

# ══════════════════════════════════════════════════════════════
#  HUD — inventory/gold snapshot shown at scene start
# ══════════════════════════════════════════════════════════════

def show_hud(player: dict):
    """Compact HUD showing gold, HP, equipped gear, and spell slots."""
    from art import C  # use local C
    hp  = player.get("hp", 1)
    mhp_val = _calc_max_hp_simple(player)
    pct = hp / mhp_val if mhp_val else 0
    hc  = C.GREEN if pct > 0.5 else C.ORANGE if pct > 0.25 else C.RED
    hpbar = f"{hc}{'█'*int(pct*20)}{'░'*(20-int(pct*20))}{C.RESET}"

    eq      = player.get("equipped", {})
    weapon  = eq.get("weapon", "—") or "—"
    armor   = eq.get("armor",  "—") or "—"
    gold    = player.get("gold", 0)
    slots   = player.get("spell_slots_current", 0)
    mslots  = player.get("spell_slots_max", 0)
    name    = player.get("name", "?")
    lvl     = player.get("level", 1)
    cls     = player.get("class", "?")

    slot_str = ""
    if mslots > 0:
        slot_str = f"  {C.MAGENTA}Slots:{C.RESET} {C.MAGENTA}{'◆'*slots}{'◇'*(mslots-slots)}{C.RESET}"

    conds = player.get("conditions", [])
    cond_str = ""
    if conds:
        cond_str = f"  {C.ORANGE}⚠ {', '.join(conds).upper()}{C.RESET}"

    print(f"\n{C.GRAY}{'─'*W}{C.RESET}")
    print(
        f"  {C.BOLD}{C.CYAN}{name}{C.RESET} "
        f"{C.GRAY}Lvl {lvl} {cls}{C.RESET}  "
        f"HP:{hc}{hp}/{mhp_val}{C.RESET} [{hpbar}]  "
        f"{C.YELLOW}💰{gold}gp{C.RESET}  "
        f"{C.BLUE}🛡{armor}{C.RESET}  "
        f"{C.YELLOW}⚔{weapon}{C.RESET}"
        f"{slot_str}{cond_str}"
    )
    print(f"{C.GRAY}{'─'*W}{C.RESET}\n")

def _calc_max_hp_simple(char: dict) -> int:
    hd_map = {
        "Barbarian":12,"Fighter":10,"Paladin":10,"Ranger":10,
        "Cleric":8,"Druid":8,"Monk":8,"Rogue":8,"Bard":8,"Warlock":8,
        "Wizard":6,"Sorcerer":6
    }
    hd  = hd_map.get(char.get("class","Fighter"), 8)
    con = (char.get("stats", {}).get("CON", 12) - 10) // 2
    lvl = char.get("level", 1)
    return max(1, hd + con + (hd // 2 + 1 + con) * (lvl - 1))

# ══════════════════════════════════════════════════════════════
#  AUTO-DETECT: scan DM response for enemies / locations
# ══════════════════════════════════════════════════════════════

ENEMY_KEYWORDS = {
    "orc":       ["orc","orcs","orcish"],
    "skeleton":  ["skeleton","skeletons","undead","bones"],
    "spider":    ["spider","spiders","arachnid","eight legs"],
    "dragon":    ["dragon","wyrm","dragonborn enemy","scaled beast"],
    "wolf":      ["wolf","wolves","dire wolf","pack"],
    "goblin":    ["goblin","goblins","goblinoid"],
    "troll":     ["troll","trolls","cave troll"],
    "lich":      ["lich","necromancer","undead lord","phylactery"],
    "bandit":    ["bandit","bandits","thief","thieves","cutthroat","brigand"],
    "guard":     ["guard","guards","soldier","city watch","captain"],
    "vampire":   ["vampire","vampires","vampire lord","nosferatu"],
    "elemental": ["elemental","fire elemental","flame"],
}

LOCATION_KEYWORDS = {
    "tavern":    ["tavern","inn","bar","alehouse","pub"],
    "warning":   ["trespassing","trespassers","forbidden","keep out","no entry"],
    "wanted":    ["wanted","bounty","reward","poster"],
    "dungeon":   ["dungeon","crypt","tomb","underdark","depths","cave"],
    "graveyard": ["graveyard","cemetery","burial","graves","tombstone"],
    "forest":    ["forest","woods","trees","thicket","wilderness"],
    "merchant":  ["merchant","shop","market","smithy","blacksmith"],
}

# Strong combat phrases only — no false positives from narrative
COMBAT_KEYWORDS = [
    "attacks you", "charges at you", "lunges toward you", "leaps at you",
    "battle begins", "combat starts", "moves to strike", "the fight begins",
    "draws their blade and charges", "initiative is rolled", "raises their weapon and",
    "slashes at you", "swings at you", "fires an arrow at you",
]

# Track last shown art to prevent spam
_art_shown = {}

def detect_and_show(response: str, player: dict = None):
    """Smart art detection — avoids false positives and spam."""
    text = response.lower()

    # Always show HUD if player provided
    if player:
        show_hud(player)

    # Non-combat responses — skip combat art entirely
    peaceful = ["illuminati","light spell","cantrip","you cast","arcane tome",
                "meditation","studying","reading","you rest","you sleep",
                "you eat","you drink","stepping carefully","moving through"]
    if any(w in text for w in peaceful):
        _check_location(text)
        return

    # COMBAT — only on strong explicit phrases
    if any(kw in text for kw in COMBAT_KEYWORDS):
        for enemy_key, keywords in ENEMY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                art_key = f"combat_{enemy_key}"
                if _art_shown.get(art_key) != text[:50]:
                    banner_fight()
                    fn = ENEMY_ART.get(enemy_key)
                    if fn: fn()
                    _art_shown[art_key] = text[:50]
                return
        # Generic combat — only if not recently shown
        if _art_shown.get("combat") != text[:50]:
            banner_fight()
            _art_shown["combat"] = text[:50]
        return

    # AMBUSH — specific phrases only
    if any(kw in text for kw in ["you are ambushed","surprise attack","caught off guard","from the shadows, they strike"]):
        if _art_shown.get("ambush") != text[:50]:
            banner_ambush()
            _art_shown["ambush"] = text[:50]
        return

    # LOCATIONS
    _check_location(text)

    # TREASURE — only on actual discovery verbs
    find_verbs = ["you find", "you discover", "you loot", "you pocket", "you take",
                  "reveals a chest", "the chest contains", "you pry open"]
    if any(v in text for v in find_verbs):
        if any(kw in text for kw in ["gold","coin","treasure","gem","jewel"]):
            if _art_shown.get("treasure") != text[:50]:
                treasure_chest()
                _art_shown["treasure"] = text[:50]

def _check_location(text: str):
    """Show location sign only when clearly entering a new place."""
    enter_words = ["you enter", "you step into", "you arrive at", "you walk into",
                   "you push open", "you approach the", "you reach the",
                   "you find yourself inside", "you stand before"]
    if not any(w in text for w in enter_words):
        return
    for loc_key, keywords in LOCATION_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            art_key = f"loc_{loc_key}"
            if _art_shown.get(art_key) != text[:50]:
                fn = {
                    "tavern":    sign_tavern,
                    "warning":   sign_warning,
                    "wanted":    sign_wanted,
                    "dungeon":   sign_dungeon,
                    "graveyard": sign_graveyard,
                    "forest":    sign_forest,
                    "merchant":  sign_merchant,
                }.get(loc_key)
                if fn:
                    fn()
                    _art_shown[art_key] = text[:50]
            break

# ══════════════════════════════════════════════════════════════
#  TITLE SCREEN
# ══════════════════════════════════════════════════════════════

def title_screen():
    print()
    print(f"{C.GRAY}             . · * · .  · * · . · * · . · * · .{C.RESET}")
    print(f"{C.MAGENTA}  ╔══════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}                                                          {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.CYAN}  ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ███████╗ ██████╗{C.RESET}  {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.CYAN}  ██╔══██╗██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.CYAN}  ██║  ██║██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██║   ██║{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.CYAN}  ██║  ██║██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██║   ██║{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.CYAN}  ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝███████╗╚██████╔╝{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.CYAN}  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}                                                          {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.RED}      ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗{C.RESET}  {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.RED}      ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.RED}      ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.RED}      ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.RED}      ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.RED}      ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝{C.RESET} {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}                                                          {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ╠══════════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.BOLD}{C.YELLOW}  QUICK CONTROLS{C.RESET}                                          {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.GREEN}  [A]{C.RESET} / {C.YELLOW}[B]{C.RESET}  Choose your path each scene                  {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.CYAN}  [I]{C.RESET}        Full inventory, stats & equipment screen     {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.MAGENTA}  [T]{C.RESET}        Talent tree — spend points, learn abilities   {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.WHITE}  [O]{C.RESET}        Other — type any free action                   {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}  {C.GRAY}  /inn  /merchant  /spells  /status  /story  /quit{C.RESET}       {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}                                                          {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ║{C.RESET}        {C.YELLOW}✦  Powered by Ollama · Runs fully local  ✦{C.RESET}          {C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}  ╚══════════════════════════════════════════════════════════╝{C.RESET}")
    print(f"{C.GRAY}             . · * · .  · * · . · * · . · * · .{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  SCENE ART — misc moments
# ══════════════════════════════════════════════════════════════

def scene_camp():
    lines = [
        "          *   .    *  .   *",
        "        .   *   .    *   .  *",
        "              /\\",
        "             /  \\",
        "            / __ \\",
        "           /  ()  \\",
        "          /________\\",
        "         /    ||    \\",
        "        /_____|_____\\",
        "            _||_",
        "       ____/    \\____",
        "      /   CAMPFIRE    \\",
        "     ~ ~ ~ ~ ~ ~ ~ ~ ~",
        "  🔥  Rest and recover  🔥",
    ]
    _print_art(lines, C.ORANGE)

def scene_level_up_flash():
    lines = [
        r"         · · · ✦ · · ·",
        r"      · ✦               ✦ ·",
        r"    ✦     POWER SURGES     ✦",
        r"   ·        WITHIN         ·",
        r"    ✦     YOU GROW         ✦",
        r"      · ✦               ✦ ·",
        r"         · · · ✦ · · ·",
    ]
    _print_art(lines, C.MAGENTA)

def scene_darkness():
    lines = [
        r"  . . . . . . . . . . . . . . .",
        r"  .                           .",
        r"  .    The darkness watches.  .",
        r"  .                           .",
        r"  .   Something is in here    .",
        r"  .       with you.           .",
        r"  .                           .",
        r"  . . . . . . . . . . . . . . .",
        r"               👁",
    ]
    _print_art(lines, C.GRAY)

def scene_portal():
    lines = [
        r"      *~*~*~*~*~*~*~*~*~*",
        r"    *~  ╔═══════════════╗ ~*",
        r"   *~   ║  · · · · · ·  ║  ~*",
        r"  *~    ║ · PORTAL  · · ║   ~*",
        r"  *~    ║  · · · · · ·  ║   ~*",
        r"   *~   ║  TO ELSEWHERE ║  ~*",
        r"    *~  ╚═══════════════╝ ~*",
        r"      *~*~*~*~*~*~*~*~*~*",
        r"   ✦  Step through if you dare  ✦",
    ]
    _print_art(lines, C.MAGENTA)

def scene_storm():
    lines = [
        r"  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        r"  ~ ~ ~ ~  STORM APPROACHES ~ ~ ~ ~",
        r"  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        r"        ⚡         ⚡",
        r"  _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _",
        r"  _ _ _ _ _ _ _ _/ \_ _ _ _ _ _ _",
        r"   \  \  \  \  /   \ \  \  \  \ ",
        "    \\  \\  \\  \\/     \\  \\  \\  \\",
        r"         ⚡               ⚡",
        r"  ⛈  Lightning threatens all  ⛈",
    ]
    _print_art(lines, C.YELLOW)

def scene_mystery_door():
    lines = [
        r"        .================.",
        "       /|                |\\",
        "      / |   ??????????  | \\",
        r"     |  |                |  |",
        r"     |  |   .-------.   |  |",
        r"     |  |   |  👁   |   |  |",
        r"     |  |   |       |   |  |",
        r"     |  |   '-------'   |  |",
        r"     |  |                |  |",
        r"      \ |________________| /",
        r"  🗝  What lies beyond...  🗝",
    ]
    _print_art(lines, C.CYAN)

def scene_town():
    lines = [
        "    /\\  /\\  /\\  /\\  /\\  /\\",
        "   /  \\/  \\/  \\/  \\/  \\/  \\",
        r"  |  TOWN  ||  INN  ||SMITH|",
        r"  |________|________|______|",
        r"  |   []   ||  []   || []  |",
        r"  |________|________|______|",
        r"  ~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        r"    People, quests, and coin",
        r"  🏘  SETTLEMENT AHEAD  🏘",
    ]
    _print_art(lines, C.YELLOW)

def scene_ruins():
    lines = [
        r"   _   _   _   _   _   _",
        r"  | | | | | | | | | | | |",
        r"  |_| |_| |_| |_| |_| |_|",
        r"       ___         ___",
        r"      |   |       |   |",
        r"      |   |       | X |",
        r"      |___|       |___|",
        r"  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        r"  🏛  ANCIENT RUINS — power lingers  🏛",
    ]
    _print_art(lines, C.GRAY)

SCENE_ART = {
    "camp":      scene_camp,
    "levelup":   scene_level_up_flash,
    "darkness":  scene_darkness,
    "portal":    scene_portal,
    "storm":     scene_storm,
    "door":      scene_mystery_door,
    "town":      scene_town,
    "ruins":     scene_ruins,
}

# Extended location keywords for scene detection
SCENE_KEYWORDS = {
    "camp":      ["make camp","set up camp","camp for the night","build a fire","huddle around the fire"],
    "darkness":  ["pitch black","plunged into darkness","all goes dark","lights go out","consumed by darkness"],
    "portal":    ["swirling portal","magical gateway","dimensional rift","step through the portal"],
    "storm":     ["storm rolls in","lightning strikes overhead","thunder crashes","caught in a storm"],
    "door":      ["mysterious door","strange sealed door","ancient door","the ornate door"],
    "town":      ["you enter the town","you arrive in the town","town gates open","the village square","enter moros"],
    "ruins":     ["ancient ruins","crumbling ruins","abandoned temple","overgrown stone ruins"],
}

def detect_scene(response: str):
    """Fire scene art based on response content."""
    text = response.lower()
    for scene_key, keywords in SCENE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            if _art_shown.get(f"scene_{scene_key}") != text[:50]:
                fn = SCENE_ART.get(scene_key)
                if fn:
                    fn()
                    _art_shown[f"scene_{scene_key}"] = text[:50]
                break

# ══════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════

def show_portrait(char_class: str):
    fn = CLASS_PORTRAITS.get(char_class)
    if fn: fn()

def show_enemy(enemy_name: str):
    key = enemy_name.lower().split()[0]
    fn  = ENEMY_ART.get(key)
    if fn: fn()
    else:  skull()

def show_sign(sign_name: str):
    signs = {
        "tavern":sign_tavern,"warning":sign_warning,"wanted":sign_wanted,
        "inn":sign_inn,"merchant":sign_merchant,"dungeon":sign_dungeon,
        "graveyard":sign_graveyard,"forest":sign_forest,
    }
    fn = signs.get(sign_name.lower())
    if fn: fn()

def show_banner(banner_name: str):
    banners = {
        "fight":banner_fight,"ambush":banner_ambush,
        "victory":banner_victory,"levelup":banner_level_up,
        "death":banner_death,
    }
    fn = banners.get(banner_name.lower())
    if fn: fn()

def show_scene(scene_name: str):
    fn = SCENE_ART.get(scene_name.lower())
    if fn: fn()

def show_title():
    title_screen()

# ══════════════════════════════════════════════════════════════
#  SCENE BORDERS — wraps every DM response
# ══════════════════════════════════════════════════════════════

_BORDER_STYLES = {
    "default":  ("╔","═","╗","║","╚","╝"),
    "dungeon":  ("┌","─","┐","│","└","┘"),
    "magic":    ("◈","─","◈","│","◈","◈"),
    "combat":   ("╔","▄","╗","█","╚","╝"),
    "tavern":   ("╔","─","╗","│","╚","╝"),
    "death":    ("█","▀","█","█","█","█"),
}

def scene_border_top(style="default", label="", color=None):
    tl,t,tr,_,_,_ = _BORDER_STYLES.get(style, _BORDER_STYLES["default"])
    c = color or C.MAGENTA
    inner = W - 2
    if label:
        pad = (inner - len(label) - 2) // 2
        mid = f"{t*pad} {label} {t*(inner-pad-len(label)-2)}"
    else:
        mid = t * inner
    print(f"{c}{tl}{mid}{tr}{C.RESET}")

def scene_border_bot(style="default", color=None):
    _,_,_,_,bl,br = _BORDER_STYLES.get(style, _BORDER_STYLES["default"])
    t = _BORDER_STYLES.get(style, _BORDER_STYLES["default"])[1]
    c = color or C.MAGENTA
    print(f"{c}{bl}{t*(W-2)}{br}{C.RESET}")

def scene_border_line(text, style="default", color=None, text_color=None):
    _,_,_,side,_,_ = _BORDER_STYLES.get(style, _BORDER_STYLES["default"])
    c   = color or C.MAGENTA
    tc  = text_color or C.RESET
    inner = W - 4
    import textwrap
    for line in textwrap.wrap(text, inner) or [""]:
        pad = inner - len(line)
        print(f"{c}{side}{C.RESET} {tc}{line}{C.RESET}{' '*pad} {c}{side}{C.RESET}")

# ══════════════════════════════════════════════════════════════
#  NEW LOCATION ART
# ══════════════════════════════════════════════════════════════

def scene_city():
    lines = [
        r"    |_|  |_|_|  |_|  |_|_|  |_|  |_|",
        r"    | |  | | |  | |  | | |  | |  | |",
        r"   /|_|\/|_|_|\/|_|\/|_|_|\/|_|\/|_|\  ",
        r"  / |_  |_____|  _| |_____| _|  |___| \ ",
        r" /__|_|_|_|_|_|_|_|_|_|_|_|_|__|_|_|__\ ",
        r"════════════════════════════════════════",
        r"         🏙  THE CITY AWAITS  🏙         ",
    ]
    _print_art(lines, C.BLUE)

def scene_mountain():
    lines = [
        r"              /\          /\ ",
        r"             /  \    /\ /  \ ",
        r"            / /\ \  /  V    \ ",
        r"           / /  \ \/    /\   \ ",
        r"          / /    \/\   /  \   \ ",
        r"    _____/ /______\ \_/____\___\ _____",
        r"   /                                   \ ",
        r"  ⛰   TREACHEROUS MOUNTAIN PASS   ⛰   ",
    ]
    _print_art(lines, C.GRAY)

def scene_cave():
    lines = [
        r"   ___________________________________________",
        r"  /  .  '    .       '       .    '    .     \ ",
        r" /  ,·´ `. ·,  '  .   ·, . ´  `. ·,  .   '  \ ",
        r"|  ( DARK )   ·,·  .   (  COLD  )   ·,  .    |",
        r"|   `·,·´  .     .  '   `·, ·´  .      .     |",
        r"|                  🕯  drip  drip               |",
        r" \___________________________________________/ ",
        r"         💀  SOMETHING IS DOWN HERE  💀        ",
    ]
    _print_art(lines, C.GRAY)

def scene_ocean():
    lines = [
        r"  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~",
        r"    ~  ~~~  ~  ~~~  ~  ~~~  ~  ~~~  ~   ",
        r" ~ ~~~  ~  ~~~  ~  ~~~  ~  ~~~  ~  ~~~ ~",
        r"        ⛵                               ",
        r"  ~~  ~~ ~~  ~~ ~~  ~~ ~~  ~~ ~~  ~~ ~~",
        r" ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~ ",
        r"  🌊  THE OPEN SEA  🌊  ENDLESS HORIZON  ",
    ]
    _print_art(lines, C.CYAN)

def scene_marketplace():
    lines = [
        r"  __|__|__|__|__|__|__|__|__|__|__|__|__",
        r" |  FRESH  | WEAPONS | MAGIC  | CLOTH  |",
        r" |  GOODS  |   &     | ITEMS  |  &     |",
        r" |  TODAY  | ARMOUR  |  HERE  | LEATHER|",
        r" |_________|_________|________|________|",
        r"    🥕  💰  ⚔  🧙  💎  🎭  🍖  🔮      ",
        r"   🏪  BUSY MARKET — WATCH YOUR COIN  🏪 ",
    ]
    _print_art(lines, C.YELLOW)

def scene_library():
    lines = [
        r"  |=====| |=====| |=====| |=====| |=====|",
        r"  |     | |     | |     | |     | |     |",
        r"  | 📖  | | 📜  | | 📚  | | 🗺  | | 📖  |",
        r"  |_____| |_____| |_____| |_____| |_____|",
        r"  |=====| |=====| |=====| |=====| |=====|",
        r"       ___________________________________",
        r"      |  ANCIENT LIBRARY — SEEK & FIND  |",
        r"      |___________________________________|",
    ]
    _print_art(lines, C.BLUE)

def scene_throne():
    lines = [
        r"              * * * * * * *",
        r"             *  ___________  *",
        r"            *  |  THRONE   |  *",
        r"           *   |   ROOM    |   *",
        r"               |___________|",
        r"              /      |      \ ",
        r"    _________/   ____|____   \_________",
        r"   |         |  |  CROWN  |  |         |",
        r"   |_________|  |_________|  |_________|",
        r"  👑  POWER LIVES HERE — KNEEL OR FIGHT  👑",
    ]
    _print_art(lines, C.YELLOW)

def scene_bard_stage():
    lines = [
        r"   ♪  ♫  ♪  ♫  ♪  ♫  ♪  ♫  ♪  ♫  ♪",
        r"  ┌────────────────────────────────────┐",
        r"  │   *         *    *         *       │",
        r"  │      THE STAGE IS YOURS            │",
        r"  │                   *         *      │",
        r"  │  🎸  Strum the lute. Move their    │",
        r"  │      hearts. Change the world.     │",
        r"  └────────────────────────────────────┘",
        r"   ♪  ♫  ♪  ♫  ♪  ♫  ♪  ♫  ♪  ♫  ♪",
    ]
    _print_art(lines, C.YELLOW)

def scene_night():
    lines = [
        r"   *    .  *   .   *  .    *  .   *   .",
        r"  .  *    .  *    .  *   .  *    .  *  ",
        r"       *  .    *     .  *    .  *    .  ",
        r"  .  *    .  *    .  🌙  .  *    .  *  ",
        r"       *  .    *     .  *    .  *    .  ",
        r"  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ",
        r"  🌑  THE NIGHT HOLDS MANY SECRETS  🌑  ",
    ]
    _print_art(lines, C.BLUE)

def scene_ambush_road():
    lines = [
        r"  🌲  🌲  🌲  🌲     🌲  🌲  🌲  🌲",
        r"  |   |   |   |       |   |   |   |",
        r"  ================================",
        r"           THE ROAD             ",
        r"  ================================",
        r"  |   |   |   |  👁  |   |   |   |",
        r"  🌲  🌲  🌲  🌲     🌲  🌲  🌲  🌲",
        r"    ⚠  EYES WATCH FROM THE TREES  ⚠",
    ]
    _print_art(lines, C.ORANGE)

def scene_ritual():
    lines = [
        r"        .  *  .  *  .  *  .  *  .",
        r"      *   ___________________   *",
        r"        /  * * * * * * * * *  \ ",
        r"       /  *   RITUAL CIRCLE  *  \ ",
        r"      |  * *   ___________  * * |",
        r"      |  * *  | ☽  ✦  ☾ |  * * |",
        r"      |  * *  |___________|  * * |",
        r"       \  *               *  / ",
        r"        \___________________/ ",
        r"       🔮  ANCIENT POWER STIRS  🔮",
    ]
    _print_art(lines, C.MAGENTA)

def scene_jail():
    lines = [
        r"  | | | | | | | | | | | | | | | |",
        r"  | |                         | |",
        r"  | |   ⛓  YOU ARE TRAPPED  ⛓  | |",
        r"  | |                         | |",
        r"  | |   Find a way out...     | |",
        r"  | |   or rot here.          | |",
        r"  | |                         | |",
        r"  | | | | | | | | | | | | | | | |",
        r"  ⛓  PRISON — ESCAPE OR BARGAIN  ⛓",
    ]
    _print_art(lines, C.RED)

def scene_ghost():
    lines = [
        r"       .  *  .  *  .  *  .  *  .",
        r"          ___",
        r"         /   \ ",
        r"        | o o |   * . *",
        r"         \   /          . *",
        r"       ~~~`-'~~~  *  .     *",
        r"     ~~~~~~~~~~~~~~~  .  *   .",
        r"   ~~~~~~~~~~~~~~~~~~~~~   *",
        r"  👻  A PRESENCE LINGERS HERE  👻",
    ]
    _print_art(lines, C.GRAY)

# ══════════════════════════════════════════════════════════════
#  NEW ENEMY ART
# ══════════════════════════════════════════════════════════════

def enemy_cultist():
    lines = [
        r"       ,----.",
        r"      / 卍  \ ",
        r"     |  ~~~  |",
        r"      \ --- /",
        r"    .--'---'--.",
        r"   /  DEVOTED  \ ",
        r"  |   TO THE   |",
        r"   \ OLD WAYS / ",
        r"    '-|   |-'",
        r"      |   |",
        r"  👁  CULTIST  👁",
    ]
    _print_art(lines, C.MAGENTA)

def enemy_witch():
    lines = [
        r"       /\ ",
        r"      /  \ ",
        r"     / /\ \ ",
        r"    ,---.  ",
        r"   / o o \ ",
        r"  |  ---  |",
        r"   \ ~~~ /",
        r"  .-'---'-.",
        r" / CURSED  \ ",
        r"|  HEXCRAFT |",
        r" \_________/",
        r"  🧙  WITCH  🧙",
    ]
    _print_art(lines, C.GREEN)

def enemy_demon():
    lines = [
        r"       /\ /\ ",
        r"      /V  V\ ",
        r"     | (X X) |",
        r"     |  /\/  |",
        r"      \/----\/",
        r"    .--'----'-.",
        r"   / HELLSPAWN \ ",
        r"  |  UNCHAINED  |",
        r"   \___________/",
        r"  🔥  DEMON  🔥",
    ]
    _print_art(lines, C.RED)

def enemy_thug():
    lines = [
        r"        ,----.",
        r"       / >  < \ ",
        r"      | (. .) |",
        r"       \ --- /",
        r"     .--'---'-.",
        r"    /  HIRED   \ ",
        r"   |    MUSCLE  |",
        r"    \___________/",
        r"       | | | |",
        r"      /  | |  \ ",
        r"  👊  STREET THUG  👊",
    ]
    _print_art(lines, C.ORANGE)

# Add new enemies to the registry
ENEMY_ART.update({
    "cultist":  enemy_cultist,
    "witch":    enemy_witch,
    "demon":    enemy_demon,
    "thug":     enemy_thug,
    "elder":    enemy_thug,    # reuse for hostile npcs
    "guard":    enemy_thug,
})

# Add new scenes to registry
SCENE_ART.update({
    "city":        scene_city,
    "mountain":    scene_mountain,
    "cave":        scene_cave,
    "ocean":       scene_ocean,
    "marketplace": scene_marketplace,
    "library":     scene_library,
    "throne":      scene_throne,
    "bard":        scene_bard_stage,
    "stage":       scene_bard_stage,
    "night":       scene_night,
    "road":        scene_ambush_road,
    "ritual":      scene_ritual,
    "jail":        scene_jail,
    "prison":      scene_jail,
    "ghost":       scene_ghost,
    "spirit":      scene_ghost,
})

# Add new scene keywords
SCENE_KEYWORDS.update({
    "city":        ["you enter the city","the great city","city gates","into the capital","the metropolis"],
    "mountain":    ["mountain pass","you climb the mountain","treacherous peaks","alpine trail","cliff face"],
    "cave":        ["you enter the cave","deep in the cavern","the cave mouth","spelunking","cave walls drip"],
    "ocean":       ["you board the ship","the open sea","port of","set sail","waves crash","harbor ahead"],
    "marketplace": ["the marketplace","busy market","the bazaar","merchant stalls","you browse the wares"],
    "library":     ["the great library","ancient archive","shelves of tomes","reading room","scroll collection"],
    "throne":      ["the throne room","you enter the court","before the king","the royal court","crown upon"],
    "bard":        ["you take the stage","perform for the crowd","strum your lute","the audience watches","you begin to sing"],
    "night":       ["as night falls","under the stars","the moon hangs","midnight approaches","darkness of night"],
    "road":        ["eyes watch from the trees","figures block the road","the road ahead narrows","an ambush"],
    "ritual":      ["the ritual begins","ritual circle","they begin to chant","dark ceremony","summoning ritual"],
    "jail":        ["thrown in a cell","behind bars","the prison","you are captured","locked in the dungeon"],
    "ghost":       ["a ghost appears","spectral figure","phantom drifts","the spirit of","haunted by"],
})

# Add new enemy keywords
ENEMY_KEYWORDS.update({
    "cultist":  ["cultist","cult","devotee","worshipper","fanatic"],
    "witch":    ["witch","hag","hex","coven","curse"],
    "demon":    ["demon","devil","fiend","hellspawn","infernal"],
    "thug":     ["thug","brute","muscle","enforcer","hired"],
})
