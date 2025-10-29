"""
Konfiguracja aplikacji - klucze API i ustawienia
"""
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = "GAbqj97MHveLyKaLpDeDhsuJpMG9nRi5iqnsgFYVZgzPH19gpjsAJQQJ99BFACfhMk5XJ3w3AAABACOGIGov"
AZURE_OPENAI_ENDPOINT = "https://stormwhirlpool.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT_NAME = "o4-mini"  # Zmiana na o4-mini (szybszy niż gpt-4.1)

# Ścieżki do plików
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
KNOWLEDGE_BASE_PATH = os.path.join(DATA_DIR, "processed", "knowledge_base.json")

# Ustawienia aplikacji
MAX_TOKENS = 8000  # Zwiększone dla 4 ofert z pełną weryfikacją
TEMPERATURE = 0.3  # Niższa temperatura dla bardziej deterministycznych odpowiedzi
