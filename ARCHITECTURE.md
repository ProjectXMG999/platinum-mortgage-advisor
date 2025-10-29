# Dokumentacja Techniczna - Platinum Mortgage Advisor

## Architektura Systemu

### Przegląd

System składa się z 4 głównych komponentów:

```
┌─────────────────┐
│   main.py       │  ← Interfejs użytkownika (CLI)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ query_engine.py │  ← Logika biznesowa
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────────┐  ┌──────────┐
│data_     │  │ai_       │
│processor │  │client    │
└──────────┘  └──────────┘
     │             │
     ▼             ▼
┌──────────┐  ┌──────────┐
│JSON DB   │  │Azure     │
│          │  │OpenAI    │
└──────────┘  └──────────┘
```

### Moduły

#### 1. config.py
**Przeznaczenie**: Centralna konfiguracja aplikacji

**Zawiera**:
- Klucze API Azure OpenAI (zahardkodowane zgodnie z wymaganiami)
- Ścieżki do plików
- Parametry modelu AI (temperatura, max tokens)

**Przykład użycia**:
```python
from config import AZURE_OPENAI_API_KEY, KNOWLEDGE_BASE_PATH
```

#### 2. data_processor.py
**Przeznaczenie**: Zarządzanie bazą wiedzy

**Klasa**: `DataProcessor`

**Metody**:
- `load_knowledge_base()` - Wczytuje JSON z bazą wiedzy
- `get_all_banks()` - Zwraca listę banków
- `get_bank_data(bank_name)` - Dane konkretnego banku
- `format_for_context()` - Formatuje dane dla AI (markdown)
- `format_compact_for_context()` - Formatuje dane dla AI (JSON)

**Przykład użycia**:
```python
processor = DataProcessor("data/processed/knowledge_base.json")
banks = processor.get_all_banks()
context = processor.format_compact_for_context()
```

#### 3. ai_client.py
**Przeznaczenie**: Komunikacja z Azure OpenAI

**Klasa**: `AIClient`

**Metody**:
- `create_chat_completion(messages)` - Podstawowa komunikacja z API
- `query_with_context(user_query, knowledge_base_context)` - Zapytanie z kontekstem bazy wiedzy

**System Prompt**:
Zawiera instrukcje dla AI:
- Rola: Ekspert ds. produktów hipotecznych
- Zadanie: Analiza zapytań i rekomendacja produktów
- Format odpowiedzi: Strukturyzowany z uzasadnieniem

**Przykład użycia**:
```python
client = AIClient()
response = client.query_with_context(
    user_query="Kredyt bez wkładu własnego",
    knowledge_base_context=json_data
)
```

#### 4. query_engine.py
**Przeznaczenie**: Koordynacja przepływu danych

**Klasa**: `QueryEngine`

**Metody**:
- `process_query(user_query)` - Główna metoda przetwarzania zapytań
- `get_available_banks()` - Lista dostępnych banków
- `get_bank_info(bank_name)` - Informacje o banku

**Przepływ**:
1. Otrzymuje zapytanie użytkownika
2. Pobiera kontekst z `DataProcessor`
3. Wysyła do `AIClient`
4. Zwraca odpowiedź

**Przykład użycia**:
```python
engine = QueryEngine("data/processed/knowledge_base.json")
response = engine.process_query("Kredyt dla osoby z małym stażem pracy")
```

#### 5. main.py
**Przeznaczenie**: Interfejs użytkownika

**Funkcje**:
- `print_header()` - Nagłówek aplikacji
- `print_menu()` - Menu opcji
- `show_example_queries()` - Przykładowe zapytania
- `run_interactive_mode(engine)` - Tryb interaktywny
- `main()` - Punkt wejścia

**Opcje menu**:
1. Zadaj zapytanie - wprowadzenie własnego zapytania
2. Zobacz przykładowe zapytania - lista 6 przykładów
3. Lista dostępnych banków - wyświetla 11 banków
4. Wyjście - zakończenie programu

## Format Danych

### Struktura JSON (knowledge_base.json)

```json
{
  "metadata": {
    "source": "...",
    "date_updated": "2025-04-01",
    "description": "..."
  },
  "banks": ["Alior Bank", "BNP Paribas", ...],
  "products": [
    {
      "bank_name": "Alior Bank",
      "parameters": {
        "01_parametry kredytu": {
          "udzoz": "PLN, EUR (tylko cel mieszkaniowy)",
          "02_kwota kredytu": "100 000 - 3 000 000 zł",
          ...
        },
        "02_wiek": {
          ...
        },
        ...
      }
    },
    ...
  ]
}
```

### Grupy Parametrów

