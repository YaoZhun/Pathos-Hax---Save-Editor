# model.py  —  pathosHax Model Layer
import re
from pathlib import Path

# ── Save directory detection ──────────────────────────
PATHOS_APP_STORE = (
    Path.home() / "Library" / "Containers" /
    "23F5B09B-E326-4C1F-A9D4-116369BDAF8D" / "Data" / "Library" / "Adventures"
)

def find_save_dir() -> str:
    if PATHOS_APP_STORE.exists():
        return str(PATHOS_APP_STORE)
    steam = Path.home() / "Library" / "Application Support" / "Steam" / "userdata"
    if steam.exists():
        for uid in steam.iterdir():
            c = uid / "679300"
            if c.exists():
                return str(c)
    return str(Path.home())

# ── Parser ────────────────────────────────────────────
# Real format: character @[000001] "Name" level N [gender] [race] [class]
#              ... life N mana N [dex] N [con] N [int] N [wis] N [cha] N
#              ... inventory { [item], [item] } square map ...

_STAT_RE = {
    "hp_current":    re.compile(r'\blife\s+(\d+)'),
    "hp_maximum":    re.compile(r'\blife\s+\d+/(\d+)'),
    "mp_current":    re.compile(r'\bmana\s+(\d+)'),
    "mp_maximum":    re.compile(r'\bmana\s+\d+/(\d+)'),
    "strength":      re.compile(r'\[str\]\s+(\d+)', re.I),
    "dexterity":     re.compile(r'\[dex\]\s+(\d+)', re.I),
    "constitution":  re.compile(r'\[con\]\s+(\d+)', re.I),
    "intelligence":  re.compile(r'\[int\]\s+(\d+)', re.I),
    "wisdom":        re.compile(r'\[wis\]\s+(\d+)', re.I),
    "charisma":      re.compile(r'\[cha\]\s+(\d+)', re.I),
}

def _player_line(text: str):
    """Return (line_index, line_text) for the @[000001] player line."""
    for i, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("character @[000001]"):
            return i, line
    return None, None

def parse(text: str) -> tuple[dict, list]:
    """Return (fields_dict, inventory_list)."""
    fields, inventory = {}, []
    _, pl = _player_line(text)
    if pl is None:
        return fields, inventory

    # Name
    m = re.search(r'@\[000001\]\s+"([^"]+)"', pl)
    if m: fields["name"] = m.group(1)

    # Level
    m = re.search(r'\blevel\s+(\d+)', pl)
    if m: fields["level"] = m.group(1)

    # Gender
    for g in ("male", "female"):
        if f"[{g}]" in pl: fields["gender"] = g; break

    # Race & Class (come after [gender])
    m = re.search(r'\[(?:male|female)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]', pl)
    if m: fields["race"] = m.group(1); fields["class"] = m.group(2)

    # Alignment
    for al in ("lawful", "neutral", "chaotic"):
        if al in pl: fields["alignment"] = al; break

    # Stats
    for key, pat in _STAT_RE.items():
        m = pat.search(pl)
        if m: fields[key] = m.group(1)

    # Fill hp/mp max if only single value
    if "hp_current" in fields and "hp_maximum" not in fields:
        fields["hp_maximum"] = fields["hp_current"]
    if "mp_current" in fields and "mp_maximum" not in fields:
        fields["mp_maximum"] = fields["mp_current"]

    # Inventory
    m = re.search(r'\binventory\s*\{([^}]*)\}', pl)
    if m:
        for chunk in m.group(1).split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            names = re.findall(r'\[([^\]]+)\]', chunk)
            if names:
                # skip qty tokens like "3 x"
                real = [n for n in names if not re.match(r'^\d+\s*x$', n)]
                if real:
                    inventory.append(real[-1])

    return fields, inventory


def serialize(original_text: str, fields: dict, inventory: list) -> str:
    """Modify the @[000001] player line in-place; return full updated text."""
    idx, pl = _player_line(original_text)
    if idx is None:
        return original_text

    line = pl

    # Name
    if "name" in fields:
        line = re.sub(r'(@\[000001\]\s+)"[^"]*"',
                      lambda m: f'{m.group(1)}"{fields["name"]}"', line)

    # Level
    if "level" in fields:
        line = re.sub(r'\blevel\s+\d+', f'level {fields["level"]}', line)

    # HP  (handles both "life N" and "life N/M")
    if fields.get("hp_current"):
        hp_c = fields["hp_current"]
        hp_m = fields.get("hp_maximum", hp_c)
        if re.search(r'\blife\s+\d+/\d+', line):
            line = re.sub(r'\blife\s+\d+/\d+', f'life {hp_c}/{hp_m}', line)
        else:
            line = re.sub(r'\blife\s+\d+', f'life {hp_c}', line)

    # MP
    if fields.get("mp_current"):
        mp_c = fields["mp_current"]
        mp_m = fields.get("mp_maximum", mp_c)
        if re.search(r'\bmana\s+\d+/\d+', line):
            line = re.sub(r'\bmana\s+\d+/\d+', f'mana {mp_c}/{mp_m}', line)
        else:
            line = re.sub(r'\bmana\s+\d+', f'mana {mp_c}', line)

    # Attributes
    for key, tok in [("strength","[str]"), ("dexterity","[dex]"),
                     ("constitution","[con]"), ("intelligence","[int]"),
                     ("wisdom","[wis]"), ("charisma","[cha]")]:
        if key in fields:
            pat = re.escape(tok) + r'\s+\d+'
            line = re.sub(pat, f'{tok} {fields[key]}', line, flags=re.I)

    # Inventory
    if inventory is not None:
        inv_str = ", ".join(f"[{it}]" for it in inventory)
        new_inv = f"inventory {{ {inv_str} }}"
        if re.search(r'\binventory\s*\{[^}]*\}', line):
            line = re.sub(r'\binventory\s*\{[^}]*\}', new_inv, line)
        else:
            line = re.sub(r'\bsquare\b', f'{new_inv} square', line)

    lines = original_text.splitlines()
    lines[idx] = line
    return "\n".join(lines)


# ── Known items for autocomplete ──────────────────────
KNOWN_ITEMS = [
    "quarterstaff","dagger","short sword","long sword","two-handed sword",
    "battle axe","war hammer","spear","trident","bow","crossbow",
    "leather armour","chain mail","plate mail","dragon scale mail",
    "shield","helmet","boots","gloves","cloak of magic resistance",
    "potion of healing","potion of full healing","potion of extra healing",
    "potion of gain energy","potion of gain level","potion of speed",
    "potion of invisibility","potion of recovery","potion of see invisible",
    "potion of divinity","potion of polymorph",
    "scroll of identify","scroll of enchantment","scroll of water",
    "scroll of enchant weapon","scroll of enchant armour",
    "scroll of teleportation","scroll of remove curse","scroll of charging",
    "ring of regeneration","ring of protection","ring of accuracy","ring of impact",
    "wand of wishing","wand of death","wand of fire","wand of lightning",
    "wand of polymorph","wand of teleportation","wand of undead turning",
    "lembas wafer","food ration","fortune cookie",
    "amulet of yendor","magic lamp","magic marker","luckstone",
]

DEMO_TEXT = """\
adventure
seed 0x00000001;
clock 0;
character @[000001] "Aldric" level 7 [male] [human] [barbarian] glyph [human male barbarian] chaotic life 45 mana 12 [str] 18 [dex] 14 [con] 16 [int] 10 [wis] 12 [cha] 9 skills [fighting] inventory { [long sword enchanted +2], [leather armour], [potion of healing], [scroll of identify], [food ration] } square map [_level//depth_ 1] (04,23);
"""
