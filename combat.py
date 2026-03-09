"""
================================================================
  AI DUNGEON MASTER v4 — Combat Engine
  combat.py

  FF3-style round menu | Spell Schools | Physical Moves
  Talent Points | Notoriety Economy Perks
================================================================
"""
import random
from typing import Dict, List, Optional, Tuple

try:
    from combat_screen import (draw_combat_screen, damage_floater,
                                enemy_death_screen, player_death_screen,
                                combat_intro, narration_box)
    SCREEN_AVAILABLE = True
except ImportError:
    SCREEN_AVAILABLE = False

# ── Colors (mirrored from solo_play) ──────────────────────────
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m"
    CYAN    = "\033[96m"; WHITE   = "\033[97m"
    YELLOW  = "\033[93m"; RED     = "\033[91m"
    GREEN   = "\033[92m"; MAGENTA = "\033[95m"
    BLUE    = "\033[94m"; ORANGE  = "\033[33m"
    GRAY    = "\033[90m"

def cc(col, t): return f"{col}{t}{C.RESET}"
def bold(t):    return f"{C.BOLD}{t}{C.RESET}"
W = 78

def divider(ch="─", col=C.GRAY): print(f"{col}{ch*W}{C.RESET}")
def cprint(col, t, wrap=True):
    import textwrap
    if wrap:
        lines = []
        for p in t.split("\n"):
            if not p.strip(): lines.append("")
            else: lines.extend(textwrap.wrap(p, W))
        t = "\n".join(lines)
    print(f"{col}{t}{C.RESET}")

# ══════════════════════════════════════════════════════════════
#  DICE
# ══════════════════════════════════════════════════════════════
def roll(sides: int, count: int = 1, bonus: int = 0) -> Tuple[int, List[int]]:
    rolls = [random.randint(1, sides) for _ in range(count)]
    return sum(rolls) + bonus, rolls

def d20(bonus: int = 0) -> Tuple[int, int]:
    r = random.randint(1, 20)
    return r + bonus, r

def mod(score: int) -> int: return (score - 10) // 2
def prof(level: int) -> int: return 2 + (level - 1) // 4

# ══════════════════════════════════════════════════════════════
#  SPELL SCHOOLS — per class, all schools defined
# ══════════════════════════════════════════════════════════════

