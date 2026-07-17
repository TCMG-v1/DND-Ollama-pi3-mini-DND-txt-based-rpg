"""
================================================================
  AI DUNGEON MASTER v4 — Dice & Check Engine
  dice.py — ASCII dice art, skill checks, challenge screen,
             WASD compass, initiative
================================================================
"""
import random
import time
import textwrap

class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m"
    CYAN    = "\033[96m"; WHITE   = "\033[97m"
    YELLOW  = "\033[93m"; RED     = "\033[91m"
    GREEN   = "\033[92m"; MAGENTA = "\033[95m"
    BLUE    = "\033[94m"; ORANGE  = "\033[33m"
    GRAY    = "\033[90m"; DARK    = "\033[2m"

W = 78

# ══════════════════════════════════════════════════════════════
#  D6 FACES — classic pips
# ══════════════════════════════════════════════════════════════
D6 = {
    1:[" _____ ","| . . |","|     |","| . . |","|_____|"],  # corners only faking center
    2:[" _____ ","| *   |","|     |","|   * |","|_____|"],
    3:[" _____ ","| *   |","|  *  |","|   * |","|_____|"],
    4:[" _____ ","| * * |","|     |","| * * |","|_____|"],
    5:[" _____ ","| * * |","|  *  |","| * * |","|_____|"],
    6:[" _____ ","| * * |","| * * |","| * * |","|_____|"],
}
# fix d6[1] to show single center pip
D6[1] = [" _____ ","|     |","|  *  |","|     |","|_____|"]

# ══════════════════════════════════════════════════════════════
#  POLYHEDRAL DICE TEMPLATES  d4 d8 d10 d12 d20
# ══════════════════════════════════════════════════════════════

def _d4(val):
    v = str(val).center(3)
    return [
        "   /\\   ",
        f"  /{v}\\  ",
        " /______\\ ",
    ]

def _d8(val):
    v = str(val).center(3)
    return [
        "   /\\   ",
        f"  /{v}\\  ",
        "  \\   /  ",
        "   \\/   ",
    ]

def _d10(val):
    v = str(val).center(3)
    return [
        "  .----. ",
        f" /{v}   \\",
        " \\      /",
        "  `----' ",
    ]

def _d12(val):
    v = str(val).center(3)
    return [
        "  /----\\ ",
        f" / {v}  \\ ",
        " |      | ",
        "  \\----/  ",
    ]

def _d20(val):
    v = str(val).center(4)
    crit  = val == 20
    fumble= val == 1
    top = "✦" if crit else ("☠" if fumble else "△")
    return [
        f"    {top}    ",
        "  .·´  `·. ",
        f" /  {v}  \\ ",
        " \\        / ",
        "  `·.,.,·´  ",
    ]

def _render_die(sides, val):
    fn = {4:_d4, 8:_d8, 10:_d10, 12:_d12, 20:_d20}.get(sides)
    if fn:
        return fn(val)
    if sides == 6 and val in D6:
        return D6[val]
    v = str(val).center(3)
    return [" _____ ", f"|{v}  |", "|     |", f"|  {v}|", "|_____|"]

# ══════════════════════════════════════════════════════════════
#  PRINT DICE SIDE BY SIDE
# ══════════════════════════════════════════════════════════════

def _print_dice_row(sides, values, color=C.YELLOW, gap=3):
    arts = [_render_die(sides, v) for v in values]
    height = max(len(a) for a in arts)
    width  = max(len(line) for a in arts for line in a)
    for a in arts:
        while len(a) < height:
            a.append(" " * width)
    for row in range(height):
        line = (" " * gap).join(
            f"{color}{a[row].ljust(width)}{C.RESET}" for a in arts
        )
        print(f"    {line}")

# ══════════════════════════════════════════════════════════════
#  ROLL ANIMATION
# ══════════════════════════════════════════════════════════════

def _animate(sides, count, color, frames=5):
    """Flash random dice values before settling."""
    lines_used = len(_render_die(sides, 1)) + 1
    for _ in range(frames):
        vals = [random.randint(1,sides) for _ in range(count)]
        _print_dice_row(sides, vals, C.GRAY)
        time.sleep(0.10)
        # move cursor back up
        print(f"\033[{lines_used}A\033[0J", end="", flush=True)

# ══════════════════════════════════════════════════════════════
#  MAIN ROLL DISPLAY
# ══════════════════════════════════════════════════════════════

