from database import (
	games_played,
	games_lost,
	average_guesses,
	guess_distribution
)

def normalize_distribution(raw_dist):
	dist = {i: 0 for i in range(1, 7)}
	dist["X"] = 0

	for key, value in raw_dist.items():
		dist[key] = value
	
	return dist

def get_player_stats(discord_id: str) -> dict:
	played = games_played(discord_id)
	lost = games_lost(discord_id)
	avg = average_guesses(discord_id)
	raw_dist = guess_distribution(discord_id)
	dist = normalize_distribution(raw_dist)

	return {
		"games_played": played,
		"games_lost": lost,
		"average_guesses": round(avg, 2) if avg is not None else None,
		"distribution": dist
	}