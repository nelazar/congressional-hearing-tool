from pathlib import Path
from datetime import datetime

# Setup constants
DATA_PATH = Path("./data/")
DOTENV_PATH = DATA_PATH / Path(".env")
DB_PATH = DATA_PATH / Path("cht.db")
OUTPUT_PATH = Path("./output/")

KEY_VAR = 'GOVINFO_KEY'

CURR_CONGRESS = (datetime.today().year - 1789) // 2 + 1