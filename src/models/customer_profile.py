"""
Model danych profilu kredytobiorcy
Predefinowana struktura do mapowania inputu użytkownika
"""
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum


# ============================================================================
# ENUMY - Predefiniowane wartości
# ============================================================================

class IncomeType(Enum):
    """Typ źródła dochodu"""
    UOP_CZAS_NIEOKRESLONY = "umowa_o_prace_czas_nieokreslony"
    UOP_CZAS_OKRESLONY = "umowa_o_prace_czas_okreslony"
    UOP_ZASTEPSTWO = "umowa_na_zastepstwo"
    KONTRAKT_MENEDZERSKI = "kontrakt_menedzerski"
    UMOWA_DZIELO = "umowa_o_dzielo"
    UMOWA_ZLECENIE = "umowa_zlecenie"
    DZIALALNOSC_PELNA_KSIEGOWOSC = "dzialalnosc_pelna_ksiegowosc"
    DZIALALNOSC_KPIR = "dzialalnosc_kpir"
    DZIALALNOSC_RYCZALT = "dzialalnosc_ryczalt"
    DZIALALNOSC_KARTA_PODATKOWA = "dzialalnosc_karta_podatkowa"
    DZIALALNOSC_ROLNICZA = "dzialalnosc_rolnicza"
    SAMOZATRUDNIENIE = "samozatrudnienie"
    DOCHODY_NAJMU = "dochody_z_najmu"
    EMERYTURA = "emerytura"
    RENTA = "renta"
    DYWIDENDY = "dywidendy"
    DIETY = "diety"
    DOCHOD_MARYNARZ = "dochody_marynarzy"
    URLOP_MACIERZYNSKI = "urlop_macierzynski"
    DOCHOD_OBCA_WALUTA = "dochod_w_obcej_walucie"
    POWOLANIE_SPOLKA = "powolanie_w_spolce"
    DODATEK_800_PLUS = "800_plus"


class LoanPurpose(Enum):
    """Cel kredytu"""
    ZAKUP_MIESZKANIA = "zakup_mieszkania_domu"
    BUDOWA_DOM_GOSPODARCZY = "budowa_domu_systemem_gospodarczym"
    BUDOWA_DOM_ZLECONY = "budowa_domu_systemem_zleconym"
    ZAKUP_DZIALKA_BUDOWLANA = "zakup_dzialki_budowlanej"
    ZAKUP_DZIALKA_ROLNA = "zakup_dzialki_rolnej_pod_zabudowe"
    ZAKUP_DZIALKA_REKREACYJNA = "zakup_dzialki_rekreacyjnej"
    ZAKUP_SIEDLISKO = "siedlisko"
    ZAKUP_DOM_LETNISKOWY = "zakup_domu_letniskowego"
    ZAKUP_LOKAL_UZYTKOWY = "zakup_lokalu_uzytkowego"
    ZAKUP_KAMIENICA = "zakup_kamienicy"
    ZAKUP_UDZIAL = "zakup_udzialu_w_nieruchomosci"
    EKSPEKTATYWA_CESJA = "ekspektatywa_cesja"
    REFINANSOWANIE_WYDATKOW = "refinansowanie_wydatkow"
    NIERUCHOMOSC_KOMERCJA = "nieruchomosc_z_komercja"
    REFINANSOWANIE_KREDYTU = "refinansowanie_kredytu"
    TRANSAKCJA_RODZINNA = "transakcja_rodzinna"
    TBS = "tbs"
    LOKAL_BUDOWA = "lokal_w_budynku_w_budowie"
    KONSOLIDACJA_NIEMIESZKANIOWA = "konsolidacja_niemieszkaniowa"
    CEL_DOWOLNY = "cel_dowolny"


class PropertyType(Enum):
    """Typ nieruchomości zabezpieczającej"""
    MIESZKANIE = "mieszkanie"
    DOM = "dom"
    DZIALKA_BUDOWLANA = "dzialka_budowlana"
    DZIALKA_ROLNA = "dzialka_rolna"
    DZIALKA_REKREACYJNA = "dzialka_rekreacyjna"
    LOKAL_UZYTKOWY = "lokal_uzytkowy"
    KAMIENICA = "kamienica"
    NIERUCHOMOSC_KOMERCYJNA = "nieruchomosc_z_komercja"
    SIEDLISKO = "siedlisko"
    DOM_LETNISKOWY = "dom_letniskowy"


