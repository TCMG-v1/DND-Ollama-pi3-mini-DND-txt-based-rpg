#!/usr/bin/env python3
"""
================================================================
  AI DUNGEON MASTER v4 — Solo Adventure
  Colors | Spell Slots | Combat Depth | Conditions
  Inn & Rest | Weapon/Armor Repair | 4d6 Drop Lowest

  Run: python3 solo_play.py
================================================================
"""
import json, os, textwrap, random
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
try:
    from art import detect_and_show, show_portrait, show_banner, show_hud, show_sign, show_title, detect_scene, show_scene
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False
    def detect_and_show(r, p=None): pass
    def show_portrait(c): pass
    def show_banner(b): pass
    def show_hud(p): pass
    def show_sign(s): pass
    def show_title(): pass
    def detect_scene(r): pass
    def show_scene(s): pass

try:
    from combat import (combat_menu, resolve_action, build_combat_narration,
                        show_talent_tree,
                        apply_merchant_discount, show_combat_header)
    COMBAT_AVAILABLE = True
except ImportError:
    COMBAT_AVAILABLE = False

try:
    from dice import (challenge_screen, roll_initiative,
                      show_compass, infer_check)
    DICE_AVAILABLE = True
except ImportError:
    DICE_AVAILABLE = False
    def show_compass(**k): pass
    def challenge_screen(s,p,**k): return {"action":s,"success":True,"total":12,"dc":12,"nat20":False,"nat1":False}
    def roll_initiative(p,e): return (10,8)
    def infer_check(t,p): return None,None

try:
    from combat_screen import (damage_floater, enemy_death_screen,
                                player_death_screen, combat_intro,
                                narration_box)
    SCREEN_AVAILABLE = True
except ImportError:
    SCREEN_AVAILABLE = False
    def damage_floater(*a,**k): pass
    def enemy_death_screen(*a,**k): pass
    def player_death_screen(*a,**k): pass
    def combat_intro(*a,**k): input("  [ Press Enter to begin combat ]")
    def narration_box(t,**k): print(f"  {t}")

load_dotenv()

CHARACTERS_FILE = "characters.json"
SOLO_SAVE_FILE  = "solo_campaign.json"
MODEL           = os.getenv("OPENAI_MODEL", "mistral")
MAX_TOKENS      = int(os.getenv("MAX_TOKENS", "700"))
MAX_COMPANIONS  = 2
W               = 78

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
)

# ══════════════════════ COLORS ════════════════════════════════
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m"
    CYAN    = "\033[96m"  # DM narration
    WHITE   = "\033[97m"  # NPC dialogue
    YELLOW  = "\033[93m"  # Gold / loot
    RED     = "\033[91m"  # Damage / danger
    GREEN   = "\033[92m"  # Healing / good news
    MAGENTA = "\033[95m"  # Magic / spells
    BLUE    = "\033[94m"  # Stats / system
    ORANGE  = "\033[33m"  # Conditions / warnings
    GRAY    = "\033[90m"  # Flavor / dim text

def cc(color, text): return f"{color}{text}{C.RESET}"
def bold(text):      return f"{C.BOLD}{text}{C.RESET}"

def cprint(color, text, wrap_text=True):
    if wrap_text:
        out = []
        for para in text.split("\n"):
            if not para.strip(): out.append("")
            else: out.extend(textwrap.wrap(para, W))
        text = "\n".join(out)
    print(f"{color}{text}{C.RESET}")

def divider(ch="─", color=C.GRAY): print(f"{color}{ch*W}{C.RESET}")

def header(text, color=C.BLUE):
    print(f"\n{C.BOLD}{color}{'═'*W}{C.RESET}")
    print(f"{C.BOLD}{color}  {text}{C.RESET}")
    print(f"{C.BOLD}{color}{'═'*W}{C.RESET}")

def dm_print(text: str):
    import re
    print()
    print("\033[95m" + "=" * 78 + "\033[0m")
    comp_colors = {
        "thalia": "\033[95m", "gruff veteran": "\033[94m", "gruff": "\033[94m",
        "moros": "\033[96m", "eager scholar": "\033[96m", "charming rogue": "\033[93m",
        "wild ranger": "\033[92m", "zealous cleric": "\033[93m",
        "bitter mercenary": "\033[33m",
    }
    RE_CHOICE_A = re.compile(r"^\[A\]")
    RE_CHOICE_B = re.compile(r"^\[B\]")
    RE_CHOICE_O = re.compile(r"^\[O\]")
    RE_NPC_FMT  = re.compile(r"^\[([A-Z][A-Za-z ]+)\]:\s*(.+)$")
    RE_SAYS_FMT = re.compile(r"^([A-Z][a-zA-Z ]+)\s+(says|whispers|growls|shouts|snarls):\s*(.+)$")
    RE_DAMAGE   = re.compile(r"\b\d+\s*(damage|slashing|piercing|fire|cold|necrotic)\b", re.I)
    RE_GOLD     = re.compile(r"\b(gold|gp|you find|loot|treasure|coin)\b", re.I)
    RE_MAGIC    = re.compile(r"\b(eldritch|arcane|crackl|surge|void|patron|spell)\b", re.I)

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            print()
            continue
        if RE_CHOICE_A.match(s):
            print(f"\n  \033[1m\033[92m[A] {s[3:].strip()}\033[0m")
            continue
        if RE_CHOICE_B.match(s):
            print(f"  \033[1m\033[93m[B] {s[3:].strip()}\033[0m")
            continue
        if RE_CHOICE_O.match(s):
            print("  \033[90m[O] Other\033[0m\n")
            continue
        m = RE_NPC_FMT.match(s)
        if m:
            name = m.group(1).strip()
            quote = m.group(2).strip().strip('"')
            col = comp_colors.get(name.lower(), "\033[97m")
            print(f"  {col}\033[1m{name}:\033[0m {col}\"{quote}\"\033[0m")
            continue
        matched_tag = False
        for tag, col in [("npc","\033[97m"),("companion","\033[95m"),("enemy","\033[91m")]:
            if f"<{tag}>" in s:
                txt = re.sub(f"</?{tag}>", "", s).strip()
                import textwrap as _tw
                for wl in _tw.wrap(txt, 74):
                    print(f"  {col}{wl}\033[0m")
                matched_tag = True
                break
        if matched_tag:
            continue
        d = RE_SAYS_FMT.match(s)
        if d:
            name = d.group(1).strip()
            quote = d.group(3).strip().strip('"')
            col = comp_colors.get(name.lower(), "\033[97m")
            print(f"  {col}\033[1m{name}:\033[0m {col}\"{quote}\"\033[0m")
            continue
        import textwrap as _tw
        if RE_DAMAGE.search(s):
            for wl in _tw.wrap(s, 74): print(f"  \033[91m{wl}\033[0m")
        elif RE_GOLD.search(s):
            for wl in _tw.wrap(s, 74): print(f"  \033[93m{wl}\033[0m")
        elif RE_MAGIC.search(s):
            for wl in _tw.wrap(s, 74): print(f"  \033[95m{wl}\033[0m")
        else:
            for wl in _tw.wrap(s, 74): print(f"  \033[96m{wl}\033[0m")
    print("\033[95m" + "=" * 78 + "\033[0m")
    print()

# ══════════════════════ D&D STATS ═════════════════════════════
STAT_NAMES = ["STR","DEX","CON","INT","WIS","CHA"]

def roll_4d6() -> int:
    r = sorted([random.randint(1,6) for _ in range(4)])
    return sum(r[1:])

def gen_stats() -> Dict[str,int]:
    return {s: roll_4d6() for s in STAT_NAMES}

def mod(score: int) -> int: return (score - 10) // 2
def mstr(score: int) -> str:
    m = mod(score); return f"+{m}" if m >= 0 else str(m)

def roll(sides:int, count:int=1, bonus:int=0) -> tuple:
    rolls = [random.randint(1,sides) for _ in range(count)]
    return sum(rolls)+bonus, rolls

# ══════════════════════ SPELL SYSTEM ══════════════════════════
# Great Old One Warlock spell list (Pact Magic — short rest recharge)
GOO_WARLOCK_SPELLS = {
    "cantrips": [
        {"name":"Eldritch Blast",    "damage":"1d10","dtype":"force",
         "desc":"A crackling beam of alien energy tears across space toward your foe."},
        {"name":"Mind Sliver",       "damage":"1d6", "dtype":"psychic",
         "desc":"You drive a spike of alien thought into the target's mind, scrambling their focus."},
        {"name":"Toll the Dead",     "damage":"1d8", "dtype":"necrotic",
         "desc":"A funereal bell tolls from somewhere beyond — necrotic energy washes over your foe."},
        {"name":"Prestidigitation",  "damage":"0",   "dtype":"utility",
         "desc":"Small impossible things happen around you — sounds, smells, cold spots."},
    ],
    "spells": [
        {"name":"Hex",               "damage":"1d6 bonus","dtype":"curse",   "slots":1,
         "desc":"A mark appears on your target. Each time you hit them, they feel your patron watching."},
        {"name":"Dissonant Whispers","damage":"3d6",      "dtype":"psychic", "slots":1,
         "desc":"You whisper something that was never meant for mortal ears. The target flees in screaming terror."},
        {"name":"Detect Thoughts",   "damage":"0",        "dtype":"psychic", "slots":1,
         "desc":"You reach out and brush the surface of nearby minds. The world goes very quiet."},
        {"name":"Hunger of Hadar",   "damage":"2d6",      "dtype":"void",    "slots":2,
         "desc":"A sphere of blackness and teeth erupts around your foes. Something from outside hungers."},
        {"name":"Synaptic Static",   "damage":"8d6",      "dtype":"psychic", "slots":5,
         "desc":"You channel pure alien madness in a burst of psychic devastation. Even you feel it."},
    ]
}

