/*
    Table SQLITE
*/
drop table if exists PTF;
CREATE TABLE PTF (
    "ptf_id" TEXT PRIMARY KEY NOT NULL,
    "ptf_name" TEXT,
    "ptf_account" TEXT,
    "ptf_date" TEXT,
    "ptf_quote" REAL DEFAULT(0),
    "ptf_percent" REAL DEFAULT(0),
    "ptf_rsi" REAL DEFAULT(0),
    "ptf_macd" REAL DEFAULT(0),
    "ptf_e200" REAL DEFAULT(0),
    "ptf_quantity" INTEGER DEFAULT(0),
    "ptf_cost" REAL DEFAULT(0),
    "ptf_gainj" REAL DEFAULT(0),
    "ptf_gain" REAL DEFAULT(0),
    "ptf_gain_percent" REAL DEFAULT(0),
    "ptf_resistance" TEXT,
    "ptf_support" TEXT,
    "ptf_note" TEXT
    "ptf_intest" TEXT,
    "ptf_test_date" TEXT,
    "ptf_test_cost" REAL,
    "ptf_test_quantity" INTEGER,
    "ptf_test_gain" REAL,
    "ptf_test_gain_percent" REAL
    "ptf_test_nbj" REAL
    "ptf_test_cumul" REAL
)
CREATE UNIQUE INDEX PTF_INDEX ON PTF (ptf_id)

drop table if exists COURS;
CREATE TABLE COURS (
    "cours_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "cours_ptf_id" TEXT NOT NULL,
    "cours_name" TEXT,
    "cours_date" TEXT,
    "cours_close" REAL,
    "cours_open" REAL,
    "cours_low" REAL,
    "cours_high" REAL,
    "cours_percent" REAL,
    "cours_volume" REAL,
    "cours_rsi" REAL,
    "cours_ema12" REAL,
    "cours_ema26" REAL,
    "cours_ema50" REAL,
    "cours_macd" REAL,
    "cours_trend" REAL,
    "cours_trade" TEXT,
    "cours_quantity" REAL,
    "cours_cost" REAL,
    "cours_nbj" REAL,
    "cours_gainj" REAL,
    "cours_gain" REAL,
    "cours_gain_percent" REAL
)

drop table if exists MVT;
CREATE TABLE MVT (
    mvt_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    mvt_ptf_id       TEXT    NOT NULL,
    ptf_account      TEXT,
    mvt_date         TEXT    NOT NULL,
    mvt_name         TEXT,
    mvt_trade        TEXT,
    mvt_quote        REAL,
    mvt_cost         REAL,
    mvt_quantity     REAL,
    mvt_charges      REAL,
    mvt_gain         REAL,
    mvt_gain_percent REAL,
    mvt_note         TEXT
)

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