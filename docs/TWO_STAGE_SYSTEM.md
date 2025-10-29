# System Dwupromptowy - Dokumentacja

## 📋 Spis treści

1. [Architektura systemu](#architektura-systemu)
2. [Etap 1: Walidacja WYMOGÓW](#etap-1-walidacja-wymogów)
3. [Etap 2: Ranking JAKOŚCI](#etap-2-ranking-jakości)
4. [Klasyfikacja parametrów](#klasyfikacja-parametrów)
5. [Użycie](#użycie)
6. [Przykłady](#przykłady)

---

## Architektura systemu

### Koncept

System składa się z **dwóch sekwencyjnych promptów AI**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROFIL KLIENTA (INPUT)                       │
│  - Wiek, dochód, cel kredytu, parametry finansowe              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETAP 1: WALIDACJA WYMOGÓW                          │
│  Prompt 1 + parameter_classification_v2.json (68 WYMOGÓW)      │
│  ───────────────────────────────────────────────────────────    │
│  ✅ Kwalifikuje się: 6 banków                                   │
│  ⚠️ Warunkowo: 2 banki                                          │
│  ❌ Nie kwalifikuje się: 3 banki                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETAP 2: RANKING JAKOŚCI                            │
│  Prompt 2 + parameter_classification_v2.json (19 JAKOŚCI)      │
│  ───────────────────────────────────────────────────────────    │
│  🏆 #1: Bank A (87/100 pkt)                                     │
│  🥈 #2: Bank B (83/100 pkt)                                     │
│  🥉 #3: Bank C (79/100 pkt)                                     │
│  ⚠️ #4: Bank D (65/100 pkt) - najgorsza opcja                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 RAPORT DLA KLIENTA (OUTPUT)                     │
│  - Szczegółowa analiza TOP 4 banków                             │
│  - Tabela porównawcza parametrów                                │
│  - Rekomendacja z uzasadnieniem                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Etap 1: Walidacja WYMOGÓW

### Cel

**Pre-screening** - eliminacja banków, które **NIE SPEŁNIAJĄ** wymogów formalnych klienta.

### Parametry WYMÓG (68 parametrów = 78% bazy)

#### Grupa 02_kredytobiorca (7 WYMOGÓW)
- ✅/❌ **Wiek klienta** - limity wiekowe (np. 18-80 lat)
- ✅/❌ **Maksymalna liczba wnioskodawców** - limit kredytobiorców
- ✅/❌ **Związek nieformalny** - traktowanie jako 1 lub 2 gospodarstwa
- ✅/❌ **Wszyscy właściciele** - wymóg przystąpienia do kredytu
- ✅/❌ **Rozdzielność majątkowa** - ile musi trwać
- ✅/❌ **Cudzoziemiec** - wymagania karty pobytu

#### Grupa 03_źródło dochodu (20 WYMOGÓW)
- ✅/❌ **Umowa o pracę czas określony** - minimalny staż, okres do przodu
- ✅/❌ **Umowa o pracę czas nieokreślony** - minimalny staż
- ✅/❌ **Działalność gospodarcza** - minimalny okres (12-24 mc)
- ✅/❌ **Emerytura/renta** - bezterminowość, okresy
- ✅/❌ **Dochód w obcej walucie** - minimalny staż za granicą
- ✅/❌ **800 plus** - akceptacja jako dochód
- *(i 14 innych typów dochodu)*

#### Grupa 04_cel kredytu (24 WYMOGI)
- ✅/❌ **Zakup mieszkania/domu** - akceptacja
- ✅/❌ **Budowa domu** - akceptacja, limity
- ✅/❌ **Zakup kamienicy** - akceptacja, limity powierzchni
- ✅/❌ **Zakup działki rekreacyjnej** - akceptacja
- ✅/❌ **Refinansowanie wydatków** - maksymalny okres wstecz
- ✅/❌ **Konsolidacja niemieszkaniowa** - max %, marża
- ✅/❌ **Cel dowolny** - max % wartości zabezpieczenia
- *(i 17 innych celów)*

#### Grupa 01_parametry kredytu (4 WYMOGI)
- ✅/❌ **LTV kredyt** - maksymalny procent (70-90%)
- ✅/❌ **Wkład własny** - minimalny procent (10-20%)
- ✅/❌ **Ile kredytów hipotecznych** - limit równoczesnych
- ✅/❌ **Wielkość działki** - maksymalna powierzchnia

#### Grupa 05_zabezpieczenia (2 WYMOGI)
- ✅/❌ **Zabezpieczenie osoby trzeciej** - akceptacja
- ✅/❌ **Działka jako wkład własny** - akceptacja

#### Grupa 08_ważność dokumentów (16 WYMOGÓW)
- ✅/❌ Terminy ważności wszystkich dokumentów

### Logika walidacji

```python
for bank in all_banks:
    spełnione_wymogi = 0
    krytyczne_problemy = []
    
    for wymóg in 68_wymogów:
        if klient_spełnia(wymóg, bank):
            spełnione_wymogi += 1
        else:
            if is_critical(wymóg):
                krytyczne_problemy.append(wymóg)
    
    if len(krytyczne_problemy) == 0:
        status = "KWALIFIKUJE_SIĘ"
    elif len(krytyczne_problemy) <= 2:
        status = "WARUNKOWO"
    else:
        status = "NIE_KWALIFIKUJE_SIĘ"
```

### Wynik etapu 1

**Format JSON**:
```json
{
  "qualified_banks": [
    {
      "bank_name": "Alior Bank",
      "requirements_met": 68,
      "requirements_total": 68,
      "critical_issues": [],
      "validation_details": { /* szczegóły */ }
    }
  ],
  "disqualified_banks": [
    {
      "bank_name": "CITI Handlowy",
      "requirements_met": 63,
      "critical_issues": [
        "❌ WIEK: Bank max 65 lat, klient ma 70 lat",
        "❌ CEL: Bank nie finansuje działek rekreacyjnych"
      ]
    }
  ],
  "validation_summary": {
    "qualified_count": 6,
    "disqualified_count": 3
  }
}
```

---

## Etap 2: Ranking JAKOŚCI

### Cel

**Ranking** - punktacja zakwalifikowanych banków według **JAKOŚCI** oferty (parametry nie-eliminujące).

### Parametry JAKOŚĆ (19 parametrów = 22% bazy)

#### Grupa 01_parametry kredytu (12 JAKOŚCI)
- **Waluta (udzoz)** - PLN, EUR, inne
- **Kwota kredytu** - limity (100k - 30mln)
- **Okres kredytowania** - max (300-420 mc)
- **WIBOR** - stawka referencyjna (1M/3M/6M)
- **Oprocentowanie stałe** - okres (5/10 lat)
- **Wcześniejsza spłata** - opłata (0%/1%/2%/3%)
- **Raty** - równe/malejące/oba
- **Karencja** - okres (0-60 mc)
- **Kredyt EKO** - obniżka marży (0.05-0.2 p.p.)

#### Grupa 06_wycena (2 JAKOŚCI)
- **Rodzaj operatu** - wewnętrzny/zewnętrzny/oba
- **Koszt operatu** - 200-1160 zł

#### Grupa 07_ubezpieczenia (5 JAKOŚCI)
- **Ubezpieczenie pomostowe** - koszt (+0.5%/+1%/brak)
- **Ubezpieczenie niskiego wkładu** - koszt (+0.2%/+0.25%/brak)
- **Ubezpieczenie na życie** - wymagalność, wpływ na marżę
- **Ubezpieczenie od utraty pracy** - dostępność
- **Ubezpieczenie nieruchomości** - dostępność, koszt

### System punktacji (0-100)

#### 1. KOSZT KREDYTU (35 punktów)
| Parametr | Punktacja |
|----------|-----------|
| Wcześniejsza spłata 0% | 10 pkt |
| Wcześniejsza spłata 1% | 7 pkt |
| Wcześniejsza spłata 2% | 4 pkt |
| Wcześniejsza spłata 3% | 0 pkt |
| Ubezp. pomostowe: brak | 8 pkt |
| Ubezp. pomostowe: +0.5% | 5 pkt |
| Ubezp. pomostowe: +1% | 2 pkt |
| Ubezp. niskiego wkładu: brak | 7 pkt |
| Ubezp. niskiego wkładu: +0.2% | 4 pkt |
| Koszt operatu ≤400 zł | 5 pkt |
| Koszt operatu 401-700 zł | 3 pkt |
| Kredyt EKO: obniżka 0.2 p.p. | 5 pkt |
| Kredyt EKO: obniżka 0.1 p.p. | 3 pkt |

#### 2. ELASTYCZNOŚĆ (25 punktów)
| Parametr | Punktacja |
|----------|-----------|
| Kwota kredytu ≥4 mln | 8 pkt |
| Kwota kredytu 3-4 mln | 6 pkt |
| Okres 420 mc | 7 pkt |
| Okres 360 mc | 5 pkt |
| Karencja do 60 mc | 5 pkt |
| Karencja do 24 mc | 3 pkt |
| Raty równe i malejące | 5 pkt |
| Raty tylko równe | 2 pkt |

#### 3. WYGODA PROCESU (20 punktów)
| Parametr | Punktacja |
|----------|-----------|
| Operat wewnętrzny | 10 pkt |
| Operat oba (wewn.+zewn.) | 7 pkt |
| Termin decyzji 90 dni | 5 pkt |
| Termin decyzji 60 dni | 3 pkt |
| Waluty: PLN+EUR+inne | 5 pkt |
| Waluty: PLN+EUR | 3 pkt |

#### 4. DODATKOWE KORZYŚCI (15 punktów)
| Parametr | Punktacja |
|----------|-----------|
| Oprocentowanie stałe 10 lat | 8 pkt |
| Oprocentowanie stałe 5 lat | 5 pkt |
| Ubezp. nieruchomości z bonusem | 4 pkt |
| Ubezp. od utraty pracy | 3 pkt |

#### 5. PARAMETRY MAX (5 punktów)
| Parametr | Punktacja |
|----------|-----------|
| LTV pożyczka 60% | 3 pkt |
| Kwota pożyczki ≥3 mln | 2 pkt |

### Wynik etapu 2

**Format Markdown** z pełną analizą:

```markdown
## 🏆 OFERTA #1: Alior Bank - NAJLEPSZA OPCJA

### 📈 OCENA JAKOŚCI: **87/100 punktów**

#### 💰 KOSZT KREDYTU: 32/35 pkt
- Wcześniejsza spłata: 0% → 10/10 pkt
- Ubezpieczenie pomostowe: brak → 8/8 pkt
- Kredyt EKO: obniżka 0.05 p.p. → 2/5 pkt
...

#### 🔧 ELASTYCZNOŚĆ: 23/25 pkt
...

### ✨ KLUCZOWE ATUTY:
1. Brak opłaty za wcześniejszą spłatę (oszczędność ~10,000 zł)
2. Najdłuższy okres kredytowania (420 mc)
3. Karencja do 60 miesięcy

## 📊 TABELA PORÓWNAWCZA
| Parametr | 🏆 #1 | 🥈 #2 | 🥉 #3 | ⚠️ #4 |
|----------|-------|-------|-------|-------|
| Punkty   | 87    | 83    | 79    | 65    |
...
```

---

## Klasyfikacja parametrów

Źródło: `data/processed/parameter_classification_v2.json`

### Statystyki

```json
{
  "total_parameters_analyzed": 87,
  "WYMÓG_count": 68,
  "JAKOŚĆ_count": 19,
  "percentage": {
    "WYMÓG": "78.2%",
    "JAKOŚĆ": "21.8%"
  }
}
```

### Definicje

**WYMÓG (Requirement)**:
- Parametry decydujące o **KWALIFIKACJI** klienta
- Jeśli nie spełnia → bank **odrzuci wniosek**
- Przykłady: wiek, staż pracy, LTV, cel kredytu

**JAKOŚĆ (Quality)**:
- Parametry określające **WARUNKI OFERTY**
- Klient może otrzymać kredyt, ale parametry wpływają na **atrakcyjność**
- Przykłady: koszt operatu, opłata za wcześniejszą spłatę, karencja

---

## Użycie

### 1. Podstawowy test

```bash
python test_two_stage.py
```

### 2. Test tylko walidacji (etap 1)

```bash
python test_two_stage.py --mode validation
```

### 3. Użycie w kodzie

```python
from src.query_engine import QueryEngine

# Inicjalizacja
engine = QueryEngine("data/processed/knowledge_base.json")

# Profil klienta
customer_profile = """
Klient: 45 lat, umowa o pracę (5 lat stażu)
Cel: Zakup mieszkania
Kwota: 640,000 zł
Wkład: 20%
"""

# Dwuetapowa analiza
result = engine.process_query(customer_profile)
print(result)
```

### 4. Użycie legacy (stary system, jeden prompt)

```python
# Dla kompatybilności wstecznej
result = engine.process_query_legacy(customer_profile)
```

---

## Przykłady

### Przykład 1: Standardowy klient (45 lat, zakup mieszkania)

**Etap 1**: 8 banków zakwalifikowanych
**Etap 2**: 
- 🏆 Alior Bank (87 pkt) - brak opłat, wysoka elastyczność
- 🥈 PKO BP (83 pkt) - duża kwota, długi okres
- 🥉 ING (81 pkt) - kredyt EKO, operat wewnętrzny
- ⚠️ CITI (72 pkt) - wysokie opłaty ubezpieczenia

### Przykład 2: Senior (68 lat, działka rekreacyjna)

**Etap 1**: 1 bank zakwalifikowany (BOŚ)
**Etap 2**: Brak rankingu (tylko 1 bank)

**Wynik**: System informuje, że tylko BOŚ akceptuje ten profil

### Przykład 3: Cudzoziemiec (karta pobytu 6 mc)

**Etap 1**: 
- ✅ Kwalifikują się: Alior, mBank, Pekao (6 mc wystarczy)
- ❌ Nie kwalifikują się: BNP, ING, Millennium (wymagają 12 mc)

**Etap 2**: Ranking 3 banków

---

## Korzyści systemu dwupromptowego

### ✅ Precyzja
- **Etap 1** eliminuje banki metodą deterministyczną (68 wymogów)
- **Etap 2** rankuje tylko realne opcje (19 kryteriów jakości)

### ✅ Przejrzystość
- Klient widzi **dlaczego** bank został odrzucony (konkretny wymóg)
- Klient widzi **dlaczego** bank #1 jest lepszy od #2 (punktacja)

### ✅ Wydajność
- Etap 2 analizuje tylko 3-8 banków (nie wszystkie 11)
- Mniej tokenów AI = szybsze odpowiedzi

### ✅ Audytowalność
- JSON z etapu 1 zawiera pełną dokumentację kwalifikacji
- Każdy punkt w etapie 2 ma uzasadnienie z bazy

### ✅ Skalowalność
- Dodanie nowego banku: aktualizacja knowledge_base.json
- Zmiana wag: edycja scoring w prompt 2
- Bez zmian w kodzie

---

## Pliki systemu

```
KredytyPlatinum/
├── data/
│   └── processed/
│       ├── knowledge_base.json              # Baza 11 banków
│       └── parameter_classification_v2.json # Klasyfikacja WYMÓG/JAKOŚĆ
├── src/
│   ├── ai_client.py           # Logika 2 promptów ⭐ ZAKTUALIZOWANY
│   ├── query_engine.py        # Dwuetapowe przetwarzanie ⭐ ZAKTUALIZOWANY
│   └── data_processor.py      # Ładowanie bazy
├── test_two_stage.py          # Testy systemu ⭐ NOWY
└── TWO_STAGE_SYSTEM.md        # Ta dokumentacja ⭐ NOWY
```

---

## FAQ

**Q: Czy mogę używać starego systemu (jeden prompt)?**  
A: Tak, użyj `engine.process_query_legacy()` - kompatybilność wsteczna zachowana.

**Q: Co jeśli żaden bank się nie kwalifikuje?**  
A: Etap 1 zwróci listę problemów dla każdego banku. Klient zobaczy co musi zmienić.

**Q: Czy mogę zmienić wagi punktacji?**  
A: Tak, edytuj `create_ranking_prompt()` w `ai_client.py` - sekcja "KRYTERIA RANKINGU".

**Q: Jak dodać nowy parametr WYMÓG?**  
A: Zaktualizuj `parameter_classification_v2.json` i `create_validation_prompt()`.

**Q: Czy system działa z Azure OpenAI?**  
A: Tak, wymaga tylko Azure OpenAI API (GPT-4+).

---

**Autor**: Platinum Financial AI Team  
**Data**: 2025-01-27  
**Wersja**: 1.0
