# 🎯 AKTUALIZACJA SYSTEMU RANKINGU JAKOŚCI

## Data: 2025-01-24
## Wersja: v3.1 - Inteligentny Ranking

---

## 📋 PODSUMOWANIE ZMIAN

System rankingu jakości został zaktualizowany, aby **punktował tylko te parametry, które są istotne dla konkretnego klienta**, zamiast oceniać wszystkie 19 parametrów dla każdego profilu.

### Kluczowa zmiana filozofii:

**PRZED:**
- Każdy klient oceniany po wszystkich 19 parametrach
- Kredyt EKO punktowany nawet jeśli klient nie wspomniał o ekologii
- Karencja oceniana dla kredytu na 10 lat
- LTV pożyczki sprawdzany przy zakupie mieszkania

**PO:**
- LLM analizuje profil i punktuje TYLKO istotne parametry
- Kredyt EKO: punktowany tylko jeśli `eco_friendly: true` lub brak danych (benefit)
- Karencja: punktowana tylko jeśli `grace_period_months` podana lub zainteresowanie
- LTV pożyczki: punktowany tylko jeśli cel to pożyczka hipoteczna
- Wynik przeskalowany proporcjonalnie do sprawdzonych parametrów

---

## 🔧 ZMODYFIKOWANE FUNKCJE

### 1. `rank_single_bank_async()` (linia ~909)

**Dodany parametr:**
```python
async def rank_single_bank_async(
    self,
    bank_name: str,
    bank_data: Dict,
    user_query: str,
    deployment_name: str = None,
    customer_profile = None  # ← NOWY
) -> Dict:
```

**Dual-path prompt:**

#### Ścieżka A: Inteligentny ranking (`if customer_profile`)
- Otrzymuje zmapowany profil w JSON
- Instrukcja: "Punktuj TYLKO parametry istotne dla TEGO klienta"
- Szczegółowe zasady dla każdego z 19 parametrów:
  - ZAWSZE punktuj: wcześniejsza spłata, koszt operatu, typ rat, rodzaj operatu, termin decyzji, ubezpieczenia (korzyści)
  - WARUNKOWO: kredyt EKO, ubezp. pomostowe, karencja, waluty, LTV pożyczki
  - Przykłady decyzyjne dla każdego parametru

#### Ścieżka B: Fallback (`else`)
- Oryginalny prompt - punktuj wszystkie 19 parametrów
- Dla kompatybilności wstecznej

**Format odpowiedzi (rozszerzony):**
```json
{
  "bank_name": "PKO BP",
  "total_score": 87,
  "scoring_method": "Sprawdzono 12/19 parametrów (max 70 pkt), uzyskano 61 pkt → (61/70)*100 = 87",
  "breakdown": {...},
  "checked_parameters": ["wczesniejsza_splata", "koszt_operatu", ...],
  "skipped_parameters": [
    "karencja - brak zainteresowania klienta",
    "ltv_pozyczka - cel to zakup mieszkania, nie pożyczka"
  ],
  "details": {
    "kredyt_eko": {
      "value": "brak",
      "points": 0,
      "checked": false,
      "reason": "Klient nie wspomniał o EKO"
    }
  }
}
```

**Przeskalowanie wyniku:**
```python
# Przykład:
# Sprawdzono: 12/19 parametrów
# Max możliwe dla sprawdzonych: 70 pkt
# Uzyskane: 61 pkt
# Wynik: (61/70) * 100 = 87/100 pkt
```

---

### 2. `rank_by_quality_async()` (linia ~1245)

**Dodany parametr:**
```python
async def rank_by_quality_async(
    self,
    user_query: str,
    knowledge_base: Dict,
    qualified_banks: List[str],
    deployment_name: str = None,
    customer_profile = None  # ← NOWY
) -> str:
```

**Aktualizacja wywołania:**
```python
task = self.rank_single_bank_async(
    bank_name=bank_name,
    bank_data=bank_data,
    user_query=user_query,
    deployment_name=deployment_name,
    customer_profile=customer_profile  # ← PRZEKAZUJE PROFIL
)
```

---

### 3. Konstrukcja wiadomości do LLM

**Zmiana w `rank_single_bank_async()`:**