# Each spell: name, school, damage_dice, damage_type, slots, range, effect, desc, color
SPELLS_BY_CLASS = {

  "Warlock": {
    "schools": ["Void","Psychic","Curse"],
    "cantrips": [
      {"name":"Eldritch Blast",  "school":"Void",    "dice":"1d10","dtype":"force",   "slots":0,"range":"120ft","effect":None,
       "desc":"A crackling beam of alien energy tears toward your foe.","color":C.MAGENTA},
      {"name":"Mind Sliver",     "school":"Psychic", "dice":"1d6", "dtype":"psychic", "slots":0,"range":"60ft","effect":"stunned",
       "desc":"A spike of alien thought scrambles their focus.","color":C.CYAN},
      {"name":"Toll the Dead",   "school":"Void",    "dice":"1d8", "dtype":"necrotic","slots":0,"range":"60ft","effect":None,
       "desc":"A funeral bell tolls from beyond.","color":C.GRAY},
      {"name":"Chill Touch",     "school":"Void",    "dice":"1d8", "dtype":"necrotic","slots":0,"range":"120ft","effect":"cursed",
       "desc":"A ghostly hand clutches your foe, preventing healing.","color":C.GRAY},
    ],
    "spells": [
      {"name":"Hex",                "school":"Curse",   "dice":"1d6 bonus","dtype":"curse",   "slots":1,"range":"90ft","effect":"cursed",
       "desc":"A dark mark on the target — every hit carries your patron's hunger.","color":C.RED},
      {"name":"Dissonant Whispers", "school":"Psychic", "dice":"3d6","dtype":"psychic","slots":1,"range":"60ft","effect":None,
       "desc":"Words never meant for mortal ears drive them screaming.","color":C.CYAN},
      {"name":"Armor of Agathys",   "school":"Void",    "dice":"0",  "dtype":"shield", "slots":1,"range":"self","effect":"shielded",
       "desc":"Icy void magic wraps you — attackers take 5 cold damage.","color":C.BLUE},
      {"name":"Hunger of Hadar",    "school":"Void",    "dice":"2d6","dtype":"cold",   "slots":2,"range":"150ft","effect":"bleeding",
       "desc":"Darkness and tentacles erupt. Something from outside hungers.","color":C.MAGENTA},
      {"name":"Crown of Madness",   "school":"Psychic", "dice":"0",  "dtype":"control","slots":2,"range":"120ft","effect":"cursed",
       "desc":"You reach into their mind and pull the strings.","color":C.CYAN},
      {"name":"Synaptic Static",    "school":"Psychic", "dice":"8d6","dtype":"psychic","slots":5,"range":"120ft","effect":"stunned",
       "desc":"Pure alien madness erupts in a psychic detonation.","color":C.MAGENTA},
    ]
  },

  "Wizard": {
    "schools": ["Fire","Ice","Lightning","Arcane"],
    "cantrips": [
      {"name":"Fire Bolt",     "school":"Fire",      "dice":"1d10","dtype":"fire",     "slots":0,"range":"120ft","effect":"burning",
       "desc":"A mote of fire streaks toward the target.","color":C.ORANGE},
      {"name":"Ray of Frost",  "school":"Ice",       "dice":"1d8", "dtype":"cold",     "slots":0,"range":"60ft","effect":"stunned",
       "desc":"A frigid ray slows and chills your foe.","color":C.CYAN},
      {"name":"Shocking Grasp","school":"Lightning", "dice":"1d8", "dtype":"lightning","slots":0,"range":"touch","effect":"stunned",
       "desc":"Lightning arcs through your touch, preventing reaction.","color":C.YELLOW},
      {"name":"Mage Hand",     "school":"Arcane",    "dice":"0",   "dtype":"utility",  "slots":0,"range":"30ft","effect":None,
       "desc":"A spectral hand manipulates objects at range.","color":C.BLUE},
    ],
    "spells": [
      {"name":"Magic Missile",   "school":"Arcane",    "dice":"3d4+3","dtype":"force",    "slots":1,"range":"120ft","effect":None,
       "desc":"Three darts of force strike unerringly.","color":C.BLUE},
      {"name":"Burning Hands",   "school":"Fire",      "dice":"3d6",  "dtype":"fire",     "slots":1,"range":"15ft cone","effect":"burning",
       "desc":"A sheet of flame roars from your fingers.","color":C.ORANGE},
      {"name":"Ice Knife",       "school":"Ice",       "dice":"1d10", "dtype":"cold",     "slots":1,"range":"60ft","effect":None,
       "desc":"A shard of ice explodes on impact.","color":C.CYAN},
      {"name":"Lightning Bolt",  "school":"Lightning", "dice":"8d6",  "dtype":"lightning","slots":3,"range":"100ft line","effect":"stunned",
       "desc":"A bolt of lightning blasts through everything in its path.","color":C.YELLOW},
      {"name":"Fireball",        "school":"Fire",      "dice":"8d6",  "dtype":"fire",     "slots":3,"range":"150ft","effect":"burning",
       "desc":"A bright streak explodes into a devastating ball of fire.","color":C.ORANGE},
      {"name":"Cone of Cold",    "school":"Ice",       "dice":"8d8",  "dtype":"cold",     "slots":5,"range":"60ft cone","effect":"stunned",
       "desc":"A blast of cold air erupts from your hands.","color":C.CYAN},
    ]
  },

  "Cleric": {
    "schools": ["Holy","Death","Healing"],
    "cantrips": [
      {"name":"Sacred Flame",   "school":"Holy",    "dice":"1d8", "dtype":"radiant", "slots":0,"range":"60ft","effect":None,
       "desc":"Flame-like radiance descends on a creature.","color":C.YELLOW},
      {"name":"Toll the Dead",  "school":"Death",   "dice":"1d8", "dtype":"necrotic","slots":0,"range":"60ft","effect":None,
       "desc":"A doleful bell tolls — necrotic energy washes over your foe.","color":C.GRAY},
      {"name":"Guidance",       "school":"Healing", "dice":"0",   "dtype":"buff",    "slots":0,"range":"touch","effect":"guided",
       "desc":"You touch a creature, granting divine guidance.","color":C.GREEN},
      {"name":"Word of Radiance","school":"Holy",   "dice":"1d6", "dtype":"radiant", "slots":0,"range":"5ft","effect":None,
       "desc":"You utter a divine word, blasting all foes nearby.","color":C.YELLOW},
    ],
    "spells": [
      {"name":"Cure Wounds",     "school":"Healing", "dice":"1d8+mod","dtype":"heal",   "slots":1,"range":"touch","effect":None,
       "desc":"Healing energy flows into the creature you touch.","color":C.GREEN},
      {"name":"Bless",           "school":"Holy",    "dice":"0",      "dtype":"buff",   "slots":1,"range":"30ft","effect":"blessed",
       "desc":"You bless three creatures — their attacks land truer.","color":C.YELLOW},
      {"name":"Inflict Wounds",  "school":"Death",   "dice":"3d10",   "dtype":"necrotic","slots":1,"range":"touch","effect":None,
       "desc":"Necrotic energy courses through your hand into the target.","color":C.GRAY},
      {"name":"Spirit Guardians","school":"Holy",    "dice":"3d8",    "dtype":"radiant","slots":3,"range":"15ft","effect":None,
       "desc":"Spirits surround you, slashing foes who enter.","color":C.YELLOW},
      {"name":"Mass Cure Wounds","school":"Healing", "dice":"3d8+mod","dtype":"heal",   "slots":5,"range":"60ft","effect":None,
       "desc":"Healing energy washes over all creatures of your choice.","color":C.GREEN},
      {"name":"Harm",            "school":"Death",   "dice":"14d6",   "dtype":"necrotic","slots":6,"range":"60ft","effect":"poisoned",
       "desc":"Disease ravages the body of a creature.","color":C.GRAY},
    ]
  },

  "Druid": {
    "schools": ["Nature","Poison","Shapeshifting"],
    "cantrips": [
      {"name":"Shillelagh",    "school":"Nature",       "dice":"1d8", "dtype":"bludgeoning","slots":0,"range":"touch","effect":None,
       "desc":"Wood and stone become a powerful magical weapon.","color":C.GREEN},
      {"name":"Poison Spray",  "school":"Poison",       "dice":"1d12","dtype":"poison",     "slots":0,"range":"10ft","effect":"poisoned",
       "desc":"You extend your hand and project a puff of noxious gas.","color":C.GREEN},
      {"name":"Thorn Whip",    "school":"Nature",       "dice":"1d6", "dtype":"piercing",   "slots":0,"range":"30ft","effect":None,
       "desc":"A vine-like whip lashes out and pulls your foe closer.","color":C.GREEN},
      {"name":"Druidcraft",    "school":"Shapeshifting","dice":"0",   "dtype":"utility",    "slots":0,"range":"30ft","effect":None,
       "desc":"A minor natural effect — weather, plants, animals respond.","color":C.GREEN},
    ],
    "spells": [
      {"name":"Entangle",        "school":"Nature",       "dice":"0",  "dtype":"control","slots":1,"range":"90ft","effect":"stunned",
       "desc":"Grasping weeds and vines sprout from the ground.","color":C.GREEN},
      {"name":"Faerie Fire",     "school":"Nature",       "dice":"0",  "dtype":"debuff", "slots":1,"range":"60ft","effect":"cursed",
       "desc":"Each object in a 20ft cube is outlined in blue, green, or violet light.","color":C.CYAN},
      {"name":"Spike Growth",    "school":"Nature",       "dice":"2d4","dtype":"piercing","slots":2,"range":"150ft","effect":"bleeding",
       "desc":"The ground in a 20-foot radius sprouts hard spikes.","color":C.GREEN},
      {"name":"Conjure Animals", "school":"Shapeshifting","dice":"0",  "dtype":"summon", "slots":3,"range":"60ft","effect":None,
       "desc":"You summon fey spirits that take the form of beasts.","color":C.GREEN},
      {"name":"Blight",          "school":"Poison",       "dice":"8d8","dtype":"necrotic","slots":4,"range":"30ft","effect":"poisoned",
       "desc":"Necrotic energy washes over a creature, withering it.","color":C.GRAY},
    ]
  },

  "Paladin": {
    "schools": ["Holy","Smite","Aura"],
    "cantrips": [
      {"name":"Sacred Flame",   "school":"Holy",  "dice":"1d8","dtype":"radiant","slots":0,"range":"60ft","effect":None,
       "desc":"Radiant flame descends on a creature you can see.","color":C.YELLOW},
      {"name":"Sword Burst",    "school":"Smite", "dice":"1d6","dtype":"force",  "slots":0,"range":"5ft","effect":None,
       "desc":"A momentary circle of force sweeps all around you.","color":C.YELLOW},
    ],
    "spells": [
      {"name":"Divine Smite",    "school":"Smite", "dice":"2d8","dtype":"radiant","slots":1,"range":"melee","effect":None,
       "desc":"When you hit, you expend a slot to deal radiant damage.","color":C.YELLOW},
      {"name":"Bless",           "school":"Holy",  "dice":"0",  "dtype":"buff",   "slots":1,"range":"30ft","effect":"blessed",
       "desc":"You bless your allies — attacks and saves ring truer.","color":C.YELLOW},
      {"name":"Shield of Faith", "school":"Aura",  "dice":"0",  "dtype":"shield", "slots":1,"range":"60ft","effect":"shielded",
       "desc":"A shimmering field of force adds +2 AC.","color":C.BLUE},
      {"name":"Aura of Courage", "school":"Aura",  "dice":"0",  "dtype":"buff",   "slots":3,"range":"10ft","effect":"blessed",
       "desc":"You and nearby allies cannot be frightened.","color":C.YELLOW},
    ]
  },

  "Ranger": {
    "schools": ["Archery","Nature","Beast"],
    "cantrips": [
      {"name":"Thorn Whip",   "school":"Nature", "dice":"1d6","dtype":"piercing","slots":0,"range":"30ft","effect":None,
       "desc":"A vine whip lashes and pulls.","color":C.GREEN},
      {"name":"Shillelagh",   "school":"Beast",  "dice":"1d8","dtype":"bludgeoning","slots":0,"range":"touch","effect":None,
       "desc":"Your weapon glows with natural magic.","color":C.GREEN},
    ],
    "spells": [
      {"name":"Hunter's Mark",   "school":"Archery","dice":"1d6 bonus","dtype":"piercing","slots":1,"range":"90ft","effect":"cursed",
       "desc":"You mark your quarry. Every hit deals extra damage.","color":C.GREEN},
      {"name":"Hail of Thorns",  "school":"Archery","dice":"1d10","dtype":"piercing","slots":1,"range":"self","effect":"bleeding",
       "desc":"Your next ranged hit explodes into a burst of thorns.","color":C.GREEN},
      {"name":"Conjure Barrage", "school":"Archery","dice":"3d8", "dtype":"piercing","slots":3,"range":"60ft cone","effect":None,
       "desc":"You throw a weapon and conjure copies — a storm of projectiles.","color":C.GREEN},
    ]
  },

  "Bard": {
    "schools": ["Inspiration","Illusion","Enchantment"],
    "cantrips": [
      {"name":"Vicious Mockery","school":"Enchantment","dice":"1d4","dtype":"psychic","slots":0,"range":"60ft","effect":"stunned",
       "desc":"You unleash a string of insults laced with subtle enchantments.","color":C.YELLOW},
      {"name":"Minor Illusion", "school":"Illusion",   "dice":"0",  "dtype":"utility","slots":0,"range":"30ft","effect":None,
       "desc":"You create a sound or image within range.","color":C.CYAN},
    ],
    "spells": [
      {"name":"Healing Word",    "school":"Inspiration","dice":"1d4+mod","dtype":"heal",   "slots":1,"range":"60ft","effect":None,
       "desc":"A word of power restores life from a distance.","color":C.GREEN},
      {"name":"Hideous Laughter","school":"Enchantment","dice":"0",      "dtype":"control","slots":1,"range":"30ft","effect":"stunned",
       "desc":"The target perceives everything as hilarious and falls prone.","color":C.YELLOW},
      {"name":"Hypnotic Pattern","school":"Illusion",   "dice":"0",      "dtype":"control","slots":3,"range":"120ft","effect":"stunned",
       "desc":"A twisting pattern of colors weaves through the air, incapacitating.","color":C.CYAN},
    ]
  },

  "Sorcerer": {
    "schools": ["Fire","Lightning","Metamagic"],
    "cantrips": [
      {"name":"Fire Bolt",      "school":"Fire",      "dice":"1d10","dtype":"fire",     "slots":0,"range":"120ft","effect":"burning",
       "desc":"A mote of fire streaks toward the target.","color":C.ORANGE},
      {"name":"Shocking Grasp", "school":"Lightning", "dice":"1d8", "dtype":"lightning","slots":0,"range":"touch","effect":"stunned",
       "desc":"Lightning arcs from your touch.","color":C.YELLOW},
      {"name":"Prestidigitation","school":"Metamagic","dice":"0",   "dtype":"utility",  "slots":0,"range":"10ft","effect":None,
       "desc":"Minor magical tricks at your fingertips.","color":C.MAGENTA},
    ],
    "spells": [
      {"name":"Chaos Bolt",     "school":"Metamagic","dice":"2d8+1d6","dtype":"random",  "slots":1,"range":"120ft","effect":None,
       "desc":"A bolt of chaotic energy — damage type shifts randomly.","color":C.MAGENTA},
      {"name":"Fireball",       "school":"Fire",     "dice":"8d6",    "dtype":"fire",    "slots":3,"range":"150ft","effect":"burning",
       "desc":"The classic. A bead of light explodes into devastation.","color":C.ORANGE},
      {"name":"Chain Lightning", "school":"Lightning","dice":"10d8",   "dtype":"lightning","slots":6,"range":"150ft","effect":"stunned",
       "desc":"Lightning arcs to up to 4 creatures.","color":C.YELLOW},
    ]
  },

  "Fighter":   {"schools":[],"cantrips":[],"spells":[]},
  "Rogue":     {"schools":[],"cantrips":[],"spells":[]},
  "Barbarian": {"schools":[],"cantrips":[],"spells":[]},
  "Monk":      {"schools":["Ki"],"cantrips":[],"spells":[
    {"name":"Stunning Strike","school":"Ki","dice":"0","dtype":"stun","slots":1,"range":"melee","effect":"stunned",
     "desc":"You spend a Ki point — the target must save or be stunned.","color":C.WHITE},
    {"name":"Step of the Wind","school":"Ki","dice":"0","dtype":"movement","slots":1,"range":"self","effect":None,
     "desc":"You spend Ki to dash or disengage as a bonus action.","color":C.WHITE},
  ]},
}

