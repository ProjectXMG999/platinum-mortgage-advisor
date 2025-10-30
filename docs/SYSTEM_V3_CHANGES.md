# 🔄 SYSTEM V3.0 - MODYFIKACJE

## 📋 PODSUMOWANIE ZMIAN

System został rozszerzony o **inteligentne mapowanie inputu** i **selektywną walidację** - sprawdzane są tylko te parametry, które użytkownik faktycznie podał.

---

## 🎯 GŁÓWNE ZMIANY

### **1. NOWY ETAP 0: MAPOWANIE DANYCH**

#### Nowe pliki:
- `src/models/customer_profile.py` - Predefinowany model danych kredytobiorcy
- `src/input_mapper.py` - Mapper inputu użytkownika na model

#### Funkcjonalność:
- **Input użytkownika** (dowolna forma) → **LLM** → **Struktura JSON**
- Ekstrakcja i strukturyzacja danych
- Walidacja kompletności
- Obliczanie brakujących wartości (np. LTV)

#### Model danych:
```python
CustomerProfile:
  ├── borrower: PersonData (WYMAGANY)
  │   ├── age ⚠️ WYMAGANE
  │   ├── income_type ⚠️ WYMAGANE
  │   ├── employment_duration_months ⚠️ WYMAGANE
  │   └── income_amount_monthly (opcjonalne)
  │
  ├── co_borrower: PersonData (opcjonalne)
  │
  ├── loan: LoanParameters
  │   ├── loan_purpose ⚠️ WYMAGANE
  │   ├── property_value ⚠️ WYMAGANE (lub loan_amount)
  │   ├── loan_amount (opcjonalne)
  │   ├── ltv (opcjonalne - auto-kalkulacja)
  │   └── ... (15 innych parametrów)
  │
  ├── property: PropertyData (opcjonalne)
  │   ├── property_type
  │   ├── property_location
  │   └── ... (13 parametrów)
  │
  └── relationship_status (opcjonalne)
```

---

### **2. INTELIGENTNA WALIDACJA - TYLKO PODANE PARAMETRY**

#### Stare podejście:
```
System sprawdza WSZYSTKIE 68 WYMOGÓW dla każdego banku
→ Długie prompty
→ Wymaga pełnych danych
→ Dużo N/D (nie dotyczy)
```

#### Nowe podejście:
```
System sprawdza TYLKO te WYMOGI, które dotyczą klienta
→ Krótsze prompty
→ Działa z niepełnymi danymi
→ Precyzyjniejsza walidacja
```

#### Przykład:
**Input użytkownika:**
```
Jan, 45 lat, UoP, staż 5 lat
Zakup mieszkania za 800k, kredyt 640k
```

**Zmapowany profil zawiera:**
- age: 45
- income_type: "umowa_o_prace_czas_nieokreslony"
- employment_duration_months: 60
- loan_purpose: "zakup_mieszkania_domu"
- property_value: 800000
- loan_amount: 640000
- ltv: 80 (auto-obliczone)

**System sprawdzi TYLKO:**
- ✅ Wiek klienta (czy mieści się w limicie banku)
- ✅ UoP na czas nieokreślony (czy bank akceptuje)
- ✅ Staż 60 miesięcy (czy spełnia minimum banku)
- ✅ Cel: zakup mieszkania (czy bank finansuje)
- ✅ LTV 80% (czy w limicie banku)

**NIE sprawdzi** (bo brak danych):
- ❌ Cudzoziemiec (brak info → pominięte)
- ❌ Działalność gospodarcza (nie dotyczy)
- ❌ Refinansowanie (nie dotyczy)
- ❌ Kamienica (nie dotyczy)
- ❌ ... (60+ innych parametrów)

---

### **3. ZAKTUALIZOWANY PRZEPŁYW DANYCH**

#### Nowy workflow:

```
📝 INPUT UŻYTKOWNIKA (dowolna forma)
  "Jan, 45 lat, UoP, zakup mieszkania 800k..."

↓ [ETAP 0: MAPOWANIE - LLM #1]

📊 ZMAPOWANY PROFIL (CustomerProfile)
  {
    "borrower": {"age": 45, "income_type": "UoP", ...},
    "loan": {"loan_purpose": "zakup_mieszkania", ...},
    ...
  }

↓ [ETAP 1: WALIDACJA - 11x LLM parallel]

✅ ZAKWALIFIKOWANE BANKI (6/11)
  - ING: spełnia 5/5 sprawdzonych wymogów
  - mBank: spełnia 5/5 sprawdzonych wymogów
  - ...

❌ ODRZUCONE BANKI (5/11)
  - BNP: wiek max 65, klient ma 70
  - ...

↓ [ETAP 2: RANKING - 6x LLM parallel]

🏆 TOP 4 RANKING
  1. ING: 91/100 pkt
  2. mBank: 87/100 pkt
  3. PKO BP: 84/100 pkt
  4. Alior: 82/100 pkt
```

---

### **4. ZMIANY W UI (main.py)**

#### Nowe elementy:
1. **Przycisk pomocy** - Przewodnik wszystkich możliwych parametrów
2. **Rozszerzone przykłady** - 4 przykładowe profile
3. **Wybór modelu MAPPER** w sidebar
4. **Podgląd zmapowanego profilu** w sidebar
5. **KROK 0 w spinner** - Użytkownik widzi proces mapowania

