import math
import os
import requests
import sys

def progress_bar(current, total, prefix = "", max_bar_length = 78):
	if current >= total:
		print(f'{prefix}[{"=" * max_bar_length}]')
		return
	percentage = current / total
	bar_length = math.floor(percentage * max_bar_length)
	print(f'{prefix}[{"=" * bar_length}>{" " * (max_bar_length - bar_length - 1)}]', end = "\r")

def print_message(message, end = "\n", length = 80):
	print(f'{message}{" " * (length - len(message))}', end = end)

def check_for_update(file_name, checksum_url):
	# Load checksum
	cached_checksum = None
	if os.path.isfile("sha256"):
		with open("sha256", "rb") as fin:
			cached_checksum = fin.read()

	# Get and compare with the latest checksum to see if an update is available
	checksum = None
	update = False
	response = requests.get(checksum_url)
	if not response.ok:
		return -1, None
	checksum = response.content
	update = cached_checksum != checksum

	return 1 if update else 0, checksum

def download_sqlite(file_name, url, progress_bar_prefix = ""):
	response = requests.get(url, stream=True)
	if not response.ok:
		return -1
	if os.path.isfile(file_name):
		os.remove(file_name)

	# Save to file
	# https://stackoverflow.com/a/16696317
	chunk_size = 1024 * 8
	content_downloaded = 0
	content_length = int(response.headers["Content-Length"])
	progress_bar(content_downloaded, content_length, progress_bar_prefix)
	with open(os.path.join(os.path.abspath("."), file_name), "wb") as fout:
		for chunk in response.iter_content(chunk_size = chunk_size):
			if chunk:
				fout.write(chunk)
				content_downloaded += chunk_size
				progress_bar(content_downloaded, content_length, progress_bar_prefix)
	return 0

def update(file_name, url, checksum_url):
	print_message("Checking for updated sqlite file...", end = "\r")
	result, checksum = check_for_update(file_name, checksum_url)
	if result == -1:
		print_message(f"Failed to get checksum from {checksum_url}.")
		return None
	elif result < 0 or checksum == None:
		print_message("Unknown error while checking for updates.")
		return None
	update = True if result == 1 else False

	if update:
		print_message("Update found!")

		result = download_sqlite(file_name, url, "Downloading... ")
		if result == -1:
			print_message(f"Request to {url} did not return OK. Failed to download {file_name}.")
			return None
		elif result < 0:
			print_message(f"Unknown error while downloading {file_name}.")
			return None
		print_message("Update finished.")
	else:
		print_message("File is up to date.")

	# Save checksum after successful download
	with open("sha256", "wb") as fout:
		fout.write(checksum)
	return update
