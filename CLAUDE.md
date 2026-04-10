# MVP Cuba 2011 Tournament Tracker

Baseball tournament tracker for a simulated Cuban National Series season played in MVP Baseball 2005. Two owners (Ernesto and Junior) each control 4 teams. Tracks standings, schedules, game results, player stats, draft, playoffs, antesala (pre-game show), and weekly recaps.

## Stack

- **Flask** with app factory pattern (`create_app()`) and **Blueprints**
- Raw **sqlite3** (no SQLAlchemy), with `sqlite3.Row` factory
- **Jinja2** server-rendered templates with reusable component macros
- **SQLite** database at `torneo.db` in project root (WAL mode)
- **Python 3**, dependencies: `flask`, `openpyxl`

## Engineering Principles

Follow `flask-sqlite-engineering-principles.md`. Key rules:
- Max 300 lines per file, single responsibility
- Type hints everywhere, Blueprints for every feature
- Component-based Jinja2 macros (no copy-paste HTML)
- Fat models / thin views — routes are glue, logic in services
- SQLite: WAL mode, `PRAGMA foreign_keys=ON`, short write transactions
- **Never DELETE database rows when refactoring UI** — modify queries/templates instead

## Project Structure

```
Torneo/
├── app.py                        # create_app() factory
├── config.py                     # BaseConfig, DevConfig, ProdConfig
├── db.py                         # get_db(), close_db(), init_app()
├── blueprints/
│   ├── main/                     # / (standings + recent games grid)
│   ├── teams/                    # /team/<short>
│   ├── players/                  # /player/<id>, /jugadores
│   ├── schedule/                 # /schedule (calendar, picks, GOTW, starters)
│   ├── games/                    # /game/<id>, /game/new/<id>, /game/save
│   ├── draft/                    # /draft
│   ├── playoffs/                 # /playoffs
│   ├── leaders/                  # /leaders
│   ├── antesala/                 # /antesala (analysts, predictions, tweet feed)
│   └── weekly/                   # /weekly, /weekly/<week_num>
├── services/
│   ├── standings.py              # get_standings(), get_all_teams()
│   ├── weekly.py                 # weekly summaries, tweets, predictions, game picks
│   ├── power_rankings.py         # compute_power_rankings()
│   ├── game_import.py            # insert_game() + validate_game()
│   └── attributes_import.py      # bulk_upsert()
├── lib/utils.py                  # format_ip() — Jinja2 global
├── templates/
│   ├── base.html                 # Layout: sidebar, {% block content %}, {% block scripts %}
│   ├── components/               # Reusable macros (see UI Components below)
│   ├── errors/                   # 404.html, 500.html
│   └── *.html                    # Page templates
├── static/
│   ├── style.css                 # Design system (see DESIGN.md)
│   ├── app.js                    # Sidebar toggle, card animations, initSortableTable()
│   └── graphics/                 # Team logos, player photos, analyst avatars, banners
├── schema.sql                    # Reference DDL only — do NOT run on populated DB
├── weekly.py                     # CLI: python weekly.py <week_num>
├── DESIGN.md                     # UI design spec (logo bleed, stat-num, etc.)
└── torneo.db                     # Live SQLite database
```

## UI Component Patterns

| Component | Macro | Purpose |
|-----------|-------|---------|
| `logo_img` | `logo_img(file, css_class, alt)` | All logos — never raw `<img>` for logos |
| `team_link` | `team_link(short, name, color, logo)` | Clickable team name + logo |
| `game_card` | `game_card(g, link)` | Game result card with logo bleed |
| `tweet_item` | `tweet_item(tweet)` | Tweet with likes, replies, hashtag |
| `pitcher_credits` | `pitcher_credits(wp, lp, ...)` | W/L pitcher line |
| `pitcher_select` | `pitcher_select(name, id, ...)` | Pitcher dropdown (game form) |
| `leaderboard_table` | `leaderboard_table(title, ...)` | Stat leader table (flexible columns) |
| `stat_box` | `stat_box(value, label)` | Stat display box |
| `empty_state` | `empty_state(message)` | Empty content placeholder |

