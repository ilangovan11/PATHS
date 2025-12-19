import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME = os.getenv("APP_NAME", "PATHS API")
    APP_VERSION = os.getenv("APP_VERSION", "0.0.1")
    ENV = os.getenv("ENV", "development")

settings = Settings()