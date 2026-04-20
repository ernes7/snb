-- MVP Cuba 2011 Tournament Database Schema
-- Reference only. Do NOT run against a populated database — it drops all tables.

DROP TABLE IF EXISTS pitching_stats;
DROP TABLE IF EXISTS batting_stats;
DROP TABLE IF EXISTS player_attributes;
DROP TABLE IF EXISTS analyst_tweets;
DROP TABLE IF EXISTS analyst_predictions;
DROP TABLE IF EXISTS analysts;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS schedule;
DROP TABLE IF EXISTS draft_picks;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    owner TEXT NOT NULL,
    rank_overall INTEGER,
    rank_pitching INTEGER,
    rank_batting INTEGER,
    rank_fielding INTEGER,
    rank_speed INTEGER,
    rank_pre_draft INTEGER,
    rank_post_draft INTEGER,
    color_primary TEXT,
    color_secondary TEXT,
    logo_file TEXT,
    banner_file TEXT
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    name TEXT NOT NULL,
    full_name TEXT,
    position TEXT NOT NULL,
    bats_throws TEXT,
    role TEXT NOT NULL CHECK (role IN ('lineup','bench','rotation','bullpen')),
    lineup_order INTEGER,
    bullpen_role TEXT,
    is_drafted INTEGER DEFAULT 0 CHECK (is_drafted IN (0,1)),
    photo_file TEXT
);

CREATE TABLE draft_picks (
    id INTEGER PRIMARY KEY,
    pick_num INTEGER,
    round INTEGER,
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    position_drafted TEXT
);

CREATE TABLE schedule (
    id INTEGER PRIMARY KEY,
    game_num INTEGER,
    week_num INTEGER,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    phase TEXT DEFAULT 'regular' CHECK (phase IN ('regular','playoffs','finals')),
    series_game INTEGER,
    CHECK (home_team_id <> away_team_id)
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY,
    schedule_id INTEGER UNIQUE REFERENCES schedule(id),
    date TEXT,
    home_runs INTEGER,
    away_runs INTEGER,
    home_hits INTEGER,
    away_hits INTEGER,
    home_errors INTEGER,
    away_errors INTEGER,
    winning_pitcher_id INTEGER REFERENCES players(id),
    losing_pitcher_id INTEGER REFERENCES players(id),
    save_pitcher_id INTEGER REFERENCES players(id),
    notes TEXT,
    home_linescore TEXT,
    away_linescore TEXT
);

CREATE TABLE player_attributes (
    id INTEGER PRIMARY KEY,
    player_id INTEGER UNIQUE REFERENCES players(id),
    power_vs_l INTEGER,
    contact_vs_l INTEGER,
    power_vs_r INTEGER,
    contact_vs_r INTEGER,
    speed INTEGER,
    stamina INTEGER,
    fastball INTEGER,
    slider INTEGER,
    curveball INTEGER,
    sinker INTEGER,
    changeup INTEGER,
    splitter INTEGER,
    screwball INTEGER,
    cutter INTEGER,
    curveball_dirt INTEGER,
    circle_changeup INTEGER
);

CREATE TABLE analysts (
    id INTEGER PRIMARY KEY,
    handle TEXT NOT NULL UNIQUE,
    edad INTEGER,
    descripcion TEXT,
    equipo_favorito_id INTEGER REFERENCES teams(id),
    equipo_odia_id INTEGER REFERENCES teams(id),
    estilo TEXT,
    frase TEXT,
    emoji TEXT,
    avatar_file TEXT
);

CREATE TABLE analyst_predictions (
    id INTEGER PRIMARY KEY,
    analyst_id INTEGER REFERENCES analysts(id),
    pred_num INTEGER,
    titulo TEXT,
    texto TEXT
);

CREATE TABLE analyst_tweets (
    id INTEGER PRIMARY KEY,
    analyst_id INTEGER REFERENCES analysts(id),
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    texto TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    week_num INTEGER,
    likes INTEGER DEFAULT 0
);

CREATE TABLE tweet_commenters (
    id INTEGER PRIMARY KEY,
    handle TEXT NOT NULL UNIQUE,
    personalidad TEXT,
    emoji TEXT,
    avatar_file TEXT
);

