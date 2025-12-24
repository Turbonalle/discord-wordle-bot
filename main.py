import os
import discord
from dotenv import load_dotenv
from datetime import date
from parser import parse_wordle_group_message
from stats import get_player_stats
from database import insert_result, init_db, get_connection

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
WORDLE_CHANNEL_ID = int(os.getenv("WORDLE_CHANNEL_ID"))
RANK_EMOJIS = ["🥇", "🥈", "🥉"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

#-----------------------------------------------------------------------------

async def resolve_usernames(client, guild_id, user_ids):
	guild = client.get_guild(guild_id)
	usernames = {}

	for uid in user_ids:
		try:
			member = await guild.fetch_member(int(uid))
			usernames[uid] = member.display_name
		except discord.NotFound:
			usernames[uid] = "Unknown User"
		except discord.Forbidden:
			usernames[uid] = "Permission Error"
		except discord.HTTPException:
			usernames[uid] = "Lookup Failed"
	
	return usernames


async def backfill_history(client):
	channel = client.get_channel(WORDLE_CHANNEL_ID)
	if channel is None:
		print("Wordle channel not found")
		return
	
	async for message in channel.history(limit=500):
		if "Your group is on" not in message.content:
			continue

		results = parse_wordle_group_message(message.content)

		day = message.created_at.date().isoformat()

		for result in results:
			insert_result(
				discord_id=result["discord_id"],
				date=day,
				guesses=result["guesses"]
			)


async def post_daily_stats(channel):
	embed = discord.Embed(
        title="Wordle Leaderboard",
        color=0x000000
    )

	guild_id = channel.guild.id

    # Fetch players
	with get_connection() as conn:
		cur = conn.execute("SELECT DISTINCT discord_id FROM results")
		user_ids = [row[0] for row in cur.fetchall()]
	
	usernames = await resolve_usernames(client, guild_id, user_ids)

	players = []

	for uid in user_ids:
		stats = get_player_stats(uid)
		stats["discord_id"] = uid
		players.append(stats)

    # Sort players
	players.sort(
        key=lambda p: (
            p["average_guesses"] is None,
            p["average_guesses"] or 999
        )
    )

	for index, p in enumerate(players, start=1):
		uid = p["discord_id"]

		rank_emoji = (
            RANK_EMOJIS[index - 1]
            if index <= 3
            else f"#{index}"
        )

		avg = (
            f"{p['average_guesses']:.2f}"
            if p["average_guesses"] is not None
            else "N/A"
        )

		header = f"-----------------------\n{rank_emoji} {usernames[uid]}"

		stats_line = (
            f"🎮 **Played:** {p['games_played']}\n"
            f"💀 **Lost:** {p['games_lost']}\n"
            f"📊 **Avg:** {avg}\n"
        )

		dist = p["distribution"]

		dist_lines = [
			f"🧩 **Guesses:** {dist[1]}, {dist[2]}, {dist[3]}, {dist[4]}, {dist[5]}, {dist[6]}"
		]

		value = stats_line + "\n".join(dist_lines)

		embed.add_field(
            name=header,
            value=value,
            inline=False
        )

	await channel.send(embed=embed)


#-----------------------------------------------------------------------------

@client.event
async def on_ready():
	init_db()
	await backfill_history(client)
	channel = client.get_channel(WORDLE_CHANNEL_ID)
	if channel is None:
		return
	await post_daily_stats(channel)
	

@client.event
async def on_message(message):
	if message.author.bot:
		return
	
	if message.channel.id != WORDLE_CHANNEL_ID:
		return

	if "Your group is on" not in message.content:
		return

	results = parse_wordle_group_message(message.content)
	day = message.created_at.date().isoformat()

	for result in results:
		insert_result(
			discord_id=result["discord_id"],
			date=day,
			guesses=result["guesses"]
		)
	
	await post_daily_stats(message.channel)


client.run(TOKEN)