**Key patterns:**
- **Logo sizes**: `inline-logo` (64px), `inline-logo-md` (32px), `inline-logo-sm` (16px)
- **Logo bleed**: Oversized logos cropped by `overflow: hidden`. See DESIGN.md §5.5
- **`{% block scripts %}`**: Page JS goes here (after app.js loads), not in `{% block content %}`
- **Sortable tables**: `data-sort="num|text"` on `<th>` + `initSortableTable(el)` in `{% block scripts %}`
- **`stat-num` class**: Barlow Condensed, `--text-2xl`, bold — for all prominent numbers

## Database Schema

| Table | Key columns / gotchas |
|-------|----------------------|
| `teams` | `short_name` (not `short`), `owner`, `color_primary`, `logo_file` |
| `players` | `name` (F. LastName format), `bats_throws` (not separate), `role` (lineup/bench/rotation/bullpen) |
| `schedule` | `game_num` (not `game_number`), `week_num`, `phase` |
| `games` | score, hits, errors, W/L/S pitcher IDs, `home_linescore`/`away_linescore` |
| `batting_stats` | Per-game: AB, R, H, doubles, triples, HR, RBI, BB, SO, SB |
| `pitching_stats` | `IP_outs` (total outs, use `format_ip()`), H, R, ER, BB, SO, HR_allowed, W, L, SV, pitches |
| `player_attributes` | power, contact, speed, pitch ratings (fastball thru curveball_dirt) |
| `analysts` | 3 personalities: Panfilo(1), Chequera(2), Facundo(3). Each has `equipo_favorito_id`, `equipo_odia_id` |
| `analyst_tweets` | **Two types**: game tweets (`game_id` set) shown on antesala, weekly analyses (`game_id IS NULL`) shown on weekly. Both have `week_num`. Has `likes` column |
| `tweet_commenters` | 10 fan personas for tweet replies |
| `tweet_replies` | Replies to analyst_tweets, with `commenter_id` and `likes` |
| `analyst_predictions` | Pre-season predictions (5 per analyst) |
| `analyst_game_picks` | Per-game winner predictions. UNIQUE(analyst_id, schedule_id) |
| `weekly_awards` | POTW, power_rankings (JSON), `game_of_week_id` per week |

## Domain Rules

- **8 teams**: Ernesto (GRA, SSP, PRI, LTU) / Junior (SCU, VCL, IND, CAV)
- **Regular season:** 96 games (4 per week, 24 weeks), each team plays 24
- **Playoffs:** Top 4 advance. Best-of-5 semis and finals
- **Draft:** 3 rounds, 8 picks each. Players marked `is_drafted=1`

## Game Data Entry — Complete Workflow

**For each game, do ALL of these steps in order:**

### Step 1: Parse box score screenshots

Games folder: `Games/game{N}/` with 6 PNG screenshots + `lanzamientos.txt`.

| Screenshot | Content |
|---|---|
| 1 | Away batting (top half) + linescore |
| 2 | Away batting (remaining + totals + extras: 2B, 3B, HR, IMP, SB, E) |
| 3 | Home batting (top half) |
| 4 | Home batting (remaining + totals + extras) |
| 5 | Away pitching |
| 6 | Home pitching |

**Parsing order:** Screenshots 2 & 4 first (totals), then 5 & 6 (pitching), then 1 & 3 (individual batting).

**Column mappings:** VB=AB, C=R, H=H, IMP=RBI, BB=BB, SO=SO, AVE=verification only. Pitching: INN=IP_outs, C=R, CL=ER, PCL=skip.

### Step 2: Insert game data

```python
from services.game_import import insert_game
game_id = insert_game(schedule_id=N, home_runs=X, away_runs=Y, ...)
```

`insert_game()` validates via 7 cross-checks and **raises ValueError** on failure.

### Step 3: Generate post-game tweets (MANDATORY)

**Every game needs 3 analyst tweets + fan replies.** Use `save_game_tweets()`.

