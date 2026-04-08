# MVP Cuba 2011 Tournament Tracker

Baseball tournament tracker for a simulated Cuban National Series season played in MVP Baseball 2005. Two owners (Ernesto and Junior) each control 4 teams. The app tracks standings, schedules, game results, player stats, a draft system, playoffs, and an "antesala" (pre-game show) with analyst commentary.

## Stack

- **Flask** with app factory pattern (`create_app()`) and **Blueprints**
- Raw **sqlite3** (no SQLAlchemy), with `sqlite3.Row` factory
- **Jinja2** server-rendered templates with reusable component macros
- **SQLite** database at `torneo.db` in project root (WAL mode)
- **Python 3**, dependencies: `flask`, `openpyxl`

## Engineering Principles

Follow `flask-sqlite-engineering-principles.md` in this repo. Key rules:
- Max 300 lines per file, single responsibility
- Type hints everywhere
- Blueprints for every feature
- Component-based Jinja2 macros (reusable, no copy-paste HTML)
- Fat models / thin views — routes are glue, logic in services
- SQLite: WAL mode, `PRAGMA foreign_keys=ON`, short write transactions
- No hardcoded secrets, env-based config
- Fix tech debt immediately, DRY on 2nd occurrence

## Project Structure

```
TOrneo/
├── app.py                          # create_app() factory, blueprint registration
├── config.py                       # BaseConfig, DevConfig, ProdConfig
├── db.py                           # get_db(), close_db(), init_app() — WAL mode
├── blueprints/
│   ├── main/                       # / (index, standings)
│   │   ├── __init__.py             # main_bp
│   │   ├── routes.py
│   │   └── services.py             # get_recent_games()
│   ├── teams/                      # /team/<short>
│   │   ├── __init__.py             # teams_bp
│   │   ├── routes.py
│   │   └── services.py             # get_team(), get_roster(), team leaders
│   ├── players/                    # /player/<int:player_id>
│   │   ├── __init__.py             # players_bp
│   │   ├── routes.py
│   │   └── services.py             # get_player(), batting/pitching logs & totals
│   ├── schedule/                   # /schedule
│   │   ├── __init__.py             # schedule_bp
│   │   ├── routes.py
│   │   └── services.py             # get_schedule_games()
│   ├── games/                      # /game/new/<id>, /game/save (POST)
│   │   ├── __init__.py             # games_bp
│   │   ├── routes.py
│   │   └── services.py             # get_game_form_data(), save_game()
│   ├── draft/                      # /draft
│   │   ├── __init__.py             # draft_bp
│   │   ├── routes.py
│   │   └── services.py             # get_draft_picks(), get_draft_teams()
│   ├── playoffs/                   # /playoffs
│   │   ├── __init__.py             # playoffs_bp
│   │   ├── routes.py
│   │   └── services.py             # get_series()
│   ├── leaders/                    # /leaders
│   │   ├── __init__.py             # leaders_bp
│   │   ├── routes.py
│   │   └── services.py             # batting/pitching leader queries
│   ├── antesala/                   # /antesala
│   │   ├── __init__.py             # antesala_bp
│   │   ├── routes.py
│   │   └── services.py             # analysts, predictions, tweets
│   └── weekly/                     # /weekly
│       ├── __init__.py             # weekly_bp
│       └── routes.py
├── services/
│   ├── standings.py                # get_standings(), get_all_teams() — shared
│   └── weekly.py                   # weekly summaries, awards, tweets
├── lib/
│   └── utils.py                    # format_ip() — registered as Jinja2 global
├── templates/
│   ├── base.html                   # Master layout with nav
│   ├── components/                 # Reusable Jinja2 macros
│   │   ├── logo_img.html           # logo_img(logo_file, css_class, alt)
│   │   ├── team_link.html          # team_link(short, name, color, logo_file)
│   │   ├── stat_box.html           # stat_box(value, label)
│   │   ├── game_score.html         # game_score(home, away, h_color, a_color)
│   │   ├── pitcher_credits.html    # pitcher_credits(wp, lp, sv)
│   │   ├── owner_badge.html        # owner_badge(owner)
│   │   ├── empty_state.html        # empty_state(message)
│   │   ├── player_cell.html        # player_cell(player, show_full_name)
│   │   ├── section_label.html      # section_label(text)
│   │   └── series_table.html       # series_table(title, games)
│   ├── errors/
│   │   ├── 404.html
│   │   └── 500.html
│   ├── index.html                  # Homepage: standings + recent games
│   ├── team.html                   # Team detail: roster, batting/pitching leaders
│   ├── player.html                 # Player detail: attributes, draft info, game log
│   ├── schedule.html               # 96-game regular season schedule
│   ├── game_form.html              # Enter/edit game results (score, pitchers)
│   ├── draft.html                  # Draft picks tracker + team rankings
│   ├── playoffs.html               # Playoff bracket (semi A, semi B, final)
│   ├── leaders.html                # Statistical leaders (AVG, HR, RBI, ERA)
│   ├── antesala.html               # Analysts, predictions, tweets
│   └── weekly.html                 # Weekly recap: POTW, power rankings, tweets
├── static/
│   ├── style.css                   # Single stylesheet (~400 lines, CSS variables)
│   └── graphics/                   # Team logos (PNG), player photos, banners
├── schema.sql                      # Reference DDL for all tables (do NOT run on populated DB)
├── weekly.py                       # CLI: python weekly.py <week_num> — prints weekly summary
├── create_tournament.py            # Generates Excel workbook with tournament info
├── torneo.db                       # SQLite database (populated)
└── flask-sqlite-engineering-principles.md
```

