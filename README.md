# Platinum Mortgage Advisor

System wyszukiwania produktów hipotecznych na podstawie zapytań w języku naturalnym.

## 🆕 NOWOŚĆ: System Dwupromptowy (2-Stage AI)

**NOWA WERSJA 2.0** wprowadza rewolucyjny system dwuetapowej analizy:

1. **ETAP 1: Walidacja WYMOGÓW** - Eliminuje banki niespełniające wymogów klienta (68 parametrów)
2. **ETAP 2: Ranking JAKOŚCI** - Rankuje zakwalifikowane banki według jakości oferty (19 parametrów, 0-100 punktów)

### Główne korzyści
- ✅ **Precyzja** - Rozdziela kwalifikację od optymalizacji
- ✅ **Transparentność** - Jasne powody akceptacji/odrzucenia każdego banku
- ✅ **Audytowalność** - Każda decyzja udokumentowana w JSON/Markdown
- ✅ **Wydajność** - Etap 2 analizuje tylko zakwalifikowane banki (nie wszystkie 11)

### Szybki start

```bash
# Test systemu dwupromptowego
python test_two_stage.py

# Zobacz wynik w:
test_results/two_stage_test_[timestamp].md
```

📖 **Pełna dokumentacja**:
- **[QUICK_START_TWO_STAGE.md](QUICK_START_TWO_STAGE.md)** - Szybki start (3 kroki)
- **[TWO_STAGE_SYSTEM.md](TWO_STAGE_SYSTEM.md)** - Szczegóły techniczne
- **[TWO_STAGE_VISUAL.md](TWO_STAGE_VISUAL.md)** - Wizualizacje i diagramy

---

## Struktura projektu

```
KredytyPlatinum/
├── venv/                          # Środowisko wirtualne
├── data/                          # Dane
│   ├── raw/                       # Surowe dane (Excel)
│   └── processed/                 # Przetworzone dane (JSON)
│       ├── knowledge_base.json              # Baza 11 banków
│       └── parameter_classification_v2.json # WYMÓG vs JAKOŚĆ ⭐ NOWY
├── src/                           # Kod źródłowy
│   ├── __init__.py
│   ├── config.py                  # Konfiguracja (klucze API itp.)
│   ├── data_processor.py          # Przetwarzanie danych
│   ├── ai_client.py               # ⭐ ZAKTUALIZOWANY - 2 prompty AI
│   ├── query_engine.py            # ⭐ ZAKTUALIZOWANY - Dwuetapowe przetwarzanie
│   └── main.py                    # Punkt wejścia aplikacji
├── tests/                         # Testy
│   ├── test_queries.py
│   └── test_customer_matching.py
├── test_two_stage.py              # ⭐ NOWY - Test systemu dwupromptowego
├── requirements.txt               # Zależności
├── .env.example                   # Przykładowa konfiguracja
├── .gitignore
├── README.md
├── QUICK_START_TWO_STAGE.md       # ⭐ NOWY - Quick start dla systemu 2.0
├── TWO_STAGE_SYSTEM.md            # ⭐ NOWY - Dokumentacja techniczna
└── TWO_STAGE_VISUAL.md            # ⭐ NOWY - Wizualizacje
```

## Instalacja

```bash
# Utwórz środowisko wirtualne
python -m venv venv

# Aktywuj środowisko
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Zainstaluj zależności
pip install -r requirements.txt
```

## Konfiguracja

1. Skopiuj `.env.example` do `.env`
2. Uzupełnij klucze API

## Użycie

### NOWOŚĆ: System Dwupromptowy (REKOMENDOWANY)

```bash
# Test nowego systemu
python test_two_stage.py

# Opcje:
python test_two_stage.py --mode full        # Pełna analiza (etap 1 + 2)
python test_two_stage.py --mode validation  # Tylko etap 1 (walidacja)
```

**W kodzie**:
```python
from src.query_engine import QueryEngine

engine = QueryEngine("data/processed/knowledge_base.json")

# NOWY SYSTEM (dwupromptowy) - domyślny
wynik = engine.process_query(profil_klienta)

# STARY SYSTEM (kompatybilność)
wynik = engine.process_query_legacy(profil_klienta)
```

📖 **Instrukcja**: [QUICK_START_TWO_STAGE.md](QUICK_START_TWO_STAGE.md)

---

### 1. Aplikacja Główna - Zapytania Interaktywne

```bash
python src/main.py
```

Menu interaktywne pozwala na:
- Zadawanie pytań w języku naturalnym
- Przeglądanie przykładowych zapytań
- Wyświetlanie listy wszystkich banków

### 2. Testowanie Profili Klientów

```bash
python tests\test_customer_matching.py
```

Opcje testowania:
- **Opcja 1**: Testuj główne kategorie (6 profili) - z pauzami
- **Opcja 2**: Testuj wszystkie profile (20) - **AUTOMATYCZNIE** ⚡
- **Opcja 3**: Testuj wszystkie profile (20) - z pauzami
- **Opcja 4**: Wybierz konkretne profile
- **Opcja 5**: Wyjście

### 3. Generowanie Raportów

Raporty są generowane **automatycznie** po zakończeniu testów:

- **`RAPORT_PELNY.md`** - szczegółowa analiza każdego profilu
- **`RAPORT_PODSUMOWANIE.md`** - tabela wyników i statystyki
- **`matching_results.json`** - surowe dane JSON

