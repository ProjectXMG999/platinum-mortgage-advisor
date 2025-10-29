# 🚀 Quick Start - System Dwupromptowy

## Czym jest system dwupromptowy?

System analizuje profile klientów w **dwóch etapach**:

1. **ETAP 1: Walidacja WYMOGÓW** - Eliminuje banki, które nie spełniają wymogów klienta (68 parametrów WYMÓG)
2. **ETAP 2: Ranking JAKOŚCI** - Rankuje zakwalifikowane banki według jakości oferty (19 parametrów JAKOŚĆ, 0-100 punktów)

---

## ⚡ Szybki start (3 kroki)

### 1. Uruchom test

```powershell
python test_two_stage.py
```

To uruchomi pełną analizę dla przykładowego klienta (45 lat, zakup mieszkania).

### 2. Zobacz wynik

System wygeneruje plik w folderze `test_results/`:
```
test_results/two_stage_test_20250127_143022.md
```

Otwórz go aby zobaczyć:
- ✅ Listę zakwalifikowanych banków (z uzasadnieniem)
- ❌ Listę odrzuconych banków (z powodami)
- 🏆 TOP 4 ranking z oceną 0-100 punktów
- 📊 Tabelę porównawczą parametrów

### 3. Użyj w swoim kodzie

```python
from src.query_engine import QueryEngine

# Inicjalizuj system
engine = QueryEngine("data/processed/knowledge_base.json")

# Profil klienta
profil = """
Klient: Jan Kowalski, 45 lat
Umowa o pracę: 5 lat stażu
Cel: Zakup mieszkania
Kwota: 640,000 zł
Wkład własny: 20%
"""

# Analiza dwuetapowa
wynik = engine.process_query(profil)
print(wynik)
```

---

## 📁 Kluczowe pliki

| Plik | Opis |
|------|------|
| `src/ai_client.py` | ⭐ Prompty dla etapu 1 i 2 |
| `src/query_engine.py` | ⭐ Orchestracja dwóch etapów |
| `data/processed/parameter_classification_v2.json` | Klasyfikacja WYMÓG vs JAKOŚĆ |
| `test_two_stage.py` | Skrypt testowy |
| `TWO_STAGE_SYSTEM.md` | Pełna dokumentacja techniczna |
| `TWO_STAGE_VISUAL.md` | Wizualizacje i diagramy |

---

## 🎯 Przykłady użycia

### Test 1: Standardowy klient

```powershell
python test_two_stage.py
```

**Rezultat**:
- Etap 1: 8 banków zakwalifikowanych
- Etap 2: TOP 4 (Alior, PKO, ING, Santander)

### Test 2: Tylko walidacja (bez rankingu)

```powershell
python test_two_stage.py --mode validation
```

**Rezultat**:
- JSON z listą zakwalifikowanych i odrzuconych banków
- Szczegółowe powody dyskwalifikacji

### Test 3: Niestandardowy profil (w kodzie)

```python
profil_senior = """
Klient: 68 lat, emeryt
Cel: Zakup działki rekreacyjnej
Kwota: 100,000 zł
"""

wynik = engine.process_query(profil_senior)
```

**Rezultat**:
- Etap 1: Tylko BOŚ Bank zakwalifikowany (jedyny finansujący działki rekreacyjne)
- Etap 2: Pominięty (tylko 1 bank)
- Rekomendacja: BOŚ Bank (jedyna opcja)

---

## 🔧 Konfiguracja

### Zmiana wag punktacji (Etap 2)

Edytuj `src/ai_client.py`, metoda `create_ranking_prompt()`:

```python
**1. KOSZT KREDYTU (35 punktów)**  # ← Zmień wagę tutaj
   - Opłata za wcześniejszą spłatę (0-10 pkt): 0% = 10 pkt, 1% = 7 pkt, ...
```

### Dodanie nowego parametru WYMÓG

1. Edytuj `data/processed/parameter_classification_v2.json`
2. Dodaj parametr do odpowiedniej grupy z `"type": "WYMÓG"`
3. Zaktualizuj `create_validation_prompt()` w `ai_client.py`