def roll_dice_display(num, sides, modifier=0, label="", dc=0,
                      color=C.YELLOW, animate=True):
    """
    Roll num dSides + modifier.
    Show ASCII art, result, pass/fail vs DC.
    Returns (total, success).
    """
    results = [random.randint(1, sides) for _ in range(num)]
    total   = sum(results) + modifier
    nat20   = sides == 20 and num == 1 and results[0] == 20
    nat1    = sides == 20 and num == 1 and results[0] == 1

    mod_str   = f" {'+' if modifier >= 0 else ''}{modifier}" if modifier else ""
    dice_str  = f"{num}d{sides}{mod_str}"

    print()
    print(f"  {C.MAGENTA}{'▓'*W}{C.RESET}")
    if label:
        print(f"  {C.BOLD}{C.WHITE}  {label}{C.RESET}  {C.GRAY}[{dice_str}]{C.RESET}")
    else:
        print(f"  {C.BOLD}{C.WHITE}  Rolling {dice_str}...{C.RESET}")
    if dc:
        bar = "▓" * dc + "░" * (20 - dc)
        print(f"  {C.GRAY}  Need {C.BOLD}{dc}+{C.RESET}{C.GRAY} to succeed  [{C.YELLOW}{bar[:dc]}{C.GRAY}{bar[dc:]}]{C.RESET}")
    print()

    if animate and num <= 5:
        _animate(sides, num, color)

    _print_dice_row(sides, results, color)
    print()

    # Show sum if multi-dice or has modifier
    if num > 1 or modifier:
        parts = " + ".join(str(r) for r in results)
        if modifier:
            parts += f" {'+' if modifier >= 0 else ''}{modifier}"
        print(f"    {C.GRAY}( {parts} ){C.RESET} = ", end="")

    result_color = C.GREEN if (not dc or nat20 or total >= dc) else C.RED
    if nat20: result_color = C.MAGENTA
    if nat1:  result_color = C.RED
    print(f"{result_color}{C.BOLD}{total}{C.RESET}")

    # Special crits
    if nat20:
        print(f"\n  {C.BOLD}{C.MAGENTA}  ✦ ✦ ✦  NATURAL 20  —  CRITICAL SUCCESS!  ✦ ✦ ✦{C.RESET}")
    elif nat1:
        print(f"\n  {C.BOLD}{C.RED}  ☠  NATURAL 1  —  CRITICAL FAILURE!  ☠{C.RESET}")

    # Pass / fail bar
    success = True
    if dc:
        if nat20 or total >= dc:
            bar_filled = min(total, 20)
            bar = f"{C.GREEN}{'█' * bar_filled}{'░' * (20 - bar_filled)}{C.RESET}"
            print(f"\n  {C.BOLD}{C.GREEN}  ✓  SUCCESS{C.RESET}  {bar}  {C.GREEN}{total}{C.RESET}/{dc}")
        else:
            bar_filled = max(0, total)
            bar = f"{C.RED}{'█' * bar_filled}{'░' * (20 - bar_filled)}{C.RESET}"
            print(f"\n  {C.BOLD}{C.RED}  ✗  FAILURE{C.RESET}  {bar}  {C.RED}{total}{C.RESET}/{dc}")
            success = False

    print(f"\n  {C.MAGENTA}{'▓'*W}{C.RESET}")
    return total, success

# ══════════════════════════════════════════════════════════════
#  CHECK PROFILES
#  (num_dice, sides, stat, base_dc, emoji_label, color)
# ══════════════════════════════════════════════════════════════
CHECK_PROFILES = {
    "attack":     (1,20,"DEX",13,"⚔  ATTACK ROLL",       C.RED),
    "shoot":      (1,20,"DEX",13,"🏹 RANGED ATTACK",      C.RED),
    "dodge":      (1,20,"DEX",14,"💨 DODGE CHECK",        C.CYAN),
    "block":      (1,20,"STR",13,"🛡  BLOCK CHECK",       C.BLUE),
    "grapple":    (1,20,"STR",15,"💪 GRAPPLE CHECK",      C.ORANGE),
    "intimidate": (1,20,"CHA",13,"😤 INTIMIDATION CHECK", C.ORANGE),
    "charge":     (1,20,"STR",12,"⚡ CHARGE CHECK",       C.YELLOW),
    "sneak":      (1,20,"DEX",14,"🌑 STEALTH CHECK",      C.MAGENTA),
    "hide":       (1,20,"DEX",13,"👤 HIDE CHECK",         C.GRAY),
    "pickpocket": (1,20,"DEX",15,"🖐  SLEIGHT OF HAND",   C.YELLOW),
    "lie":        (1,20,"CHA",14,"🎭 DECEPTION CHECK",    C.MAGENTA),
    "deceive":    (1,20,"CHA",14,"🎭 DECEPTION CHECK",    C.MAGENTA),
    "persuade":   (1,20,"CHA",13,"💬 PERSUASION CHECK",   C.GREEN),
    "investigate":(1,20,"INT",14,"🔍 INVESTIGATION CHECK",C.CYAN),
    "search":     (1,20,"WIS",12,"🔍 SEARCH CHECK",       C.CYAN),
    "detect":     (1,20,"WIS",13,"👁  PERCEPTION CHECK",  C.YELLOW),
    "cast":       (1,20,"INT",13,"✨ SPELL CHECK",         C.MAGENTA),
    "climb":      (1,20,"STR",13,"🧗 ATHLETICS CHECK",    C.GREEN),
    "swim":       (1,20,"STR",12,"🌊 ATHLETICS CHECK",    C.BLUE),
    "jump":       (1,20,"STR",12,"🦘 ATHLETICS CHECK",    C.GREEN),
    "track":      (1,20,"WIS",13,"🐾 SURVIVAL CHECK",     C.GREEN),
    "heal":       (1,20,"WIS",13,"💚 MEDICINE CHECK",     C.GREEN),
    "perform":    (1,20,"CHA",13,"🎵 PERFORMANCE CHECK",  C.YELLOW),
    "endure":     (1,20,"CON",14,"❤  CONSTITUTION SAVE",  C.RED),
    "barter":     (1,20,"CHA",12,"💰 BARTERING CHECK",    C.YELLOW),
    "recall":     (1,20,"INT",13,"📚 ARCANA CHECK",       C.CYAN),
}