Ręczne generowanie:
```bash
python tests\generate_report.py
```

📖 **Więcej informacji:** Zobacz [REPORTING.md](REPORTING.md)

## Przykładowe zapytania

1. finansowanie wkładu własnego dla osoby powyżej 60 lat
2. Finansowanie zakupu udziałów we wspólnocie
3. Kredyt bez wkładu własnego
4. Kredyt dla osoby z małym stażem pracy
5. Kredyt dla osoby z niskim dochodem na osobę w rodzinie
6. Kredyt zabezpieczony inną nieruchomością

## Architektura

### NOWA: Architektura Dwupromptowa (v2.0)

```
PROFIL KLIENTA
      ↓
┌─────────────────────────────────────────┐
│ ETAP 1: WALIDACJA WYMOGÓW               │
│ Prompt 1 + Classification (68 WYMOGÓW) │
│ ✅ Kwalifikuje: 6 banków                │
│ ❌ Odrzucone: 5 banków                  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ ETAP 2: RANKING JAKOŚCI                 │
│ Prompt 2 + Classification (19 JAKOŚCI) │
│ 🏆 #1: Bank A (87/100 pkt)              │
│ 🥈 #2: Bank B (83/100 pkt)              │
│ 🥉 #3: Bank C (79/100 pkt)              │
│ ⚠️ #4: Bank D (65/100 pkt)              │
└──────────────┬──────────────────────────┘
               ↓
        RAPORT DLA KLIENTA
```

📖 **Szczegóły**: [TWO_STAGE_VISUAL.md](TWO_STAGE_VISUAL.md)

### Przepływ danych

1. **Data Processor** - Wczytuje i przetwarza dane z Excel do JSON
2. **AI Client** - Komunikacja z Azure OpenAI
3. **Query Engine** - Przetwarza zapytania użytkownika i zwraca dopasowane produkty
4. **Main** - Interfejs użytkownika (CLI)

### Technologie

- Python 3.13+
- Azure OpenAI API (GPT-4.1)
- Pandas (przetwarzanie danych)
- JSON (format danych)

## 📊 Wyniki Testów

System został przetestowany na **20 profilach klientów** obejmujących różne scenariusze:

| Kategoria | Przykład | Liczba Profili |
|-----------|----------|----------------|
| 👴 Seniorzy | Finansowanie wkładu dla 65+ | 2 |
| 🏘️ Udziały we wspólnocie | Zakup bez księgi wieczystej | 1 |
| 💰 Bez wkładu własnego | LTV 90-100% | 2 |
| 👔 Mały staż pracy | 3-8 miesięcy zatrudnienia | 4 |
| 👨‍👩‍👧‍👦 Niski dochód per capita | Duże rodziny, samotni rodzice | 2 |
| 🏠 Dodatkowe zabezpieczenie | Inna nieruchomość jako zabezpieczenie | 3 |
| 🌍 Specjalne przypadki | Cudzoziemcy, kontrakty, refinansowanie | 6 |

### Najczęściej Rekomendowane Banki

Według wyników testów (20 profili):

1. **Santander** - 17 dopasowań (85%)
2. **PKO BP** - 16 dopasowań (80%)
3. **Alior Bank** - 16 dopasowań (80%)
4. **mBank** - 12 dopasowań (60%)
5. **Millennium** - 11 dopasowań (55%)

📖 **Szczegółowe wyniki:** `data/processed/RAPORT_PELNY.md`

## 📚 Dokumentacja

### System Dwupromptowy (v2.0) ⭐ NOWY
- **[QUICK_START_TWO_STAGE.md](QUICK_START_TWO_STAGE.md)** - Szybki start (3 kroki)
- **[TWO_STAGE_SYSTEM.md](TWO_STAGE_SYSTEM.md)** - Pełna dokumentacja techniczna
- **[TWO_STAGE_VISUAL.md](TWO_STAGE_VISUAL.md)** - Wizualizacje i diagramy

### Dokumentacja ogólna
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architektura systemu
- **[USAGE.md](USAGE.md)** - Szczegółowa instrukcja użytkowania
- **[REPORTING.md](REPORTING.md)** - System raportowania wyników
- **[CUSTOMER_PROFILES.md](CUSTOMER_PROFILES.md)** - Profile testowe klientów
- **[EXAMPLE_QUERIES.md](EXAMPLE_QUERIES.md)** - Przykładowe zapytania

---

## 🆚 Porównanie wersji

| Cecha | v1.0 (Stary) | v2.0 (Nowy - Dwupromptowy) |
|-------|-------------|---------------------------|
| Liczba promptów | 1 | 2 (sekwencyjne) |
| Czas analizy | 15-25s | 10-20s |
| Transparentność | Średnia | ✅ Wysoka (JSON + punktacja) |
| Eliminacja banków | Niejasna | ✅ Jasna (68 wymogów z uzasadnieniem) |
| Ranking | Subiektywny | ✅ Obiektywny (0-100 pkt) |
| Audytowalność | Niska | ✅ Wysoka (każdy krok udokumentowany) |
| Kompatybilność | - | ✅ Zachowana (`process_query_legacy()`) |

**Rekomendacja**: Używaj v2.0 dla wszystkich nowych projektów. v1.0 dostępna dla kompatybilności.
