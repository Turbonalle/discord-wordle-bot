import sqlite3
from typing import Dict, Optional

DB_PATH = "wordle.db"

def get_connection():
	return sqlite3.connect(DB_PATH)

def init_db():
	with get_connection() as conn:
		conn.execute("""
			CREATE TABLE IF NOT EXISTS results (
			   discord_id TEXT NOT NULL,
			   date TEXT NOT NULL,
			   guesses INTEGER,
			   PRIMARY KEY (discord_id, date)
			)
			""")

def insert_result(discord_id: str, date: str, guesses: Optional[int]):
	with get_connection() as conn:
		conn.execute("""
			   INSERT OR IGNORE INTO results (discord_id, date, guesses)
			   VALUES (?, ?, ?)
			   """, (discord_id, date, guesses))


#-- Query Functions ----------------------------------------------------------

def games_played(discord_id: str) -> int:
	with get_connection() as conn:
		cur = conn.execute(
			"SELECT COUNT(*) FROM results WHERE discord_id = ?",
			(discord_id,)
		)
		return cur.fetchone()[0]

def games_lost(discord_id: str) -> int:
	with get_connection()as conn:
		cur = conn.execute(
			"SELECT COUNT(*) FROM results WHERE discord_id = ? AND guesses IS NULL",
			(discord_id,)
		)
		return cur.fetchone()[0]

def average_guesses(discord_id: str) -> Optional[float]:
	with get_connection()as conn:
		cur = conn.execute(
			"SELECT AVG(guesses) FROM results WHERE discord_id = ? AND guesses IS NOT NULL",
			(discord_id,)
		)
		return cur.fetchone()[0]

def guess_distribution(discord_id: str) -> Dict[int, int]:
	with get_connection() as conn:
		cur = conn.execute(
			"""
			SELECT guesses, COUNT(*)
			FROM results
			WHERE discord_id = ? AND guesses IS NOT NULL
			GROUP BY guesses
			""",
			(discord_id,)
		)
		return {row[0]: row[1] for row in cur.fetchall()}