# ══════════════════════════════════════════════════════════════
#  PHYSICAL ATTACK MOVES — by class, unlock by level
# ══════════════════════════════════════════════════════════════

# Each move: name, class(es), min_level, ap_cost(1=action,0=bonus),
#            damage_bonus, damage_type, effect, condition_apply, desc, color
PHYSICAL_MOVES = {

  # ── Universal ────────────────────────────────────────────────
  "Strike":       {"classes":"all",      "min_level":1, "bonus_dmg":0,   "dtype":"weapon",
                   "effect":None,       "desc":"A direct weapon strike. Reliable damage.","color":C.WHITE},
  "Shove":        {"classes":"all",      "min_level":1, "bonus_dmg":0,   "dtype":"bludgeoning",
                   "effect":"stunned",  "desc":"Push the enemy back 10ft. Breaks their footing.","color":C.YELLOW},
  "Disarm":       {"classes":"all",      "min_level":2, "bonus_dmg":0,   "dtype":"none",
                   "effect":"disarmed", "desc":"Contest to knock their weapon free.","color":C.YELLOW},
  "Grapple":      {"classes":"all",      "min_level":1, "bonus_dmg":0,   "dtype":"none",
                   "effect":"grappled", "desc":"Grab and restrain the target.","color":C.ORANGE},

  # ── Fighter ──────────────────────────────────────────────────
  "Cleave":       {"classes":["Fighter","Barbarian","Paladin"], "min_level":1,  "bonus_dmg":4,  "dtype":"slashing",
                   "effect":None,        "desc":"A sweeping blow that can hit a second target.","color":C.RED},
  "Charge":       {"classes":["Fighter","Paladin","Barbarian"], "min_level":2,  "bonus_dmg":6,  "dtype":"bludgeoning",
                   "effect":"stunned",   "desc":"Rush 20ft and slam into the enemy. High risk, high reward.","color":C.ORANGE},
  "Shield Bash":  {"classes":["Fighter","Paladin"],             "min_level":2,  "bonus_dmg":3,  "dtype":"bludgeoning",
                   "effect":"stunned",   "desc":"Smash them with your shield. Brief stun.","color":C.BLUE},
  "Parry":        {"classes":["Fighter","Paladin","Rogue"],     "min_level":3,  "bonus_dmg":0,  "dtype":"defense",
                   "effect":"parrying",  "desc":"Sacrifice damage to reduce incoming by half next hit.","color":C.BLUE},
  "Whirlwind":    {"classes":["Fighter","Barbarian"],           "min_level":5,  "bonus_dmg":3,  "dtype":"slashing",
                   "effect":None,        "desc":"Spin and hit all enemies within 5ft.","color":C.RED},
  "Riposte":      {"classes":["Fighter","Rogue"],               "min_level":4,  "bonus_dmg":5,  "dtype":"piercing",
                   "effect":None,        "desc":"When they miss you, immediately counter.","color":C.YELLOW},
  "Disabling Strike":{"classes":["Fighter"],                    "min_level":6,  "bonus_dmg":2,  "dtype":"bludgeoning",
                   "effect":"stunned",   "desc":"A blow aimed to disable a limb.","color":C.ORANGE},

  # ── Rogue ────────────────────────────────────────────────────
  "Sneak Attack": {"classes":["Rogue"],                         "min_level":1,  "bonus_dmg":8,  "dtype":"piercing",
                   "effect":None,        "desc":"Strike from advantage. Massive burst damage.","color":C.GRAY},
  "Backstab":     {"classes":["Rogue"],                         "min_level":1,  "bonus_dmg":6,  "dtype":"piercing",
                   "effect":"bleeding",  "desc":"A blade in the back. Causes bleeding.","color":C.GRAY},
  "Maim":         {"classes":["Rogue","Ranger"],                "min_level":3,  "bonus_dmg":3,  "dtype":"slashing",
                   "effect":"poisoned",  "desc":"A vicious cut that festers.","color":C.GREEN},
  "Poison Strike":{"classes":["Rogue","Ranger"],                "min_level":2,  "bonus_dmg":2,  "dtype":"poison",
                   "effect":"poisoned",  "desc":"Coat your blade. The poison lingers.","color":C.GREEN},
  "Vanish":       {"classes":["Rogue"],                         "min_level":4,  "bonus_dmg":0,  "dtype":"utility",
                   "effect":"invisible", "desc":"Melt into shadow. Enemies lose you this round.","color":C.GRAY},
  "Garrote":      {"classes":["Rogue"],                         "min_level":5,  "bonus_dmg":4,  "dtype":"bludgeoning",
                   "effect":"stunned",   "desc":"A wire around the throat. Silence and damage.","color":C.GRAY},

  # ── Barbarian ────────────────────────────────────────────────
  "Rage":         {"classes":["Barbarian"],                     "min_level":1,  "bonus_dmg":2,  "dtype":"buff",
                   "effect":"raging",    "desc":"Enter a fury. Resistance to physical damage. +2 melee.","color":C.RED},
  "Reckless Attack":{"classes":["Barbarian"],                   "min_level":2,  "bonus_dmg":6,  "dtype":"weapon",
                   "effect":None,        "desc":"Attack with abandon. Advantage to hit, but so do they.","color":C.RED},
  "Intimidating Roar":{"classes":["Barbarian"],                 "min_level":3,  "bonus_dmg":0,  "dtype":"psychic",
                   "effect":"stunned",   "desc":"A terrifying roar. Enemy loses their action in fear.","color":C.ORANGE},
  "Frenzied Strike":{"classes":["Barbarian"],                   "min_level":3,  "bonus_dmg":4,  "dtype":"slashing",
                   "effect":"bleeding",  "desc":"A savage flurry of blows.","color":C.RED},
  "Ground Slam":  {"classes":["Barbarian"],                     "min_level":4,  "bonus_dmg":5,  "dtype":"bludgeoning",
                   "effect":"stunned",   "desc":"Bring your weapon down with both hands. Shakes the earth.","color":C.ORANGE},

  # ── Ranger ───────────────────────────────────────────────────
  "Aimed Shot":   {"classes":["Ranger"],                        "min_level":1,  "bonus_dmg":4,  "dtype":"piercing",
                   "effect":None,        "desc":"Take careful aim. Bonus damage on the precise shot.","color":C.GREEN},
  "Volley":       {"classes":["Ranger"],                        "min_level":3,  "bonus_dmg":2,  "dtype":"piercing",
                   "effect":None,        "desc":"Rapid fire. Hit up to 3 targets in a 10ft radius.","color":C.GREEN},
  "Pinning Shot": {"classes":["Ranger"],                        "min_level":4,  "bonus_dmg":2,  "dtype":"piercing",
                   "effect":"grappled",  "desc":"Pin their foot to the ground. They can't move.","color":C.GREEN},
  "Colossus Slayer":{"classes":["Ranger"],                      "min_level":2,  "bonus_dmg":4,  "dtype":"piercing",
                   "effect":None,        "desc":"You deal extra damage to bloodied creatures.","color":C.GREEN},

  # ── Paladin ──────────────────────────────────────────────────
  "Holy Strike":  {"classes":["Paladin"],                       "min_level":1,  "bonus_dmg":4,  "dtype":"radiant",
                   "effect":None,        "desc":"A blessed blow that burns the unholy.","color":C.YELLOW},
  "Lay on Hands": {"classes":["Paladin"],                       "min_level":1,  "bonus_dmg":-8, "dtype":"heal",
                   "effect":None,        "desc":"Touch to heal 5 HP. Negative bonus = healing.","color":C.GREEN},
  "Avenging Strike":{"classes":["Paladin"],                     "min_level":5,  "bonus_dmg":8,  "dtype":"radiant",
                   "effect":"burning",   "desc":"A radiant explosion on impact.","color":C.YELLOW},

  # ── Monk ─────────────────────────────────────────────────────
  "Flurry of Blows":{"classes":["Monk"],                        "min_level":1,  "bonus_dmg":4,  "dtype":"bludgeoning",
                   "effect":None,        "desc":"Two unarmed strikes as a bonus action.","color":C.WHITE},
  "Deflect Missiles":{"classes":["Monk"],                       "min_level":3,  "bonus_dmg":0,  "dtype":"defense",
                   "effect":None,        "desc":"Reduce ranged damage by 1d10+DEX+level.","color":C.WHITE},
  "Quivering Palm":{"classes":["Monk"],                         "min_level":7,  "bonus_dmg":10, "dtype":"necrotic",
                   "effect":"stunned",   "desc":"Set up fatal vibrations. Trigger later for massive damage.","color":C.WHITE},
}

