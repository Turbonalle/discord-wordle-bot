import re
from typing import List, Dict

RESULT_RE = re.compile(r"(\d|X)/6:")
MENTION_RE = re.compile(r"<@!?(\d+)>")

def parse_wordle_group_message(content: str) -> List[Dict]:
	results = []

	for line in content.splitlines():
		line = line.strip()

		if not RESULT_RE.search(line):
			continue

		guess_match = RESULT_RE.search(line)
		guess_raw = guess_match.group(1)

		guesses = None if guess_raw =="X" else int(guess_raw)

		user_ids = MENTION_RE.findall(line)

		for uid in user_ids:
			results.append({
				"discord_id": uid,
				"guesses": guesses
			})
		
	return results