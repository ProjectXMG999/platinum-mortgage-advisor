# 🚀 PLAN OPTYMALIZACJI WYDAJNOŚCI SYSTEMU

## 📊 Wyniki Benchmarku

**Średni czas przetwarzania: 64.4 sekundy** (cel: < 15s)
**Przekroczenie: +49.4 sekundy (330% wolniej niż cel)**

### Podział czasów:
- **ETAP 1 (Walidacja)**: ~31s (48%)
- **ETAP 2 (Ranking)**: ~33s (51%)
- **Inicjalizacja**: ~0.4s (1%)

---

## 🎯 STRATEGIA OPTYMALIZACJI (CEL: < 15s)

### FAZA 1: QUICK WINS (Oczekiwane: -40s, do 24s) ⚡ PRIORYTET

#### 1.1 Zmiana modelu AI na szybszy
**Problem**: GPT-4o jest dokładny ale wolny  
**Rozwiązanie**: GPT-4o-mini (4-6x szybciej)
- Czas ETAP 1: 31s → **6s** (oszczędność: ~25s)
- Czas ETAP 2: 33s → **7s** (oszczędność: ~26s)

**Implementacja**:
```python
# src/config.py
DEPLOYMENT_NAME = "gpt-4o-mini"  # Zmiana z "gpt-4o"
```

**Ryzyko**: Nieznacznie niższa jakość (testujemy)  
**Czas wdrożenia**: 5 minut

---

#### 1.2 Redukcja max_tokens
**Problem**: 16000 tokenów dla ETAP 1 to overkill  
**Rozwiązanie**: Zmniejsz do 8000 (JSON dla 11 banków ~4000-6000 tokenów)

**Implementacja**:
```python
# src/ai_client.py - line 527
max_tokens=8000  # Zmiana z 16000
```

**Oszczędność**: ~3-5s (mniej tokenów = szybsza generacja)  
**Czas wdrożenia**: 1 minuta

---

#### 1.3 Uprość prompty
**Problem**: Prompty są bardzo szczegółowe (długie = wolne)  
**Rozwiązanie**: 
- Usuń przykłady z promptu walidacyjnego (~500 tokenów)
- Skróć instrukcje (50% tekstu)

**Oszczędność**: ~2-4s (mniej tokenów wejściowych)  
**Czas wdrożenia**: 30 minut

---

### FAZA 2: ARCHITEKTURA (Oczekiwane: -10s, do 14s) 🏗️ PRIORYTET

#### 2.1 Ranking tylko TOP 4 (zamiast wszystkich)
**Problem**: ETAP 2 rankuje wszystkie zakwalifikowane banki (nawet 10)  
**Rozwiązanie**: Wybierz 4 najlepsze banki PO prostej heurystyce

**Implementacja**:
```python
def pre_filter_top_candidates(qualified_banks, validation_data):
    """Wybierz TOP 4-6 banków przed rankingiem AI"""
    # Heurystyka: sortuj po liczbie spełnionych wymogów
    sorted_banks = sorted(
        qualified_banks, 
        key=lambda b: validation_data[b]["requirements_met"],
        reverse=True
    )
    return sorted_banks[:6]  # Weź TOP 6, AI zrankuje do TOP 4
```

**Oszczędność**: ~10-15s (mniej tokenów output w ETAP 2)  
**Czas wdrożenia**: 1 godzina

---

#### 2.2 Asynchroniczne wywołania (jeśli możliwe)
**Problem**: ETAP 1 i ETAP 2 działają sekwencyjnie  
**Rozwiązanie**: Jeśli API wspiera batch, rankuj TOP banki równolegle

**Implementacja** (zaawansowana):
```python
import asyncio

async def rank_bank_async(bank_name, context):
    # Rankuj 1 bank asynchronicznie
    pass

# Zamiast 1 wywołania dla 10 banków → 4 równoległe dla TOP 4
```

**Oszczędność**: ~5-10s (równoległość)  
**Czas wdrożenia**: 4 godziny (wymaga async refactor)

---

### FAZA 3: CACHE I OPTYMALIZACJE (Oczekiwane: -2s, do 12s) 💾

#### 3.1 Cache powtarzających się zapytań
**Problem**: Podobne profile generują podobne wyniki  
**Rozwiązanie**: Redis/memory cache dla validation_prompt + query hash

**Implementacja**:
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_validation(query_hash):
    # Cache wyników ETAP 1
    pass
```

**Oszczędność**: ~30s dla powtórzeń (0s dla nowych)  
**Czas wdrożenia**: 2 godziny

---

#### 3.2 Prekompilowane prompty
**Problem**: Prompt tworzony przy każdym wywołaniu  
**Rozwiązanie**: Wczytaj raz przy inicjalizacji

**Oszczędność**: ~0.5s  
**Czas wdrożenia**: 30 minut

---

## 📈 PRZEWIDYWANE WYNIKI PO OPTYMALIZACJI

| Faza | Zmiana | Czas ETAP 1 | Czas ETAP 2 | CAŁKOWITY | vs Cel |
|------|--------|-------------|-------------|-----------|--------|
| **Obecny** | - | 31s | 33s | **64s** | +49s ❌ |
| **Faza 1** | Szybszy model + tokens | 6s | 7s | **13s** | -2s ✅ |
| **Faza 2** | TOP 4 filter | 6s | 4s | **10s** | -5s ✅✅ |
| **Faza 3** | Cache | 3s* | 4s | **7s** | -8s ✅✅✅ |

*Cache działa tylko dla powtórzeń

---

## 🛠️ PLAN WDROŻENIA (REKOMENDOWANY)

### SPRINT 1 (1 godzina) - CRITICAL PATH
1. ✅ Zmiana modelu na gpt-4o-mini (5 min)
2. ✅ Redukcja max_tokens do 8000 (1 min)
3. ✅ Test wydajności (10 min)
4. ✅ Jeśli < 20s → przechodzimy do FAZA 2

### SPRINT 2 (2 godziny) - OPTIMIZATION
5. ✅ Ranking TOP 4 zamiast wszystkich (1h)
6. ✅ Uproszczenie promptów (30 min)
7. ✅ Test wydajności (30 min)
8. ✅ Jeśli < 15s → SUKCES! Jeśli nie → FAZA 3

### SPRINT 3 (opcjonalny, 4 godziny) - POLISH
9. Cache dla powtarzających się zapytań
10. Async wywołania (jeśli Azure wspiera)
11. Monitoring wydajności w Streamlit

---

## ⚠️ RYZYKA

| Ryzyko | Prawdopodobieństwo | Mitygacja |
|--------|-------------------|-----------|
| GPT-4o-mini mniej dokładny | Średnie | A/B test jakości wyników |
| Redukcja max_tokens obcina JSON | Niskie | Walidacja parsowania |
| Cache daje stare wyniki | Niskie | TTL 1h, invalidacja po update bazy |

---

## 🎯 METRYKI SUKCESU

- ✅ **Czas < 15s** dla 80% zapytań
- ✅ **Czas < 20s** dla 100% zapytań
- ✅ **Jakość rankingu** > 90% zgodności z GPT-4o (test A/B)
- ✅ **Zero błędów** parsowania JSON

---

## 📝 NASTĘPNE KROKI

**TERAZ:**
1. Zatwierdź plan optymalizacji
2. Uruchom SPRINT 1 (zmiana modelu)
3. Zmierz wyniki

**Czy rozpoczynamy SPRINT 1?** 🚀