# ══════════════════════════════════════════════════════════════
#  TALENT TREES — WoW backbone, RavenQuest freedom, FF equipment
# ══════════════════════════════════════════════════════════════

TALENT_TREES = {
  "Warlock": {
    "specs": {
      "Great Old One":  "Psychic control and alien terror. The patron sees through your eyes.",
      "Fiend":          "Fire and necrotic devastation. Power through destruction.",
      "Archfey":        "Charm and illusion. Reality bends at your patron's whim.",
    },
    "talents": [
      # Tier 1 (Level 2)
      {"name":"Agonizing Blast",  "tier":1,"spec":"Great Old One","cost":1,
       "desc":"Add CHA mod to Eldritch Blast damage.","effect":"eldritch_bonus"},
      {"name":"Repelling Blast",  "tier":1,"spec":"Great Old One","cost":1,
       "desc":"Eldritch Blast pushes targets 10ft back.","effect":"repelling"},
      {"name":"Dark One's Blessing","tier":1,"spec":"Fiend","cost":1,
       "desc":"When you kill, gain THP equal to CHA+level.","effect":"kill_thp"},
      # Tier 2 (Level 4)
      {"name":"Misty Step",       "tier":2,"spec":None,"cost":1,
       "desc":"Bonus action teleport 30ft.","effect":"misty_step"},
      {"name":"Eldritch Mind",    "tier":2,"spec":"Great Old One","cost":1,
       "desc":"Advantage on Concentration saves.","effect":"conc_adv"},
      {"name":"Voice of the Chain","tier":2,"spec":"Great Old One","cost":2,
       "desc":"Communicate telepathically with any creature you can see.","effect":"telepathy"},
      # Tier 3 (Level 6)
      {"name":"Dreadful Word",    "tier":3,"spec":"Great Old One","cost":2,
       "desc":"Confuse a target — they act randomly next round.","effect":"confuse"},
      {"name":"Thirsting Blade",  "tier":3,"spec":"Fiend","cost":2,
       "desc":"Attack twice with Pact weapon.","effect":"extra_attack"},
      # Tier 4 (Level 8)
      {"name":"Thought Shield",   "tier":4,"spec":"Great Old One","cost":2,
       "desc":"Psychic damage resistance. Attackers take half back.","effect":"thought_shield"},
      {"name":"Lifedrinker",      "tier":4,"spec":"Fiend","cost":2,
       "desc":"Pact weapon adds CHA to damage.","effect":"lifedrinker"},
    ]
  },
  "Fighter": {
    "specs": {
      "Champion":      "Pure martial excellence. Every swing hits harder.",
      "Battle Master": "Tactical superiority. Combat maneuvers and momentum.",
      "Eldritch Knight":"Steel and sorcery combined. Magic enhances every blow.",
    },
    "talents": [
      {"name":"Second Wind",      "tier":1,"spec":None,"cost":1,
       "desc":"Bonus action: regain 1d10+level HP once per rest.","effect":"second_wind"},
      {"name":"Action Surge",     "tier":1,"spec":None,"cost":1,
       "desc":"Take an additional action this turn.","effect":"action_surge"},
      {"name":"Improved Critical","tier":2,"spec":"Champion","cost":1,
       "desc":"Critical hits on 19-20 instead of just 20.","effect":"improved_crit"},
      {"name":"Combat Superiority","tier":2,"spec":"Battle Master","cost":2,
       "desc":"Gain 4 superiority dice (d8) for maneuvers.","effect":"superiority"},
      {"name":"Trip Attack",      "tier":2,"spec":"Battle Master","cost":1,
       "desc":"Expend a die to knock target prone on hit.","effect":"trip"},
      {"name":"Indomitable",      "tier":3,"spec":None,"cost":2,
       "desc":"Reroll a failed saving throw.","effect":"indomitable"},
      {"name":"Eldritch Strike",  "tier":3,"spec":"Eldritch Knight","cost":2,
       "desc":"Weapon hits impose disadvantage on spell saves.","effect":"eldritch_strike"},
    ]
  },
  "Rogue": {
    "specs": {
      "Assassin":    "Kill before they see you coming. Crits from stealth are devastating.",
      "Arcane Trickster":"Blend magic and theft. Invisible hands, invisible blades.",
      "Thief":       "The fastest hands. Grab, dash, survive.",
    },
    "talents": [
      {"name":"Cunning Action",   "tier":1,"spec":None,"cost":1,
       "desc":"Bonus action Dash, Disengage, or Hide.","effect":"cunning_action"},
      {"name":"Uncanny Dodge",    "tier":2,"spec":None,"cost":1,
       "desc":"Reaction: halve incoming damage from one attack.","effect":"uncanny_dodge"},
      {"name":"Assassinate",      "tier":2,"spec":"Assassin","cost":2,
       "desc":"Auto-crit surprised targets. Advantage on initiative.","effect":"assassinate"},
      {"name":"Evasion",          "tier":3,"spec":None,"cost":2,
       "desc":"Take no damage on successful DEX saves, half on fail.","effect":"evasion"},
      {"name":"Reliable Talent",  "tier":4,"spec":None,"cost":2,
       "desc":"Any skill roll below 10 = 10.","effect":"reliable_talent"},
    ]
  },
  "Barbarian": {
    "specs": {
      "Berserker":  "Absolute destruction. Frenzied attacks every turn.",
      "Totem Warrior":"Channel animal spirits. Bear, Eagle, or Wolf.",
      "Storm Herald":"Elemental rage. Fire, ice, or lightning aura.",
    },
    "talents": [
      {"name":"Unarmored Defense","tier":1,"spec":None,"cost":1,
       "desc":"AC = 10 + DEX mod + CON mod when unarmored.","effect":"unarmored_def"},
      {"name":"Frenzy",          "tier":1,"spec":"Berserker","cost":1,
       "desc":"Extra attack while raging. Exhaustion afterward.","effect":"frenzy"},
      {"name":"Reckless Abandon","tier":2,"spec":"Berserker","cost":1,
       "desc":"Reckless Attack also grants THP equal to CON mod.","effect":"reckless_thp"},
      {"name":"Bear Totem",      "tier":2,"spec":"Totem Warrior","cost":2,
       "desc":"Resistance to ALL damage types while raging.","effect":"bear_totem"},
      {"name":"Relentless Rage", "tier":3,"spec":None,"cost":2,
       "desc":"When reduced to 0 HP in rage, make CON save to stay at 1.","effect":"relentless_rage"},
    ]
  },
}