class RelationshipStatus(Enum):
    """Status związku"""
    MALZENSTWO = "malzenstwo"
    ZWIAZEK_NIEFORMALNY = "zwiazek_nieformalny"
    SINGLE = "single"
    ROZDZIELNOSC_MAJATKOWA = "rozdzielnosc_majatkowa"


class Currency(Enum):
    """Waluta kredytu"""
    PLN = "PLN"
    EUR = "EUR"
    USD = "USD"
    CHF = "CHF"


# ============================================================================
# DATACLASSES - Struktura danych
# ============================================================================

@dataclass
class PersonData:
    """Dane pojedynczej osoby (kredytobiorca lub współkredytobiorca)"""
    # WYMAGANE
    age: Optional[int] = None  # Wiek w latach
    
    # Źródło dochodu
    income_type: Optional[IncomeType] = None
    income_amount_monthly: Optional[float] = None  # Dochód miesięczny netto (PLN)
    employment_duration_months: Optional[int] = None  # Staż pracy w miesiącach
    
    # OPCJONALNE
    is_polish_citizen: Optional[bool] = True  # Domyślnie obywatel Polski
    has_residence_card: Optional[bool] = None  # Karta pobytu (dla cudzoziemców)
    residence_card_type: Optional[str] = None  # "stały" / "czasowy"
    
    # Dodatkowe źródła dochodu
    additional_income_sources: List[Dict] = field(default_factory=list)  # [{"type": IncomeType, "amount": float}]
    
    # Inne
    is_property_owner: Optional[bool] = None  # Czy właściciel nieruchomości zabezpieczającej
    

@dataclass
class LoanParameters:
    """Parametry kredytu - KLUCZOWE DANE"""
    # WYMAGANE (minimum)
    loan_purpose: Optional[LoanPurpose] = None  # CEL KREDYTU
    property_value: Optional[float] = None  # Wartość nieruchomości (PLN)
    loan_amount: Optional[float] = None  # Kwota kredytu (PLN)
    
    # OPCJONALNE (ale ważne)
    down_payment: Optional[float] = None  # Wkład własny (PLN)
    down_payment_percent: Optional[float] = None  # Wkład własny (%)
    ltv: Optional[float] = None  # Loan-to-Value (%)
    
    loan_period_months: Optional[int] = None  # Okres kredytowania (miesiące)
    loan_period_years: Optional[int] = None  # Okres kredytowania (lata)
    
    currency: Optional[Currency] = Currency.PLN  # Waluta (domyślnie PLN)
    
    # Dodatkowe parametry
    grace_period_months: Optional[int] = None  # Karencja (miesiące)
    fixed_rate_period_years: Optional[int] = None  # Oprocentowanie stałe (lata)
    eco_friendly: Optional[bool] = None  # Kredyt EKO (energooszczędność)
    
    # Refinansowanie
    refinancing_period_months: Optional[int] = None  # Ile miesięcy wstecz refinansować
    existing_mortgage_count: Optional[int] = 0  # Liczba istniejących kredytów hipotecznych
    
    # Konsolidacja
    consolidation_amount: Optional[float] = None  # Kwota do konsolidacji (PLN)


@dataclass
class PropertyData:
    """Dane nieruchomości zabezpieczającej"""
    # OPCJONALNE
    property_type: Optional[PropertyType] = None
    property_location: Optional[str] = None  # Miasto/województwo
    property_area_sqm: Optional[float] = None  # Powierzchnia (m2)
    
    # Specyficzne dla działek
    plot_area_sqm: Optional[float] = None  # Powierzchnia działki (m2)
    
    # Specyficzne dla budowy
    construction_cost_per_sqm: Optional[float] = None  # Koszt budowy za m2
    has_building_permit: Optional[bool] = None  # Pozwolenie na budowę
    
    # Specyficzne dla komercji
    commercial_space_percent: Optional[float] = None  # % powierzchni komercyjnej
    
    # Lokalizacja
    is_city_above_100k: Optional[bool] = None  # Miasto >100k mieszkańców
    
    # Własność
    is_family_transaction: Optional[bool] = None  # Transakcja rodzinna
    is_shared_ownership: Optional[bool] = None  # Zakup udziału
    ownership_percent: Optional[float] = None  # % udziału
    
    # Zabezpieczenie
    is_third_party_collateral: Optional[bool] = None  # Zabezpieczenie osoby trzeciej
    plot_as_down_payment: Optional[bool] = None  # Działka jako wkład własny


