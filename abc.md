# ABC Technique

## Installation du Virtualenv
```shell
virtualenv --python=/usr/bin/python3.6 venv
source venv/bin/activate

sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
pip3 install pycairo
pip3 install PyGObject
pip3 install matplotlib
pip3 install requests
pip3 install schedule
```
### Pour VSCodium
- Installer l'extension ```ms-python.python```
- Installer pylint pour python ```pip3 install pylint```

## SQL
- Utilisation de DB Browser for SQLite http://sqlitebrowser.org/
- Création des tables SQLite

```sql
CREATE TABLE ACCOUNT (acc_id TEXT PRIMARY KEY, acc_date TEXT, acc_money REAL DEFAULT (0), acc_latent REAL DEFAULT (0), acc_initial REAL DEFAULT (0), acc_fee REAL DEFAULT (0), acc_gain REAL DEFAULT (0), acc_gain_day REAL DEFAULT (0), acc_bet REAL DEFAULT (0), acc_percent REAL DEFAULT (0))

CREATE TABLE COURS (cours_id INTEGER PRIMARY KEY AUTOINCREMENT, cours_ptf_id TEXT NOT NULL, cours_name TEXT, cours_date TEXT, cours_close REAL, cours_open REAL, cours_low REAL, cours_high REAL, cours_percent REAL, cours_volume REAL, cours_volp REAL, cours_rsi REAL, cours_ema12 REAL, cours_ema26 REAL, cours_ema50 REAL, cours_q12 INTEGER, cours_q26 INTEGER, cours_q50 INTEGER, cours_max12 REAL, cours_max26 REAL, cours_max50 REAL, cours_min12 REAL, cours_min26 REAL, cours_min50 REAL, cours_trend12 REAL, cours_trend26 REAL, cours_trend50 REAL, cours_trade TEXT, cours_quantity REAL, cours_cost REAL, cours_nbj REAL, cours_gainj REAL, cours_gain REAL, cours_gainp REAL, cours_inptf INTEGER, cours_intest INTEGER)

CREATE TABLE COURS_VOL (ptf_id TEXT, vol_moy REAL, vol_max INTEGER)

CREATE TABLE MVT (mvt_id INTEGER PRIMARY KEY AUTOINCREMENT, mvt_ptf_id TEXT NOT NULL, mvt_account TEXT DEFAULT (''), mvt_date TEXT NOT NULL, mvt_trade TEXT DEFAULT (''), mvt_exec REAL DEFAULT (0), mvt_quantity INTEGER DEFAULT (0), mvt_fee REAL DEFAULT (0), mvt_output REAL DEFAULT (0), mvt_input REAL DEFAULT (0), mvt_money REAL DEFAULT (0), mvt_quote REAL DEFAULT (0), mvt_percent REAL DEFAULT (0), mvt_left INTEGER DEFAULT (0), mvt_gain_day REAL DEFAULT (0), mvt_gain REAL DEFAULT (0), mvt_gain_percent REAL DEFAULT (0), mvt_note TEXT DEFAULT (''), mvt_select BOOLEAN)

CREATE TABLE "cac40" ( "isin" TEXT, "name" TEXT, "code" TEXT )

CREATE TABLE pea (Date, Opération, Type, Qté, Code, "Code ISIN", Libellé, "", Montant, "Frais TTC", Devise, "Date Opé")

CREATE TABLE ptf (ptf_id TEXT NOT NULL PRIMARY KEY, ptf_name TEXT, ptf_disabled INTEGER, ptf_cac40 INTEGER, ptf_account TEXT, ptf_quote REAL DEFAULT (0), ptf_percent REAL, ptf_gainj REAL, ptf_rsi REAL DEFAULT (0), ptf_q12 INTEGER, ptf_q26 INTEGER, ptf_q50 INTEGER, ptf_trend50 REAL, ptf_volp REAL, ptf_vol_moy REAL, ptf_vol_max INTEGER, ptf_trade TEXT, ptf_date TEXT, ptf_cost REAL DEFAULT (0), ptf_quantity INTEGER DEFAULT (0), ptf_gain REAL DEFAULT (0), ptf_gainp REAL DEFAULT (0), ptf_nbj INTEGER, ptf_note TEXT)

CREATE TABLE ORDRES ( ordre_ptf_id TEXT, ordre_date TEXT, ordre_type TEXT, -- aaa ou vvv ordre_quote REAL, ordre_cost REAL, ordre_quantity REAL, ordre_gain REAL, ordre_gain_percent REAL )

CREATE TABLE "quotes" ( "id" TEXT, "name" TEXT, "date" TEXT, "open" REAL, "high" REAL, "low" REAL, "close" REAL, "adjclose" REAL, "volume" INTEGER )

CREATE TABLE resume (resume_date TEXT, resume_time TEXT, resume_investi REAL, resume_gainj REAL, resume_gain REAL, resume_percent REAL, resume_simul TEXT)

CREATE TABLE "sbf" ( "isin" TEXT, "name" TEXT, "code" TEXT )
CREATE UNIQUE INDEX PTF_INDEX ON ptf (ptf_id)

-- Cours du jour 
CREATE TABLE `cdays` (
	`cdays_id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`cdays_ptf_id`	TEXT NOT NULL,
	`cdays_name`	TEXT,
	`cdays_date`	TEXT,
	`cdays_close`	REAL,
	`cdays_open`	REAL,
	`cdays_volume`	REAL,
	`cdays_low`	REAL,
	`cdays_high`	REAL,
	`cdays_time`	TEXT,
	`cdays_percent`	REAL,
	`cdays_min`	REAL,
	`cdays_max`	REAL,
	`cdays_ema`	REAL,
	`cdays_sma`	REAL,
	`cdays_inptf`	INTEGER,
	`cdays_quantity`	REAL,
	`cdays_cost`	REAL,
	`cdays_gain`	REAL,
	`cdays_gainp`	REAL
);

```

## Démarche

## Dessins
https://drive.google.com/open?id=1v-FKCZdRNJAXW89Xy-yA2kBaMQPxnXQT