# Default empty tree for classes without one yet
for cls in ["Cleric","Druid","Ranger","Paladin","Bard","Wizard","Sorcerer","Monk"]:
    if cls not in TALENT_TREES:
        TALENT_TREES[cls] = {"specs":{},"talents":[]}

# ══════════════════════════════════════════════════════════════
#  NOTORIETY ECONOMY PERKS
# ══════════════════════════════════════════════════════════════

NOTORIETY_PERKS = {
  # Infamous perks (score < -50)
  "infamous": {
    "merchant_discount": 0.25,        # 25% off dark merchants
    "guild_access": True,             # Thieves/assassins guild quests
    "guard_hostility": True,          # Guards attack on sight
    "bounty_hunting": True,           # Can take bounty hunting contracts
    "thieves_respect": True,          # Street thieves won't rob you
    "undead_tolerance": True,         # Necromancers treat you as neutral
    "dark_merchant_items": [          # Exclusive items
        "Poisoned Dagger","Shadow Cloak","Dark Contract","Assassin's Tools",
    ],
    "flavor": "The shadows know your name. Dark alleys open for you.",
  },
  # Heralded perks (score > 50)
  "heralded": {
    "merchant_discount": 0.20,        # 20% off holy merchants
    "temple_access": True,            # Free healing at temples
    "guard_protection": True,         # Guards help you in combat
    "noble_quests": True,             # Access to noble/court quests
    "peasant_aid": True,              # Common folk help and give info
    "divine_resilience": True,        # +2 death saving throw bonus
    "holy_merchant_items": [          # Exclusive items
        "Holy Water","Blessed Armor","Divine Scroll","Saint's Relic",
    ],
    "flavor": "Your deeds are sung in the streets. Doors open before you knock.",
  },
  # Neutral (no perks but no enemies either)
  "neutral": {
    "merchant_discount": 0.0,
    "flavor": "You are unknown. Neither feared nor beloved.",
  }
}

def get_notoriety_perks(score: int) -> dict:
    if score < -50:   return NOTORIETY_PERKS["infamous"]
    if score > 50:    return NOTORIETY_PERKS["heralded"]
    return NOTORIETY_PERKS["neutral"]

def apply_merchant_discount(price: int, player: dict) -> int:
    score = player.get("notoriety_score", 0)
    perks = get_notoriety_perks(score)
    disc  = perks.get("merchant_discount", 0)
    return max(1, int(price * (1 - disc)))

# ══════════════════════════════════════════════════════════════
#  COMBAT ROUND ENGINE — FF3 style
# ══════════════════════════════════════════════════════════════

def get_available_moves(char: dict) -> List[dict]:
    """Get physical moves available to this character at their level."""
    cls = char.get("class", "Fighter")
    lvl = char.get("level", 1)
    available = []
    for move_name, move in PHYSICAL_MOVES.items():
        classes = move["classes"]
        if classes == "all" or cls in classes:
            if lvl >= move["min_level"]:
                available.append({"name": move_name, **move})
    return available

def get_available_spells(char: dict) -> dict:
    """Get spells available to this character."""
    cls = char.get("class", "Fighter")
    return SPELLS_BY_CLASS.get(cls, {"schools":[],"cantrips":[],"spells":[]})

