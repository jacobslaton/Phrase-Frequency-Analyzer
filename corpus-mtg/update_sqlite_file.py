import gzip
import os
import shutil
import sys

ROOT = os.path.abspath("..")
sys.path.insert(0, ROOT)

import file_updater

file_name = "AllPrintings.sqlite.gz"
url = f"https://mtgjson.com/api/v5/{file_name}"
checksum_url = url + ".sha256"

update = file_updater.update(file_name, url, checksum_url)
if update == None:
	sys.exit(-1)
elif update == True:
	gz_file_name = file_name[:file_name.rfind(".")]
	if os.path.isfile(gz_file_name):
		os.remove(gz_file_name)
	# Unzip gz file
	# https://stackoverflow.com/a/44712152
	file_updater.print_message(f"Unzipping {gz_file_name}...", end = "\r")
	with gzip.open(file_name, "rb") as fin:
		with open(gz_file_name, "wb") as fout:
			shutil.copyfileobj(fin, fout)
	file_updater.print_message(f"{gz_file_name} unzipped.")