#### Sidebar:
```
🤖 Konfiguracja modeli AI
├── 🔄 Model MAPPER (Ekstrakcja danych) ← NOWY
├── 🔍 Model ETAP 1 (Walidacja WYMOGÓW)
├── 🏅 Model ETAP 2 (Ranking JAKOŚCI)
└── ⚡ Async Parallel Processing

📋 Zmapowany profil ← NOWY
├── ✅ Profil kompletny
├── 👤 Wiek: 45 lat
├── 💼 Dochód: umowa_o_prace_czas_nieokreslony
├── 🎯 Cel: zakup_mieszkania_domu
├── 💰 Kwota: 640,000 PLN
└── 🔍 Pełny JSON (expander)
```

---

### **5. ZMIENIONE PLIKI**

#### `main.py`:
- Dodano import `InputMapper` i `CUSTOMER_PROFILE_TEMPLATE`
- Dodano `st.session_state.input_mapper`
- Dodano `st.session_state.customer_profile`
- Dodano `st.session_state.mapped_profile_json`
- Dodano KROK 0: Mapowanie przed ETAP 1
- Rozszerzono przykładowe profile (4 zamiast 3)
- Dodano expander z przewodnikiem parametrów
- Dodano wybór modelu MAPPER w sidebar
- Dodano podgląd zmapowanego profilu w sidebar

#### `src/ai_client.py`:
- `query_two_stage()` - dodano parametr `customer_profile`
- `validate_requirements_async()` - dodano parametr `customer_profile`
- `validate_single_bank_async()` - dodano parametr `customer_profile`
- Zmieniono print "DWUETAPOWY" → "TRZYETAPOWY"

---

### **6. WYMAGANE POLA (MINIMUM)**

⚠️ Aby przeprowadzić analizę, system wymaga **5 podstawowych informacji**:

1. **borrower.age** - Wiek kredytobiorcy
2. **borrower.income_type** - Typ dochodu
3. **borrower.employment_duration_months** - Staż pracy
4. **loan.loan_purpose** - Cel kredytu
5. **loan.property_value** LUB **loan.loan_amount** - Wartość/Kwota

Jeśli któregoś brak → system wyświetli ostrzeżenie, ale przeprowadzi analizę.

---

### **7. KORZYŚCI NOWEGO SYSTEMU**

✅ **Elastyczny input** - Użytkownik może podać dane w dowolnej formie  
✅ **Inteligentna walidacja** - Sprawdzane tylko podane parametry  
✅ **Szybsza analiza** - Krótsze prompty = szybsze odpowiedzi  
✅ **Lepsze wyniki** - Mniej "szumu" w walidacji  
✅ **Przejrzystość** - Użytkownik widzi co zostało zmapowane  
✅ **Auto-kalkulacja** - System oblicza LTV, wkład własny itp.

---

### **8. PRZYKŁAD UŻYCIA**

#### Input (skrócony):
```
Jan, 45 lat
UoP, 5 lat
Zakup mieszkania 800k
```

#### Zmapowany profil:
```json
{
  "borrower": {
    "age": 45,
    "income_type": "umowa_o_prace_czas_nieokreslony",
    "employment_duration_months": 60,
    "income_amount_monthly": null,
    "is_polish_citizen": true
  },
  "loan": {
    "loan_purpose": "zakup_mieszkania_domu",
    "property_value": 800000.0,
    "loan_amount": null,
    "ltv": null,
    "currency": "PLN"
  },
  "property": {
    "property_type": "mieszkanie",
    "property_location": null
  }
}
```

#### Walidacja banku (ING):
```
Sprawdzam TYLKO:
✅ Wiek 45: ING akceptuje 18-67 → OK
✅ UoP czas nieokreślony: ING wymaga min 3 mc → 60 mc OK
✅ Zakup mieszkania: ING akceptuje → OK
✅ Wartość 800k: ING limit 4 mln → OK

Status: QUALIFIED (4/4 sprawdzonych wymogów spełnionych)
```

---

### **9. NASTĘPNE KROKI (TODO)**

1. ✅ Stworzenie modelu danych (`customer_profile.py`)
2. ✅ Stworzenie mappera (`input_mapper.py`)
3. ✅ Aktualizacja UI (`main.py`)
4. ✅ Aktualizacja `query_two_stage()` i `validate_requirements_async()`
5. ⏳ **Aktualizacja `validate_single_bank_async()`** - inteligentna walidacja
6. ⏳ **Aktualizacja `rank_single_bank_async()`** - inteligentny ranking
7. ⏳ **Testy** - sprawdzenie czy system działa poprawnie

---

### **10. UWAGI TECHNICZNE**

#### Mapowanie Enum:
```python
# String → Enum
income_type = "umowa_o_prace_czas_nieokreslony"
income_enum = IncomeType.UOP_CZAS_NIEOKRESLONY

# Enum → String (dla JSON)
income_enum.value  # → "umowa_o_prace_czas_nieokreslony"
```

#### Walidacja profilu:
```python
profile.is_complete()  # → True/False
profile.get_missing_required_fields()  # → ["borrower_age", ...]
validate_profile(profile)  # → (is_valid, errors)
```

#### Auto-kalkulacja:
```python
profile.calculate_ltv()
# Jeśli loan_amount=640k i property_value=800k
# → ltv=80%
# → down_payment_percent=20%
# → down_payment=160k
```

---

## 📊 PODSUMOWANIE

System V3.0 wprowadza **inteligentne mapowanie** i **selektywną walidację**, co znacząco poprawia:
- Elastyczność inputu
- Dokładność analizy
- Szybkość działania
- User Experience

Użytkownik może teraz podać **minimum 5 informacji** i otrzymać dopasowane rekomendacje, zamiast wypełniać wszystkie 87 parametrów.