def calc_hit(attacker: dict, target_ac: int, move: dict = None) -> Tuple[bool, bool, int]:
    """
    Roll to hit. Returns (hit, crit, roll).
    """
    stats  = attacker.get("stats", {})
    lvl    = attacker.get("level", 1)
    p      = prof(lvl)
    weapon = attacker.get("equipped", {}).get("weapon", "")

    # Attack stat
    arcane = ["Arcane Tome","Eldritch Focus"]
    finesse= ["Dagger","Shortsword","Rapier"]
    if any(a in weapon for a in arcane):
        stat_val = max(stats.get("INT",10), stats.get("CHA",10))
    elif any(f in weapon for f in finesse):
        stat_val = max(stats.get("STR",10), stats.get("DEX",10))
    else:
        stat_val = stats.get("STR", 10)

    atk_bonus = mod(stat_val) + p
    roll_val, raw = d20(atk_bonus)

    # Crit range check (improved_crit talent)
    crit_range = 19 if "improved_crit" in char_talents(attacker) else 20

    is_crit = raw >= crit_range
    is_miss = raw == 1
    if is_miss:  return False, False, raw
    if is_crit:  return True,  True,  raw
    return roll_val >= target_ac, False, raw

def char_talents(char: dict) -> List[str]:
    return [t["name"] for t in char.get("talents_learned", [])]

def calc_damage(attacker: dict, move_name: str, is_crit: bool = False, spell: dict = None) -> Tuple[int, str]:
    """
    Calculate damage for a move or spell.
    Returns (damage, description).
    """
    stats  = attacker.get("stats", {})
    weapon = attacker.get("equipped", {}).get("weapon", "")

    if spell:
        # Parse dice string like "2d6", "1d10", "8d8"
        dice_str = spell.get("dice", "1d6")
        if "d" in dice_str:
            parts = dice_str.split("d")
            count = int(parts[0]) if parts[0] else 1
            sides_bonus = parts[1].split("+")
            sides = int(sides_bonus[0])
            bonus_extra = int(sides_bonus[1]) if len(sides_bonus)>1 else 0
        else:
            return 0, "utility"
        dmg, rolls = roll(sides, count, bonus_extra)
        if is_crit: dmg *= 2
        dtype = spell.get("dtype","magic")
        return dmg, dtype

    # Physical move
    move_data = PHYSICAL_MOVES.get(move_name, {})
    bonus_dmg = move_data.get("bonus_dmg", 0)

    if bonus_dmg < 0:  # healing
        heal, _ = roll(6, 1, abs(bonus_dmg))
        return -heal, "heal"

    # Base weapon damage
    from combat import WEAPONS_DMG
    wdice = WEAPONS_DMG.get(weapon, "1d6")
    if "d" in wdice:
        parts = wdice.split("d")
        count = int(parts[0]) if parts[0] else 1
        sides = int(parts[1])
    else:
        count, sides = 1, 6
    dmg, rolls = roll(sides, count)
    dmg += bonus_dmg + mod(stats.get("STR", 10))
    if is_crit: dmg = dmg * 2
    return max(1, dmg), move_data.get("dtype","physical")

WEAPONS_DMG = {
    "Dagger":"1d4","Shortsword":"1d6","Longsword":"1d8","Greatsword":"2d6",
    "Handaxe":"1d6","Greataxe":"1d12","Quarterstaff":"1d6",
    "Shortbow":"1d6","Longbow":"1d8","Eldritch Focus":"1d10","Arcane Tome":"1d6",
}

# ══════════════════════════════════════════════════════════════
#  COMBAT ROUND MENU (FF3 style)
# ══════════════════════════════════════════════════════════════

def show_combat_header(player: dict, enemy_name: str, enemy_hp: int,
                       enemy_max_hp: int, round_num: int,
                       round_log: list = None, flash_msg: str = "",
                       flash_col: str = ""):
    """Display the cinematic combat screen."""
    if SCREEN_AVAILABLE:
        draw_combat_screen(player, enemy_name, enemy_hp, enemy_max_hp,
                           round_num, round_log=round_log,
                           flash_msg=flash_msg, flash_col=flash_col)
    else:
        # Fallback plain header
        divider("═", C.RED)
        print(f"{C.BOLD}{C.RED}  ⚔  COMBAT — Round {round_num}  ⚔{C.RESET}")
        divider("─", C.GRAY)
        hp = player.get("hp",1); mhp = _simple_max_hp(player)
        pct = hp/mhp if mhp else 0
        hcol = C.GREEN if pct>0.5 else C.ORANGE if pct>0.25 else C.RED
        hbar = cc(hcol,"█"*int(pct*20))+cc(C.GRAY,"░"*(20-int(pct*20)))
        print(f"  {C.BOLD}{C.CYAN}{player['name']:20}{C.RESET} HP:[{hbar}]{hcol}{hp}/{mhp}{C.RESET}")
        epct = enemy_hp/enemy_max_hp if enemy_max_hp else 0
        ecol = C.GREEN if epct>0.5 else C.ORANGE if epct>0.25 else C.RED
        ebar = cc(ecol,"█"*int(epct*20))+cc(C.GRAY,"░"*(20-int(epct*20)))
        print(f"  {C.BOLD}{C.RED}{enemy_name:20}{C.RESET} HP:[{ebar}]{ecol}{enemy_hp}/{enemy_max_hp}{C.RESET}")
        divider("─", C.GRAY)