@dataclass
class CustomerProfile:
    """
    Pełny profil kredytobiorcy - predefinowany model danych
    
    WYMAGANE MINIMUM (do przeprowadzenia analizy):
    - borrower.age
    - borrower.income_type
    - borrower.employment_duration_months
    - loan.loan_purpose
    - loan.property_value OR loan.loan_amount
    """
    
    # OSOBY (1-4 kredytobiorców)
    borrower: PersonData = field(default_factory=PersonData)  # Główny kredytobiorca
    co_borrower: Optional[PersonData] = None  # Współkredytobiorca
    additional_borrowers: List[PersonData] = field(default_factory=list)  # Dodatkowi (max 2)
    
    # RELACJE
    relationship_status: Optional[RelationshipStatus] = None
    
    # PARAMETRY KREDYTU
    loan: LoanParameters = field(default_factory=LoanParameters)
    
    # NIERUCHOMOŚĆ
    property: PropertyData = field(default_factory=PropertyData)
    
    # METADANE
    raw_input: Optional[str] = None  # Oryginalny input użytkownika
    
    def to_dict(self) -> Dict:
        """Konwertuje profil do słownika (dla JSON)"""
        def convert_enum(obj):
            if isinstance(obj, Enum):
                return obj.value
            return obj
        
        data = asdict(self)
        
        # Konwertuj enumy na stringi
        def process_dict(d):
            for key, value in d.items():
                if isinstance(value, Enum):
                    d[key] = value.value
                elif isinstance(value, dict):
                    process_dict(value)
                elif isinstance(value, list):
                    d[key] = [process_dict(item) if isinstance(item, dict) else convert_enum(item) for item in value]
            return d
        
        return process_dict(data)
    
    def get_required_fields_status(self) -> Dict[str, bool]:
        """Sprawdza które wymagane pola są wypełnione"""
        return {
            "borrower_age": self.borrower.age is not None,
            "borrower_income_type": self.borrower.income_type is not None,
            "borrower_employment_duration": self.borrower.employment_duration_months is not None,
            "loan_purpose": self.loan.loan_purpose is not None,
            "loan_value": (self.loan.property_value is not None) or (self.loan.loan_amount is not None)
        }
    
    def is_complete(self) -> bool:
        """Czy profil zawiera minimum wymaganych danych do analizy"""
        required = self.get_required_fields_status()
        return all(required.values())
    
    def get_missing_required_fields(self) -> List[str]:
        """Zwraca listę brakujących wymaganych pól"""
        required = self.get_required_fields_status()
        return [field for field, filled in required.items() if not filled]
    
    def calculate_ltv(self):
        """Oblicza LTV jeśli brakuje"""
        if self.loan.ltv is None and self.loan.loan_amount and self.loan.property_value:
            self.loan.ltv = (self.loan.loan_amount / self.loan.property_value) * 100
        
        if self.loan.down_payment_percent is None and self.loan.ltv:
            self.loan.down_payment_percent = 100 - self.loan.ltv
        
        if self.loan.down_payment is None and self.loan.property_value and self.loan.down_payment_percent:
            self.loan.down_payment = self.loan.property_value * (self.loan.down_payment_percent / 100)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_empty_profile() -> CustomerProfile:
    """Zwraca pusty profil klienta"""
    return CustomerProfile()


def validate_profile(profile: CustomerProfile) -> tuple[bool, List[str]]:
    """
    Waliduje profil klienta
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    # Sprawdź wymagane pola
    if not profile.is_complete():
        missing = profile.get_missing_required_fields()
        errors.append(f"Brakujące wymagane pola: {', '.join(missing)}")
    
    # Walidacja wartości
    if profile.borrower.age is not None:
        if profile.borrower.age < 18 or profile.borrower.age > 100:
            errors.append("Wiek musi być w przedziale 18-100 lat")
    
    if profile.loan.ltv is not None:
        if profile.loan.ltv < 0 or profile.loan.ltv > 100:
            errors.append("LTV musi być w przedziale 0-100%")
    
    if profile.loan.loan_amount is not None and profile.loan.loan_amount <= 0:
        errors.append("Kwota kredytu musi być większa od 0")
    
    # Oblicz LTV jeśli możliwe
    profile.calculate_ltv()
    
    return (len(errors) == 0, errors)


# ============================================================================
# TEMPLATE - Opis wszystkich możliwych parametrów
# ============================================================================

CUSTOMER_PROFILE_TEMPLATE = """
# 📋 SZABLON PROFILU KREDYTOBIORCY - KOMPLETNY PRZEWODNIK