BROAD_MAP = {
    "arrow":"shoot","bow":"shoot","fire":"shoot",
    "strike":"attack","slash":"attack","stab":"attack","punch":"attack","hit":"attack","swing":"attack",
    "run away":"dodge","flee":"dodge","escape":"dodge","roll":"dodge","sidestep":"dodge",
    "grab":"grapple","hold":"grapple","wrestle":"grapple","tackle":"grapple",
    "sneak":"sneak","creep":"sneak","tiptoe":"sneak","quietly":"sneak","silent":"sneak",
    "bluff":"lie","trick":"deceive","fool":"deceive","fake":"deceive",
    "convince":"persuade","talk":"persuade","reason":"persuade","plead":"persuade",
    "look":"search","peer":"detect","listen":"detect","scan":"detect","watch":"detect",
    "spell":"cast","magic":"cast","arcane":"cast","incantation":"cast",
    "climb":"climb","scale":"climb","scramble":"climb",
    "sing":"perform","play music":"perform","dance":"perform","strum":"perform","lute":"perform",
    "haggle":"barter","negotiate":"barter","trade":"barter",
    "track":"track","follow":"track","hunt":"track",
    "bandage":"heal","treat":"heal","tend":"heal","mend":"heal",
}

def _stat_mod(player, key):
    return (player.get("stats",{}).get(key,10) - 10) // 2

def _prof(player):
    return 2 + (player.get("level",1) - 1) // 4

def infer_check(text, player):
    tl = text.lower()
    for kw, prof in CHECK_PROFILES.items():
        if kw in tl:
            return kw, prof
    for kw, pk in BROAD_MAP.items():
        if kw in tl and pk in CHECK_PROFILES:
            return pk, CHECK_PROFILES[pk]
    return None, None

# ══════════════════════════════════════════════════════════════
#  CHALLENGE SCREEN  — the immersive full-screen prompt
# ══════════════════════════════════════════════════════════════

