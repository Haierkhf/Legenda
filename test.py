from dotenv import load_dotenv
import os

load_dotenv()

print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
print("CRYPTOBOT_API_KEY:", os.getenv("CRYPTOBOT_API_KEY"))
print("PROFILE_TOKEN:", os.getenv("PROFILE_TOKEN"))
