/*
    Table SQLITE
*/
drop table if exists PTF;
CREATE TABLE ptf (
    ptf_id                TEXT    NOT NULL,
    ptf_name              TEXT,
    ptf_account           TEXT,
    ptf_quantity          INTEGER DEFAULT (0),
    ptf_quote             REAL    DEFAULT (0),
    ptf_cost              REAL    DEFAULT (0),
    ptf_percent           REAL,
    ptf_rsi               REAL    DEFAULT (0),
    ptf_q26               INTEGER,
    ptf_q12               INTEGER,
    ptf_trade             TEXT,
    ptf_date              TEXT,
    ptf_gain              REAL    DEFAULT (0),
    ptf_gain_percent      REAL    DEFAULT (0),
    ptf_note              TEXT,
    ptf_cac40             INTEGER
);

CREATE UNIQUE INDEX PTF_INDEX ON PTF (ptf_id)

drop table if exists COURS;
CREATE TABLE COURS (
    cours_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    cours_ptf_id       TEXT    NOT NULL,
    cours_name         TEXT,
    cours_date         TEXT,
    cours_close        REAL,
    cours_open         REAL,
    cours_low          REAL,
    cours_high         REAL,
    cours_percent      REAL,
    cours_volume       REAL,
    cours_rsi          REAL,
    cours_ema12        REAL,
    cours_ema26        REAL,
    cours_ema50        REAL,
    cours_q12          INTEGER,
    cours_q26          INTEGER,
    cours_trade        TEXT,
    cours_quantity     REAL,
    cours_cost         REAL,
    cours_nbj          REAL,
    cours_gainj        REAL,
    cours_gain         REAL,
    cours_gain_percent REAL,
    cours_inptf        INTEGER,
    cours_intest       INTEGER
);

drop table if exists MVT;
CREATE TABLE MVT (
    mvt_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    mvt_ptf_id       TEXT    NOT NULL,
    mvt_account      TEXT    DEFAULT (''),
    mvt_date         TEXT    NOT NULL,
    mvt_trade        TEXT    DEFAULT (''),
    mvt_exec         REAL    DEFAULT (0),
    mvt_quantity     INTEGER DEFAULT (0),
    mvt_fee          REAL    DEFAULT (0),
    mvt_output       REAL    DEFAULT (0),
    mvt_input        REAL    DEFAULT (0),
    mvt_money        REAL    DEFAULT (0),
    mvt_quote        REAL    DEFAULT (0),
    mvt_percent      REAL    DEFAULT (0),
    mvt_left         INTEGER DEFAULT (0),
    mvt_gain_day     REAL    DEFAULT (0),
    mvt_gain         REAL    DEFAULT (0),
    mvt_gain_percent REAL    DEFAULT (0),
    mvt_note         TEXT    DEFAULT (''),
    mvt_select       BOOLEAN
);

drop table if exists ACCOUNT;
CREATE TABLE ACCOUNT (
    acc_id       TEXT PRIMARY KEY,
    acc_date     TEXT,
    acc_money    REAL DEFAULT (0),
    acc_latent   REAL DEFAULT (0),
    acc_initial  REAL DEFAULT (0),
    acc_fee      REAL DEFAULT (0),
    acc_gain     REAL DEFAULT (0),
    acc_gain_day REAL DEFAULT (0),
    acc_bet      REAL DEFAULT (0) 
);

drop table if exists RESUME;
CREATE TABLE RESUME (
    resume_date TEXT,
    resume_time TEXT,
    resume_investi REAL,
    resume_gain REAL,
    resume_percent REAL
)
DELETE FROM RESUME
INSERT INTO RESUME (resume_date, resume_time, resume_investi, resume_gain, resume_percent, resume_test) VALUES ('', '', 0, 0, 0)