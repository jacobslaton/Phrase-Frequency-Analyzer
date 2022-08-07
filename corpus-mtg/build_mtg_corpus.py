import json
import nltk
import sqlite3

stemmer = nltk.stem.snowball.SnowballStemmer("english")

def dumpDdl(cursor):
	tables = cursor.execute("SELECT * FROM sqlite_master WHERE type='table';").fetchall()
	with open("mtg-ddl.sql", "w") as fout:
		for table in tables:
			if table[1] != "sqlite_sequence":
				fout.write(table[4].replace("\\n", "\n").replace("\\t", "\t") + ";\n")

# Splits a phrase into tokens. It also combines symbols with their brackets and discards reminder text.
def tokenize(input):
	nlTokens = nltk.word_tokenize(input)
	tokens = []
	parenToken = ""
	squareBracketToken = ""
	curlyBracketToken = ""
	for token in nlTokens:
		if token == ")":
			parenToken = ""
		elif token == "(" or parenToken != "":
			parenToken += token
		elif token == "]":
			squareBracketToken += token
			tokens.append(squareBracketToken)
			squareBracketToken = ""
		elif token == "[" or squareBracketToken != "":
			squareBracketToken += token
		elif token == "}":
			curlyBracketToken += token
			tokens.append(curlyBracketToken)
			curlyBracketToken = ""
		elif token == "{" or curlyBracketToken != "":
			curlyBracketToken += token
		else:
			tokens.append(token)
	return tokens

def build_corpus(cursor):
	set_blacklist = [
		"HBG",  # Alchemy Horizons: Baldur's Gate
		"PUNH", # Unhinged Promos
		"PUST", # Unstable Promos
		"SLD",  # Secret Lair Drop
		"SLU",  # Secret Lair: Ultimate Edition
		"SUNF", # Unfinity Sticker Sheets
		"UGL",  # Unglued
		"UND",  # Unsanctioned
		"UNF",  # Unfinity
		"UNH",  # Unhinged
		"UST",  # Unstable
		"YMID", # Alchemy: Innistrad
		"YNEO", # Alchemy: Kamigawa
		"YSNC", # Alchemy: New Capenna
	]
	sql_set_blacklist = "(" + ", ".join([f"'{set_code}'" for set_code in set_blacklist]) + ")"

	# Get the ID for the latest printing of each desired card
	results = cursor.execute(f"select id, setCode, printings from cards where not setCode in {sql_set_blacklist} and not text is null and printings != '';").fetchall()
	card_ids = []
	for row in results:
		card = {
			"id": row[0],
			"setCode": row[1],
			"printings": row[2],
		}
		printings = [set_code for set_code in card["printings"].split(",") if not set_code in set_blacklist]
		latest_set_code = printings[-1]
		if card["setCode"] == latest_set_code:
			card_ids.append(card["id"])

	# Use the IDs to build the corpus
	sql_card_ids = "(" + ", ".join([f"'{id}'" for id in card_ids]) + ")"
	results = cursor.execute(f"select name, text from cards where id in {sql_card_ids};").fetchall()
	corpus = []
	for row in results:
		card = {
			"name": row[0],
			"text": row[1],
		}
		# Replace the card name whenever it appears in the text
		sni = card["name"].find(",") if "," in card["name"] else len(card["name"])
		shortname = card["name"][:sni]
		augmented_text = card["text"].replace(card["name"], "{name}").replace(shortname, "{shortname}")
		tokens = tokenize(augmented_text)
		if len(tokens) > 0: # Exclude cards that only have reminder text, yielding no tokens
			corpus.append(tokens)

	# Save corpus to file
	with open("mtg-corpus.json", "w") as fout:
		fout.write(json.dumps(corpus))

def main():
	db = sqlite3.connect("AllPrintings.sqlite")
	cursor = db.cursor()

	build_corpus(cursor)

	db.close()

if __name__ == "__main__":
	main()
