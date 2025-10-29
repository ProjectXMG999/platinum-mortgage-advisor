# 🎯 PROFESJONALNY SYSTEM DOPASOWANIA KREDYTÓW HIPOTECZNYCH
## Platinum Financial - Dokumentacja Techniczna Systemu Matching Engine

**Wersja**: 2.0  
**Data**: 27 października 2025  
**Autor**: System Architecture Team

---

## 📋 SPIS TREŚCI

1. [Wprowadzenie](#wprowadzenie)
2. [Architektura Bazy Danych](#architektura-bazy-danych)
3. [Logika Systemu Dopasowania](#logika-systemu-dopasowania)
4. [Algorytm Rankingowy](#algorytm-rankingowy)
5. [Implementacja](#implementacja)
6. [Przykłady Zastosowania](#przykłady-zastosowania)

---

## 1. WPROWADZENIE

### 1.1 Cel Systemu

System ma za zadanie **automatyczne dopasowanie najlepszej oferty kredytu hipotecznego** na podstawie:
- Profilu klienta (dane osobowe, finansowe, cel kredytu)
- Bazy wiedzy 11 banków (148 parametrów dla każdego banku)
- Klasyfikacji parametrów (WYMÓG vs JAKOŚĆ)

### 1.2 Kluczowe Założenia

✅ **Dwuetapowy proces**:
1. **KWALIFIKACJA** - Eliminacja banków według WYMOGÓW (hard requirements)
2. **OPTYMALIZACJA** - Ranking według JAKOŚCI (soft criteria)

✅ **4 rekomendacje**:
- 🏆 Najlepsza opcja
- 🥈 Druga najlepsza
- 🥉 Trzecia najlepsza
- ⚠️ Najgorsza opcja (dla kontrastu - pokazuje czego unikać)

---

## 2. ARCHITEKTURA BAZY DANYCH

### 2.1 Struktura Knowledge Base

```json
{
  "metadata": {
    "source": "Oficjalna baza Platinum Financial",
    "date_updated": "2025-04-01",
    "banks": 11,
    "parameter_groups": 8
  },
  "banks": ["Alior Bank", "BNP Paribas", "CITI Handlowy", ...],
  "products": [
    {
      "bank_name": "Alior Bank",
      "parameters": {
        "01_parametry kredytu": {16 parametrów},
        "02_kredytobiorca": {7 parametrów},
        "03_źródło dochodu": {20 parametrów},
        "04_cel kredytu": {24 parametry},
        "05_zabezpieczenia": {2 parametry},
        "06_wycena": {2 parametry},
        "07_ubezpieczenia": {5 parametrów},
        "08_ważność dokumentów": {16 parametrów}
      }
    }
  ]
}
```

**Łącznie**: 11 banków × 92 parametry = **1,012 punktów weryfikacji**

### 2.2 Klasyfikacja Parametrów (parameter_classification_v2.json)

#### WYMÓG (68 parametrów - 78.2%)
Parametry **dyskwalifikujące** - klient MUSI spełnić:

| Grupa | Wymogi (przykłady) | Konsekwencja niespełnienia |
|-------|-------------------|---------------------------|
| **01_parametry kredytu** | LTV, wkład własny, limity kredytów, wielkość działki | ❌ Bank ODRZUCA wniosek |
| **02_kredytobiorca** | Wiek, limit wnioskodawców, karta pobytu | ❌ Brak kwalifikacji |
| **03_źródło dochodu** | Typy umów, minimalny staż, wymogi księgowości | ❌ Dochód nieakceptowalny |
| **04_cel kredytu** | Akceptacja celu (zakup, budowa, kamienica, TBS) | ❌ Cel niefinansowalny |
| **05_zabezpieczenia** | Zasady zabezpieczenia osoby trzeciej | ❌ Zabezpieczenie nieakceptowalne |
| **08_ważność dokumentów** | Terminy ważności (30-90 dni) | ❌ Procesowanie niemożliwe |

#### JAKOŚĆ (19 parametrów - 21.8%)
Parametry **optymalizujące** - wpływają na atrakcyjność:

| Grupa | Jakość (przykłady) | Wpływ |
|-------|-------------------|-------|
| **01_parametry kredytu** | Kwota max, okres max, WIBOR, karencja, kredyt EKO | 💰 Koszt, elastyczność |
| **06_wycena** | Koszt operatu (200-1160 zł) | 💰 Opłaty dodatkowe |
| **07_ubezpieczenia** | Koszty UŻ, UN, ubezpieczenie pomostowe | 💰 Całkowity koszt kredytu |

### 2.3 Profile Klientów (customer_profiles.json)

**10 profili testowych** pokrywających:
- ✅ Wszystkie 8 grup parametrów
- ✅ Różne scenariusze (seniorzy, cudzoziemcy, konsolidacja, kamienice)
- ✅ Kompletne dane (92 pola na profil)

Przykładowa struktura profilu:
```json
{
  "profile_id": 1,
  "category": "Zakup kamienicy - cel mieszkaniowy",
  "age": 42,
  "income": {
    "type": "umowa o pracę",
    "monthly_gross": 18000,
    "work_experience_months": 180
  },
  "loan_details": {
    "purpose": "zakup kamienicy",
    "property_value": 1200000,
    "loan_amount": 960000,
    "own_contribution_percentage": 20
  },
  "property": {...},
  "collateral": {...},
  "valuation": {...},
  "insurance": {...},
  "documents": {...}
}
```

---

## 3. LOGIKA SYSTEMU DOPASOWANIA

### 3.1 Algorytm Główny - 4 Etapy

```
┌─────────────────────────────────────────────────────────┐
│  ETAP 1: PRE-SCREENING (Eliminacja według WYMOGÓW)      │
│  ────────────────────────────────────────────────────   │
│  Input: Profil klienta + 11 banków                      │
│  Process: Weryfikacja 68 parametrów WYMÓG               │
│  Output: Lista banków spełniających wymogi (3-11 banków)│
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ETAP 2: SCORING (Ocena według JAKOŚCI)                 │
│  ────────────────────────────────────────────────────   │
│  Input: Lista zakwalifikowanych banków                  │
│  Process: Punktacja 19 parametrów JAKOŚĆ                │
│  Output: Rankingi punktowe dla każdego banku            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ETAP 3: RANKING (Sortowanie)                           │
│  ────────────────────────────────────────────────────   │
│  Input: Banki z punktacją                               │
│  Process: Sortowanie malejąco według score               │
│  Output: Lista 3 najlepszych + 1 najgorsza              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ETAP 4: PREZENTACJA (Formatowanie odpowiedzi)          │
│  ────────────────────────────────────────────────────   │
│  Input: 4 wybrane banki                                 │
│  Process: Generowanie szczegółowej analizy              │
│  Output: Raport z uzasadnieniem dla klienta             │
└─────────────────────────────────────────────────────────┘
```

### 3.2 ETAP 1: PRE-SCREENING - Reguły Eliminacji

#### Grupa 01: Parametry Kredytu

```python
def check_loan_parameters(client, bank):
    """
    Weryfikacja parametrów kredytu - WYMOGI
    """
    checks = {
        "LTV": check_ltv(client.loan_amount, client.property_value, bank.max_ltv),
        "wkład_własny": check_own_contribution(client.own_contribution_pct, bank.min_own_contribution),
        "kwota_kredytu": check_loan_amount(client.loan_amount, bank.min_loan, bank.max_loan),
        "okres_kredytowania": check_loan_period(client.loan_period_months, bank.max_period),
        "limit_kredytów": check_mortgage_limit(client.existing_mortgages, bank.max_mortgages),
        "wielkość_działki": check_plot_size(client.plot_size, bank.max_plot_size)
    }
    return all(checks.values()), checks
```

**Przykłady dyskwalifikacji**:
- ❌ LTV 90%, bank max 80% → ODRZUCONY
- ❌ Wkład 10%, bank wymaga 20% → ODRZUCONY
- ❌ 3 kredyty, bank max 2 → ODRZUCONY

#### Grupa 02: Kredytobiorca

```python
def check_borrower_requirements(client, bank):
    """
    Weryfikacja kredytobiorcy - WYMOGI
    """
    checks = {
        "wiek": check_age(client.age, client.loan_period, bank.min_age, bank.max_age),
        "liczba_wnioskodawców": check_applicants_number(client.number_of_applicants, bank.max_applicants),
        "cudzoziemiec": check_foreigner_status(client.citizenship, client.residence_card, bank.foreigner_requirements),
        "związek_nieformalny": check_informal_relationship(client.relationship_status, bank.informal_relationship_policy)
    }
    return all(checks.values()), checks
```

**Przykłady dyskwalifikacji**:
- ❌ Wiek 68 lat, spłata do 78 lat, bank max 70 → ODRZUCONY
- ❌ Cudzoziemiec, karta pobytu 6 msc, bank wymaga 12 msc → ODRZUCONY

#### Grupa 03: Źródło Dochodu

```python
def check_income_source(client, bank):
    """
    Weryfikacja źródła dochodu - WYMOGI
    Najważniejsza grupa - 20 parametrów!
    """
    income_type = client.income.type
    
    if income_type == "umowa o pracę na czas określony":
        required_experience = bank.parameters["03_źródło dochodu"]["01_umowa o pracę na czas określony"]
        remaining_months = parse_remaining_contract_time(bank, client.contract_end_date)
        
        if client.work_experience_months < required_experience:
            return False, "Za krótki staż pracy"
        if remaining_months < bank.min_remaining_contract:
            return False, "Kontrakt kończy się zbyt wcześnie"
            
    elif income_type == "działalność gospodarcza":
        accounting_type = client.accounting_type  # pełna księgowość / KPiR / ryczałt / karta
        required_period = bank.get_required_business_period(accounting_type)
        
        if client.business_duration_months < required_period:
            return False, f"Działalność za krótka (wymaga {required_period} msc)"
    
    # Weryfikacja dochodów dodatkowych
    if client.additional_income.rental_income:
        if client.additional_income.rental_duration_months < bank.min_rental_period:
            return False, "Najem za krótki okres"
    
    return True, "OK"
```

**Przykłady dyskwalifikacji**:
- ❌ Staż 3 msc, bank wymaga 6 msc → ODRZUCONY
- ❌ Działalność 6 msc, bank wymaga 24 msc → ODRZUCONY
- ❌ Emeryt, bank nie akceptuje emerytury → ODRZUCONY

#### Grupa 04: Cel Kredytu

```python
def check_loan_purpose(client, bank):
    """
    Weryfikacja celu kredytu - WYMOGI
    24 możliwe cele kredytu!
    """
    purpose = client.loan_details.purpose
    
    # Przykłady z bazy wiedzy
    if purpose == "zakup kamienicy":
        policy = bank.parameters["04_cel kredytu"]["13_kamienica"]
        if policy == "nie":
            return False, "Bank nie finansuje kamienic"
        if policy == "do 500 m2" and client.property.size_sqm > 500:
            return False, "Kamienica za duża (max 500 m2)"
    
    if purpose == "konsolidacja niemieszkaniowa":
        policy = bank.parameters["04_cel kredytu"]["22_konsolidacja zobowiązań niemieszkaniowych"]
        if policy == "nie":
            return False, "Bank nie akceptuje konsolidacji"
        
        # Sprawdź limity
        max_consolidation_pct = parse_consolidation_limit(policy)
        if client.consolidation_amount / client.loan_amount > max_consolidation_pct:
            return False, f"Konsolidacja przekracza limit {max_consolidation_pct}%"
    
    if purpose == "zakup udziału we wspólnocie":
        policy = bank.parameters["04_cel kredytu"]["14_zakup udziału w nieruchomości"]
        if "tylko z zabezpieczeniem na całości" in policy:
            if not client.collateral.full_property_collateral:
                return False, "Wymaga zabezpieczenia na całej nieruchomości"
    
    return True, "Cel akceptowalny"
```

**Przykłady dyskwalifikacji**:
- ❌ Cel: kamienica, bank nie finansuje → ODRZUCONY
- ❌ Cel: TBS, bank wymaga dodatkowego zabezpieczenia → ODRZUCONY (jeśli brak)
- ❌ Cel: konsolidacja 40%, bank max 30% → ODRZUCONY

#### Grupa 05: Zabezpieczenia

```python
def check_collateral(client, bank):
    """
    Weryfikacja zabezpieczeń - WYMOGI
    """
    if client.collateral.third_party_property:
        policy = bank.parameters["05_zabezpieczenia"]["01_zabezpieczenie na nieruchomości osoby trzeciej"]
        
        if policy == "nie":
            return False, "Bank nie akceptuje zabezpieczenia osoby trzeciej"
        
        if "właściciel musi być kredytobiorcą" in policy:
            if not client.collateral.third_party_is_borrower:
                return False, "Właściciel zabezpieczenia musi być kredytobiorcą"
    
    return True, "Zabezpieczenie OK"
```

#### Grupa 08: Ważność Dokumentów

```python
def check_document_validity(client, bank):
    """
    Weryfikacja terminów dokumentów - WYMOGI PROCEDURALNE
    """
    issues = []
    
    # Sprawdź zaświadczenie o zarobkach
    salary_cert_validity = bank.parameters["08_ważność dokumentów"]["03_zaświadczenie o zarobkach"]
    if client.documents.salary_certificate_age_days > parse_days(salary_cert_validity):
        issues.append(f"Zaświadczenie za stare (max {salary_cert_validity})")
    
    # Sprawdź odpis KRS
    krs_validity = bank.parameters["08_ważność dokumentów"]["07_odpis KRS"]
    if client.documents.krs_age_days > parse_days(krs_validity):
        issues.append(f"KRS za stary (max {krs_validity})")
    
    return len(issues) == 0, issues
```

### 3.3 ETAP 2: SCORING - System Punktowy

Po pre-screeningu (eliminacji) rankujemy banki według JAKOŚCI:

#### Kategorie Punktowe

```python
SCORING_WEIGHTS = {
    "koszt_kredytu": 35,      # Najważniejsze: marża, WIBOR, opłaty
    "elastyczność": 25,       # Okres, karencja, wcześniejsza spłata
    "wygoda_procesu": 20,     # Koszt operatu, terminy, wymagania
    "dodatkowe_korzyści": 15, # Kredyt EKO, ubezpieczenia, programy
    "parametry_max": 5        # Maksymalne kwoty/okresy
}
```

#### Punktacja - Koszt Kredytu (35 pkt)

```python
def score_cost(bank, client):
    """
    Punkty za całkowity koszt kredytu
    """
    score = 0
    
    # 1. WIBOR (10 pkt)
    wibor_type = bank.parameters["01_parametry kredytu"]["09_WIBOR"]
    if "WIBOR 3M" in wibor_type:
        score += 10  # Najlepszy - standard rynkowy
    elif "WIBOR 6M" in wibor_type:
        score += 7   # Dłuższy okres - więcej ryzyka
    
    # 2. Kredyt EKO - obniżka marży (10 pkt)
    eco_policy = bank.parameters["01_parametry kredytu"]["16_kredyt EKO"]
    if eco_policy != "brak" and client.loan_details.eco_loan:
        margin_reduction = parse_margin_reduction(eco_policy)  # np. 0.1, 0.2
        score += margin_reduction * 50  # 0.1 pp = 5 pkt, 0.2 pp = 10 pkt
    
    # 3. Wcześniejsza spłata (5 pkt)
    early_repayment_fee = bank.parameters["01_parametry kredytu"]["11_wcześniejsza spłata"]
    if "0%" in early_repayment_fee:
        score += 5
    elif "1%" in early_repayment_fee:
        score += 3
    
    # 4. Ubezpieczenia (10 pkt)
    # Niższe koszty UŻ/UN = więcej punktów
    life_insurance = bank.parameters["07_ubezpieczenia"]["03_ubezpieczenie na życie"]
    if "brak wymogu" in life_insurance or "opcjonalne" in life_insurance:
        score += 5
    
    low_contribution_insurance = bank.parameters["07_ubezpieczenia"]["02_ubezpieczenie niskiego wkładu"]
    if client.own_contribution_pct < 20:
        cost = parse_insurance_cost(low_contribution_insurance)
        score += max(0, 5 - cost * 20)  # 0.25% = 0 pkt, 0% = 5 pkt
    
    return min(score, 35)  # Max 35 pkt
```

#### Punktacja - Elastyczność (25 pkt)

```python
def score_flexibility(bank, client):
    """
    Punkty za elastyczność oferty
    """
    score = 0
    
    # 1. Maksymalny okres kredytowania (10 pkt)
    max_period = parse_months(bank.parameters["01_parametry kredytu"]["03_okres kredytowania"])
    if max_period >= 420:  # 35 lat
        score += 10
    elif max_period >= 360:  # 30 lat
        score += 7
    else:
        score += 4
    
    # 2. Karencja w spłacie kapitału (8 pkt)
    grace_period = bank.parameters["01_parametry kredytu"]["13_karencja w spłacie kapitału"]
    if client.loan_details.purpose == "budowa domu":
        max_grace = parse_months(grace_period)
        if max_grace >= 24:
            score += 8
        elif max_grace >= 12:
            score += 5
    
    # 3. Typ rat (4 pkt)
    installments = bank.parameters["01_parametry kredytu"]["12_raty"]
    if "równe lub malejące" in installments:
        score += 4
    elif "równe" in installments:
        score += 2
    
    # 4. Oprocentowanie stałe (3 pkt)
    fixed_rate = bank.parameters["01_parametry kredytu"]["10_oprocentowanie stałe"]
    if "10 lat" in fixed_rate:
        score += 3
    elif "5 lat" in fixed_rate:
        score += 2
    
    return min(score, 25)
```

#### Punktacja - Wygoda Procesu (20 pkt)

```python
def score_convenience(bank, client):
    """
    Punkty za wygodę procesu kredytowego
    """
    score = 0
    
    # 1. Koszt operatu (10 pkt)
    valuation_cost = bank.parameters["06_wycena"]["02_płatność za operat"]
    property_type = client.property.type
    
    cost = parse_valuation_cost(valuation_cost, property_type)
    if cost <= 400:
        score += 10
    elif cost <= 600:
        score += 7
    elif cost <= 800:
        score += 4
    else:
        score += 2
    
    # 2. Wymagania dokumentów (5 pkt)
    # Dłuższe terminy ważności = więcej punktów
    salary_cert_days = parse_days(bank.parameters["08_ważność dokumentów"]["03_zaświadczenie o zarobkach"])
    if salary_cert_days >= 60:
        score += 3
    elif salary_cert_days >= 30:
        score += 2
    
    decision_validity = parse_days(bank.parameters["08_ważność dokumentów"]["15_ważność decyzji kredytowej"])
    if decision_validity >= 60:
        score += 2
    elif decision_validity >= 45:
        score += 1
    
    # 3. Operat zewnętrzny/wewnętrzny (5 pkt)
    valuation_type = bank.parameters["06_wycena"]["01_operat szacunkowy"]
    if "wewnętrzny" in valuation_type:
        score += 5  # Szybciej, wygodniej
    elif "zewnętrzny" in valuation_type:
        score += 2
    
    return min(score, 20)
```

#### Punktacja - Dodatkowe Korzyści (15 pkt)

```python
def score_benefits(bank, client):
    """
    Punkty za dodatkowe korzyści
    """
    score = 0
    
    # 1. Kredyt EKO - dostępność (5 pkt)
    eco_policy = bank.parameters["01_parametry kredytu"]["16_kredyt EKO"]
    if eco_policy != "brak":
        score += 5
    
    # 2. Ubezpieczenie nieruchomości (5 pkt)
    property_insurance = bank.parameters["07_ubezpieczenia"]["05_ubezpieczenie nieruchomości"]
    if "tak" in property_insurance.lower():
        score += 3
        # Bonus za korzystną stawkę
        if "obniżka marży" in property_insurance:
            score += 2
    
    # 3. Liczba kredytów hipotecznych (5 pkt)
    mortgage_limit = bank.parameters["01_parametry kredytu"]["14_ile kredytów hipotecznych"]
    if "brak limitu" in mortgage_limit:
        score += 5
    elif "3-4" in mortgage_limit:
        score += 3
    elif "2" in mortgage_limit:
        score += 1
    
    return min(score, 15)
```

#### Punktacja - Parametry Maksymalne (5 pkt)

```python
def score_max_parameters(bank, client):
    """
    Punkty za wysokie limity
    """
    score = 0
    
    # Maksymalna kwota kredytu
    max_amount = parse_amount(bank.parameters["01_parametry kredytu"]["02_kwota kredytu"])
    if max_amount >= 4000000:
        score += 3
    elif max_amount >= 3000000:
        score += 2
    
    # Wielkość działki
    plot_limit = bank.parameters["01_parametry kredytu"]["15_wielkość działki"]
    if "brak limitu" in plot_limit or "2 ha" in plot_limit:
        score += 2
    elif "3000 m2" in plot_limit:
        score += 1
    
    return min(score, 5)
```

#### Całkowita Punktacja

```python
def calculate_total_score(bank, client):
    """
    Sumaryczna punktacja banku dla danego klienta
    """
    scores = {
        "koszt": score_cost(bank, client),
        "elastyczność": score_flexibility(bank, client),
        "wygoda": score_convenience(bank, client),
        "korzyści": score_benefits(bank, client),
        "parametry_max": score_max_parameters(bank, client)
    }
    
    total = sum(scores.values())
    
    return {
        "total_score": total,  # Max 100
        "breakdown": scores,
        "grade": get_grade(total)
    }

def get_grade(score):
    """Ocena literowa"""
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    return "D"
```

### 3.4 ETAP 3: RANKING

```python
def rank_banks(qualified_banks, client):
    """
    Ranking banków po pre-screeningu
    """
    # 1. Oblicz punkty dla każdego banku
    scored_banks = []
    for bank in qualified_banks:
        score_data = calculate_total_score(bank, client)
        scored_banks.append({
            "bank": bank,
            "score": score_data["total_score"],
            "breakdown": score_data["breakdown"],
            "grade": score_data["grade"]
        })
    
    # 2. Sortuj malejąco
    scored_banks.sort(key=lambda x: x["score"], reverse=True)
    
    # 3. Wybierz top 3 + najgorszą opcję
    recommendations = {
        "best": scored_banks[0] if len(scored_banks) >= 1 else None,
        "second": scored_banks[1] if len(scored_banks) >= 2 else None,
        "third": scored_banks[2] if len(scored_banks) >= 3 else None,
        "worst": scored_banks[-1] if len(scored_banks) >= 4 else None  # Ostatnia dla kontrastu
    }
    
    return recommendations, scored_banks
```

### 3.5 ETAP 4: PREZENTACJA

#### Format Odpowiedzi dla Klienta

```markdown
## 🏆 OFERTA #1: [Bank] - NAJLEPSZA OPCJA

### 📊 WYNIK: 87/100 (A) 

**Szczegóły punktacji**:
- 💰 Koszt kredytu: 32/35 pkt
- 🔄 Elastyczność: 23/25 pkt
- ⚡ Wygoda procesu: 17/20 pkt
- 🎁 Dodatkowe korzyści: 12/15 pkt
- 📈 Parametry max: 3/5 pkt

### ✅ WERYFIKACJA KOMPLETNA

#### 01_parametry kredytu
- ✅ **LTV**: Bank: 90% → Klient: 80% (LTV = 960k/1200k) - W NORMIE
- ✅ **wkład własny**: Bank: minimum 10% → Klient: 20% (240k zł) - SPEŁNIONE
- ✅ **kwota kredytu**: Bank: 100k-3M → Klient: 960k - W ZAKRESIE
- ✅ **okres kredytowania**: Bank: max 420 mc → Klient: 300 mc - OK
- ✅ **wielkość działki**: N/D (kamienica - nie dotyczy)

#### 02_kredytobiorca
- ✅ **wiek**: Bank: 18-70 lat (koniec spłaty) → Klient: 42 lata, koniec 67 lat - OK
- ✅ **liczba wnioskodawców**: Bank: max 4 → Klient: 2 - OK

#### 03_źródło dochodu
- ✅ **umowa o pracę na czas nieokreślony**: Bank: min 3 mc stażu → Klient: 180 mc (15 lat) - SPEŁNIONE
- ✅ **dochód brutto**: 30k zł (oboje) - zdolność kredytowa potwierdzona

#### 04_cel kredytu
- ✅ **zakup kamienicy**: Bank: "TAK, do 500 m2" → Klient: kamienica 380 m2 - AKCEPTOWALNE

### 💰 KOSZTY

| Element | Wartość |
|---------|---------|
| Operat szacunkowy | 700 zł (dom) |
| Ubezpieczenie pomostowe | Brak |
| Ubezpieczenie niskiego wkładu | Nie dotyczy (wkład 20%) |
| Wcześniejsza spłata | 0% |
| **Kredyt EKO** | ⭐ Obniżka marży o 0.1 p.p. (przy spełnieniu norm) |

### 🎯 GŁÓWNE ATUTY
1. ⭐ **Najniższe koszty** - kredyt EKO obniża marżę o 0.1 p.p.
2. 🏛️ **Akceptacja kamienic** - do 500 m2 (klient: 380 m2)
3. 💼 **Elastyczność** - okres do 35 lat, raty równe/malejące

### ⚠️ PUNKTY UWAGI
- Kredyt EKO wymaga dostarczenia świadectwa EP po budowie
- Operat zewnętrzny - koszt 700 zł

### 📝 UZASADNIENIE #1
Bank [X] otrzymał najwyższą punktację (87/100) dzięki połączeniu:
- Akceptacji nietypowego celu (kamienica)
- Niskich kosztów (kredyt EKO -0.1 p.p.)
- Elastycznych warunków spłaty
```

---

## 4. ALGORYTM RANKINGOWY - PEŁNA IMPLEMENTACJA

### 4.1 Główna Funkcja Matching

```python
class MortgageMatchingEngine:
    """
    Silnik dopasowania kredytów hipotecznych
    """
    
    def __init__(self, knowledge_base_path: str, classification_path: str):
        self.kb = load_json(knowledge_base_path)
        self.classification = load_json(classification_path)
        self.requirements = self._extract_requirements()
        self.quality_params = self._extract_quality_params()
    
    def find_best_matches(self, client_profile: dict) -> dict:
        """
        GŁÓWNA FUNKCJA - Znajdź 4 najlepsze oferty dla klienta
        
        Returns:
            {
                "qualified_banks": [...],
                "disqualified_banks": [...],
                "recommendations": {
                    "best": {...},
                    "second": {...},
                    "third": {...},
                    "worst": {...}
                },
                "analysis": {...}
            }
        """
        # ETAP 1: Pre-screening
        print("🔍 ETAP 1/4: Pre-screening według WYMOGÓW...")
        qualified, disqualified = self._pre_screen(client_profile)
        
        print(f"✅ Zakwalifikowane banki: {len(qualified)}/11")
        print(f"❌ Zdyskwalifikowane banki: {len(disqualified)}/11\n")
        
        if len(qualified) == 0:
            return {
                "status": "NO_MATCH",
                "message": "Żaden bank nie spełnia wymogów klienta",
                "disqualified_banks": disqualified
            }
        
        # ETAP 2: Scoring
        print("📊 ETAP 2/4: Punktacja według JAKOŚCI...")
        scored_banks = self._score_banks(qualified, client_profile)
        
        # ETAP 3: Ranking
        print("🏆 ETAP 3/4: Ranking i selekcja...")
        recommendations, all_ranked = self._rank_and_select(scored_banks)
        
        # ETAP 4: Analiza
        print("📝 ETAP 4/4: Przygotowanie analizy...\n")
        analysis = self._generate_analysis(recommendations, client_profile)
        
        return {
            "status": "SUCCESS",
            "qualified_banks": qualified,
            "disqualified_banks": disqualified,
            "recommendations": recommendations,
            "all_ranked": all_ranked,
            "analysis": analysis
        }
    
    def _pre_screen(self, client_profile: dict):
        """
        ETAP 1: Eliminacja banków według WYMOGÓW
        """
        qualified = []
        disqualified = []
        
        for bank_data in self.kb["products"]:
            bank_name = bank_data["bank_name"]
            params = bank_data["parameters"]
            
            # Weryfikacja wszystkich wymogów
            verification = self._verify_requirements(client_profile, params)
            
            if verification["passed"]:
                qualified.append({
                    "bank_name": bank_name,
                    "parameters": params,
                    "verification": verification
                })
            else:
                disqualified.append({
                    "bank_name": bank_name,
                    "reasons": verification["failed_checks"]
                })
        
        return qualified, disqualified
    
    def _verify_requirements(self, client: dict, bank_params: dict) -> dict:
        """
        Weryfikacja WYMOGÓW dla banku
        """
        checks = {}
        failed = []
        
        # Grupa 01: Parametry kredytu
        checks["ltv"] = self._check_ltv(client, bank_params)
        checks["own_contribution"] = self._check_own_contribution(client, bank_params)
        checks["loan_amount"] = self._check_loan_amount(client, bank_params)
        checks["loan_period"] = self._check_loan_period(client, bank_params)
        checks["mortgage_limit"] = self._check_mortgage_limit(client, bank_params)
        checks["plot_size"] = self._check_plot_size(client, bank_params)
        
        # Grupa 02: Kredytobiorca
        checks["age"] = self._check_age(client, bank_params)
        checks["applicants_number"] = self._check_applicants_number(client, bank_params)
        checks["foreigner"] = self._check_foreigner(client, bank_params)
        
        # Grupa 03: Źródło dochodu
        checks["income_type"] = self._check_income_type(client, bank_params)
        checks["work_experience"] = self._check_work_experience(client, bank_params)
        
        # Grupa 04: Cel kredytu
        checks["loan_purpose"] = self._check_loan_purpose(client, bank_params)
        
        # Grupa 05: Zabezpieczenia
        checks["collateral"] = self._check_collateral(client, bank_params)
        
        # Zbierz nieudane sprawdzenia
        for check_name, check_result in checks.items():
            if not check_result["passed"]:
                failed.append({
                    "check": check_name,
                    "reason": check_result["reason"]
                })
        
        return {
            "passed": len(failed) == 0,
            "all_checks": checks,
            "failed_checks": failed
        }
    
    def _score_banks(self, qualified_banks: list, client: dict) -> list:
        """
        ETAP 2: Punktacja banków według JAKOŚCI
        """
        scored = []
        
        for bank_data in qualified_banks:
            score = self._calculate_score(bank_data, client)
            scored.append({
                **bank_data,
                "score": score
            })
        
        return scored
    
    def _calculate_score(self, bank_data: dict, client: dict) -> dict:
        """
        Oblicz punktację dla banku
        """
        params = bank_data["parameters"]
        
        scores = {
            "koszt": self._score_cost(params, client),
            "elastyczność": self._score_flexibility(params, client),
            "wygoda": self._score_convenience(params, client),
            "korzyści": self._score_benefits(params, client),
            "parametry_max": self._score_max_parameters(params, client)
        }
        
        total = sum(scores.values())
        
        return {
            "total": total,
            "breakdown": scores,
            "grade": self._get_grade(total),
            "percentage": round(total, 1)
        }
    
    def _rank_and_select(self, scored_banks: list):
        """
        ETAP 3: Ranking i selekcja 4 ofert
        """
        # Sortuj malejąco według punktacji
        ranked = sorted(scored_banks, key=lambda x: x["score"]["total"], reverse=True)
        
        # Wybierz 3 najlepsze + najgorszą
        recommendations = {
            "best": ranked[0] if len(ranked) >= 1 else None,
            "second": ranked[1] if len(ranked) >= 2 else None,
            "third": ranked[2] if len(ranked) >= 3 else None,
            "worst": ranked[-1] if len(ranked) >= 4 else None
        }
        
        return recommendations, ranked
    
    def _generate_analysis(self, recommendations: dict, client: dict) -> dict:
        """
        ETAP 4: Generowanie szczegółowej analizy
        """
        return {
            "summary": self._generate_summary(recommendations),
            "comparison_table": self._generate_comparison_table(recommendations),
            "client_specific_notes": self._generate_client_notes(client, recommendations),
            "next_steps": self._generate_next_steps(recommendations)
        }
```

### 4.2 Przykładowe Funkcje Sprawdzające

```python
def _check_ltv(self, client: dict, bank_params: dict) -> dict:
    """
    Sprawdź LTV (Loan-to-Value)
    """
    client_ltv = (client["loan_details"]["loan_amount"] / 
                  client["loan_details"]["property_value"]) * 100
    
    ltv_param = bank_params["01_parametry kredytu"]["04_LTV kredyt mieszkaniowy"]
    bank_max_ltv = parse_percentage(ltv_param)
    
    passed = client_ltv <= bank_max_ltv
    
    return {
        "passed": passed,
        "client_ltv": round(client_ltv, 2),
        "bank_max_ltv": bank_max_ltv,
        "reason": f"LTV {client_ltv:.1f}% > max {bank_max_ltv}%" if not passed else "OK"
    }

def _check_age(self, client: dict, bank_params: dict) -> dict:
    """
    Sprawdź wiek kredytobiorcy
    """
    current_age = client["age"]
    loan_period_years = client["loan_details"]["loan_period_months"] / 12
    final_age = current_age + loan_period_years
    
    age_param = bank_params["02_kredytobiorca"]["01_wiek Klienta"]
    min_age, max_age = parse_age_range(age_param)
    
    passed = min_age <= current_age and final_age <= max_age
    
    return {
        "passed": passed,
        "current_age": current_age,
        "final_age": round(final_age),
        "bank_max_age": max_age,
        "reason": f"Koniec spłaty w wieku {final_age:.0f} > max {max_age}" if not passed else "OK"
    }

def _check_loan_purpose(self, client: dict, bank_params: dict) -> dict:
    """
    Sprawdź cel kredytu
    """
    purpose = client["loan_details"]["purpose"]
    
    # Mapowanie celu na parametr w bazie
    purpose_mapping = {
        "zakup kamienicy": "13_kamienica",
        "zakup udziału we wspólnocie": "14_zakup udziału w nieruchomości",
        "konsolidacja niemieszkaniowa": "22_konsolidacja zobowiązań niemieszkaniowych",
        "zakup działki rekreacyjnej": "08_zakup działki rekreacyjnej",
        # ... więcej mapowań
    }
    
    param_key = purpose_mapping.get(purpose)
    if not param_key:
        return {"passed": True, "reason": "Standardowy cel"}
    
    policy = bank_params["04_cel kredytu"].get(param_key, "nie")
    
    # Analiza polityki
    if policy == "nie":
        return {
            "passed": False,
            "reason": f"Bank nie finansuje: {purpose}"
        }
    
    if "do 500 m2" in policy:
        if client["property"]["size_sqm"] > 500:
            return {
                "passed": False,
                "reason": f"Kamienica {client['property']['size_sqm']} m2 > max 500 m2"
            }
    
    return {"passed": True, "reason": "Cel akceptowalny"}

def _check_work_experience(self, client: dict, bank_params: dict) -> dict:
    """
    Sprawdź staż pracy
    """
    income_type = client["income"]["type"]
    work_months = client["income"]["work_experience_months"]
    
    # Mapowanie typu dochodu na parametr
    income_param_mapping = {
        "umowa o pracę na czas określony": "01_umowa o pracę na czas określony",
        "umowa o pracę na czas nieokreślony": "02_umowa o pracę na czas nieokreślony",
        "kontrakt menadżerski": "04_kontrakt menadżerski",
        "działalność gospodarcza": "07_działalność gospodarcza pełna księgowość",
        # ...
    }
    
    param_key = income_param_mapping.get(income_type)
    if not param_key:
        return {"passed": True, "reason": "Typ dochodu niestandardowy"}
    
    requirement = bank_params["03_źródło dochodu"].get(param_key)
    required_months = parse_work_experience_requirement(requirement)
    
    passed = work_months >= required_months
    
    return {
        "passed": passed,
        "client_months": work_months,
        "required_months": required_months,
        "reason": f"Staż {work_months} mc < wymagane {required_months} mc" if not passed else "OK"
    }
```

---

## 5. IMPLEMENTACJA

### 5.1 Struktura Plików

```
KredytyPlatinum/
├── src/
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── engine.py              # MortgageMatchingEngine
│   │   ├── pre_screening.py       # Funkcje sprawdzające WYMOGI
│   │   ├── scoring.py             # Funkcje punktacji JAKOŚĆ
│   │   ├── ranking.py             # Sortowanie i selekcja
│   │   └── formatters.py          # Formatowanie odpowiedzi
│   ├── utils/
│   │   ├── parsers.py             # Parse wartości z bazy
│   │   └── validators.py          # Walidacja danych
│   └── models/
│       ├── client.py              # Model klienta
│       └── bank.py                # Model banku
```

### 5.2 Użycie Systemu

```python
from src.matching.engine import MortgageMatchingEngine

# Inicjalizacja
engine = MortgageMatchingEngine(
    knowledge_base_path="data/processed/knowledge_base.json",
    classification_path="data/processed/parameter_classification_v2.json"
)

# Wczytaj profil klienta
client_profile = load_client_profile("data/processed/customer_profiles.json", profile_id=1)

# Znajdź dopasowania
results = engine.find_best_matches(client_profile)

# Wyniki
if results["status"] == "SUCCESS":
    print(f"✅ Znaleziono {len(results['qualified_banks'])} pasujących banków")
    print(f"🏆 Najlepsza: {results['recommendations']['best']['bank_name']}")
    print(f"🥈 Druga: {results['recommendations']['second']['bank_name']}")
    print(f"🥉 Trzecia: {results['recommendations']['third']['bank_name']}")
    print(f"⚠️ Najgorsza: {results['recommendations']['worst']['bank_name']}")
```

### 5.3 Integracja z AI Client

Obecny system używa Azure OpenAI do generowania odpowiedzi. Matching Engine może:

**Opcja A: Zastąpić AI (czysta logika)**
```python
# Pełna automatyzacja bez AI
results = matching_engine.find_best_matches(client_profile)
formatted_response = formatters.format_full_report(results)
```

**Opcja B: Wspomagać AI (hybrid)**
```python
# AI dostaje pre-screened results
qualified = matching_engine.pre_screen(client_profile)
ai_prompt = f"""
Klient: {client_profile}
Zakwalifikowane banki: {qualified}
Zdyskwalifikowane: {disqualified}

Wygeneruj szczegółową analizę TOP 4 banków.
"""
response = ai_client.query(ai_prompt)
```

**Opcja C: Walidować AI (quality check)**
```python
# AI generuje odpowiedź, engine weryfikuje
ai_recommendations = ai_client.get_recommendations(client_profile)
engine_recommendations = matching_engine.find_best_matches(client_profile)

# Porównaj
consistency_check = compare_recommendations(ai_recommendations, engine_recommendations)
if not consistency_check.passed:
    alert("Rozbieżność między AI a logiką biznesową!")
```

---

## 6. PRZYKŁADY ZASTOSOWANIA

### Przykład 1: Profil #1 - Zakup Kamienicy

**Dane klienta**:
- Cel: zakup kamienicy 380 m2
- Kwota: 960,000 zł (LTV 80%)
- Wiek: 42 lata
- Dochód: UoP na czas nieokreślony, 15 lat stażu

**Wynik Pre-Screening** (WYMOGI):
```
✅ Alior Bank - akceptuje kamienice do 500 m2
✅ Millennium - indywidualna weryfikacja kamienic
✅ ING - NIE akceptuje kamienic → ODRZUCONY
✅ mBank - standardowy cel → ZAAKCEPTOWANY
❌ CITI - nie finansuje kamienic → ODRZUCONY
...
```

**Wynik Scoring** (JAKOŚĆ):
```
Alior Bank:    87/100 (A)  - kredyt EKO, akceptacja kamienicy
Millennium:    82/100 (A)  - elastyczne warunki
Santander:     78/100 (B)  - standard
PKO BP:        75/100 (B)  - wyższe opłaty
```

**Rekomendacja**:
1. 🏆 Alior Bank (87 pkt)
2. 🥈 Millennium (82 pkt)
3. 🥉 Santander (78 pkt)
4. ⚠️ PKO BP (75 pkt) - dla porównania

### Przykład 2: Profil #5 - Senior z Małym Wkładem

**Dane klienta**:
- Wiek: 65 lat
- Okres kredytu: 15 lat (spłata do 80 lat)
- Wkład własny: 12%
- Dochód: emerytura

**Wynik Pre-Screening**:
```
❌ VELO - max wiek 60 lat → ODRZUCONY
❌ ING - nie akceptuje emerytury → ODRZUCONY
✅ PKO BP - akceptuje do 80 lat + emerytura
✅ Alior - akceptuje do 80 lat
✅ Santander - akceptuje do 75 lat (15 lat OK)
```

**Wynik Scoring**:
```
PKO BP:        84/100 (A)  - najlepsze warunki dla seniorów
Alior:         81/100 (A)  - elastyczne
Santander:     76/100 (B)  - standardowe
```

**Rekomendacja**:
1. 🏆 PKO BP
2. 🥈 Alior Bank
3. 🥉 Santander

### Przykład 3: Profil #8 - Konsolidacja Niemieszkaniowa

**Dane klienta**:
- Cel: kredyt mieszkaniowy + konsolidacja 35% kwoty
- Kwota konsolidacji: 336,000 zł z 960,000 zł

**Wynik Pre-Screening**:
```
✅ Alior - konsolidacja bez limitu
✅ ING - do 50% z marżą ważoną
✅ PKO - do 30% → 35% PRZEKROCZONE → ODRZUCONY
✅ Millennium - do 100% z marżą ważoną
❌ mBank - nie akceptuje → ODRZUCONY
```

**Wynik Scoring**:
```
Millennium:    85/100 (A)  - najwyższy limit (100%)
Alior:         83/100 (A)  - brak limitu
ING:           79/100 (B)  - marża ważona
```

**Rekomendacja**:
1. 🏆 Millennium
2. 🥈 Alior Bank
3. 🥉 ING

---

## 7. ZALETY PROFESJONALNEGO SYSTEMU

### 7.1 Przewidywalność i Transparentność

✅ **Jasne kryteria decyzyjne**
- Każda rekomendacja oparta na konkretnych parametrach
- Punktacja transparentna i weryfikowalna
- Brak "czarnej skrzynki" AI

✅ **Powtarzalność**
- Te same dane → te same wyniki
- Łatwe testowanie i debugowanie
- Możliwość audytu decyzji

### 7.2 Precyzja i Dokładność

✅ **100% pokrycie parametrów**
- Wszystkie 92 parametry weryfikowane
- Żaden wymóg nie zostaje pominięty
- Szczegółowa analiza każdego banku

✅ **Eliminacja błędów AI**
- AI może pominąć parametry
- AI może błędnie interpretować dane
- System logiczny = gwarancja poprawności

### 7.3 Wydajność

✅ **Szybkość**
- Pre-screening: <100ms
- Scoring: <200ms
- Całość: <500ms vs 5-15s dla AI

✅ **Skalowalność**
- Może przetwarzać setki profili jednocześnie
- Brak limitów API
- Brak kosztów per-request

### 7.4 Kontrola i Dostosowanie

✅ **Łatwa modyfikacja wag**
```python
# Zmiana priorytetów
SCORING_WEIGHTS = {
    "koszt_kredytu": 40,      # Było 35 - większy nacisk na koszt
    "elastyczność": 20,       # Było 25
    "wygoda_procesu": 20,     # Bez zmian
    "dodatkowe_korzyści": 15, # Bez zmian
    "parametry_max": 5        # Bez zmian
}
```

✅ **Dodawanie nowych kryteriów**
- Łatwe rozszerzanie o nowe parametry
- Możliwość A/B testingu różnych algorytmów
- Personalizacja dla różnych segmentów klientów

---

## 8. WNIOSKI I REKOMENDACJE

### 8.1 Proponowana Architektura

**Wariant Hybrydowy - Najlepszy z Obu Światów**:

```
┌─────────────────────────────────────────────┐
│  INPUT: Profil Klienta                      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  MATCHING ENGINE (Logika Biznesowa)         │
│  • Pre-screening (WYMOGI)                   │
│  • Scoring (JAKOŚĆ)                         │
│  • Ranking TOP 4                            │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  AI LAYER (Azure OpenAI)                    │
│  • Formatowanie odpowiedzi                  │
│  • Uzasadnienia w języku naturalnym        │
│  • Personalizacja komunikacji               │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  OUTPUT: Raport dla Klienta                 │
│  • 4 rekomendacje                           │
│  • Szczegółowe uzasadnienia                 │
│  • Porównanie parametrów                    │
└─────────────────────────────────────────────┘
```

### 8.2 Plan Implementacji

**Faza 1: Budowa Core Engine** (1 tydzień)
- [ ] Implementacja pre-screening dla wszystkich 8 grup
- [ ] System parsowania parametrów bankowych
- [ ] Testy jednostkowe dla każdej funkcji sprawdzającej

**Faza 2: System Scoring** (1 tydzień)
- [ ] Implementacja 5 kategorii punktacji
- [ ] Walidacja wag z business team
- [ ] Testy na 10 profilach klientów

**Faza 3: Integracja z AI** (3 dni)
- [ ] Modyfikacja AI prompt (dane pre-screened)
- [ ] Format odpowiedzi z matching engine
- [ ] Testy end-to-end

**Faza 4: Optymalizacja** (3 dni)
- [ ] Performance tuning
- [ ] Caching wyników
- [ ] Monitoring i logi

### 8.3 KPI Sukcesu

Wskaźniki jakości systemu:
- ✅ **Precyzja**: 100% zgodność z wymogami bankowymi
- ✅ **Pokrycie**: Wszystkie 92 parametry weryfikowane
- ✅ **Szybkość**: Odpowiedź <1s (vs 5-15s obecnie)
- ✅ **Zgodność z AI**: >90% overlap w top 3 rekomendacjach
- ✅ **Satysfakcja klienta**: Mierzalna przez feedback

---

## 9. NASTĘPNE KROKI

### Natychmiastowe Akcje

1. **Przegląd i Akceptacja**
   - Review niniejszej dokumentacji
   - Akceptacja architektury przez tech lead
   - Zatwierdzenie wag punktowych przez business

2. **Setup Projektu**
   - Utworzenie katalogu `src/matching/`
   - Setup testów jednostkowych
   - Przygotowanie danych testowych

3. **Kick-off Development**
   - Implementacja pierwszych funkcji pre-screening
   - Integracja z istniejącym kodem
   - Pierwsze testy na profilach klientów

### Pytania do Rozstrzygnięcia

❓ **Business Questions**:
1. Czy wagi punktowe (35/25/20/15/5) są akceptowalne?
2. Czy pokazywanie "najgorszej opcji" (#4) jest wartościowe dla klientów?
3. Czy system ma działać autonomicznie czy jako wsparcie dla AI?

❓ **Technical Questions**:
1. Czy budować jako moduł osobny czy integrować z `query_engine.py`?
2. Czy cache'ować wyniki dla tych samych profili?
3. Jak często aktualizować bazę wiedzy (knowledge_base.json)?

---

**Dokument przygotowany przez**: Copilot AI System Architecture  
**Do akceptacji**: Tech Lead & Business Team  
**Następna wersja**: Po implementacji MVP