### Dodanie nowego parametru JAKOŚĆ

1. Edytuj `parameter_classification_v2.json` → `"type": "JAKOŚĆ"`
2. Zaktualizuj punktację w `create_ranking_prompt()`

---

## 📊 Jak czytać wyniki

### Etap 1: Walidacja (JSON)

```json
{
  "qualified_banks": [
    {
      "bank_name": "Alior Bank",
      "requirements_met": 68,      // ← Spełnia wszystkie wymogi
      "critical_issues": []         // ← Brak problemów
    }
  ],
  "disqualified_banks": [
    {
      "bank_name": "VELO BANK",
      "requirements_met": 65,       // ← 3 wymogi niespełnione
      "critical_issues": [
        "❌ WIEK: Max 65 lat, klient ma 68"
      ]
    }
  ]
}
```

### Etap 2: Ranking (Markdown)

```markdown
## 🏆 OFERTA #1: Alior Bank - 87/100 pkt

### 💰 KOSZT KREDYTU: 32/35 pkt
- Wcześniejsza spłata: 0% → 10/10 pkt ✅
- Ubezpieczenie pomostowe: brak → 8/8 pkt ✅
...

### ✨ KLUCZOWE ATUTY:
1. Brak opłaty za wcześniejszą spłatę (oszczędność ~10,000 zł)
2. Najdłuższy okres kredytowania (420 mc)
```

---

## ❓ FAQ

**Q: Czy mogę używać starego systemu (1 prompt)?**  
A: Tak: `engine.process_query_legacy(profil)` - kompatybilność zachowana.

**Q: Co jeśli żaden bank się nie kwalifikuje?**  
A: Etap 1 pokaże listę problemów dla każdego banku.

**Q: Ile czasu zajmuje analiza?**  
A: 10-20 sekund (zależy od Azure OpenAI API).

**Q: Czy wyniki są zapisywane?**  
A: Tak, w `test_results/` z timestamp.

**Q: Jak zmienić liczbę rekomendowanych banków (TOP 4)?**  
A: Edytuj prompt w `create_ranking_prompt()` - zmień "TOP 4" na "TOP 5" itp.

---

## 🆘 Rozwiązywanie problemów

### Problem: "Błąd parsowania JSON z etapu 1"

**Rozwiązanie**: AI zwrócił niepoprawny JSON. Sprawdź:
```python
# W ai_client.py zwiększ temperature dla etapu 1:
temperature=0.1  # Zmień na 0.05 (bardziej deterministyczne)
```

### Problem: "Za mało zakwalifikowanych banków"

**Przyczyna**: Profil klienta bardzo specyficzny (np. senior, działka rekreacyjna).

**To normalne** - system pokazuje realność. Sprawdź `disqualified_banks` aby zobaczyć powody.

### Problem: "Token limit exceeded"

**Rozwiązanie**: Zwiększ `max_tokens` w konfiguracji:
```python
# W config.py
MAX_TOKENS = 6000  # Zwiększ z 4000
```

---

## 📚 Dalsze materiały

- **Pełna dokumentacja**: [TWO_STAGE_SYSTEM.md](TWO_STAGE_SYSTEM.md)
- **Wizualizacje**: [TWO_STAGE_VISUAL.md](TWO_STAGE_VISUAL.md)
- **Architektura ogólna**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ✅ Checklist wdrożenia

- [ ] Uruchom `python test_two_stage.py` - sprawdź czy działa
- [ ] Przejrzyj wynik w `test_results/` - zrozum format
- [ ] Przetestuj z własnym profilem klienta
- [ ] Dostosuj wagi punktacji (jeśli potrzeba)
- [ ] Zintegruj z główną aplikacją (zamień `process_query_legacy` na `process_query`)

---

**Gotowy do użycia!** 🎉

Jeśli masz pytania, sprawdź [TWO_STAGE_SYSTEM.md](TWO_STAGE_SYSTEM.md) lub uruchom:
```powershell
python test_two_stage.py --help
```