# Slots by class/level (Warlock uses Pact Magic)
SLOT_TABLE = {
    "Warlock": {1:1,2:2,3:2,4:2,5:2,6:2,7:2,8:2,9:2,10:2,11:3,12:3,13:3,14:3},
    "Wizard":  {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Sorcerer":{1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Cleric":  {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Druid":   {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Bard":    {1:2,2:3,3:4,4:6,5:7,6:9,7:10,8:11,9:12},
    "Paladin": {1:2,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6},
    "Ranger":  {1:2,2:2,3:3,4:3,5:4,6:4,7:5,8:5,9:6},
}

def max_slots(char:dict) -> int:
    tbl = SLOT_TABLE.get(char.get("class","Fighter"),{})
    return tbl.get(min(char.get("level",1), max(tbl.keys(),default=1)), 0) if tbl else 0

def init_slots(char:dict):
    char["spell_slots_max"]     = max_slots(char)
    char["spell_slots_current"] = char["spell_slots_max"]

def get_spells(char:dict) -> dict:
    cls = char.get("class","Fighter")
    if cls == "Warlock": return GOO_WARLOCK_SPELLS
    # Generic fallback for other casters
    return {"cantrips":[],"spells":[]}

# ══════════════════════ CONDITIONS ════════════════════════════
CONDITIONS = {
    "bleeding":  (C.RED,    "Losing 1d4 HP per turn until treated"),
    "burning":   (C.ORANGE, "1d6 fire damage per turn"),
    "poisoned":  (C.GREEN,  "-2 to attacks and saves"),
    "cursed":    (C.MAGENTA,"Disadvantage on ability checks"),
    "near-death":(C.RED,    "One bad hit could end you"),
}

def add_condition(char:dict, cond:str):
    char.setdefault("conditions",[])
    if cond not in char["conditions"]:
        char["conditions"].append(cond)
        col,desc = CONDITIONS.get(cond,(C.ORANGE,""))
        cprint(col, f"  ⚠  {char['name']} is now {cond.upper()}! {desc}")

def remove_condition(char:dict, cond:str):
    if cond in char.get("conditions",[]):
        char["conditions"].remove(cond)
        cprint(C.GREEN, f"  ✓  {char['name']} is no longer {cond}.")

def tick_conditions(char:dict) -> int:
    total = 0
    for cond in char.get("conditions",[]):
        if cond == "bleeding":
            dmg,_ = roll(4); total += dmg
            cprint(C.RED, f"  💉 {char['name']} bleeds for {dmg} damage!")
        elif cond == "burning":
            dmg,_ = roll(6); total += dmg
            cprint(C.ORANGE, f"  🔥 {char['name']} burns for {dmg} damage!")
    return total

# ══════════════════════ GEAR ══════════════════════════════════
WEAPONS = {
    "Dagger":         {"damage":"1d4", "dtype":"piercing",    "value":2},
    "Shortsword":     {"damage":"1d6", "dtype":"piercing",    "value":10},
    "Longsword":      {"damage":"1d8", "dtype":"slashing",    "value":15},
    "Greatsword":     {"damage":"2d6", "dtype":"slashing",    "value":50},
    "Handaxe":        {"damage":"1d6", "dtype":"slashing",    "value":5},
    "Greataxe":       {"damage":"1d12","dtype":"slashing",    "value":30},
    "Quarterstaff":   {"damage":"1d6", "dtype":"bludgeoning", "value":2},
    "Shortbow":       {"damage":"1d6", "dtype":"piercing",    "value":25},
    "Longbow":        {"damage":"1d8", "dtype":"piercing",    "value":50},
    "Eldritch Focus": {"damage":"1d10","dtype":"force",       "value":60},
    "Arcane Tome":    {"damage":"1d6", "dtype":"psychic",     "value":75},
}
ARMORS = {
    "Leather Armor":   {"ac":11,"value":10},
    "Studded Leather": {"ac":12,"value":45},
    "Hide Armor":      {"ac":12,"value":10},
    "Chain Mail":      {"ac":16,"value":75},
    "Scale Mail":      {"ac":14,"value":50},
    "Breastplate":     {"ac":14,"value":400},
    "Half Plate":      {"ac":15,"value":750},
    "Full Plate":      {"ac":18,"value":1500},
    "Mage Robes":      {"ac":10,"value":30},
}
STARTING_GEAR = {
    "Fighter":   ("Longsword","Chain Mail"),
    "Wizard":    ("Arcane Tome","Mage Robes"),
    "Rogue":     ("Shortsword","Leather Armor"),
    "Cleric":    ("Quarterstaff","Chain Mail"),
    "Ranger":    ("Longbow","Studded Leather"),
    "Paladin":   ("Longsword","Chain Mail"),
    "Barbarian": ("Greataxe","Hide Armor"),
    "Bard":      ("Shortsword","Leather Armor"),
    "Druid":     ("Quarterstaff","Hide Armor"),
    "Monk":      ("Quarterstaff",""),
    "Sorcerer":  ("Arcane Tome","Mage Robes"),
    "Warlock":   ("Eldritch Focus","Mage Robes"),
}
HIT_DICE = {
    "Barbarian":12,"Fighter":10,"Paladin":10,"Ranger":10,
    "Cleric":8,"Druid":8,"Monk":8,"Rogue":8,"Bard":8,"Warlock":8,
    "Wizard":6,"Sorcerer":6
}
ITEM_STATES  = ["pristine","good","worn","damaged","broken"]
REPAIR_COSTS = {"pristine":0,"good":5,"worn":20,"damaged":60,"broken":120}

def item_cond(char:dict, item:str) -> str:
    return char.get("item_conditions",{}).get(item,"good")

def degrade_item(char:dict, slot:str):
    item = char.get("equipped",{}).get(slot,"")
    if not item: return
    cur = item_cond(char, item)
    idx = ITEM_STATES.index(cur)
    if idx < len(ITEM_STATES)-1:
        nxt = ITEM_STATES[idx+1]
        char.setdefault("item_conditions",{})[item] = nxt
        col = C.ORANGE if nxt in ("worn","damaged") else C.RED
        cprint(col, f"  ⚔  Your {item} is now {nxt.upper()}!")
        if nxt == "broken":
            cprint(C.RED, f"  ✗  Your {item} has BROKEN!")
            char["equipped"][slot] = ""

# ══════════════════════ DERIVED STATS ═════════════════════════
def max_hp(char:dict) -> int:
    hd  = HIT_DICE.get(char.get("class","Fighter"),8)
    con = mod(char.get("stats",{}).get("CON",12))
    lvl = char.get("level",1)
    return max(1, hd + con + (hd//2+1+con)*(lvl-1))

def calc_ac(char:dict) -> int:
    dex   = mod(char.get("stats",{}).get("DEX",10))
    armor = char.get("equipped",{}).get("armor","")
    if item_cond(char,armor) == "broken": return 10 + dex
    base  = ARMORS.get(armor,{}).get("ac",10)
    return base + (dex if "Plate" not in armor else 0)

def calc_atk(char:dict) -> int:
    prof   = 2 + (char.get("level",1)-1)//4
    weapon = char.get("equipped",{}).get("weapon","")
    if item_cond(char,weapon) == "broken": return 0
    stats  = char.get("stats",{})
    finesse = ["Dagger","Shortsword","Rapier"]
    arcane  = ["Arcane Tome","Eldritch Focus","Wand of Magic"]
    if any(f in weapon for f in finesse):
        sv = max(stats.get("STR",10), stats.get("DEX",10))
    elif any(a in weapon for a in arcane):
        sv = max(stats.get("INT",10), stats.get("CHA",10))
    else:
        sv = stats.get("STR",10)
    return mod(sv) + prof

def hp_color(char:dict) -> str:
    hp = char.get("hp",1); mhp = max_hp(char); pct = hp/mhp if mhp else 0
    return C.GREEN if pct > 0.5 else C.ORANGE if pct > 0.25 else C.RED

def hp_status(char:dict) -> str:
    hp = char.get("hp",1); mhp = max_hp(char); pct = hp/mhp if mhp else 0
    if hp <= 0:    return cc(C.RED,    "☠  UNCONSCIOUS")
    if pct <= 0.25:return cc(C.RED,    "💀 NEAR DEATH")
    if pct <= 0.5: return cc(C.ORANGE, "🩸 BLOODIED")
    if pct <= 0.75:return cc(C.YELLOW, "⚠  WOUNDED")
    return cc(C.GREEN, "♥  HEALTHY")

# ══════════════════════ NOTORIETY ═════════════════════════════
NOTORIETY = [
    (-1000,-601,"Villain",   C.RED,    "Your name is spoken in fearful whispers."),
    (-600, -301,"Outlaw",    C.ORANGE, "Wanted posters bear your likeness."),
    (-300,  -51,"Scoundrel", C.YELLOW, "Folk eye you with suspicion."),
    (-50,    50,"Wanderer",  C.GRAY,   "Your reputation is unwritten."),
    (51,    300,"Goodfellow",C.GREEN,  "People smile when you enter a room."),
    (301,   600,"Champion",  C.CYAN,   "Bards sing of your deeds."),
    (601,  1000,"Legend",    C.MAGENTA,"Your name alone inspires courage."),
]

def get_rep(score:int) -> tuple:
    for lo,hi,title,col,flavor in NOTORIETY:
        if lo <= score <= hi: return title,col,flavor
    return "Wanderer",C.GRAY,"Your reputation is unwritten."

def rep_side(score:int) -> str:
    return "heralded" if score>50 else "infamous" if score<-50 else "neutral"

def apply_notoriety(char:dict, delta:int, reason:str) -> str:
    old = char.get("notoriety_score",0); old_t,_,_ = get_rep(old)
    new = max(-1000,min(1000,old+delta)); char["notoriety_score"] = new
    t,col,flavor = get_rep(new)
    sign = "+" if delta>=0 else ""
    dcol = C.GREEN if delta>0 else C.RED
    msg  = f"{dcol}  [Notoriety {sign}{delta}: {reason}]{C.RESET}"
    if old_t != t:
        msg += f"\n{col}  {'★'*40}\n  You are now known as: {bold(t)}\n  {flavor}\n  {'★'*40}{C.RESET}"
    return msg

# ══════════════════════ XP ════════════════════════════════════
XP_THRESH = {
    1:300,2:900,3:2700,4:6500,5:14000,6:23000,7:34000,
    8:48000,9:64000,10:85000,11:100000,12:120000,13:140000,
    14:165000,15:195000,16:225000,17:265000,18:305000,19:355000
}
def xp_next(lvl:int) -> int: return XP_THRESH.get(lvl,999999)
def lvl_up_check(char:dict) -> Optional[int]:
    lvl = char.get("level",1)
    return lvl+1 if lvl<20 and char.get("xp",0)>=xp_next(lvl) else None

# ══════════════════════ SAVE/LOAD ═════════════════════════════
def load_chars() -> Dict[str,dict]:
    if not os.path.exists(CHARACTERS_FILE): return {}
    try:
        with open(CHARACTERS_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_chars(chars:Dict[str,dict]):
    with open(CHARACTERS_FILE,"w",encoding="utf-8") as f:
        json.dump(chars,f,indent=2,ensure_ascii=False)

def load_campaign() -> dict:
    if not os.path.exists(SOLO_SAVE_FILE):
        return {
            "title":"A Solo Journey","tone":"Gritty adventure with room for redemption.",
            "difficulty":"normal","world_notes":[
                "The world is fractured — old empires crumbled, new ones rise.",
                "Magic is rare and feared by common folk.",
                "The roads are dangerous but rich with opportunity.",
                "Something vast and ancient stirs in the dark between the stars.",
            ],
            "session_log":[],"session_number":1,"story_so_far":[],
        }
    with open(SOLO_SAVE_FILE,"r",encoding="utf-8") as f: return json.load(f)

def save_campaign(state:dict):
    with open(SOLO_SAVE_FILE,"w",encoding="utf-8") as f:
        json.dump(state,f,indent=2,ensure_ascii=False)

# ══════════════════════ AI ════════════════════════════════════
def ai_call(messages:list, max_tokens:int=MAX_TOKENS) -> str:
    try:
        r = client.chat.completions.create(
            model=MODEL, messages=messages,
            temperature=0.85, max_tokens=max_tokens)
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"[The world holds its breath... AI error: {e}]"


def validate_action(state:dict, player:dict, user_input:str) -> tuple:
    """Check if a free-form action makes sense in context."""
    recent = " | ".join(state["session_log"][-4:])
    check  = ai_call([{"role":"user","content":
        f"You are a D&D referee. One word only — YES or NO: "
        f"Is this action physically possible and contextually sensible? "
        f"Scene: {recent} | Action: {user_input} "
        f"Answer only YES or NO."}], max_tokens=5)
    return "yes" in check.lower(), check.strip()

def build_prompt(state:dict, player:dict, companions:List[dict]) -> str:
    """Ultra-tight system prompt — less is more for local models."""
    eq   = player.get("equipped",{})
    hp   = player.get("hp",1); mhp = max_hp(player); pct = hp/mhp if mhp else 1
    slots= player.get("spell_slots_current",0); mslots=player.get("spell_slots_max",0)
    conds= player.get("conditions",[])
    t,_,_= get_rep(player.get("notoriety_score",0))

    if pct <= 0.25:   hp_note = f"NEAR DEATH ({hp}/{mhp}hp) — describe as desperate, staggering"
    elif pct <= 0.5:  hp_note = f"bloodied ({hp}/{mhp}hp) — show strain"
    else:             hp_note = f"healthy ({hp}/{mhp}hp)"

    comp_str = ""
    for c in companions:
        if c.get("alive",True):
            chp=c.get("hp","?"); cmhp=max_hp(c)
            comp_str += f"  {c['name']} ({c['class']}): {chp}/{cmhp}hp | {c['personality']}\n"

    story_str = ""
    if state.get("story_so_far"):
        story_str = "Story so far: " + state["story_so_far"][-1][:200]

    cond_str = f" CONDITIONS: {','.join(conds)}" if conds else ""
    slot_str = f" Slots:{slots}/{mslots}" if mslots else ""

    pname = player['name']
    prace = player['race']
    pcls  = player['class']
    return f"""You are a Dungeon Master running a D&D adventure.

CHARACTER: {pname} ({prace} {pcls} Lv{player['level']}) — {hp_note}{cond_str}{slot_str}
WEAPON: {eq.get('weapon','none')} | ARMOR: {eq.get('armor','none')} | GOLD: {player.get('gold',0)}gp
PARTY: {comp_str.strip() or 'traveling alone'}
{story_str}

CRITICAL: You are narrating for {pname} ONLY. Do not narrate actions for any other player character.
If companions act, describe their actions briefly. {pname} is the hero of this story.

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
    import re

    # Pre-process: strip meta-labels and template artifacts
    text = re.sub(r'^(PARAGRAPH|NPC LINE|NPC|SCENE|NARRATION|STORY|ACTION|CHOICE|OUTCOME):\s*', '', raw, flags=re.MULTILINE|re.IGNORECASE)
    # Strip literal template tags the model echoes back
    text = re.sub(r'\[2 sentences[^\]]*\]\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^NAME:\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\[NAME\][^"]*"', '', text, flags=re.MULTILINE)
    # Strip numbered list prefixes "1. " "2. " "6. [A]" etc
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s*(\[)', r'\1', text, flags=re.MULTILINE)
    # Normalize "A: text" / "B: text" at line start to [A]/[B]
    text = re.sub(r'^A:\s+', '[A] ', text, flags=re.MULTILINE)
    text = re.sub(r'^B:\s+', '[B] ', text, flags=re.MULTILINE)
    # Strip markdown bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Force [O] to always be plain "[O] Other" — never custom content
    text = re.sub(r'\[O\].*', '[O] Other', text)
    # CUT everything after [O] Other — model keeps adding narration after choices
    if '[O] Other' in text:
        text = text[:text.index('[O] Other') + len('[O] Other')]
    raw = text

    SKIP_IF_STARTS = [
        "narration:","hp:","gold:","companions:","stats:","spells:","conditions:",
        "leveled spells:","cantrips:","weapon:","armor:","spell slots:","xp:",
        "compiled by","butterfly effect","continued...","(continued",
        "- strength","- dexterity","- constitution","- intelligence",
        "- wisdom","- charisma",
    ]
    SKIP_IF_CONTAINS = [
        "implications for","has implications",
        "'s health:","'s stats:","'s gold:","'s spell",
        "hp (confident)","hp (healthy)","hp (bloodied)","hp (near death)",
    ]
    SKIP_RE = [
        re.compile(r"^(STR|DEX|CON|INT|WIS|CHA|AC|ATK|HP|XP)[\t :]", re.I),
        re.compile(r"^compiled by", re.I),
        re.compile(r"^butterfly", re.I),
        re.compile(r"^\-\s+(strength|dexterity|constitution|intelligence|wisdom|charisma)\b", re.I),
        re.compile(r"\d+/\d+\s*hp\s*\(", re.I),
    ]

    lines = raw.split("\n")
    seen_a = False
    out = []

    for line in lines:
        s = line.strip()
        if not s:
            out.append("")
            continue
        sl = s.lower()
        if any(sl.startswith(p) for p in SKIP_IF_STARTS):
            continue
        if any(p in sl for p in SKIP_IF_CONTAINS):
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

def get_response(state:dict, player:dict, companions:List[dict], user_input:str) -> str:
    msgs = [{"role":"system","content":build_prompt(state,player,companions)}]
    # Only last 4 exchanges — less context = less confusion for local models
    for entry in state["session_log"][-4:]:
        role = "assistant" if entry.startswith("[DM]") else "user"
        content = entry.replace("[DM] ","").replace("[YOU] ","")
        # Trim long AI responses in history to just first 120 chars
        if role == "assistant": content = content[:120] + ("..." if len(content)>120 else "")
        msgs.append({"role":role,"content":content})
    msgs.append({"role":"user","content":user_input})
    raw = ai_call(msgs, max_tokens=260)
    return clean_response(raw)

# ══════════════════════ NPC ARCHETYPES ════════════════════════
ARCHETYPES = {
    "1":{"name":"Gruff Veteran",   "personality":"Blunt, battle-hardened, few words but unshakeable loyalty once earned.","bias":0,   "class":"Fighter","race":"Dwarf"},
    "2":{"name":"Eager Scholar",   "personality":"Curious, bookish, brilliant under pressure but tends to overthink.","bias":150,"class":"Wizard", "race":"Human"},
    "3":{"name":"Charming Rogue",  "personality":"Quick with a joke and quicker with a knife. Morally flexible.","bias":-100,"class":"Rogue",  "race":"Half-Elf"},
    "4":{"name":"Zealous Cleric",  "personality":"Devoted to their deity, judgmental of sin, heals without question.","bias":300,"class":"Cleric", "race":"Human"},
    "5":{"name":"Wild Ranger",     "personality":"Speaks more to animals than people. Unpredictable but fiercely protective.","bias":50, "class":"Ranger", "race":"Wood Elf"},
    "6":{"name":"Bitter Mercenary","personality":"Only in it for coin. Complains constantly but never deserts mid-contract.","bias":-200,"class":"Fighter","race":"Half-Orc"},
}

def make_npc(key:str, name:str, cls:str, race:str, notes:str="") -> dict:
    arch = ARCHETYPES[key]; stats = gen_stats()
    w,a  = STARTING_GEAR.get(cls,("Dagger",""))
    inv  = [w]+([a] if a else [])
    npc  = {
        "name":name,"type":"npc","class":cls,"race":race,
        "level":1,"xp":0,"stats":stats,
        "hp":max_hp({"class":cls,"level":1,"stats":stats}),
        "gold":random.randint(3,12),
        "notoriety_score":arch["bias"],"personality":arch["personality"],"archetype":arch["name"],
        "inventory":inv,"equipped":{"weapon":w,"armor":a,"offhand":"","accessory":""},
        "item_conditions":{},"conditions":[],
        "notes":notes,"alive":True,"sessions_played":0,
        "last_seen":datetime.now().strftime("%Y-%m-%d"),
    }
    init_slots(npc); return npc

# ══════════════════════ CHARACTER CREATION ════════════════════
def create_char(existing:dict) -> dict:
    header("CREATE YOUR CHARACTER", C.MAGENTA)
    classes = list(STARTING_GEAR.keys())
    races   = ["Human","Elf","Dwarf","Halfling","Half-Orc","Half-Elf","Gnome","Tiefling","Dragonborn"]

    while True:
        name = input(f"  {C.CYAN}Character name:{C.RESET} ").strip()
        if not name: continue
        if name in existing:
            cprint(C.YELLOW, f"  '{name}' already exists.")
            if input("  Load existing? (y/n): ").strip().lower()=="y": return existing[name]
            continue
        break

    cprint(C.BLUE, "\n  Classes:", wrap_text=False)
    for i,c in enumerate(classes,1): print(f"  {C.GRAY}{i:2}.{C.RESET} {c}")
    while True:
        try: cls=classes[int(input(f"  {C.CYAN}Choose class:{C.RESET} "))-1]; break
        except: cprint(C.RED,"  Invalid.")

    cprint(C.BLUE, "\n  Races:", wrap_text=False)
    for i,r in enumerate(races,1): print(f"  {C.GRAY}{i:2}.{C.RESET} {r}")
    while True:
        try: race=races[int(input(f"  {C.CYAN}Choose race:{C.RESET} "))-1]; break
        except: cprint(C.RED,"  Invalid.")

    backstory = input(f"\n  {C.CYAN}Brief backstory (Enter to skip):{C.RESET} ").strip()

    cprint(C.MAGENTA, "\n  Rolling stats (4d6 drop lowest)...", wrap_text=False)
    stats = gen_stats()
    for s,v in stats.items():
        bar = cc(C.MAGENTA,"█"*(v//2)) + cc(C.GRAY,"░"*(9-v//2))
        col = C.GREEN if v>=15 else C.YELLOW if v>=12 else C.GRAY
        print(f"  {C.BOLD}{s}{C.RESET}  {col}{v:2}{C.RESET} ({mstr(v):>3})  {bar}")

    if input(f"\n  {C.CYAN}Reroll? (y/n):{C.RESET} ").strip().lower()=="y":
        stats = gen_stats()
        cprint(C.MAGENTA, "  New rolls:", wrap_text=False)
        for s,v in stats.items():
            bar = cc(C.MAGENTA,"█"*(v//2))+cc(C.GRAY,"░"*(9-v//2))
            col = C.GREEN if v>=15 else C.YELLOW if v>=12 else C.GRAY
            print(f"  {C.BOLD}{s}{C.RESET}  {col}{v:2}{C.RESET} ({mstr(v):>3})  {bar}")

    w,a = STARTING_GEAR.get(cls,("Dagger",""))
    inv = [w]+([a] if a else [])+["Adventurer's pack"]

    char = {
        "name":name,"type":"player","class":cls,"race":race,
        "level":1,"xp":0,"stats":stats,
        "hp":max_hp({"class":cls,"level":1,"stats":stats}),
        "gold":15,"notoriety_score":0,
        "inventory":inv,
        "equipped":{"weapon":w,"armor":a,"offhand":"","accessory":""},
        "item_conditions":{},"conditions":[],
        "notes":backstory,"sessions_played":0,
        "last_seen":datetime.now().strftime("%Y-%m-%d"),
        "companions_lost":[],
    }
    init_slots(char)
    mhp = max_hp(char)
    cprint(C.GREEN,  f"\n  {name} the {race} {cls} steps into the world!")
    cprint(C.YELLOW, f"  HP:{mhp} | AC:{calc_ac(char)} | Atk:{calc_atk(char):+d} | Gold:15gp")
    if char["spell_slots_max"]>0:
        cprint(C.MAGENTA, f"  Spell Slots:{char['spell_slots_max']}")
        if char.get("class")=="Warlock":
            cprint(C.GRAY, "  (Warlocks recover all slots on short rest)")
    return char

# ══════════════════════ RECRUIT COMPANION ═════════════════════
def recruit(player:dict, taken_names:list) -> Optional[dict]:
    header("RECRUIT A COMPANION", C.BLUE)
    p_side = rep_side(player.get("notoriety_score",0))
    for k,a in ARCHETYPES.items():
        side  = rep_side(a["bias"])
        label = cc(C.GREEN,"Heralded") if side=="heralded" else cc(C.RED,"Infamous") if side=="infamous" else cc(C.GRAY,"Neutral")
        print(f"  {C.BOLD}[{k}]{C.RESET} {a['name']} — {a['race']} {a['class']}")
        print(f"       {C.GRAY}{a['personality']}{C.RESET}")
        print(f"       Lean: {label}\n")

    ch = input("  Choose (1-6) or [S]kip: ").strip()
    if ch.upper()=="S" or ch not in ARCHETYPES: return None

    a = ARCHETYPES[ch]; npc_side = rep_side(a["bias"])
    if npc_side!="neutral" and npc_side!=p_side and p_side!="neutral":
        cprint(C.ORANGE,f"\n  ⚠  This companion leans {npc_side.upper()} — you are {p_side.upper()}.")
        cprint(C.ORANGE,"  They may betray, steal, or abandon you at the worst moment.")
        if input("  Recruit anyway? (y/n): ").strip().lower()!="y": return None

    while True:
        nm = input(f"  Name them (default: {a['name']}): ").strip() or a["name"]
        if nm not in taken_names: break
        cprint(C.RED,"  Name taken.")

    cls, race = a["class"], a["race"]
    classes = list(STARTING_GEAR.keys())
    races   = ["Human","Elf","Dwarf","Halfling","Half-Orc","Half-Elf","Gnome","Tiefling","Dragonborn"]
    if input(f"  Customize class/race? [{cls} {race}] (y/n): ").strip().lower()=="y":
        print("  "+"|".join(f"[{i+1}]{c}" for i,c in enumerate(classes)))
        try: cls=classes[int(input("  Class: "))-1]
        except: pass
        print("  "+"|".join(f"[{i+1}]{r}" for i,r in enumerate(races)))
        try: race=races[int(input("  Race: "))-1]
        except: pass

    notes = input("  Notes (Enter to skip): ").strip()
    npc   = make_npc(ch, nm, cls, race, notes)
    cprint(C.GREEN, f"\n  {nm} the {race} {cls} joins your party!")
    return npc

# ══════════════════════ NPC DEATH ═════════════════════════════
def npc_death(player:dict, npc:dict) -> str:
    npc["alive"] = False; loot = npc.get("inventory",[])
    print(f"\n{C.RED}{'═'*W}{C.RESET}")
    cprint(C.RED,    f"  {npc['name']} has fallen. Their story ends here.")
    cprint(C.YELLOW, f"  Belongings: {', '.join(loot) if loot else 'nothing'}")
    divider("─",C.GRAY)
    cprint(C.RED,   "  [L] Loot and leave   (Notoriety -50)",wrap_text=False)
    cprint(C.GREEN, "  [B] Bury with honor  (Notoriety +50)",wrap_text=False)
    cprint(C.GRAY,  "  [N] Leave untouched",wrap_text=False)
    print(f"{C.RED}{'═'*W}{C.RESET}")
    ch = input("  (L/B/N): ").strip().upper(); res=[]
    if ch=="L":
        if loot: player.setdefault("inventory",[]).extend(loot); res.append(cc(C.YELLOW,f"  You take: {', '.join(loot)}"))
        npc["inventory"]=[]; res.append(apply_notoriety(player,-50,f"looted {npc['name']}"))
    elif ch=="B":
        res.append(cc(C.CYAN,f"  You bury {npc['name']} with care."))
        res.append(apply_notoriety(player,+50,f"honored {npc['name']} in death"))
    else: res.append(cc(C.GRAY,f"  You leave {npc['name']} where they fell."))
    return "\n".join(res)

# ══════════════════════ STATUS SCREENS ════════════════════════
def show_status(p:dict):
    st=p.get("stats",{}); eq=p.get("equipped",{})
    t,col,flv=get_rep(p.get("notoriety_score",0))
    mhp=max_hp(p); hp=p.get("hp",mhp); hpct=hp/mhp if mhp else 0
    hc=hp_color(p); slots=p.get("spell_slots_current",0); msl=p.get("spell_slots_max",0)
    hpbar=cc(hc,"█"*int(hpct*30))+cc(C.GRAY,"░"*(30-int(hpct*30)))
    print(f"\n{C.BOLD}{C.BLUE}{'═'*W}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {p['name']} — {p['race']} {p['class']} | Lvl {p['level']}{C.RESET}")
    divider("─",C.GRAY)
    print(f"  HP: {hc}{hp}/{mhp}{C.RESET} [{hpbar}]  {hp_status(p)}")
    print(f"  AC: {cc(C.CYAN,str(calc_ac(p)))}  Atk: {cc(C.YELLOW,f'{calc_atk(p):+d}')}  Gold: {cc(C.YELLOW,str(p.get('gold',0))+' gp')}")
    if msl>0:
        sb=cc(C.MAGENTA,"◆"*slots)+cc(C.GRAY,"◇"*(msl-slots))
        print(f"  Spell Slots: {sb} {slots}/{msl}" + (" (recover on short rest)" if p.get("class")=="Warlock" else ""))
    divider("─",C.GRAY)
    print(f"  {C.BOLD}STATS:{C.RESET}")
    line="  "
    for s in STAT_NAMES:
        v=st.get(s,10); sc=C.GREEN if v>=15 else C.YELLOW if v>=12 else C.GRAY
        line+=f"{C.BOLD}{s}{C.RESET}:{sc}{v}{C.RESET}({mstr(v)})  "
    print(line)
    divider("─",C.GRAY)
    print(f"  {C.BOLD}EQUIPPED:{C.RESET}")
    for slot in ["weapon","armor","offhand","accessory"]:
        item=eq.get(slot,"")
        if item:
            cond=item_cond(p,item)
            cc2=C.GREEN if cond in ("pristine","good") else C.ORANGE if cond=="worn" else C.RED
            print(f"  {slot.capitalize():10} {cc(C.YELLOW,item)} [{cc2}{cond}{C.RESET}]")
        else: print(f"  {C.GRAY}{slot.capitalize():10} —{C.RESET}")
    divider("─",C.GRAY)
    print(f"  Reputation: {col}{bold(t)}{C.RESET}  ({p.get('notoriety_score',0):+d})")
    cprint(C.GRAY, f"  {flv}")
    if p.get("conditions"): cprint(C.ORANGE, f"  ⚠  Conditions: {', '.join(p['conditions']).upper()}", wrap_text=False)
    print(f"  XP: {p.get('xp',0)}/{xp_next(p['level'])} | Sessions: {p.get('sessions_played',0)}")
    print(f"{C.BOLD}{C.BLUE}{'═'*W}{C.RESET}")

def show_spells(p:dict):
    spells=get_spells(p); cls=p.get("class",""); slots=p.get("spell_slots_current",0); msl=p.get("spell_slots_max",0)
    header(f"{cls} SPELLS",C.MAGENTA)
    if spells.get("cantrips"):
        cprint(C.CYAN,"  CANTRIPS — free, unlimited:",wrap_text=False)
        for sp in spells["cantrips"]:
            dmg=f" — {sp['damage']} {sp['dtype']}" if sp['damage']!="0" else " — utility"
            print(f"  {C.BOLD}{sp['name']}{C.RESET}{C.GRAY}{dmg}{C.RESET}")
            cprint(C.GRAY,f"    {sp['desc']}")
    if spells.get("spells"):
        sb=cc(C.MAGENTA,"◆"*slots)+cc(C.GRAY,"◇"*(msl-slots))
        print(f"\n  {C.BOLD}SPELLS{C.RESET} — Slots: {sb} {slots}/{msl}")
        if cls=="Warlock": cprint(C.GRAY,"  (Warlocks recover all slots on short rest — visit the inn!)")
        for sp in spells["spells"]:
            avail=cc(C.GREEN,"✓") if slots>=sp.get("slots",1) else cc(C.RED,"✗")
            print(f"  {avail} {C.BOLD}{sp['name']}{C.RESET} [{sp.get('slots',1)} slot]  {sp['damage']} {sp['dtype']}")
            cprint(C.GRAY,f"     {sp['desc']}")
    divider("─",C.MAGENTA)

def _slot_ascii(slot:str) -> str:
    """ASCII body diagram slot labels."""
    return {"weapon":"⚔ R.HAND","armor":"🛡 BODY","offhand":"🗡 L.HAND","accessory":"💍 NECK"}.get(slot,"   ?   ")

def show_inventory(p:dict):
    inv  = p.get("inventory",[])
    eq   = p.get("equipped",{})
    eq_set = {v for v in eq.values() if v}
    stats  = p.get("stats",{})
    mhp    = max_hp(p); hp = p.get("hp",mhp)
    slots  = p.get("spell_slots_current",0); mslots = p.get("spell_slots_max",0)
    t,col,flavor = get_rep(p.get("notoriety_score",0))
    hpct   = hp/mhp if mhp else 0
    hcol   = C.GREEN if hpct>0.5 else C.ORANGE if hpct>0.25 else C.RED
    hpbar  = cc(hcol,"█"*int(hpct*24))+cc(C.GRAY,"░"*(24-int(hpct*24)))

    # ── Header ──────────────────────────────────────────────
    print(f"\n{C.BOLD}{C.YELLOW}╔{'═'*(W-2)}╗{C.RESET}")
    print(f"{C.BOLD}{C.YELLOW}║{C.RESET}  {C.BOLD}{C.CYAN}{p['name']}{C.RESET}  {C.GRAY}Lvl {p['level']} {p['race']} {p['class']}{C.RESET}")
    print(f"{C.YELLOW}╠{'═'*(W-2)}╣{C.RESET}")

    # ── Stats row ───────────────────────────────────────────
    stat_parts = []
    for s in STAT_NAMES:
        v = stats.get(s,10)
        sc = C.GREEN if v>=15 else C.YELLOW if v>=12 else C.GRAY
        stat_parts.append(f"{C.BOLD}{s}{C.RESET}:{sc}{v}{C.RESET}({mstr(v)})")
    print(f"{C.YELLOW}║{C.RESET}  " + "  ".join(stat_parts))

    # ── HP / AC / Gold ──────────────────────────────────────
    print(f"{C.YELLOW}║{C.RESET}  HP [{hpbar}] {hcol}{hp}/{mhp}{C.RESET}  AC:{cc(C.CYAN,str(calc_ac(p)))}  Atk:{cc(C.YELLOW,f'{calc_atk(p):+d}')}  {cc(C.YELLOW,str(p.get('gold',0))+' ⚜ gp')}")
    if mslots > 0:
        sb = cc(C.MAGENTA,"◆"*slots)+cc(C.GRAY,"◇"*(mslots-slots))
        rr = " (short rest)" if p.get("class")=="Warlock" else ""
        print(f"{C.YELLOW}║{C.RESET}  Spell Slots: {sb} {slots}/{mslots}{C.GRAY}{rr}{C.RESET}")
    print(f"{C.YELLOW}║{C.RESET}  Reputation: {col}{t}{C.RESET}  {C.GRAY}{flavor}{C.RESET}")
    if p.get("conditions"):
        cond_str = "  ".join(f"{C.ORANGE}⚠{c.upper()}{C.RESET}" for c in p["conditions"])
        print(f"{C.YELLOW}║{C.RESET}  {cond_str}")

    # ── Body diagram + equipped ──────────────────────────────
    print(f"{C.YELLOW}╠{'═'*(W-2)}╣{C.RESET}")
    print(f"{C.YELLOW}║{C.RESET}  {C.BOLD}EQUIPPED{C.RESET}")
    slot_display = {
        "weapon":  eq.get("weapon","—") or "—",
        "armor":   eq.get("armor","—") or "—",
        "offhand": eq.get("offhand","—") or "—",
        "accessory":eq.get("accessory","—") or "—",
    }
    slot_order = ["weapon","offhand","armor","accessory"]
    for slot in slot_order:
        item = slot_display[slot]
        cond = item_cond(p,item) if item != "—" else ""
        cc2  = C.GREEN if cond in ("pristine","good","") else C.ORANGE if cond=="worn" else C.RED
        slot_icon = _slot_ascii(slot)
        wdata = WEAPONS.get(item,{}); adata = ARMORS.get(item,{})
        stats_str = ""
        if wdata: stats_str = f" {C.GRAY}[{wdata.get('damage','?')} {wdata.get('dtype','?')}]{C.RESET}"
        elif adata: stats_str = f" {C.GRAY}[AC:{adata.get('ac','?')}]{C.RESET}"
        cond_str = f" {cc2}[{cond}]{C.RESET}" if cond else ""
        print(f"{C.YELLOW}║{C.RESET}    {C.GRAY}{slot_icon}{C.RESET}  {C.BOLD}{C.WHITE}{item}{C.RESET}{stats_str}{cond_str}")

    # ── Inventory list ───────────────────────────────────────
    print(f"{C.YELLOW}╠{'═'*(W-2)}╣{C.RESET}")
    print(f"{C.YELLOW}║{C.RESET}  {C.BOLD}BACKPACK{C.RESET}  {C.GRAY}({len(inv)} items){C.RESET}")
    if not inv:
        print(f"{C.YELLOW}║{C.RESET}    {C.GRAY}(empty){C.RESET}")
    for item in inv:
        is_eq   = item in eq_set
        cond    = item_cond(p,item)
        cc2     = C.GREEN if cond in ("pristine","good") else C.ORANGE if cond=="worn" else C.RED
        cd_str  = f" {cc2}[{cond}]{C.RESET}" if item in p.get("item_conditions",{}) else ""
        eq_tag  = cc(C.GREEN," ✓EQ") if is_eq else ""
        wdata   = WEAPONS.get(item,{}); adata = ARMORS.get(item,{})
        val     = wdata.get("value") or adata.get("value")
        val_str = cc(C.YELLOW,f"  {val//2}gp") if val else ""
        stat_s  = ""
        if wdata: stat_s = f"  {C.GRAY}{wdata.get('damage','?')} {wdata.get('dtype','?')}{C.RESET}"
        elif adata: stat_s = f"  {C.GRAY}AC:{adata.get('ac','?')}{C.RESET}"
        print(f"{C.YELLOW}║{C.RESET}    {C.WHITE}{item}{C.RESET}{eq_tag}{cd_str}{stat_s}{val_str}")

    # ── XP bar ──────────────────────────────────────────────
    xp     = p.get("xp",0); xp_nxt = xp_next(p["level"])
    xp_pct = min(1.0, xp/xp_nxt) if xp_nxt else 0
    xpbar  = cc(C.MAGENTA,"█"*int(xp_pct*30))+cc(C.GRAY,"░"*(30-int(xp_pct*30)))
    print(f"{C.YELLOW}╠{'═'*(W-2)}╣{C.RESET}")
    print(f"{C.YELLOW}║{C.RESET}  XP [{xpbar}] {xp}/{xp_nxt}  Sessions:{p.get('sessions_played',0)}")
    print(f"{C.BOLD}{C.YELLOW}╚{'═'*(W-2)}╝{C.RESET}")

def show_companions(comps:List[dict]):
    header("COMPANIONS",C.BLUE)
    if not comps: cprint(C.GRAY,"  Traveling alone."); return
    for c in comps:
        status=cc(C.GREEN,"● ALIVE") if c.get("alive",True) else cc(C.RED,"✝ DEAD")
        t,col,_=get_rep(c.get("notoriety_score",0)); st=c.get("stats",{})
        eq=c.get("equipped",{}); mhp=max_hp(c); hp=c.get("hp",mhp)
        hc=hp_color(c)
        print(f"\n  {C.BOLD}{c['name']}{C.RESET} {status} — {c['archetype']}")
        print(f"  {c['race']} {c['class']} Lvl {c['level']} | HP:{hc}{hp}/{mhp}{C.RESET} | AC:{calc_ac(c)}")
        print(f"  {col}{t}{C.RESET} | Gold:{c.get('gold',0)}gp")
        line="  "+" ".join(f"{s}:{cc(C.YELLOW,str(st.get(s,'?')))}" for s in STAT_NAMES)
        print(line)
        print(f"  Weapon:{cc(C.YELLOW,eq.get('weapon','none'))} Armor:{cc(C.YELLOW,eq.get('armor','none'))}")
        if c.get("conditions"): cprint(C.ORANGE,f"  ⚠ {', '.join(c['conditions']).upper()}",wrap_text=False)
        cprint(C.GRAY,f"  \"{c['personality']}\"")
    divider("─",C.BLUE)

# ══════════════════════ EQUIP / TRADE ═════════════════════════
def equip_item(p:dict, item_name:str):
    inv = p.get("inventory", [])
    found = next((i for i in inv if i.lower() == item_name.lower()), None)
    if not found:
        cprint(C.RED, f"  '{item_name}' not in inventory.")
        return
    match = found
    eq=p.setdefault("equipped",{"weapon":"","armor":"","offhand":"","accessory":""})
    if match in WEAPONS:
        old=eq.get("weapon",""); eq["weapon"]=match
        cprint(C.GREEN,f"  Equipped {match} as weapon."+(f" (replaced {old})" if old else ""))
    elif match in ARMORS:
        old=eq.get("armor",""); eq["armor"]=match
        cprint(C.GREEN,f"  Equipped {match} as armor."+(f" (replaced {old})" if old else ""))
    else:
        sl=input(f"  Equip '{match}' as [O]ff-hand or [A]ccessory? ").strip().upper()
        if sl=="O": eq["offhand"]=match; cprint(C.GREEN,f"  Off-hand: {match}")
        else: eq["accessory"]=match; cprint(C.GREEN,f"  Accessory: {match}")

def unequip_item(p:dict, slot:str):
    slot=slot.lower()
    if slot not in {"weapon","armor","offhand","accessory"}: cprint(C.RED,"  Slots: weapon armor offhand accessory"); return
    eq=p.get("equipped",{}); old=eq.get(slot,"")
    if not old: cprint(C.YELLOW,f"  Nothing in {slot}."); return
    eq[slot]=""; cprint(C.YELLOW,f"  Unequipped {old}.")

def do_trade(p:dict, comps:List[dict], name:str):
    target=next((c for c in comps if c["name"].lower()==name.lower() and c.get("alive",True)),None)
    if not target: cprint(C.RED,f"  '{name}' not found."); return
    show_inventory(p)
    cprint(C.BLUE,f"  {target['name']}: {', '.join(target.get('inventory',[]))} | Gold:{target.get('gold',0)}gp",wrap_text=False)
    d=input("\n  [G]ive  [T]ake  [M]oney: ").strip().upper()
    if d=="G":
        item=input("  Give which item? ").strip()
        if item in p.get("inventory",[]):
            p["inventory"].remove(item); target.setdefault("inventory",[]).append(item)
            cprint(C.GREEN,f"  Gave {item} to {target['name']}.")
        else: cprint(C.RED,f"  You don't have '{item}'.")
    elif d=="T":
        item=input(f"  Take what from {target['name']}? ").strip()
        if item in target.get("inventory",[]):
            target["inventory"].remove(item); p.setdefault("inventory",[]).append(item)
            cprint(C.GREEN,f"  Took {item}.")
        else: cprint(C.RED,f"  {target['name']} doesn't have that.")
    elif d=="M":
        try:
            amt=int(input("  Gold to give: "))
            if amt<=p.get("gold",0):
                p["gold"]-=amt; target["gold"]=target.get("gold",0)+amt
                cprint(C.YELLOW,f"  Gave {amt}gp to {target['name']}.")
            else: cprint(C.RED,"  Not enough gold.")
        except ValueError: cprint(C.RED,"  Invalid.")

# ══════════════════════ MERCHANT ══════════════════════════════
def visit_merchant(p:dict):
    header("MERCHANT",C.YELLOW)
    cprint(C.GRAY,"  A weathered merchant eyes your coin pouch with practiced interest.\n")
    while True:
        cprint(C.YELLOW,f"  Gold: {p.get('gold',0)} gp",wrap_text=False)
        print(f"  {C.BOLD}[B]{C.RESET}uy  {C.BOLD}[S]{C.RESET}ell  {C.BOLD}[R]{C.RESET}epair  {C.BOLD}[L]{C.RESET}eave")
        action=input("  > ").strip().upper()
        if action=="L": cprint(C.GRAY,"  'Safe travels.'"); break

        elif action=="B":
            all_items=list(WEAPONS.items())+list(ARMORS.items())
            cprint(C.YELLOW,"\n  ── FOR SALE ──────────────────────────────────────",wrap_text=False)
            for i,(name,data) in enumerate(all_items,1):
                val=data.get("value",0); extra=data.get("damage","") or f"AC:{data.get('ac','?')}"
                can=cc(C.GREEN,"✓") if p.get("gold",0)>=val else cc(C.RED,"✗")
                print(f"  {can} [{i:2}] {C.WHITE}{name:22}{C.RESET} {C.GRAY}{str(extra):14}{C.RESET} {cc(C.YELLOW,str(val)+' gp')}")
            print(f"  {C.GRAY}[0] Cancel{C.RESET}")
            try:
                ch=int(input("\n  Buy which? "))
                if ch==0: continue
                if 1<=ch<=len(all_items):
                    nm,dt=all_items[ch-1]; price=dt["value"]
                    if COMBAT_AVAILABLE: price=apply_merchant_discount(price,p)
                    if p.get("gold",0)>=price:
                        p["gold"]-=price; p.setdefault("inventory",[]).append(nm)
                        p.setdefault("item_conditions",{})[nm]="pristine"
                        cprint(C.GREEN,f"  Bought {nm} for {price}gp.")
                        cprint(C.YELLOW,f"  Gold: {p['gold']}gp")
                        if input("  Equip now? (y/n): ").strip().lower()=="y": equip_item(p,nm)
                    else: cprint(C.RED,f"  Need {price}gp, have {p.get('gold',0)}gp.")
            except (ValueError,IndexError): cprint(C.RED,"  Invalid.")

        elif action=="S":
            inv=p.get("inventory",[]); sellable=[]
            if not inv: cprint(C.YELLOW,"  Nothing to sell."); continue
            cprint(C.YELLOW,"\n  ── YOUR ITEMS ────────────────────────────────────",wrap_text=False)
            for i,item in enumerate(inv,1):
                val=WEAPONS.get(item,{}).get("value") or ARMORS.get(item,{}).get("value")
                if val:
                    cond=item_cond(p,item)
                    mult={"pristine":1.0,"good":0.8,"worn":0.5,"damaged":0.3,"broken":0.1}.get(cond,0.8)
                    sp=max(1,int(val//2*mult))
                    cc2=C.GREEN if cond in ("pristine","good") else C.ORANGE if cond=="worn" else C.RED
                    print(f"  [{i}] {C.WHITE}{item:25}{C.RESET} [{cc2}{cond}{C.RESET}] ~{cc(C.YELLOW,str(sp)+'gp')}")
                    sellable.append((i,item,sp))
                else: print(f"  {C.GRAY}[{i}] {item:25} (no value){C.RESET}")
            print(f"  {C.GRAY}[0] Cancel{C.RESET}")
            try:
                ch=int(input("\n  Sell which? "))
                if ch==0: continue
                m=next(((i,n,s) for i,n,s in sellable if i==ch),None)
                if m:
                    _,nm,sp=m; eq=p.get("equipped",{})
                    for sl,v in eq.items():
                        if v==nm: eq[sl]=""; cprint(C.YELLOW,f"  Unequipped {nm}.")
                    p["inventory"].remove(nm); p["gold"]=p.get("gold",0)+sp
                    cprint(C.GREEN,f"  Sold {nm} for {sp}gp. Gold: {p['gold']}gp")
                else: cprint(C.RED,"  Can't sell that.")
            except (ValueError,IndexError): cprint(C.RED,"  Invalid.")

        elif action=="R":
            broken=[( item,cond) for item,cond in p.get("item_conditions",{}).items()
                    if cond not in ("pristine","good") and item in p.get("inventory",[])]
            if not broken: cprint(C.GREEN,"  All gear in good shape!"); continue
            cprint(C.BLUE,"\n  ── REPAIRS ───────────────────────────────────────",wrap_text=False)
            for i,(item,cond) in enumerate(broken,1):
                cost=REPAIR_COSTS.get(cond,30)
                can=cc(C.GREEN,"✓") if p.get("gold",0)>=cost else cc(C.RED,"✗")
                cc2=C.ORANGE if cond in ("worn","damaged") else C.RED
                print(f"  {can} [{i}] {C.WHITE}{item:25}{C.RESET} [{cc2}{cond}{C.RESET}] {cc(C.YELLOW,str(cost)+'gp')}")
            print(f"  {C.GRAY}[0] Cancel{C.RESET}")
            try:
                ch=int(input("\n  Repair which? "))
                if ch==0: continue
                if 1<=ch<=len(broken):
                    nm,cond=broken[ch-1]; cost=REPAIR_COSTS.get(cond,30)
                    if p.get("gold",0)>=cost:
                        p["gold"]-=cost; p.setdefault("item_conditions",{})[nm]="good"
                        cprint(C.GREEN,f"  {nm} repaired to GOOD. Gold: {p['gold']}gp")
                    else: cprint(C.RED,f"  Need {cost}gp.")
            except (ValueError,IndexError): cprint(C.RED,"  Invalid.")

# ══════════════════════ INN ═══════════════════════════════════
def visit_inn(p:dict, comps:List[dict], state:dict):
    header("THE INN — The Wanderer's Rest",C.CYAN)
    cprint(C.CYAN,"  Warm firelight and the smell of roasted meat fill the air.")
    cprint(C.CYAN,"  The innkeeper nods as you enter.\n")
    while True:
        cprint(C.YELLOW,f"  Gold: {p.get('gold',0)}gp",wrap_text=False)
        mhp=max_hp(p); hp=p.get("hp",mhp)
        slots=p.get("spell_slots_current",0); msl=p.get("spell_slots_max",0)
        print(f"  HP: {hp_color(p)}{hp}/{mhp}{C.RESET}  |  Slots: {cc(C.MAGENTA,str(slots))}/{msl}\n")
        print(f"  {C.BOLD}[1]{C.RESET} Short Rest (free) — recover spell slots + some HP")
        print(f"  {C.BOLD}[2]{C.RESET} Long Rest  (5gp)  — full HP, all slots, clear conditions")
        print(f"  {C.BOLD}[3]{C.RESET} Rent a room (2gp) — save your progress")
        print(f"  {C.BOLD}[4]{C.RESET} Buy a drink (1gp) — hear a rumor")
        print(f"  {C.BOLD}[L]{C.RESET} Leave")
        action=input("\n  > ").strip().upper()

        if action=="L": cprint(C.GRAY,"  You step back out into the night."); break

        elif action=="1":
            old=p.get("spell_slots_current",0); init_slots(p); rec=p["spell_slots_current"]-old
            cprint(C.CYAN,"\n  You find a quiet corner and rest for an hour.")
            if p.get("class")=="Warlock" and rec>0:
                cprint(C.MAGENTA,f"  Your pact magic stirs in the dark — {rec} slot(s) recovered!")
            elif rec>0: cprint(C.GREEN,f"  {rec} spell slot(s) recovered.")
            con_rec=max(1,p.get("level",1)//2+mod(p.get("stats",{}).get("CON",10)))
            p["hp"]=min(max_hp(p),p.get("hp",max_hp(p))+con_rec)
            cprint(C.GREEN,f"  Recovered {con_rec} HP. ({p['hp']}/{max_hp(p)})")
            for c in comps:
                if c.get("alive",True):
                    if c.get("class")=="Warlock": init_slots(c)
                    c["hp"]=min(max_hp(c),c.get("hp",max_hp(c))+max(1,c.get("level",1)//2))

        elif action=="2":
            if p.get("gold",0)>=5:
                p["gold"]-=5; mhp2=max_hp(p); p["hp"]=mhp2
                init_slots(p); p["conditions"]=[]
                cprint(C.GREEN,"\n  You sleep deeply. All wounds healed.")
                cprint(C.GREEN,f"  HP: {mhp2}/{mhp2}")
                if p.get("spell_slots_max",0)>0:
                    cprint(C.MAGENTA,f"  Spell slots: {p['spell_slots_current']}/{p['spell_slots_max']} restored")
                cprint(C.GREEN,"  All conditions cleared.")
                for c in comps:
                    if c.get("alive",True):
                        c["hp"]=max_hp(c); init_slots(c); c["conditions"]=[]
                        cprint(C.GREEN,f"  {c['name']} fully rested.")
            else: cprint(C.RED,"  Long rest costs 5gp.")

        elif action=="3":
            if p.get("gold",0)>=2:
                p["gold"]-=2
                cprint(C.CYAN,"\n  A small but clean room. You sleep soundly.")
                cprint(C.GREEN,"  Progress saved."); save_campaign(state); save_chars({p["name"]:p})
            else: cprint(C.RED,"  A room costs 2gp.")

        elif action=="4":
            if p.get("gold",0)>=1:
                p["gold"]-=1; cprint(C.GRAY,"\n  Generating a rumor...\n")
                rumor=ai_call([{"role":"user","content":
                    f"Give ONE short mysterious D&D tavern rumor (2 sentences). "
                    f"It should hint at a dangerous adventure hook. "
                    f"World: {state.get('title')}. Notes: {' | '.join(state.get('world_notes',[]))}. "
                    f"Make it feel ominous and intriguing. No preamble."}], max_tokens=80)
                cprint(C.WHITE,f"  A grizzled sailor leans in: \"{rumor}\"")
            else: cprint(C.RED,"  A drink costs 1gp.")

# ══════════════════════ SESSION END ═══════════════════════════
def end_session(state:dict, p:dict, comps:List[dict], all_chars:dict):
    xp={"easy":150,"normal":300,"hard":500}.get(state["difficulty"],300)
    header("SESSION COMPLETE",C.GREEN)
    p["xp"]=p.get("xp",0)+xp; p["sessions_played"]=p.get("sessions_played",0)+1
    p["last_seen"]=datetime.now().strftime("%Y-%m-%d")
    cprint(C.GREEN,f"  XP awarded: +{xp}")
    nl=lvl_up_check(p)
    if nl:
        p["level"]=nl; p["hp"]=max_hp(p); init_slots(p)
        cprint(C.MAGENTA,f"\n  ★★★ {p['name']} reached Level {nl}! ★★★")
        cprint(C.GREEN,  f"  Max HP: {p['hp']}  |  Spell Slots: {p.get('spell_slots_max',0)}")
    for c in comps:
        if c.get("alive",True):
            c["xp"]=c.get("xp",0)+xp; c["sessions_played"]=c.get("sessions_played",0)+1
            cl=lvl_up_check(c)
            if cl:
                c["level"]=cl; c["hp"]=max_hp(c); init_slots(c)
                cprint(C.GREEN,f"  ★ {c['name']} reached Level {cl}!")
    t,col,flv=get_rep(p.get("notoriety_score",0))
    cprint(col,f"\n  Reputation: {t} | {flv}")
    cprint(C.BLUE,"\n  Generating session summary...")
    summary=ai_call([{"role":"user","content":
        f"Write a 2-sentence campaign log entry for this D&D session. "
        f"Events: {' | '.join(state['session_log'][-6:])}"}],max_tokens=100)
    state["story_so_far"].append(f"Session {state['session_number']}: {summary}")
    cprint(C.GRAY,f"  {summary}")
    state["session_number"]+=1; state["session_log"]=[]
    save_campaign(state); all_chars[p["name"]]=p
    for c in comps: all_chars[c["name"]]=c
    save_chars(all_chars)
    cprint(C.GREEN,f"\n  Saved. Next session: #{state['session_number']}")
    divider("═",C.GREEN)

# ══════════════════════ HELP ══════════════════════════════════
def print_help():
    print(f"""
{C.BOLD}{C.BLUE}  ── Commands ──────────────────────────────────────────────{C.RESET}
  {C.CYAN}/status{C.RESET}              Full character sheet with all stats
  {C.CYAN}/spells{C.RESET}              Spell list and remaining slots
  {C.CYAN}/inventory{C.RESET}           Items, conditions, sell values
  {C.CYAN}/equip <item>{C.RESET}        Equip an item from inventory
  {C.CYAN}/unequip <slot>{C.RESET}      Unequip weapon/armor/offhand/accessory
  {C.CYAN}/companions{C.RESET}          Companion stats and conditions
  {C.CYAN}/trade <name>{C.RESET}        Trade items or gold with a companion
  {C.CYAN}/merchant{C.RESET}            Buy, sell, or repair gear
  {C.CYAN}/inn{C.RESET}                 Rest, recover spells, hear rumors
  {C.CYAN}/notoriety{C.RESET}           Your reputation bar
  {C.CYAN}/story{C.RESET}               Previous session summaries
  {C.CYAN}/difficulty{C.RESET}          Change difficulty
  {C.CYAN}/talents{C.RESET}             Talent tree — spend points, learn abilities
  {C.CYAN}/combat <enemy>{C.RESET}      Start a combat encounter (e.g. /combat orc)
  {C.CYAN}/ooc <msg>{C.RESET}           Out-of-character note
  {C.CYAN}/quit{C.RESET}                Save and end session
{C.BLUE}  ──────────────────────────────────────────────────────────{C.RESET}""")

# ══════════════════════ MAIN ══════════════════════════════════
# ══════════════════════ COMBAT ENCOUNTER ══════════════════════
def run_combat_encounter(player:dict, companions:List[dict], state:dict,
                          all_chars:dict, enemy_name:str="Enemy",
                          enemy_hp:int=20, enemy_ac:int=12) -> str:
    """Full cinematic FF3-style combat. Returns 'victory', 'defeat', or 'fled'."""
    enemy_max_hp = enemy_hp
    round_num    = 1
    round_log    = []

    # ── Initiative roll + cinematic intro ─────────────────────
    if DICE_AVAILABLE:
        p_init, e_init = roll_initiative(player, enemy_name)
    else:
        p_init, e_init = random.randint(1,20), random.randint(1,20)

    if SCREEN_AVAILABLE:
        combat_intro(player, enemy_name, enemy_hp, enemy_max_hp, p_init, e_init)
    else:
        try:
            from art import show_banner, show_enemy
            show_banner("fight"); show_enemy(enemy_name)
        except: pass
        cprint(C.RED, f"  ⚔  {enemy_name} (HP:{enemy_hp} AC:{enemy_ac})")
        input("  [ Press Enter ]")


    while player.get("hp",1) > 0 and enemy_hp > 0:
        # ── Draw combat screen ─────────────────────────────────
        if COMBAT_AVAILABLE:
            show_combat_header(player, enemy_name, enemy_hp, enemy_max_hp,
                               round_num, round_log=round_log[-3:])
        else:
            hc = hp_color(player); mhp = max_hp(player)
            print(f"  Round {round_num} | {player['name']} HP:{hc}{player['hp']}/{mhp}{C.RESET} vs {enemy_name} HP:{C.RED}{enemy_hp}/{enemy_max_hp}{C.RESET}")

        # ── Player action ──────────────────────────────────────
        if COMBAT_AVAILABLE:
            action = combat_menu(player)
        else:
            raw = input("  Action (attack/run): ").strip().lower()
            action = ({"type":"run","name":"Flee","data":{"success":True}}
                      if "run" in raw else {"type":"attack","name":"Strike","data":{}})

        if action["type"] == "run":
            if action["data"].get("success", True):
                round_log.append(f"{C.GRAY}  ↩ You disengage and flee!{C.RESET}")
                cprint(C.GRAY, f"  You disengage and flee from {enemy_name}!")
                return "fled"
            else:
                round_log.append(f"{C.RED}  ✗ Escape blocked!{C.RESET}")
                cprint(C.RED, f"  {enemy_name} cuts off your escape!")
        else:
            # ── Resolve player action ──────────────────────────
            if COMBAT_AVAILABLE:
                result = resolve_action(player, action, enemy_ac, enemy_hp, enemy_max_hp)
            else:
                hit = random.randint(1,20) + calc_atk(player) >= enemy_ac
                dmg = random.randint(1,8) if hit else 0
                result = {"hit":hit,"crit":False,"damage":dmg,"dtype":"physical",
                          "effect":None,"enemy_hp":max(0,enemy_hp-dmg),
                          "enemy_max_hp":enemy_max_hp,"player_hp_change":0}

            enemy_hp = result.get("enemy_hp", enemy_hp)
            is_crit  = result.get("crit", False)
            is_hit   = result.get("hit", False)
            dmg      = result.get("damage", 0)
            dtype    = result.get("dtype","physical")

            # ── Damage floater ─────────────────────────────────
            if SCREEN_AVAILABLE:
                if not is_hit:
                    damage_floater(0, is_miss=True)
                    round_log.append(f"{C.GRAY}  ✗ MISS — {action['name']}{C.RESET}")
                elif dtype == "heal":
                    damage_floater(dmg, is_heal=True)
                    round_log.append(f"{C.GREEN}  ♥ +{dmg} HP healed{C.RESET}")
                else:
                    damage_floater(dmg, dtype, is_crit=is_crit)
                    crit_str = " ✦CRITICAL!" if is_crit else ""
                    round_log.append(f"{C.YELLOW}  ⚔ {action['name']}: {dmg} {dtype} dmg{crit_str}{C.RESET}")

            # ── Healing ────────────────────────────────────────
            hpc = result.get("player_hp_change",0)
            if hpc > 0:
                player["hp"] = min(max_hp(player), player.get("hp",1)+hpc)

            # ── AI narration ───────────────────────────────────
            if COMBAT_AVAILABLE:
                narr_prompt = build_combat_narration(player, action, enemy_name, enemy_ac, result)
            else:
                narr_prompt = (f"Narrate {player['name']} {'hits' if is_hit else 'misses'} "
                               f"{enemy_name} with {action['name']}. 2 vivid sentences.")
            narration = ai_call([{"role":"user","content":narr_prompt+" 2 sentences max, vivid, no stat blocks."}], max_tokens=100)
            if SCREEN_AVAILABLE:
                narration_box(clean_response(narration), C.CYAN)
            else:
                dm_print(narration)

        # ── Enemy defeated? ────────────────────────────────────
        if enemy_hp <= 0:
            xp_reward   = {"easy":150,"normal":300,"hard":500}.get(state.get("difficulty","normal"),300)
            gold_loot   = random.randint(5,25)
            item_chance = random.random()
            loot_items  = []
            if item_chance > 0.7:
                loot_pool = ["Health Potion","Bandage Kit","Adventurer's Ration",
                             "Silver Arrow x5","Antidote","Thieves' Tools"]
                loot_items.append(random.choice(loot_pool))
                player.setdefault("inventory",[]).extend(loot_items)
            player["gold"] = player.get("gold",0) + gold_loot
            if SCREEN_AVAILABLE:
                enemy_death_screen(enemy_name, xp=xp_reward,
                                   loot=[f"{gold_loot} gold"]+loot_items)
            else:
                try:
                    from art import show_banner
                    show_banner("victory")
                except: pass
                cprint(C.GREEN, f"  ✓ {enemy_name} defeated! +{xp_reward}XP +{gold_loot}gp")
            return "victory"

        # ── Enemy turn ─────────────────────────────────────────
        defending = action.get("type") == "defend"
        raw_dmg   = random.randint(4,14)
        if defending:
            raw_dmg = max(1, raw_dmg // 2)
            round_log.append(f"{C.BLUE}  🛡 Guard! Reduced damage to {raw_dmg}{C.RESET}")
        player["hp"] = max(0, player.get("hp",1) - raw_dmg)

        if SCREEN_AVAILABLE:
            damage_floater(raw_dmg, "physical", is_crit=False)
            round_log.append(f"{C.RED}  💢 {enemy_name} hits for {raw_dmg} damage!{C.RESET}")
        else:
            hc = hp_color(player); mhp = max_hp(player)
            cprint(C.RED, f"  {enemy_name} hits you for {raw_dmg}! HP:{hc}{player['hp']}/{mhp}{C.RESET}")

        # Condition ticks
        cond_dmg = tick_conditions(player)
        if cond_dmg > 0:
            player["hp"] = max(0, player.get("hp",1) - cond_dmg)
            round_log.append(f"{C.ORANGE}  ⚠ Condition damage: {cond_dmg}{C.RESET}")

        # ── Player death ───────────────────────────────────────
        if player["hp"] <= 0:
            if SCREEN_AVAILABLE:
                player_death_screen(player, enemy_name)
            else:
                try:
                    from art import show_banner
                    show_banner("death")
                except: pass
                cprint(C.RED, f"  {player['name']} has been defeated by {enemy_name}.")
            return "defeat"

        round_num += 1

    return "victory" if enemy_hp <= 0 else "defeat"


def main():
    print(f"{C.BOLD}{C.MAGENTA}{'═'*W}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  ⚔  AI DUNGEON MASTER  v4  ⚔{C.RESET}")
    print(f"{C.GRAY}  Model: {MODEL}  |  WASD Navigate  |  [A]/[B] Choices  |  Actions trigger dice rolls{C.RESET}")
    print(f"{C.GRAY}  Created by Icycereal477TCMG-v1  ·  Co-created with Claude (Anthropic){C.RESET}")
    print(f"{C.BOLD}{C.MAGENTA}{'═'*W}{C.RESET}")

    all_chars = load_chars()
    state     = load_campaign()

    # Character select
    header("YOUR CHARACTER",C.CYAN)
    pchars={k:v for k,v in all_chars.items() if v.get("type")=="player"}
    if pchars:
        cprint(C.BLUE,"  Existing characters:\n",wrap_text=False)
        for i,(n,ch) in enumerate(pchars.items(),1):
            t,col,_=get_rep(ch.get("notoriety_score",0)); mhp=max_hp(ch); hp=ch.get("hp",mhp)
            hc=hp_color(ch)
            print(f"  [{i}] {C.BOLD}{n}{C.RESET} — Lvl {ch['level']} {ch['race']} {ch['class']} "
                  f"HP:{hc}{hp}/{mhp}{C.RESET} | {col}{t}{C.RESET}")
        print(f"  {C.GRAY}[N] New character{C.RESET}\n")
        choice=input("  Choose: ").strip()
        if choice.upper()!="N":
            try:
                p=list(pchars.values())[int(choice)-1]
                if "stats" not in p or not p["stats"]: p["stats"]=gen_stats()
                if "equipped" not in p:
                    w,a=STARTING_GEAR.get(p.get("class","Fighter"),("Dagger",""))
                    p["equipped"]={"weapon":w,"armor":a,"offhand":"","accessory":""}
                if "gold"           not in p: p["gold"]=15
                if "item_conditions"not in p: p["item_conditions"]={}
                if "conditions"     not in p: p["conditions"]=[]
                if "spell_slots_max"not in p: init_slots(p)
                cprint(C.GREEN,f"\n  Welcome back, {p['name']}!")
            except (ValueError,IndexError): p=create_char(all_chars)
        else: p=create_char(all_chars)
    else: p=create_char(all_chars)
    all_chars[p["name"]]=p

    # Companions
    comps:List[dict]=[]
    living={k:v for k,v in all_chars.items() if v.get("type")=="npc" and v.get("alive",True)}
    if living:
        cprint(C.BLUE,"\n  Living companions:",wrap_text=False)
        nlist=list(living.items())
        for i,(n,c) in enumerate(nlist,1):
            t,col,_=get_rep(c.get("notoriety_score",0))
            print(f"  [{i}] {C.BOLD}{n}{C.RESET} Lvl {c['level']} {c['race']} {c['class']} | {col}{t}{C.RESET}")
        print(f"  {C.GRAY}[R] Recruit new  [S] Travel alone{C.RESET}")
        cc_choice=input("\n  Choose (e.g. 1,2 or R or S): ").strip()
        if cc_choice.upper()=="R":
            for _ in range(MAX_COMPANIONS):
                npc=recruit(p,[c["name"] for c in comps])
                if npc: comps.append(npc); all_chars[npc["name"]]=npc
                if len(comps)>=MAX_COMPANIONS: break
        elif cc_choice.upper()!="S":
            for idx in cc_choice.split(","):
                try:
                    nm=nlist[int(idx.strip())-1][0]; comps.append(all_chars[nm])
                except: pass
                if len(comps)>=MAX_COMPANIONS: break
    else:
        for _ in range(MAX_COMPANIONS):
            npc=recruit(p,[c["name"] for c in comps])
            if npc: comps.append(npc); all_chars[npc["name"]]=npc
            if len(comps)>=MAX_COMPANIONS: break
            if input("  Recruit another? (y/n): ").strip().lower()!="y": break
    save_chars(all_chars)

    diff_ch=input(f"\n  {C.CYAN}Difficulty [{state['difficulty']}] (easy/normal/hard or Enter):{C.RESET} ").strip().lower()
    if diff_ch in ("easy","normal","hard"): state["difficulty"]=diff_ch

    print(f"\n{C.BOLD}{C.MAGENTA}{'═'*W}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  SESSION #{state['session_number']} — {state['title'].upper()}{C.RESET}")
    print(f"{C.BOLD}{C.MAGENTA}{'═'*W}{C.RESET}")
    alive_comps=[c for c in comps if c.get("alive",True)]
    party=p["name"]+(f" with {', '.join(c['name'] for c in alive_comps)}" if alive_comps else "")
    cprint(C.GRAY,f"  Party: {party}\n  Type /help for commands\n")

    opening=(
        "Begin with a vivid, immersive opening scene. Set the mood and hint at danger ahead. "
        "This Elf Warlock's power is alien, untrained, and slightly wrong — like a live wire he can't control. "
        "His mother was a witch. His father — a powerful sorcerer — abandoned him. "
        "The Great Old One filled that void. Its presence should feel vast and cold. "
        "If companions are present, let them show their personalities briefly."
        if not state["session_log"] else
        "Resume where we left off. Brief atmospheric recap, then back into the action."
    )
    cprint(C.GRAY,"  [Generating opening scene...]\n",wrap_text=False)
    resp=get_response(state,p,comps,opening)
    state["session_log"].append(f"[DM] {resp}")
    save_campaign(state)
    dm_print(resp)

    # ── Game loop ─────────────────────────────────────────────
    print(f"\n{C.GRAY}  ╔═══════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}CHOICES:{C.RESET}  {C.GREEN}[A]{C.RESET}=bold  {C.YELLOW}[B]{C.RESET}=cunning  {C.WHITE}[O]{C.RESET}=roleplay freely         {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}MOVE:{C.RESET}     {C.CYAN}[W]{C.RESET}=North {C.YELLOW}[A]{C.RESET}=West {C.ORANGE}[S]{C.RESET}=South {C.GREEN}[D]{C.RESET}=East {C.MAGENTA}[E]{C.RESET}=Examine  {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}MENUS:{C.RESET}    {C.CYAN}[I]{C.RESET}=Inventory  {C.MAGENTA}[T]{C.RESET}=Talents  /inn  /merchant  {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ║{C.RESET}  {C.BOLD}TYPE:{C.RESET}     Anything — actions trigger real dice rolls         {C.GRAY}║{C.RESET}")
    print(f"{C.GRAY}  ╚═══════════════════════════════════════════════════════════╝{C.RESET}\n")
    while True:
        try:
            user_input=input(f"\n{C.BOLD}{C.WHITE}  ❯{C.RESET} ").strip()
        except (EOFError,KeyboardInterrupt):
            print("\n"); end_session(state,p,comps,all_chars); break

        if not user_input: continue

        # ── Parse input ──────────────────────────────────────────
        import re as _re2, textwrap as _tw2
        _ul = user_input.strip().upper()

        # Quick-access keys that don't advance the story
        if _ul == "I":
            show_inventory(p); continue
        if _ul == "T":
            if COMBAT_AVAILABLE: show_talent_tree(p); save_chars(all_chars)
            continue

        # ── Compass navigation W/S/D/E only (A reserved for choices) ──
        _NAV = {"W":"north","S":"south","D":"east"}
        if _ul in _NAV:
            _direction = _NAV[_ul]
            if DICE_AVAILABLE: show_compass()
            print(f"  {C.BOLD}{C.CYAN}┌─ MOVING ──────────────────────────────────────────┐{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {C.WHITE}You head {_direction.upper()}...{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")
            user_input = (f"I move {_direction} and explore what lies there. "
                          f"Describe what I find — a new scene, encounter, or landmark.")
        elif _ul == "E":
            if DICE_AVAILABLE: show_compass()
            print(f"  {C.BOLD}{C.CYAN}┌─ EXAMINING ───────────────────────────────────────┐{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}│{C.RESET}  {C.WHITE}You study your surroundings carefully...{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")
            user_input = ("I examine my surroundings very carefully. "
                          "Describe hidden details, clues, dangers, or opportunities I notice.")

        # ── Binary choice shortcuts ───────────────────────────
        elif _ul in ("[A]","A") and state.get("_last_choice_a"):
            user_input = state["_last_choice_a"]
            print(f"  {C.BOLD}{C.GREEN}┌─ YOUR CHOICE ─────────────────────────────────────┐{C.RESET}")
            for _wl in _tw2.wrap(user_input, 51):
                print(f"  {C.BOLD}{C.GREEN}│{C.RESET} {C.WHITE}{_wl}{C.RESET}")
            print(f"  {C.BOLD}{C.GREEN}└───────────────────────────────────────────────────┘{C.RESET}")
        elif _ul in ("[B]","B") and state.get("_last_choice_b"):
            user_input = state["_last_choice_b"]
            print(f"  {C.BOLD}{C.YELLOW}┌─ YOUR CHOICE ─────────────────────────────────────┐{C.RESET}")
            for _wl in _tw2.wrap(user_input, 51):
                print(f"  {C.BOLD}{C.YELLOW}│{C.RESET} {C.WHITE}{_wl}{C.RESET}")
            print(f"  {C.BOLD}{C.YELLOW}└───────────────────────────────────────────────────┘{C.RESET}")
        elif _ul.startswith("O") and len(_ul) <= 2:
            # [O] = free roleplay prompt
            try:
                user_input = input(f"\n  {C.CYAN}What do you do? {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if not user_input: user_input = "look around carefully"
            print(f"  {C.BOLD}{C.CYAN}┌─ YOUR ACTION ─────────────────────────────────────┐{C.RESET}")
            for _wl in _tw2.wrap(user_input, 51):
                print(f"  {C.BOLD}{C.CYAN}│{C.RESET} {C.WHITE}{_wl}{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")

        # ── Free-typed action ─────────────────────────────────
        elif not user_input.startswith("/"):
            print(f"  {C.BOLD}{C.CYAN}┌─ YOUR ACTION ─────────────────────────────────────┐{C.RESET}")
            for _wl in _tw2.wrap(user_input, 51):
                print(f"  {C.BOLD}{C.CYAN}│{C.RESET} {C.WHITE}{_wl}{C.RESET}")
            print(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")

            # ── Dice check: infer from what they typed ────────
            if DICE_AVAILABLE and len(user_input.split()) >= 2:
                _ck, _prof = infer_check(user_input, p)
                if _ck:
                    _difficulty = state.get("difficulty","normal")
                    _dc_adjust  = {"easy":-3,"normal":0,"hard":3}.get(_difficulty,0)
                    _fdc = _prof[3] + _dc_adjust
                    _result = challenge_screen(
                        situation=(
                            f"You attempt: \"{user_input}\". "
                            f"The situation demands a {_prof[4].strip()} — "
                            f"roll {_prof[1]}+ to succeed."
                        ),
                        player=p,
                        forced_check=_ck,
                        forced_dc=_fdc,
                    )
                    _how = "successfully" if _result["success"] else "but failed to"
                    if _result.get("nat20"):
                        _how = "with a spectacular CRITICAL SUCCESS, brilliantly"
                    elif _result.get("nat1"):
                        _how = "but critically FUMBLED and disastrously failed to"
                    user_input = (
                        f"I attempted to {user_input} and {_how} do so "
                        f"(rolled {_result['total']} vs DC {_result['dc']}). "
                        f"Narrate the outcome dramatically in 2 sentences, then give [A]/[B] choices."
                    )

        # ── fight / attack / kill <target> shortcut ──────────
        _fmatch = _re2.match(r"^(fight|attack|kill|strike|assault|battle)\s+(.+)",
                             user_input.strip(), _re2.IGNORECASE)
        if _fmatch and not user_input.startswith("/"):
            _target = _fmatch.group(2).strip().title()
            _comp_names = [c["name"].lower() for c in comps if c.get("alive",True)]
            if _target.lower() in _comp_names:
                cprint(C.ORANGE, f"  ⚠  You turn on {_target}! Companions remember betrayal.")
                apply_notoriety(p, -25, f"attacked companion {_target}")
            cprint(C.RED, f"\n  ⚔  Entering combat with {_target}...")
            if DICE_AVAILABLE:
                _pi, _ei = roll_initiative(p, _target)
                input(f"\n  {C.GRAY}[ Press Enter to begin combat ]{C.RESET}")
            _ehp = random.randint(14,32); _eac = random.randint(11,16)
            _outcome = run_combat_encounter(p, comps, state, all_chars, _target, _ehp, _eac)
            save_chars(all_chars)
            if _outcome == "defeat":
                end_session(state, p, comps, all_chars); break
            user_input = f"After the fight with {_target} ({_outcome}), continue the story."

        if user_input.startswith("/"):
            parts=user_input.split(None,1); cmd=parts[0].lower()
            if   cmd=="/quit":       end_session(state,p,comps,all_chars); break
            elif cmd=="/help":       print_help()
            elif cmd=="/status":     show_status(p)
            elif cmd=="/spells":     show_spells(p)
            elif cmd=="/inventory":  show_inventory(p)
            elif cmd=="/companions": show_companions(comps)
            elif cmd=="/merchant":   visit_merchant(p); save_chars(all_chars)
            elif cmd=="/inn":        visit_inn(p,comps,state); save_chars(all_chars)
            elif cmd=="/equip":
                if len(parts)<2: cprint(C.RED,"  Usage: /equip <item name>")
                else: equip_item(p,parts[1])
            elif cmd=="/unequip":
                if len(parts)<2: cprint(C.RED,"  Usage: /unequip <slot>")
                else: unequip_item(p,parts[1])
            elif cmd=="/trade":
                if len(parts)<2: cprint(C.RED,"  Usage: /trade <companion name>")
                else: do_trade(p,comps,parts[1]); save_chars(all_chars)
            elif cmd=="/notoriety":
                score=p.get("notoriety_score",0); t,col,flv=get_rep(score)
                bar_pos=int((score+1000)/2000*40)
                bar=cc(col,"█"*bar_pos)+cc(C.GRAY,"░"*(40-bar_pos))
                print(f"\n  {col}{bold(t)}{C.RESET}  ({score:+d})")
                cprint(C.GRAY,f"  {flv}")
                print(f"  Infamous [{bar}] Heralded")
            elif cmd=="/story":
                if state.get("story_so_far"):
                    header("STORY SO FAR",C.CYAN)
                    for e in state["story_so_far"][-5:]: cprint(C.GRAY,f"  {e}")
                else: cprint(C.GRAY,"  No previous sessions yet.")
            elif cmd=="/difficulty":
                dc=input("  (easy/normal/hard): ").strip().lower()
                if dc in ("easy","normal","hard"):
                    state["difficulty"]=dc; cprint(C.YELLOW,f"  Difficulty: {dc.upper()}")
            elif cmd=="/talents":
                if COMBAT_AVAILABLE: show_talent_tree(p); save_chars(all_chars)
                else: cprint(C.RED,"  Combat module not loaded.")
            elif cmd=="/combat":
                enemy = parts[1] if len(parts)>1 else "Bandit"
                enemy_hp  = random.randint(15,35)
                enemy_ac  = random.randint(11,16)
                outcome   = run_combat_encounter(p,comps,state,all_chars,enemy,enemy_hp,enemy_ac)
                save_chars(all_chars)
                if outcome=="defeat":
                    end_session(state,p,comps,all_chars); break
            elif cmd=="/ooc":
                if len(parts)>1: cprint(C.GRAY,f"  [OOC: {parts[1]}]")
            else: cprint(C.RED,"  Unknown command. /help for list.")
            continue

        # ── Random ambush check ──────────────────────────────
        _turn_count = state.get("turn_count", 0) + 1
        state["turn_count"] = _turn_count
        _last_ambush = state.get("last_ambush_turn", -99)
        _ambush_roll = random.randint(1, 10)
        if (_turn_count - _last_ambush >= 5 and          # 5-turn cooldown
            _ambush_roll == 1 and                         # 1-in-10 chance
            not user_input.startswith("/")):              # not a command
            state["last_ambush_turn"] = _turn_count
            _ambush_enemies = ["Goblin Scout","Bandit","Wolf","Skeleton","Orc Raider",
                                "Cultist","Giant Spider","Cave Troll"]
            _ambush_name = random.choice(_ambush_enemies)
            _ambush_hp   = random.randint(12, 28)
            _ambush_ac   = random.randint(11, 15)
            try:
                from art import banner_ambush
                banner_ambush()
            except: pass
            cprint(C.RED, f"\n  ⚠  AMBUSH! A {_ambush_name} strikes from the shadows!")
            if DICE_AVAILABLE:
                roll_initiative(p, _ambush_name)
                input(f"  {C.GRAY}[ Press Enter to fight! ]{C.RESET}")
            _outcome = run_combat_encounter(p, comps, state, all_chars,
                                            _ambush_name, _ambush_hp, _ambush_ac)
            save_chars(all_chars)
            if _outcome == "defeat":
                end_session(state, p, comps, all_chars); break
            user_input = f"After being ambushed by a {_ambush_name} ({_outcome}), continue the story."

        # DM response
        state["session_log"].append(f"[YOU] {user_input}")
        cprint(C.GRAY,"\n  [The DM considers your action...]\n",wrap_text=False)
        resp=get_response(state,p,comps,user_input)
        state["session_log"].append(f"[DM] {resp}")
        # Extract binary choices for shortcut keys
        import re as _re
        _ca = _re.search(r"\[A\]\s*(.+)", resp)
        _cb = _re.search(r"\[B\]\s*(.+)", resp)
        if _ca:
            _atxt = _re.sub(r"\*+","",_ca.group(1)).strip()
            state["_last_choice_a"] = _atxt
        if _cb:
            _btxt = _re.sub(r"\*+","",_cb.group(1)).strip()
            state["_last_choice_b"] = _btxt

        save_campaign(state)
        detect_and_show(resp, p)
        dm_print(resp)
        try: detect_scene(resp)
        except: pass

        # Auto-detect combat from DM narration
        _combat_triggers = ["attacks you","charges at you","lunges toward","draws their weapon",
                            "battle begins","combat starts","moves to strike","raises their weapon",
                            "draws a blade","leaps at you"]
        if COMBAT_AVAILABLE and any(t in resp.lower() for t in _combat_triggers):
            _enemy_name = "Enemy"
            for _c in ["orc","goblin","bandit","guard","wolf","spider","skeleton",
                       "troll","vampire","lich","dragon","thug","soldier"]:
                if _c in resp.lower(): _enemy_name = _c.capitalize(); break
            cprint(C.RED, f"\n  ⚔  {_enemy_name} engages! Entering combat...")
            _outcome = run_combat_encounter(p,comps,state,all_chars,_enemy_name,
                                            random.randint(15,40),random.randint(11,16))
            save_chars(all_chars)
            if _outcome == "defeat":
                end_session(state,p,comps,all_chars); break

        # Condition ticks
        dmg=tick_conditions(p)
        if dmg>0:
            p["hp"]=max(0,p.get("hp",1)-dmg)
            if p["hp"]<=0:
                cprint(C.RED,f"\n  ☠  {p['name']} has fallen!")
                end_session(state,p,comps,all_chars); break

        # Near-death check
        nd_thresh=max(1,max_hp(p)//4)
        if 0<p.get("hp",1)<=nd_thresh:
            if "near-death" not in p.get("conditions",[]): add_condition(p,"near-death")
        elif "near-death" in p.get("conditions",[]): remove_condition(p,"near-death")

        # NPC death detection
        for c in comps:
            if not c.get("alive",True): continue
            rl=resp.lower(); nl=c["name"].lower()
            if any(ph in rl for ph in [f"{nl} falls",f"{nl} dies",f"{nl} is slain",
                    f"{nl} is dead",f"{nl} collapses",f"{nl} perishes"]):
                print(npc_death(p,c)); save_chars(all_chars)

        # Notoriety
        al=user_input.lower()
        if any(w in al for w in ["steal","murder","betray","loot the body","threaten","rob"]):
            print(apply_notoriety(p,-25,"dark deed"))
        elif any(w in al for w in ["help","donate","save","protect","heal","rescue","spare"]):
            print(apply_notoriety(p,+25,"good deed"))

        # Equipment degradation (1 in 10 chance on combat actions)
        if any(w in al for w in ["attack","strike","fight","slash","stab","shoot","cast","swing","charge","block","bash"]):
            if random.randint(1,10)==1: degrade_item(p,random.choice(["weapon","armor"]))

        all_chars[p["name"]]=p; save_chars(all_chars)

if __name__=="__main__":
    main()
