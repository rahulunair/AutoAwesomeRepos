import toml

config = toml.load("awesome.toml")

PROGRESS_FILE = config["PROGRESS_FILE"]
NUM_STARS = config["NUM_STARS"]
DAYS_AGO = config["DAYS_AGO"]
README_KEYWORDS = config["README_KEYWORDS"]