Baza wiedzy zawiera następujące grupy (93 parametry):
- `01_parametry kredytu` - Kwoty, okresy, LTV, wkład własny
- `02_wiek` - Wymagania wiekowe
- `03_staż pracy` - Wymagania dotyczące zatrudnienia
- `04_wymagany dochód` - Minimalne dochody
- `05_cel kredytu` - Dopuszczalne cele kredytowania
- `06_zabezpieczenia` - Typy zabezpieczeń
- ...i więcej

## Przepływ Przetwarzania Zapytania

### Krok 1: Inicjalizacja
```
main.py → QueryEngine → DataProcessor + AIClient
```

### Krok 2: Wczytanie Danych
```
DataProcessor → knowledge_base.json → Pamięć
```

### Krok 3: Zapytanie Użytkownika
```
Użytkownik → main.py → QueryEngine.process_query()
```

### Krok 4: Przygotowanie Kontekstu
```
QueryEngine → DataProcessor.format_compact_for_context()
→ Pełna baza wiedzy w JSON (wszystkie 11 banków)
```

### Krok 5: Zapytanie AI
```
QueryEngine → AIClient.query_with_context()
→ System Prompt + Baza Wiedzy + Zapytanie
→ Azure OpenAI API
```

### Krok 6: Odpowiedź
```
Azure OpenAI → AIClient → QueryEngine → main.py → Użytkownik
```

## Przykładowe Zapytania i Oczekiwane Wyniki

### 1. "finansowanie wkładu własnego dla osoby powyżej 60 lat"

**Analiza**:
- Parametr: wiek > 60 lat
- Parametr: finansowanie wkładu własnego

**Oczekiwany wynik**: Banki akceptujące kredytobiorców 60+ i oferujące finansowanie wkładu

### 2. "Kredyt bez wkładu własnego"

**Analiza**:
- Parametr: LTV = 100% lub wkład własny = 0%

**Oczekiwany wynik**: Banki z LTV 90%+ lub specjalne programy

### 3. "Kredyt dla osoby z małym stażem pracy"

**Analiza**:
- Parametr: minimalny staż pracy

**Oczekiwany wynik**: Banki z najniższymi wymaganiami stażowymi

## Konfiguracja Azure OpenAI

### Parametry zahardkodowane w config.py:

```python
AZURE_OPENAI_API_KEY = "GAbqj97MHveLyKaLpDeDhsuJpMG9nRi5iqnsgFYVZgzPH19gpjsAJQQJ99BFACfhMk5XJ3w3AAABACOGIGov"
AZURE_OPENAI_ENDPOINT = "https://stormwhirlpool.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
```

### Parametry modelu:

```python
TEMPERATURE = 0.3  # Niska dla spójności
MAX_TOKENS = 4000  # Wystarczające dla szczegółowych odpowiedzi
```

## Testowanie

### Uruchomienie testów:

```bash
python tests/test_queries.py
```

### Testy obejmują:
- 6 predefiniowanych zapytań
- Sprawdzenie poprawności odpowiedzi
- Raportowanie błędów

## Obsługa Błędów

### Typy błędów:

1. **FileNotFoundError** - Brak pliku bazy wiedzy
2. **JSONDecodeError** - Uszkodzony plik JSON
3. **APIError** - Błąd Azure OpenAI
4. **KeyboardInterrupt** - Przerwanie przez użytkownika

### Strategia:
- Wszystkie błędy są wychwytywane i raportowane
- System wyświetla przyjazne komunikaty
- W razie potrzeby pokazuje stack trace

## Rozszerzalność

### Jak dodać nowy bank:
1. Zaktualizuj plik Excel
2. Uruchom `data/raw/convert_to_json.py`
3. System automatycznie załaduje nowe dane

### Jak zmienić model AI:
1. Zmodyfikuj `AZURE_OPENAI_DEPLOYMENT_NAME` w `config.py`
2. Dostosuj `TEMPERATURE` i `MAX_TOKENS` jeśli potrzeba

### Jak dodać nową funkcję:
1. Rozszerz odpowiedni moduł
2. Zaktualizuj menu w `main.py`
3. Dodaj testy w `tests/`

## Wymagania Systemowe

- Python 3.13+
- Windows (PowerShell 5.1+)
- Połączenie internetowe (Azure OpenAI)
- ~50 MB wolnego miejsca

## Performance

- **Czas inicjalizacji**: ~2-3 sekundy
- **Czas odpowiedzi**: ~5-15 sekund (zależnie od Azure)
- **Użycie pamięci**: ~100-200 MB
- **Rozmiar bazy wiedzy**: ~150 KB JSON
