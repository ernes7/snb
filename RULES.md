# League Rules — Serie Nacional Cuba 2011

## Teams

**8 teams**, two owners:
- **Ernesto:** GRA (Granma), SSP (Sancti Spiritus), PRI (Pinar del Rio), LTU (Las Tunas)
- **Junior:** SCU (Santiago de Cuba), VCL (Villa Clara), IND (Industriales), CAV (Ciego de Avila)

Same-owner teams never play each other.

## Regular Season

- 96 games total (4 per week, 24 weeks)
- Each team plays 24 games

## Standings Tiebreakers

Sort order: win% → in-group tiebreaker → sub-tie H2H → overall run differential → runs scored.

- **2-way tie**: head-to-head wins, then run differential *within those same H2H games* if H2H is level — **unless the two teams share an owner** (same-owner teams never play each other), in which case the tiebreaker is overall run differential directly.
- **3+ way tie**: run differential restricted to games played among the tied teams only. If two teams within a 3+ group remain tied on intra-group RD, they are re-broken via H2H (if different owners).
- **Final fallback**: overall run differential → total runs scored (higher ranks first).
- **GB column**: computed from the top team's W-L after sorting — two teams at the top show "-" even if they got there by tiebreak.

Implementation lives in `services/standings.py`.

## Playoffs

- Top 4 advance. Best-of-5 semifinals and finals.
- **Same-owner rule**: if 3 teams from the same owner qualify, that owner must eliminate one of their teams before the bracket is set. The other owner (with 1 qualifying team) plays both rounds normally.

## Draft

- 3 rounds, 3 picks per team (24 total picks)
- Players marked `is_drafted=1`

## Season Awards

Six awards, each with its own scoring mechanic. All rendered at `/mvp-race`.

### Premio Kindelan — Batter MVP
OPS-driven. Base = `OPS × 100`, plus top-5 bonus in AVG / HR / RBI (5-4-3-2-1 points). Multiplied by team standing (1st = ×1.06, 8th = ×0.92, 2% steps). Qualifies: `AB + BB ≥ 2 × team games`.

### Premio Lazo — Pitcher Cy Young
ERA-driven. Base = `max(0, 10 − ERA) × 10`, plus top-5 bonus in SO / ERA / W. Same team multiplier. Qualifies: `IP_outs ≥ 2.4 × team games`.

### Premio al Artesano — Best Starter by Consistency
Bill James Game Score per start: `outs + 2·SO − 3·ER − 2·BB − 4·HR`. Quality start = ≥18 outs and ≤3 ER. Dominant = ≥21 outs and ≤1 ER. Disaster = <9 outs or ≥6 ER. Total = sum of game scores + total outs + 10·dominant − 15·disasters + 2·QS streak. Bonus top-5 in QS / DOM / fewest disasters. **No team multiplier.** Qualifies: `role='rotation'` with ≥2 starts or ≥15 total outs.

### Premio Clutch — Best in Decisive Moments
Only counts *clutch games*: final margin ≤2 runs or opponent in top-4 of that week's power ranking. Score = `clutch_OPS × 100 × √(clutch_AB / 10)`. **No bonus or team multiplier.** Qualifies: ≥10 AB in clutch games.

### Cinco Herramientas — Most Complete Player
Three tools, each 40% scout rating + 60% real production converted to league percentile: Contact (contact ratings + AVG), Power (power ratings + ISO), Speed (speed rating + R/(H+BB)). Final = `100 × geometric mean` of three tools. Bonus top-5 per tool. **No team multiplier.**

### Premio Encubierto — Best Low-OVR Batter
Kindelan formula restricted to batters with OVR below league average. Extra bonus: `+0.5 × (avg − OVR)`. **No team multiplier.** Qualifies: OVR below average and `AB + BB ≥ 1 × team games`.

### Award details
- Full scoring formula in `memory/project_mvp_awards.md` and `blueprints/mvp_race/services.py` (Kindelan/Lazo) + `blueprints/mvp_race/awards.py` (other four).
- Team multiplier: 2% steps (1.06 to 0.92) — only Kindelan and Lazo use it.
- Batter triple crown: AVG / HR / RBI. Pitcher triple crown: SO / ERA / W.
- Tiebreakers in bonus grading: most AB for batters, most IP_outs for pitchers.

## Leader Tiebreakers

When stats tie on `/leaders`, batters break ties by most AB, pitchers by most IP_outs. Same logic used in MVP race bonus grading (`_grade_ranks` in `blueprints/mvp_race/services.py`).