```python
# PRZED:
messages = [
    {"role": "system", "content": ranking_prompt},
    {"role": "system", "content": f"DANE BANKU {bank_name}:\n\n{bank_context}"},
    {"role": "user", "content": f"PROFIL KLIENTA:\n\n{user_query}"}
]

# PO:
messages = [
    {"role": "system", "content": ranking_prompt},
    {"role": "system", "content": f"DANE BANKU {bank_name}:\n\n{bank_context}"}
]

if customer_profile:
    profile_json = json.dumps(customer_profile.to_dict(), ensure_ascii=False, indent=2)
    messages.append({
        "role": "user",
        "content": f"ZMAPOWANY PROFIL KLIENTA (JSON):\n\n{profile_json}\n\n⚠️ PAMIĘTAJ: Punktuj TYLKO parametry istotne dla tego profilu!"
    })
else:
    messages.append({
        "role": "user",
        "content": f"PROFIL KLIENTA:\n\n{user_query}"
    })
```

---

## 📊 ZASADY PUNKTOWANIA (19 PARAMETRÓW)

### A) KOSZT KREDYTU (max 35 pkt)

| Parametr | Punktacja | Kiedy punktować |
|----------|-----------|-----------------|
| **Wcześniejsza spłata** | 0-10 pkt | **ZAWSZE** (uniwersalny benefit) |
| **Ubezp. pomostowe** | 0-8 pkt | JEŚLI `ltv` lub `down_payment_percent` podane |
| **Ubezp. niskiego wkładu** | 0-7 pkt | JEŚLI `ltv > 80%` lub `down_payment_percent < 20%` |
| **Koszt operatu** | 0-5 pkt | **ZAWSZE** (każdy klient potrzebuje) |
| **Kredyt EKO** | 0-5 pkt | JEŚLI `eco_friendly: true` LUB nie podano (benefit) |

### B) ELASTYCZNOŚĆ (max 25 pkt)

| Parametr | Punktacja | Kiedy punktować |
|----------|-----------|-----------------|
| **Kwota max** | 0-8 pkt | JEŚLI `loan_amount` podana (kontekst) |
| **Okres kredytowania** | 0-7 pkt | JEŚLI `loan_period` podany |
| **Karencja** | 0-5 pkt | JEŚLI `grace_period_months` podana LUB zainteresowanie |
| **Typ rat** | 0-5 pkt | **ZAWSZE** (preferencje mogą się zmienić) |

### C) WYGODA (max 20 pkt)

| Parametr | Punktacja | Kiedy punktować |
|----------|-----------|-----------------|
| **Rodzaj operatu** | 0-10 pkt | **ZAWSZE** |
| **Termin decyzji** | 0-5 pkt | **ZAWSZE** |
| **Waluty** | 0-5 pkt | JEŚLI `currency` podana LUB różna od PLN |

### D) KORZYŚCI (max 15 pkt)

| Parametr | Punktacja | Kiedy punktować |
|----------|-----------|-----------------|
| **Oprocentowanie stałe** | 0-8 pkt | JEŚLI `fixed_rate_period_years` podana LUB brak info |
| **Ubezp. nieruchomości** | 0-4 pkt | **ZAWSZE** (benefit) |
| **Ubezp. utraty pracy** | 0-3 pkt | **ZAWSZE** (benefit) |

### E) PARAMETRY MAX (max 5 pkt)

| Parametr | Punktacja | Kiedy punktować |
|----------|-----------|-----------------|
| **LTV pożyczka** | 0-3 pkt | JEŚLI cel to **pożyczka hipoteczna** |
| **Kwota pożyczki** | 0-2 pkt | JEŚLI cel to **pożyczka hipoteczna** |

---

## 🎓 PRZYKŁADY UŻYCIA

### Przykład 1: Minimalny profil

**Input:**
```
Jan, 45 lat, UoP 5 lat, zakup mieszkania 800k
```

**Zmapowany profil:**
```json
{
  "borrower": {
    "age": 45,
    "income_type": "employment_contract",
    "employment_duration_months": 60
  },
  "loan": {
    "loan_purpose": "apartment_purchase",
    "property_value": 800000
  }
}
```