Poniżej znajdziesz WSZYSTKIE informacje, które możesz podać w profilu kredytobiorcy.
Pola oznaczone ⚠️ **WYMAGANE** są niezbędne do przeprowadzenia analizy.
Pozostałe pola są opcjonalne - podaj tylko te, które dotyczą Twojej sytuacji.

---

## 👤 KREDYTOBIORCA (Główny)

### ⚠️ **WYMAGANE:**
- **Wiek**: [liczba lat, np. 45]
- **Typ dochodu**: [wybierz z listy poniżej]
- **Staż pracy**: [liczba miesięcy, np. 60 dla 5 lat]

### 📊 TYPY DOCHODU (wybierz jeden lub więcej):
- Umowa o pracę na czas nieokreślony
- Umowa o pracę na czas określony
- Umowa na zastępstwo
- Kontrakt menadżerski
- Umowa o dzieło
- Umowa zlecenie
- Działalność gospodarcza - pełna księgowość
- Działalność gospodarcza - KPiR
- Działalność gospodarcza - ryczałt
- Działalność gospodarcza - karta podatkowa
- Działalność rolnicza
- Samozatrudnienie
- Dochody z najmu
- Emerytura
- Renta
- Dywidendy
- Diety
- Dochody marynarzy
- Urlop macierzyński
- Dochód w obcej walucie
- Powołanie w spółce
- 800 plus

### 💰 OPCJONALNE (dochody):
- **Dochód miesięczny netto**: [kwota w PLN, np. 8000]
- **Dodatkowe źródła dochodu**: [lista z typem i kwotą]

### 🌍 OPCJONALNE (obywatelstwo):
- **Obywatelstwo**: [polskie / cudzoziemiec]
- **Karta pobytu**: [tak/nie, jeśli cudzoziemiec]
- **Typ karty pobytu**: [stały / czasowy]

### 🏠 OPCJONALNE (inne):
- **Właściciel nieruchomości zabezpieczającej**: [tak/nie]

---

## 👥 WSPÓŁKREDYTOBIORCA (Opcjonalnie)

Jeśli kredyt będzie brany wspólnie, podaj te same informacje co dla głównego kredytobiorcy:
- Wiek
- Typ dochodu
- Staż pracy
- Dochód miesięczny netto
- [wszystkie pozostałe pola jak wyżej]

### 💑 STATUS ZWIĄZKU:
- Małżeństwo
- Związek nieformalny
- Single
- Rozdzielność majątkowa

---

## 💳 PARAMETRY KREDYTU

### ⚠️ **WYMAGANE:**
- **Cel kredytu**: [wybierz z listy poniżej]
- **Wartość nieruchomości**: [kwota w PLN, np. 800000] LUB
- **Kwota kredytu**: [kwota w PLN, np. 640000]

### 🎯 CEL KREDYTU (wybierz jeden):
- Zakup mieszkania/domu
- Budowa domu systemem gospodarczym
- Budowa domu systemem zleconym
- Zakup działki budowlanej
- Zakup działki rolnej pod zabudowę
- Zakup działki rekreacyjnej
- Siedlisko
- Zakup domu letniskowego
- Zakup lokalu użytkowego
- Zakup kamienicy
- Zakup udziału w nieruchomości
- Ekspektatywa/cesja
- Refinansowanie wydatków
- Nieruchomość z komercją
- Refinansowanie kredytu
- Transakcja rodzinna
- TBS
- Lokal w budynku w budowie
- Konsolidacja niemieszkaniowa
- Cel dowolny (pożyczka hipoteczna)

### 💰 OPCJONALNE (parametry finansowe):
- **Wkład własny**: [kwota w PLN, np. 160000]
- **Wkład własny %**: [procent, np. 20]
- **LTV**: [procent Loan-to-Value, np. 80]
- **Okres kredytowania**: [miesiące lub lata, np. 300 miesięcy / 25 lat]
- **Waluta**: [PLN / EUR / USD / CHF]

### ⚙️ OPCJONALNE (dodatkowe):
- **Karencja**: [liczba miesięcy, np. 12]
- **Oprocentowanie stałe**: [liczba lat, np. 5]
- **Kredyt EKO**: [tak/nie - dom energooszczędny]
- **Liczba istniejących kredytów hipotecznych**: [liczba, np. 0]