def combat_menu(player: dict) -> dict:
    """
    Display the full FF3-style combat menu and return the chosen action.
    Returns a dict: {type, name, data, target}
    """
    moves   = get_available_moves(player)
    spells  = get_available_spells(player)
    has_spells = bool(spells.get("cantrips") or spells.get("spells"))
    slots   = player.get("spell_slots_current", 0)

    while True:
        print(f"\n  {C.BOLD}┌─ YOUR TURN ──────────────────────────────────────┐{C.RESET}")
        print(f"  {C.BOLD}│{C.RESET}  {cc(C.YELLOW,'[A]')} Attack    {cc(C.MAGENTA,'[M]')} Magic     {cc(C.CYAN,'[S]')} Skills    │")
        print(f"  {C.BOLD}│{C.RESET}  {cc(C.GREEN, '[I]')} Item      {cc(C.ORANGE,'[D]')} Defend    {cc(C.RED,  '[R]')} Run       │")
        print(f"  {C.BOLD}└──────────────────────────────────────────────────┘{C.RESET}")

        choice = input(f"  {C.BOLD}Action:{C.RESET} ").strip().upper()

        # ── ATTACK ──────────────────────────────────────────
        if choice == "A":
            weapon = player.get("equipped",{}).get("weapon","Fist")
            basic  = {"name":"Strike","bonus_dmg":0,"dtype":"weapon",
                      "desc":f"Attack with your {weapon}.","color":C.WHITE}
            print(f"\n  {C.BOLD}{C.WHITE}── ATTACK ─────────────────────────────────────{C.RESET}")
            print(f"  {cc(C.WHITE,'[1]')} Strike          Your {weapon} — basic attack")
            print(f"  {cc(C.GRAY, '[B]')} Back")
            sub = input("  > ").strip().upper()
            if sub == "B": continue
            return {"type":"attack","name":"Strike","data":basic}

        # ── MAGIC ───────────────────────────────────────────
        elif choice == "M":
            if not has_spells:
                cprint(C.GRAY,"  No spells available for your class."); continue
            print(f"\n  {C.BOLD}{C.MAGENTA}── MAGIC ──────────────────────────────────────{C.RESET}")
            all_spells = []
            idx = 1

            if spells.get("cantrips"):
                print(f"  {C.CYAN}Cantrips (free):{C.RESET}")
                for sp in spells["cantrips"]:
                    print(f"  {cc(C.CYAN,f'[{idx}]')} {C.BOLD}{sp['name']:20}{C.RESET} "
                          f"{C.GRAY}{sp['dice']} {sp['dtype']}{C.RESET}")
                    print(f"       {C.GRAY}{sp['desc']}{C.RESET}")
                    all_spells.append(("cantrip", sp))
                    idx += 1

            if spells.get("spells"):
                print(f"\n  {C.MAGENTA}Spells (slots: {slots}/{player.get('spell_slots_max',0)}):{C.RESET}")
                for sp in spells["spells"]:
                    cost = sp.get("slots",1)
                    avail= cc(C.GREEN,"✓") if slots>=cost else cc(C.RED,"✗")
                    print(f"  {avail} {cc(C.MAGENTA,f'[{idx}]')} {C.BOLD}{sp['name']:20}{C.RESET} "
                          f"{C.GRAY}[{cost}slot] {sp['dice']} {sp['dtype']}{C.RESET}")
                    print(f"       {C.GRAY}{sp['desc']}{C.RESET}")
                    all_spells.append(("spell", sp))
                    idx += 1

            print(f"  {cc(C.GRAY,'[B]')} Back")
            sub = input("  > ").strip().upper()
            if sub == "B": continue
            try:
                si  = int(sub) - 1
                stype, sp = all_spells[si]
                if stype == "spell" and slots < sp.get("slots",1):
                    cprint(C.RED, f"  Not enough spell slots! Need {sp['slots']}, have {slots}.")
                    continue
                return {"type":"spell","name":sp["name"],"data":sp,"stype":stype}
            except (ValueError,IndexError):
                cprint(C.RED,"  Invalid choice."); continue

        # ── SKILLS (physical moves) ──────────────────────────
        elif choice == "S":
            # Show available moves for this class/level
            atk_moves = [m for m in moves if m.get("dtype") not in ("buff","defense","utility","heal")]
            def_moves  = [m for m in moves if m.get("dtype") in ("defense","utility")]
            all_moves  = atk_moves + def_moves

            print(f"\n  {C.BOLD}{C.YELLOW}── SKILLS ─────────────────────────────────────{C.RESET}")
            for i, mv in enumerate(all_moves, 1):
                col = mv.get("color", C.WHITE)
                eff = f"  → {mv['effect']}" if mv.get("effect") else ""
                print(f"  {cc(C.YELLOW,f'[{i}]')} {col}{C.BOLD}{mv['name']:20}{C.RESET} "
                      f"{C.GRAY}+{mv['bonus_dmg']}dmg{eff}{C.RESET}")
                print(f"       {C.GRAY}{mv['desc']}{C.RESET}")
            print(f"  {cc(C.GRAY,'[B]')} Back")

            sub = input("  > ").strip().upper()
            if sub == "B": continue
            try:
                mi  = int(sub) - 1
                mv  = all_moves[mi]
                return {"type":"skill","name":mv["name"],"data":mv}
            except (ValueError,IndexError):
                cprint(C.RED,"  Invalid choice."); continue

        # ── ITEM ────────────────────────────────────────────
        elif choice == "I":
            inv = player.get("inventory", [])
            usable = [item for item in inv if any(w in item.lower()
                      for w in ["potion","bandage","antidote","scroll","elixir","salve"])]
            if not usable:
                cprint(C.GRAY,"  No usable items in combat."); continue
            print(f"\n  {C.BOLD}{C.GREEN}── ITEMS ──────────────────────────────────────{C.RESET}")
            for i, item in enumerate(usable, 1):
                print(f"  {cc(C.GREEN,f'[{i}]')} {item}")
            print(f"  {cc(C.GRAY,'[B]')} Back")
            sub = input("  > ").strip().upper()
            if sub == "B": continue
            try:
                item = usable[int(sub)-1]
                return {"type":"item","name":item,"data":{"item":item}}
            except (ValueError,IndexError):
                cprint(C.RED,"  Invalid."); continue

        # ── DEFEND ──────────────────────────────────────────
        elif choice == "D":
            cprint(C.BLUE,"\n  You take a defensive stance. +4 AC until your next turn.")
            return {"type":"defend","name":"Defend","data":{}}

        # ── RUN ─────────────────────────────────────────────
        elif choice == "R":
            dex_check, raw = d20(mod(player.get("stats",{}).get("DEX",10)))
            if dex_check >= 12:
                cprint(C.GRAY,f"  You disengage and flee! (rolled {raw})")
                return {"type":"run","name":"Flee","data":{"success":True}}
            else:
                cprint(C.RED,f"  You try to flee but they cut off your escape! (rolled {raw})")
                return {"type":"run","name":"Flee","data":{"success":False}}

        else:
            cprint(C.RED,"  Invalid. Choose A/M/S/I/D/R")

def build_combat_narration(player: dict, action: dict, enemy_name: str,
                            enemy_ac: int, result: dict) -> str:
    """
    Build a rich prompt for the AI to narrate this combat round.
    """
    stats = player.get("stats", {})
    action_type = action["type"]
    action_name = action["name"]
    hit     = result.get("hit", False)
    crit    = result.get("crit", False)
    damage  = result.get("damage", 0)
    effect  = result.get("effect")
    dtype   = result.get("dtype","")
    enemy_hp= result.get("enemy_hp", "unknown")
    enemy_max=result.get("enemy_max_hp","unknown")

    hp_desc = ""
    if isinstance(enemy_hp, int) and isinstance(enemy_max, int) and enemy_max > 0:
        pct = enemy_hp / enemy_max
        if pct <= 0:     hp_desc = "The enemy has fallen!"
        elif pct <= 0.25:hp_desc = f"The {enemy_name} is barely standing, near death."
        elif pct <= 0.5: hp_desc = f"The {enemy_name} is bloodied and struggling."
        else:            hp_desc = f"The {enemy_name} is still fighting hard."

    if action_type == "run":
        if result.get("success"): return f"Narrate {player['name']} successfully fleeing the battle."
        return f"Narrate {player['name']} attempting to flee but being cut off. They must keep fighting."

    if action_type == "defend":
        return (f"Narrate {player['name']} taking a defensive stance against {enemy_name}. "
                f"Describe their guard and positioning.")

    if not hit:
        return (f"Narrate a MISS. {player['name']} used {action_name} against {enemy_name} "
                f"but failed to land the blow. Make it dramatic — near miss, blade deflected, "
                f"spell fizzled, etc. {hp_desc}")

    if crit:
        return (f"Narrate a DEVASTATING CRITICAL HIT! {player['name']} used {action_name} "
                f"against {enemy_name} for {damage} {dtype} damage — DOUBLE DAMAGE. "
                f"Something dramatic happens: weapon shatters on impact, foe is sent flying, "
                f"psychic explosion, etc. {hp_desc}")

    effect_str = f" The attack applies the '{effect}' condition." if effect else ""
    return (f"Narrate {player['name']} using {action_name} against {enemy_name} for "
            f"{damage} {dtype} damage.{effect_str} {hp_desc} "
            f"Keep it cinematic — one vivid paragraph, no stat blocks.")