**Sprawdzone parametry (9/19):**
- ✅ Wcześniejsza spłata (ZAWSZE)
- ✅ Koszt operatu (ZAWSZE)
- ✅ Typ rat (ZAWSZE)
- ✅ Rodzaj operatu (ZAWSZE)
- ✅ Termin decyzji (ZAWSZE)
- ✅ Ubezp. nieruchomości (ZAWSZE)
- ✅ Ubezp. utraty pracy (ZAWSZE)
- ✅ Oprocentowanie stałe (brak info → benefit dla wszystkich)
- ✅ Kredyt EKO (brak info → benefit dla wszystkich)

**Pominięte (10/19):**
- ⏭️ Ubezp. pomostowe (brak LTV)
- ⏭️ Ubezp. niskiego wkładu (brak LTV)
- ⏭️ Kwota max (brak loan_amount)
- ⏭️ Okres kredytowania (brak loan_period)
- ⏭️ Karencja (brak zainteresowania)
- ⏭️ Waluty (brak wzmianki)
- ⏭️ LTV pożyczka (cel: zakup, nie pożyczka)
- ⏭️ Kwota pożyczki (cel: zakup, nie pożyczka)

**Scoring:**
- Max możliwe dla 9 sprawdzonych: ~55 pkt
- Uzyskane: 48 pkt
- **Wynik: (48/55) * 100 = 87/100 pkt**

---

### Przykład 2: Pełny profil EKO

**Input:**
```
Ania, 32 lata, UoP 3 lata, dochód 12k/mc
Zakup domu energooszczędnego 1.2M (kredyt 900k, wkład 300k)
25 lat spłaty, karencja 6 mc, waluta PLN
```

**Zmapowany profil:**
```json
{
  "borrower": {
    "age": 32,
    "income_type": "employment_contract",
    "employment_duration_months": 36,
    "monthly_income": 12000
  },
  "loan": {
    "loan_purpose": "house_purchase",
    "loan_amount": 900000,
    "property_value": 1200000,
    "down_payment": 300000,
    "down_payment_percent": 25,
    "ltv": 75,
    "loan_period_years": 25,
    "grace_period_months": 6,
    "currency": "PLN"
  },
  "property": {
    "eco_friendly": true
  }
}
```

**Sprawdzone parametry (17/19):**
- ✅ Wszystkie z grupy KOSZT (5/5) - w tym kredyt EKO (eco_friendly: true)
- ✅ Wszystkie z grupy ELASTYCZNOŚĆ (4/4)
- ✅ Wszystkie z grupy WYGODA (3/3)
- ✅ Wszystkie z grupy KORZYŚCI (3/3)
- ⏭️ Grupa PARAMETRY MAX (0/2) - cel: zakup domu, nie pożyczka

**Scoring:**
- Max możliwe dla 17 sprawdzonych: 95 pkt
- Uzyskane: 82 pkt
- **Wynik: (82/95) * 100 = 86/100 pkt**

---

### Przykład 3: Pożyczka hipoteczna

**Input:**
```
Tomasz, 55 lat, działalność 10 lat
Pożyczka hipoteczna 500k (cel: dowolny)
Zabezpieczenie: dom wart 1M
```

**Zmapowany profil:**
```json
{
  "borrower": {
    "age": 55,
    "income_type": "business_activity",
    "employment_duration_months": 120
  },
  "loan": {
    "loan_purpose": "mortgage_loan",
    "loan_amount": 500000,
    "property_value": 1000000,
    "ltv": 50
  }
}
```

**Sprawdzone parametry (14/19):**
- ✅ Wszystkie uniwersalne (9 parametrów)
- ✅ Ubezp. pomostowe (LTV podane)
- ✅ Kwota max (loan_amount podana)
- ✅ **LTV pożyczka** (cel: pożyczka hipoteczna) ← TERAZ PUNKTOWANE
- ✅ **Kwota pożyczki** (cel: pożyczka hipoteczna) ← TERAZ PUNKTOWANE
- ⏭️ Karencja (brak wzmianki)
- ⏭️ Okres kredytowania (brak loan_period)
- ⏭️ Waluty (brak wzmianki)
- ⏭️ Oprocentowanie stałe (brak fixed_rate_period_years)

---

## ✅ KORZYŚCI Z AKTUALIZACJI

### 1. **Precyzyjniejsza ocena**
   - Bank nie traci punktów za parametry nieistotne dla klienta
   - Kredyt EKO nie obniża wyniku jeśli klient nie chce budować EKO

