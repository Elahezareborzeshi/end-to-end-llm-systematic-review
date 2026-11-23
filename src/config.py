import os
from dotenv import load_dotenv

# Load environment variables from .env file (never commit real secrets)
load_dotenv()

class Config:
    PUBMED_API_KEY = os.getenv('PUBMED_API_KEY')
    PUBMED_EMAIL = os.getenv('PUBMED_EMAIL', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # Optional local paths for validation / comparison features
    ENDNOTE_FILE_PATH = os.getenv('ENDNOTE_FILE_PATH', '')
    MANUAL_QUERY_PATH = os.getenv('MANUAL_QUERY_PATH', '')

    @classmethod
    def get(cls, key, default=None):
        return getattr(cls, key, default)

config = Config()