CREATE TABLE tweet_replies (
    id INTEGER PRIMARY KEY,
    tweet_id INTEGER REFERENCES analyst_tweets(id) ON DELETE CASCADE,
    commenter_id INTEGER REFERENCES tweet_commenters(id),
    texto TEXT NOT NULL,
    likes INTEGER DEFAULT 0
);

CREATE TABLE weekly_awards (
    id INTEGER PRIMARY KEY,
    week_num INTEGER NOT NULL,
    potw_player_id INTEGER REFERENCES players(id),
    potw_summary TEXT,
    power_rankings TEXT,
    game_of_week_id INTEGER REFERENCES schedule(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_num)
);

CREATE TABLE newspaper_editions (
    id INTEGER PRIMARY KEY,
    edition_num INTEGER UNIQUE NOT NULL,
    week_num INTEGER NOT NULL,
    headline TEXT NOT NULL,
    subheadline TEXT,
    articles TEXT NOT NULL,
    interview TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE analyst_game_picks (
    id INTEGER PRIMARY KEY,
    analyst_id INTEGER REFERENCES analysts(id),
    schedule_id INTEGER REFERENCES schedule(id),
    picked_team_id INTEGER REFERENCES teams(id),
    week_num INTEGER NOT NULL,
    UNIQUE(analyst_id, schedule_id)
);

CREATE TABLE batting_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    AB INTEGER DEFAULT 0,
    R INTEGER DEFAULT 0,
    H INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    HR INTEGER DEFAULT 0,
    RBI INTEGER DEFAULT 0,
    BB INTEGER DEFAULT 0,
    SO INTEGER DEFAULT 0,
    SB INTEGER DEFAULT 0,
    UNIQUE(game_id, player_id)
);

CREATE TABLE pitching_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    IP_outs INTEGER DEFAULT 0,
    H INTEGER DEFAULT 0,
    R INTEGER DEFAULT 0,
    ER INTEGER DEFAULT 0,
    BB INTEGER DEFAULT 0,
    SO INTEGER DEFAULT 0,
    HR_allowed INTEGER DEFAULT 0,
    W INTEGER DEFAULT 0,
    L INTEGER DEFAULT 0,
    SV INTEGER DEFAULT 0,
    pitches INTEGER DEFAULT 0,
    UNIQUE(game_id, player_id)
);

-- -------------------------------------------------------------------
-- Indexes on hot paths (queries that filter/join heavily on these cols)
-- -------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_batting_stats_game    ON batting_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_batting_stats_player  ON batting_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_batting_stats_team    ON batting_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_pitching_stats_game   ON pitching_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_pitching_stats_player ON pitching_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pitching_stats_team   ON pitching_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_schedule_week_phase   ON schedule(phase, week_num);
CREATE INDEX IF NOT EXISTS idx_schedule_home         ON schedule(home_team_id);
CREATE INDEX IF NOT EXISTS idx_schedule_away         ON schedule(away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_schedule        ON games(schedule_id);
CREATE INDEX IF NOT EXISTS idx_analyst_tweets_week   ON analyst_tweets(week_num);
CREATE INDEX IF NOT EXISTS idx_analyst_tweets_game   ON analyst_tweets(game_id);
CREATE INDEX IF NOT EXISTS idx_tweet_replies_tweet   ON tweet_replies(tweet_id);
CREATE INDEX IF NOT EXISTS idx_players_team          ON players(team_id);

-- -------------------------------------------------------------------
-- Player moneylines — data-driven prop predictions per game
-- -------------------------------------------------------------------
CREATE TABLE game_moneylines (
    id INTEGER PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedule(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    prop_type TEXT NOT NULL,
    prop_text TEXT NOT NULL,
    stat_detail TEXT NOT NULL,
    confidence REAL NOT NULL,
    slot INTEGER NOT NULL CHECK (slot IN (1, 2, 3)),
    week_num INTEGER NOT NULL,
    UNIQUE(schedule_id, slot)
);
CREATE INDEX IF NOT EXISTS idx_moneylines_schedule ON game_moneylines(schedule_id);
CREATE INDEX IF NOT EXISTS idx_moneylines_week     ON game_moneylines(week_num);