### 🔄 OPCJONALNE (refinansowanie):
- **Refinansowanie - okres wstecz**: [liczba miesięcy, np. 12]

### 📊 OPCJONALNE (konsolidacja):
- **Kwota do konsolidacji**: [kwota w PLN]

---

## 🏡 NIERUCHOMOŚĆ

### 🏠 OPCJONALNE (podstawowe):
- **Typ nieruchomości**: 
  - Mieszkanie
  - Dom
  - Działka budowlana
  - Działka rolna
  - Działka rekreacyjna
  - Lokal użytkowy
  - Kamienica
  - Nieruchomość z komercją
  - Siedlisko
  - Dom letniskowy

- **Lokalizacja**: [miasto/województwo, np. "Warszawa"]
- **Powierzchnia**: [m2, np. 75]

### 📐 OPCJONALNE (działki):
- **Powierzchnia działki**: [m2, np. 1000]

### 🏗️ OPCJONALNE (budowa):
- **Koszt budowy za m2**: [kwota w PLN, np. 3500]
- **Pozwolenie na budowę**: [tak/nie]

### 🏢 OPCJONALNE (komercja):
- **Procent powierzchni komercyjnej**: [%, np. 30]

### 📍 OPCJONALNE (lokalizacja):
- **Miasto powyżej 100k mieszkańców**: [tak/nie]

### 👨‍👩‍👧 OPCJONALNE (własność):
- **Transakcja rodzinna**: [tak/nie]
- **Zakup udziału**: [tak/nie]
- **Procent udziału**: [%, np. 50]

### 🔒 OPCJONALNE (zabezpieczenie):
- **Zabezpieczenie na nieruchomości osoby trzeciej**: [tak/nie]
- **Działka jako wkład własny**: [tak/nie]

---

## ✅ PRZYKŁAD KOMPLETNEGO PROFILU (WYMAGANE MINIMUM):

```
Klient: Jan Kowalski, 45 lat
Dochód: Umowa o pracę na czas nieokreślony
Staż pracy: 5 lat (60 miesięcy)

CEL: Zakup mieszkania
Wartość mieszkania: 800,000 zł
Kwota kredytu: 640,000 zł
```

## ✅ PRZYKŁAD ROZSZERZONEGO PROFILU:

```
KREDYTOBIORCA:
- Imię: Jan Kowalski
- Wiek: 45 lat
- Dochód: Umowa o pracę na czas nieokreślony
- Dochód miesięczny netto: 8,000 zł
- Staż pracy: 5 lat (60 miesięcy)
- Obywatelstwo: polskie

WSPÓŁKREDYTOBIORCA:
- Imię: Anna Kowalska
- Wiek: 42 lata
- Dochód: Umowa o pracę na czas nieokreślony
- Dochód miesięczny netto: 6,000 zł
- Staż pracy: 3 lata (36 miesięcy)

STATUS: Małżeństwo

KREDYT:
- Cel: Zakup mieszkania na rynku wtórnym
- Wartość mieszkania: 800,000 zł
- Wkład własny: 160,000 zł (20%)
- Kwota kredytu: 640,000 zł
- LTV: 80%
- Okres: 25 lat (300 miesięcy)
- Waluta: PLN

NIERUCHOMOŚĆ:
- Typ: Mieszkanie
- Lokalizacja: Warszawa (miasto >100k)
- Powierzchnia: 75 m2

DODATKOWE:
- Kredyt EKO: tak (dom energooszczędny)
- Liczba istniejących kredytów hipotecznych: 0
```

---

## 📌 WSKAZÓWKI:

1. **Minimalne dane wymagane** (⚠️):
   - Wiek kredytobiorcy
   - Typ dochodu
   - Staż pracy
   - Cel kredytu
   - Wartość nieruchomości LUB kwota kredytu

2. **Im więcej danych podasz, tym dokładniejsza analiza**

3. **Pola opcjonalne** - podawaj tylko jeśli dotyczą Twojej sytuacji

4. **System automatycznie obliczy**:
   - LTV (jeśli podasz wartość nieruchomości i kwotę kredytu)
   - Wkład własny (jeśli podasz wartość i LTV)

5. **Możesz podać dane w dowolnej formie** - system AI zmapuje je do modelu
"""