def resolve_action(player: dict, action: dict, enemy_ac: int, enemy_hp: int, enemy_max_hp: int) -> dict:
    """
    Mechanically resolve a combat action.
    Returns result dict with hit/damage/effects.
    """
    result = {
        "hit": False, "crit": False, "damage": 0,
        "dtype": "physical", "effect": None,
        "enemy_hp": enemy_hp, "enemy_max_hp": enemy_max_hp,
        "player_hp_change": 0,
    }

    atype = action["type"]

    if atype == "defend":
        player.setdefault("temp_effects", []).append("defending")
        return result

    if atype == "run":
        return result

    if atype == "item":
        item_name = action["name"]
        inv = player.get("inventory", [])
        if item_name in inv:
            inv.remove(item_name)
            heal = 0
            if "potion" in item_name.lower() or "elixir" in item_name.lower():
                heal, _ = roll(8, 2, 2)
            elif "bandage" in item_name.lower():
                heal, _ = roll(4, 1, 2)
            elif "antidote" in item_name.lower():
                if "poisoned" in player.get("conditions",[]): player["conditions"].remove("poisoned")
                heal = 0
            result["hit"]           = True
            result["player_hp_change"] = heal
            result["dtype"]         = "heal"
            result["damage"]        = heal
        return result

    if atype in ("attack","skill"):
        move_name = action["name"]
        hit, crit, roll_val = calc_hit(player, enemy_ac)
        result["hit"]  = hit
        result["crit"] = crit
        if hit:
            dmg, dtype = calc_damage(player, move_name, crit)
            result["damage"] = dmg
            result["dtype"]  = dtype
            move_data = action.get("data", {})
            if move_data.get("effect") and random.random() < 0.65:
                result["effect"] = move_data["effect"]
            result["enemy_hp"] = max(0, enemy_hp - dmg)
        return result

    if atype == "spell":
        spell = action["data"]
        stype = action.get("stype", "cantrip")
        slots = player.get("spell_slots_current", 0)
        dtype = spell.get("dtype","magic")

        # Healing spells
        if dtype == "heal":
            dice_str = spell.get("dice","1d8")
            if "d" in dice_str:
                p, s = dice_str.split("d")[:2]
                s = s.split("+")[0]
                heal, _ = roll(int(s), int(p) if p else 1,
                               mod(player.get("stats",{}).get("WIS",10)))
            else:
                heal = 4
            result["hit"]              = True
            result["player_hp_change"] = heal
            result["dtype"]            = "heal"
            result["damage"]           = heal
        elif dtype in ("buff","control","utility","shield"):
            result["hit"]   = True
            result["damage"]= 0
            result["effect"]= spell.get("effect")
        else:
            # Damage spell — most auto-hit, some require save
            result["hit"]  = True
            result["crit"] = random.random() < 0.05
            dmg, dtype2 = calc_damage(player, "", result["crit"], spell)
            result["damage"] = dmg
            result["dtype"]  = spell.get("dtype","magic")
            result["enemy_hp"] = max(0, enemy_hp - dmg)
            if spell.get("effect"): result["effect"] = spell["effect"]

        # Deduct slot for leveled spells
        if stype == "spell":
            player["spell_slots_current"] = max(0, slots - spell.get("slots",1))
            if player["spell_slots_current"] == 0:
                cprint(C.RED, f"  ⚠  Last spell slot used!")

        return result

def _simple_max_hp(char: dict) -> int:
    hd  = {"Barbarian":12,"Fighter":10,"Paladin":10,"Ranger":10,"Cleric":8,
           "Druid":8,"Monk":8,"Rogue":8,"Bard":8,"Warlock":8,"Wizard":6,"Sorcerer":6
           }.get(char.get("class","Fighter"),8)
    con = mod(char.get("stats",{}).get("CON",12))
    lvl = char.get("level",1)
    return max(1, hd + con + (hd//2+1+con)*(lvl-1))

# ══════════════════════════════════════════════════════════════
#  TALENT SYSTEM
# ══════════════════════════════════════════════════════════════

def show_talent_tree(player: dict):
    """Display the talent tree for the player's class."""
    cls  = player.get("class","Fighter")
    tree = TALENT_TREES.get(cls, {"specs":{},"talents":[]})
    lvl  = player.get("level",1)
    pts  = player.get("talent_points", 0)
    learned = [t["name"] for t in player.get("talents_learned",[])]

    divider("═",C.MAGENTA)
    print(f"{C.BOLD}{C.MAGENTA}  TALENT TREE — {cls}{C.RESET}  {cc(C.YELLOW,f'({pts} points available)')}")
    divider("─",C.GRAY)

    if tree.get("specs"):
        print(f"  {C.BOLD}Specializations:{C.RESET}")
        for spec, desc in tree["specs"].items():
            active = cc(C.GREEN,"★ ") if player.get("spec") == spec else "  "
            print(f"  {active}{C.BOLD}{spec}{C.RESET}: {C.GRAY}{desc}{C.RESET}")
        print()

    if not tree.get("talents"):
        cprint(C.GRAY,"  No talent tree available for this class yet.")
        divider("═",C.MAGENTA); return

    tiers = {}
    for t in tree["talents"]:
        tiers.setdefault(t["tier"],[]).append(t)

    tier_names = {1:"Tier 1 (Lvl 2+)",2:"Tier 2 (Lvl 4+)",3:"Tier 3 (Lvl 6+)",4:"Tier 4 (Lvl 8+)"}
    tier_req   = {1:2, 2:4, 3:6, 4:8}

    available_to_learn = []
    for tier_num in sorted(tiers.keys()):
        req = tier_req.get(tier_num, 2)
        unlocked = lvl >= req
        print(f"\n  {C.BOLD}{C.BLUE}{tier_names.get(tier_num,'Tier '+str(tier_num))}{C.RESET}"
              + (f" {cc(C.GREEN,'[UNLOCKED]')}" if unlocked else f" {cc(C.RED,'[Need Lvl '+str(req)+']')}"))

        for i, t in enumerate(tiers[tier_num]):
            is_learned  = t["name"] in learned
            can_afford  = pts >= t["cost"] and unlocked and not is_learned
            spec_str    = f" [{t['spec']}]" if t.get("spec") else ""
            status      = cc(C.GREEN,"✓ LEARNED") if is_learned else (
                          cc(C.CYAN, f"[{len(available_to_learn)+1}] {t['cost']}pt") if can_afford else
                          cc(C.GRAY, "  —"))
            print(f"    {status} {C.BOLD}{t['name']}{C.RESET}{C.GRAY}{spec_str}{C.RESET}")
            print(f"         {C.GRAY}{t['desc']}{C.RESET}")
            if can_afford:
                available_to_learn.append(t)

    divider("─",C.GRAY)
    if available_to_learn and pts > 0:
        choice = input(f"  Learn a talent? (1-{len(available_to_learn)} or Enter to skip): ").strip()
        try:
            t = available_to_learn[int(choice)-1]
            player.setdefault("talents_learned",[]).append(t)
            player["talent_points"] = pts - t["cost"]
            cprint(C.MAGENTA, f"  ✦ Learned: {t['name']}!")
            cprint(C.GRAY,    f"  {t['desc']}")
        except (ValueError,IndexError):
            pass
    elif pts == 0:
        cprint(C.GRAY,"  No talent points. Earn more by leveling up.")
    divider("═",C.MAGENTA)

def grant_talent_point(player: dict):
    """Give a talent point on level up."""
    player["talent_points"] = player.get("talent_points",0) + 1
    cprint(C.MAGENTA, f"  ✦ You gained a Talent Point! ({player['talent_points']} total)")
    cprint(C.GRAY,    "  Use /talents to spend it.")
