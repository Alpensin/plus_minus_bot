import os

from dotenv import load_dotenv

load_dotenv()
telegram_token = os.environ.get("TELEGRAM_TOKEN")

db = "plusminus.db"

tables = {
    "persons": ("name", "tg_user"),
    "marks": ("person_id", "mark", "comment")
}