def challenge_screen(situation, player, forced_check=None, forced_dc=None):
    """
    Full-screen challenge: show the dilemma, player types their action,
    dice roll fires, returns result dict.
    """
    print()
    print(f"  {C.BOLD}{C.YELLOW}{'▓'*W}{C.RESET}")
    print(f"  {C.BOLD}{C.YELLOW}  ⚡ CHALLENGE  —  What do you do?{C.RESET}")
    print(f"  {C.YELLOW}{'▓'*W}{C.RESET}")
    print()
    for line in textwrap.wrap(situation, W - 6):
        print(f"    {C.CYAN}{line}{C.RESET}")
    print()
    print(f"  {C.GRAY}  Type your action. Your stats will be tested.{C.RESET}")
    print(f"  {C.YELLOW}{'─'*W}{C.RESET}")
    print()

    try:
        action = input(f"    {C.BOLD}{C.WHITE}❯ {C.RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        action = "stand firm"
    if not action:
        action = "stand firm"

    # Action echo
    print()
    print(f"  {C.BOLD}{C.CYAN}┌─ YOUR ACTION {'─'*(W-18)}┐{C.RESET}")
    for line in textwrap.wrap(action, W - 8):
        print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {C.WHITE}{line:<{W-6}}{C.CYAN}│{C.RESET}")
    print(f"  {C.BOLD}{C.CYAN}└{'─'*(W-4)}┘{C.RESET}")
    print()

    # Determine check
    if forced_check and forced_check in CHECK_PROFILES:
        key  = forced_check
        prof = list(CHECK_PROFILES[forced_check])
    else:
        key, prof = infer_check(action, player)

    if not prof:
        key  = "detect"
        prof = list(CHECK_PROFILES["detect"])

    num, sides, stat, base_dc, lbl, col = prof
    mod = _stat_mod(player, stat) + _prof(player)
    dc  = forced_dc if forced_dc else base_dc

    print(f"  {C.GRAY}  Stat used: {C.BOLD}{stat}{C.RESET}{C.GRAY}  Modifier: {C.BOLD}{mod:+d}{C.RESET}{C.GRAY}  DC: {C.BOLD}{dc}{C.RESET}")
    time.sleep(0.4)

    total, success = roll_dice_display(num, sides, mod, lbl, dc, col, animate=True)

    nat20 = sides == 20 and num == 1 and (total - mod) == 20
    nat1  = sides == 20 and num == 1 and (total - mod) == 1

    return {
        "action":  action,
        "check":   key,
        "total":   total,
        "dc":      dc,
        "success": success,
        "nat20":   nat20,
        "nat1":    nat1,
        "modifier":mod,
        "stat":    stat,
    }

# ══════════════════════════════════════════════════════════════
#  COMPASS ROSE
# ══════════════════════════════════════════════════════════════

def show_compass(available=None):
    """
    Print a compass rose. available = dict of which dirs are open.
    e.g. {"N":True,"W":False,"S":True,"E":True}
    """
    def _arrow(key, symbol, col):
        if available is None or available.get(key, True):
            return f"{col}{C.BOLD}{symbol}{C.RESET}"
        return f"{C.DARK}·{C.RESET}"

    N = _arrow("N","↑",C.CYAN)
    W = _arrow("W","←",C.YELLOW)
    S = _arrow("S","↓",C.ORANGE)
    E = _arrow("E","→",C.GREEN)
    X = _arrow("X","✦",C.MAGENTA)   # examine

    print()
    print(f"  {C.GRAY}  ┌──────────────────────────────────────┐{C.RESET}")
    print(f"  {C.GRAY}  │{C.RESET}        {N} {C.GRAY}[W] North{C.RESET}              {C.GRAY}│{C.RESET}")
    print(f"  {C.GRAY}  │{C.RESET}   {W} {C.GRAY}[A]   {X}   [D]{C.RESET} {E}          {C.GRAY}│{C.RESET}")
    print(f"  {C.GRAY}  │{C.RESET}        {S} {C.GRAY}[S] South   [E] Examine{C.RESET}  {C.GRAY}│{C.RESET}")
    print(f"  {C.GRAY}  └──────────────────────────────────────┘{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════
#  INITIATIVE ROLL
# ══════════════════════════════════════════════════════════════

def roll_initiative(player, enemy_name):
    dex = _stat_mod(player, "DEX")
    p_roll = random.randint(1,20); p_total = p_roll + dex
    e_roll = random.randint(1,20); e_total = e_roll + random.randint(-1,3)

    print()
    print(f"  {C.BOLD}{C.RED}{'═'*W}{C.RESET}")
    print(f"  {C.BOLD}{C.RED}  ⚔  INITIATIVE  ⚔{C.RESET}")
    print(f"  {C.BOLD}{C.RED}{'═'*W}{C.RESET}")
    print()
    print(f"  {C.WHITE}{player['name']}{C.RESET} rolls...")
    _print_dice_row(20, [p_roll], C.GREEN)
    print(f"  {C.GREEN}{C.BOLD}→ {p_total}{C.RESET}  (d20:{p_roll} + DEX {dex:+d})")
    print()
    print(f"  {C.RED}{enemy_name}{C.RESET} rolls...")
    _print_dice_row(20, [e_roll], C.RED)
    print(f"  {C.RED}{C.BOLD}→ {e_total}{C.RESET}  (d20:{e_roll})")
    print()
    if p_total >= e_total:
        print(f"  {C.BOLD}{C.GREEN}  ✓  {player['name']} acts FIRST!{C.RESET}")
    else:
        print(f"  {C.BOLD}{C.RED}  ✗  {enemy_name} acts FIRST!{C.RESET}")
    print(f"  {C.BOLD}{C.RED}{'═'*W}{C.RESET}")
    return p_total, e_total

# ══════════════════════════════════════════════════════════════
#  QUICK HELPERS
# ══════════════════════════════════════════════════════════════

def saving_throw(player, stat, dc, label=""):
    mod = _stat_mod(player, stat) + _prof(player)
    lbl = label or f"💀 {stat} SAVING THROW"
    return roll_dice_display(1, 20, mod, lbl, dc, C.RED)

def ability_check(player, stat, dc, label=""):
    mod = _stat_mod(player, stat) + _prof(player)
    lbl = label or f"🎲 {stat} CHECK"
    return roll_dice_display(1, 20, mod, lbl, dc, C.CYAN)

def quick_roll(sides, mod=0):
    return random.randint(1, sides) + mod