## Routes (blueprint-qualified)

| Route | Endpoint | Purpose |
|-------|----------|---------|
| `/` | `main.index` | Standings table + last 10 games |
| `/team/<short>` | `teams.team` | Team roster, record, batting/pitching leaders |
| `/player/<int:player_id>` | `players.player` | Full player page with attributes, stats, game log |
| `/schedule` | `schedule.schedule` | Regular season schedule with scores |
| `/game/new/<int:schedule_id>` | `games.game_new` | Game entry/edit form |
| `/game/save` (POST) | `games.game_save` | Save game result |
| `/draft` | `draft.draft` | Draft picks display |
| `/playoffs` | `playoffs.playoffs` | Playoff bracket |
| `/leaders` | `leaders.leaders` | League statistical leaders |
| `/antesala` | `antesala.antesala` | Analyst show: predictions + tweets |
| `/weekly` | `weekly.weekly` | Weekly recap: POTW, rankings, tweets |
| `/weekly/<int:week_num>` | `weekly.weekly` | Weekly recap for specific week |

## Database Schema (torneo.db)

| Table | Purpose |
|-------|---------|
| `teams` | 8 teams with rankings, colors, logos, owner (Ernesto/Junior) |
| `players` | 71 players — role: lineup/bench/rotation/bullpen |
| `draft_picks` | 24 picks (3 rounds, 8 teams) linking to player IDs |
| `schedule` | 96 regular + playoff games, phase: regular/semi_a/semi_b/final |
| `games` | Results: score, hits, errors, W/L/S pitchers |
| `player_attributes` | Power, contact, speed, pitch ratings per player |
| `batting_stats` | Per-game: AB, R, H, 2B, 3B, HR, RBI, BB, SO, SB |
| `pitching_stats` | Per-game: IP_outs, H, R, ER, BB, SO, HR, W, L, SV |
| `analysts` | 4 commentator personalities with favorite/hated teams |
| `analyst_predictions` | Pre-season predictions per analyst |
| `analyst_tweets` | Game/weekly commentary per analyst (week_num for weekly) |
| `weekly_awards` | Player of the Week + Tele Rebelde Power Rankings per week |

**IP_outs:** Pitching innings are stored as total outs (not innings). Use `format_ip()` to display (e.g., 19 outs = "6.1").

## Key Architecture Patterns

- **App factory:** `create_app()` in `app.py` — creates app, registers blueprints, error handlers, Jinja2 globals
- **DB connection:** `db.get_db()` — request-scoped via Flask `g`, WAL mode, foreign keys ON, busy timeout 5s
- **Shared services:** `services/standings.py` — used by main, teams, and playoffs blueprints
- **Thin routes:** Routes call service functions and pass results to templates
- **Component macros:** Reusable Jinja2 macros in `templates/components/` — imported with `{% from %}` syntax

## Domain Rules

- **8 teams**, split between two owners: Ernesto (GRA, SSP, PRI, LTU) and Junior (SCU, VCL, IND, CAV)
- **Regular season:** 96 games (each team plays 24 — round-robin)
- **Playoffs:** Top 4 advance. Best-of-5 semis and finals
- **Draft:** 3 rounds, 8 picks each (24 total). Players marked `is_drafted=1`
- **Team short names** are 3-letter codes used in URLs: `/team/GRA`, `/team/IND`, etc.

## Running

```bash
pip install flask openpyxl
python app.py         # Runs on http://localhost:5000
```

## Schema Reference

`schema.sql` contains the full DDL for all tables. It is for reference only — do NOT run it against a populated database (it drops all tables). The live database is `torneo.db`; keep a backup.
