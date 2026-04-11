"""Stat line value objects — single source of truth for rate stats.

`BattingLine` and `PitchingLine` wrap a set of counting stats and expose
rate stats (AVG/OBP/SLG/OPS, ERA/WHIP/K9) as computed properties. Build
one from a `sqlite3.Row` or dict via `from_row()`; any query that returns
the raw SUM() columns with the expected names will work.

All rate stats return 0.0 when the denominator is 0, so templates can
render them unconditionally. OPS is computed from unrounded OBP + SLG
to avoid cumulative rounding drift.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _get(row: Any, key: str) -> int:
    """Safely read an int column from a sqlite3.Row or mapping."""
    if row is None:
        return 0
    try:
        val = row[key]
    except (KeyError, IndexError):
        return 0
    return int(val) if val is not None else 0


@dataclass(frozen=True)
class BattingLine:
    """A batting stat line. Counting stats are fields; rate stats are properties."""
    AB: int = 0
    R: int = 0
    H: int = 0
    doubles: int = 0
    triples: int = 0
    HR: int = 0
    RBI: int = 0
    BB: int = 0
    SO: int = 0
    SB: int = 0

    @property
    def singles(self) -> int:
        return self.H - self.doubles - self.triples - self.HR

    @property
    def TB(self) -> int:
        """Total bases."""
        return self.H + self.doubles + 2 * self.triples + 3 * self.HR

    @property
    def AVG(self) -> float:
        return round(self.H / self.AB, 3) if self.AB else 0.0

    @property
    def OBP(self) -> float:
        """On-base percentage — (H+BB)/(AB+BB) approximation (no HBP/SF tracked)."""
        denom = self.AB + self.BB
        return round((self.H + self.BB) / denom, 3) if denom else 0.0

    @property
    def SLG(self) -> float:
        return round(self.TB / self.AB, 3) if self.AB else 0.0

    @property
    def OPS(self) -> float:
        """On-base + slugging, computed from unrounded components."""
        if not self.AB:
            return 0.0
        obp_raw = (self.H + self.BB) / (self.AB + self.BB) if (self.AB + self.BB) else 0.0
        slg_raw = self.TB / self.AB
        return round(obp_raw + slg_raw, 3)

    @property
    def ISO(self) -> float:
        """Isolated power — SLG minus AVG."""
        return round(self.SLG - self.AVG, 3) if self.AB else 0.0

    @classmethod
    def from_row(cls, row: Any) -> "BattingLine":
        """Build a BattingLine from a sqlite3.Row or dict of SUM() columns."""
        return cls(
            AB=_get(row, "AB"),
            R=_get(row, "R"),
            H=_get(row, "H"),
            doubles=_get(row, "doubles"),
            triples=_get(row, "triples"),
            HR=_get(row, "HR"),
            RBI=_get(row, "RBI"),
            BB=_get(row, "BB"),
            SO=_get(row, "SO"),
            SB=_get(row, "SB"),
        )


@dataclass(frozen=True)
class PitchingLine:
    """A pitching stat line. Counting stats are fields; rate stats are properties."""
    IP_outs: int = 0
    H: int = 0
    R: int = 0
    ER: int = 0
    BB: int = 0
    SO: int = 0
    HR_allowed: int = 0
    W: int = 0
    L: int = 0
    SV: int = 0

    @property
    def ERA(self) -> float:
        return round(self.ER * 27 / self.IP_outs, 2) if self.IP_outs else 0.0

    @property
    def WHIP(self) -> float:
        """Walks + hits per inning pitched."""
        return round((self.BB + self.H) * 3 / self.IP_outs, 2) if self.IP_outs else 0.0

    @property
    def K9(self) -> float:
        """Strikeouts per 9 innings."""
        return round(self.SO * 27 / self.IP_outs, 2) if self.IP_outs else 0.0

    @classmethod
    def from_row(cls, row: Any) -> "PitchingLine":
        return cls(
            IP_outs=_get(row, "IP_outs"),
            H=_get(row, "H"),
            R=_get(row, "R"),
            ER=_get(row, "ER"),
            BB=_get(row, "BB"),
            SO=_get(row, "SO"),
            HR_allowed=_get(row, "HR_allowed"),
            W=_get(row, "W"),
            L=_get(row, "L"),
            SV=_get(row, "SV"),
        )
