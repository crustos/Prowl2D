"""Emoji handling: find emoji clusters in text, measure them, turn them into identifiers.

Python can't have emoji in identifiers, so the parser rewrites every emoji cluster to
a readable name such as ``tile_BRICK`` or ``tile_LARGE_PURPLE_SQUARE``. A cluster is the
whole visible glyph: base char + variation selector, ZWJ sequences, skin tones, flags, keycaps.
"""
from __future__ import annotations

import re
import unicodedata

ZWJ = "‍"
VS15 = "︎"  # text presentation
VS16 = "️"  # emoji presentation
KEYCAP = "⃣"


def is_symbol_start(ch: str) -> bool:
    """True for characters that can start an emoji/symbol cluster."""
    cp = ord(ch)
    if cp < 0x203C:  # ASCII, Latin, punctuation etc. are never tiles
        return False
    if 0x1F3FB <= cp <= 0x1F3FF:  # skin tone modifiers
        return True
    cat = unicodedata.category(ch)
    if cat == "So":
        return True
    # emoji newer than this Python's unicode database show up as unassigned
    return cat == "Cn" and 0x1F000 <= cp <= 0x1FAFF


def scan_cluster(s: str, i: int) -> int:
    """If an emoji cluster starts at s[i], return its end index, else return i."""
    n = len(s)
    ch = s[i]
    if ch in "0123456789#*":  # keycap: 1️⃣
        j = i + 1
        if j < n and s[j] == VS16:
            j += 1
        return j + 1 if j < n and s[j] == KEYCAP else i
    if not is_symbol_start(ch):
        return i
    j = i + 1
    if 0x1F1E6 <= ord(ch) <= 0x1F1FF:  # flag = two regional indicators
        if j < n and 0x1F1E6 <= ord(s[j]) <= 0x1F1FF:
            j += 1
        return j
    while True:
        while j < n and (
            s[j] in (VS15, VS16, KEYCAP)
            or 0x1F3FB <= ord(s[j]) <= 0x1F3FF
            or 0xE0020 <= ord(s[j]) <= 0xE007F
        ):
            j += 1
        if j + 1 < n and s[j] == ZWJ and is_symbol_start(s[j + 1]):
            j += 2
            continue
        return j


def cluster_width(cluster: str) -> int:
    """Terminal/editor cell width of a cluster (emoji are 2 cells wide)."""
    if VS15 in cluster:
        return 1
    if VS16 in cluster or ZWJ in cluster or KEYCAP in cluster:
        return 2
    if 0x1F1E6 <= ord(cluster[0]) <= 0x1F1FF:
        return 2
    return 2 if unicodedata.east_asian_width(cluster[0]) in ("W", "F") else 1


def char_width(ch: str) -> int:
    if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def ident_for(cluster: str) -> str:
    """tile_BRICK for 🧱, tile_MOUNTAIN for ⛰️ (variation selectors are ignored)."""
    parts = []
    for c in cluster:
        if c in (VS15, VS16, ZWJ):
            continue
        try:
            name = unicodedata.name(c)
        except ValueError:
            name = f"U{ord(c):X}"
        parts.append(re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_"))
    return "tile_" + "_".join(parts)


class SymbolTable:
    """name -> glyph registry filled while translating."""

    def __init__(self) -> None:
        self.glyphs: dict[str, str] = {}

    def name_for(self, cluster: str) -> str:
        name = ident_for(cluster)
        old = self.glyphs.get(name)
        # prefer the spelling with VS16 so emoji fonts pick the colour glyph
        if old is None or (VS16 in cluster and VS16 not in old):
            self.glyphs[name] = cluster
        return name