**Analysts:**
| ID | Handle | Style | Fav | Hate |
|----|--------|-------|-----|------|
| 1 | Panfilo | Nostalgic, suffering, pitcher-focused | PRI | IND |
| 2 | Chequera | ALL CAPS, exaggerated, power-obsessed | GRA | CAV |
| 3 | Facundo | Formal, disciplined, methodical | SCU | LTU |

**10 Fan commenters for replies:**
| ID | Handle | Style |
|----|--------|-------|
| 1 | ElPelotero85 | Casual fan, Cuban slang |
| 2 | YasnielDLH | Stats guy, numbers, hashtags |
| 3 | LaViejaMarta | Grandma, emotional, grandson |
| 4 | TioRafael | Old school, 80s comparisons |
| 5 | MayelinPR | Pinar superfan, defensive |
| 6 | ElProfe_Beisbol | Technical, corrects everyone |
| 7 | NegroDeLoma | Santiago fan, loud, rivalry |
| 8 | Carlitosss | Teen, basic questions |
| 9 | DonaMercedes | Gossip, barrio news |
| 10 | ElGuajiro_VCL | Villa Clara farmer, proverbs |

**Tweet rules:** 1 sentence + 1 hashtag per analyst. 1-3 replies per tweet from random fans. Likes auto-randomized.

```python
from services.weekly import save_game_tweets
save_game_tweets(game_id=N, tweets=[
    {"analyst_id": 1, "texto": "Panfilo reaction. #Hashtag",
     "replies": [{"commenter_id": 3, "texto": "LaViejaMarta reply"}]},
    {"analyst_id": 2, "texto": "CHEQUERA CAPS REACTION! #Hashtag",
     "replies": [{"commenter_id": 1, "texto": "ElPelotero85 reply"}]},
    {"analyst_id": 3, "texto": "Facundo formal analysis. #Hashtag",
     "replies": [{"commenter_id": 6, "texto": "ElProfe reply"}]},
])
```

## Weekly Content Workflow

After all 4 games of week N are entered:

### Step 1: Generate weekly report
Run `python weekly.py N` — prints results, standings, top performers, upcoming games with rankings.

### Step 2: Save weekly content
- **POTW + Power Rankings**: `compute_power_rankings(N)` then `save_weekly_awards(N, potw_id, summary, rankings, game_of_week_id)`
- **Weekly analyses** (3 per week, 4 sentences each, NOT tweets): `save_weekly_tweets(N, [...])`
  - These are longer analysis pieces shown on `/weekly`, different from per-game tweets
  - `save_weekly_tweets` only deletes weekly tweets (`game_id IS NULL`), not game tweets

### Step 3: Generate predictions for week N+1
```python
picks = generate_game_picks(N+1)  # weighted: fav bias > rankings > pitching > H2H
save_game_picks(N+1, picks)
gotw = pick_game_of_week(N+1)     # closest power ranking matchup
```

Predictions show on `/schedule` — analyst avatars next to predicted winner, gold "Juego de la Semana" badge.

### Analyst prediction weights
| Factor | Panfilo | Chequera | Facundo |
|--------|---------|----------|---------|
| Favorite/hate bias | 0.40 | 0.45 | 0.35 |
| Power rankings | 0.20 | 0.25 | 0.25 |
| Pitcher matchup | 0.25 | 0.15 | 0.25 |
| Head-to-head | 0.15 | 0.15 | 0.15 |

Prediction accuracy tracked via `get_prediction_records()` — correct/total/pct per analyst.

## Player Attributes Entry

All 8 teams entered. Use `services/attributes_import.py :: bulk_upsert()`.

Screenshots in `C:\Users\ernes\Videos\Captures`, crop with `python scripts/crop_attributes.py`.

**Batter:** vs ZUR (power_vs_l, contact_vs_l) / vs DER (power_vs_r, contact_vs_r) / Vel (speed)

**Pitcher:** ESTAMINA (stamina) + pitch types: R4C=fastball, SLD=slider, CRV=curveball, SNK=sinker, TND=changeup, SPL=splitter, SCR=screwball, CBB=curveball_dirt, RCT=cutter

**Duplicate names:** Use `upsert_attributes(player_id, attrs)` with specific ID.