### 2. **Sprawiedliwsze porównanie**
   - Dwa banki oceniane po tych samych kryteriach (istotnych dla klienta)
   - Przeskalowanie wyniku wyrównuje szanse

### 3. **Lepsza transparentność**
   - Pole `checked_parameters` - co uwzględniono
   - Pole `skipped_parameters` - co pominięto i dlaczego
   - Pole `scoring_method` - jak obliczono wynik

### 4. **Elastyczność LLM**
   - LLM decyduje co jest istotne (nie hardcoded logic)
   - Może uwzględnić kontekst (np. "młode małżeństwo" → karencja istotna)

---

## 🔗 INTEGRACJA Z RESZTĄ SYSTEMU

### Przepływ danych:

```
1. main.py (KROK 0)
   └─> InputMapper.map_input_to_profile(user_input)
       └─> CustomerProfile object

2. main.py (ETAP 1)
   └─> QueryEngine.process_query(user_query, customer_profile)
       └─> AIClient.query_two_stage(user_query, customer_profile)
           └─> validate_requirements_async(user_query, customer_profile)
               └─> validate_single_bank_async(..., customer_profile)
                   └─> LLM sprawdza TYLKO non-null fields

3. main.py (ETAP 2)
   └─> AIClient.rank_by_quality_async(user_query, ..., customer_profile)
       └─> rank_single_bank_async(..., customer_profile)  ← TUTAJ
           └─> LLM punktuje TYLKO istotne parametry
```

### Sygnatura funkcji w całym łańcuchu:

```python
# query_engine.py
def process_query(self, user_query: str, customer_profile=None) -> str:
    return asyncio.run(
        self.ai_client.query_two_stage(user_query, customer_profile)
    )

# ai_client.py
async def query_two_stage(self, user_query: str, customer_profile=None):
    # ETAP 1
    validation_json, validation_dict = await self.validate_requirements_async(
        user_query, customer_profile
    )
    
    # ETAP 2
    ranking_markdown = await self.rank_by_quality_async(
        user_query, ..., qualified_banks, customer_profile=customer_profile
    )
```

---

## 🧪 TESTOWANIE

### Test 1: Minimalny profil
```python
user_input = "Jan, 45 lat, UoP 5 lat, zakup mieszkania 800k"
# Oczekiwane: ~9 sprawdzonych parametrów, ~10 pominiętych
```

### Test 2: Profil EKO
```python
user_input = "Dom energooszczędny, kredyt 900k, EKO"
# Oczekiwane: kredyt_eko.checked = True
```

### Test 3: Pożyczka hipoteczna
```python
user_input = "Pożyczka hipoteczna 500k, cel dowolny"
# Oczekiwane: ltv_pozyczka.checked = True, kwota_pozyczki.checked = True
```

### Test 4: Bez eco_friendly
```python
user_input = "Zwykły dom, kredyt 800k"
# Oczekiwane: kredyt_eko.checked = True (benefit dla wszystkich)
```

### Test 5: eco_friendly = False
```python
user_input = "Stary dom do remontu, nie EKO"
# Oczekiwane: kredyt_eko.checked = False, reason: "Klient nie chce EKO"
```

---

## 📝 NOTES

1. **Backward compatibility**: Fallback do starego promptu jeśli `customer_profile` nie podany
2. **LLM intelligence**: LLM sam decyduje co jest istotne (nie sztywne `if` w kodzie)
3. **Przeskalowanie**: Zawsze wynik 0-100, niezależnie ile parametrów sprawdzono
4. **Format JSON rozszerzony**: Dodano `checked_parameters`, `skipped_parameters`, `scoring_method`

---

## 🚀 NASTĘPNE KROKI

- [x] Aktualizacja `rank_single_bank_async()` - dodany parametr, dual-path prompt
- [x] Aktualizacja `rank_by_quality_async()` - przekazywanie customer_profile
- [x] Aktualizacja konstrukcji wiadomości - JSON profilu zamiast raw text
- [ ] Testowanie end-to-end z różnymi profilami
- [ ] Walidacja wyników - czy LLM poprawnie kategoryzuje parametry
- [ ] Optymalizacja promptu - jeśli LLM myli się w kategoryzacji

---

**Autor:** AI Assistant  
**Data:** 2025-01-24  
**Wersja systemu:** v3.1 - Inteligentny Ranking
