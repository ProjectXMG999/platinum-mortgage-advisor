"""
Konfiguracja aplikacji - klucze API i ustawienia
"""
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env (lokalnie)
load_dotenv()

# Sprawdź czy działa w Streamlit Cloud (st.secrets) czy lokalnie (.env)
try:
    import streamlit as st
    # Streamlit Cloud - użyj st.secrets
    AZURE_OPENAI_API_KEY = st.secrets.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = st.secrets.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = st.secrets.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = st.secrets.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
except (ImportError, FileNotFoundError):
    # Lokalne środowisko - użyj .env
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1")

# Walidacja wymaganych zmiennych środowiskowych
if not AZURE_OPENAI_API_KEY:
    raise ValueError(
        "❌ AZURE_OPENAI_API_KEY nie jest ustawiony!\n"
        "   Sprawdź plik .env (skopiuj z .env.example i uzupełnij)"
    )
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError(
        "❌ AZURE_OPENAI_ENDPOINT nie jest ustawiony!\n"
        "   Sprawdź plik .env (skopiuj z .env.example i uzupełnij)"
    )

# Ścieżki do plików
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
KNOWLEDGE_BASE_PATH = os.path.join(DATA_DIR, "processed", "knowledge_base.json")

# Ustawienia aplikacji
MAX_TOKENS = 8000  # Zwiększone dla 4 ofert z pełną weryfikacją
TEMPERATURE = 0.3  # Niższa temperatura dla bardziej deterministycznych odpowiedzi
