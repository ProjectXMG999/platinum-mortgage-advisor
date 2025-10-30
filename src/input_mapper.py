"""
Mapper inputu użytkownika na predefinowany model CustomerProfile
Wykorzystuje LLM do ekstrakcji i strukturyzacji danych
"""
import json
from typing import Dict, Tuple
from src.models.customer_profile import (
    CustomerProfile, PersonData, LoanParameters, PropertyData,
    IncomeType, LoanPurpose, PropertyType, RelationshipStatus, Currency,
    validate_profile, CUSTOMER_PROFILE_TEMPLATE
)


class InputMapper:
    """Mapuje surowy input użytkownika na strukturę CustomerProfile"""
    
    def __init__(self, ai_client):
        """
        Inicjalizacja mappera
        
        Args:
            ai_client: Instancja AIClient do komunikacji z LLM
        """
        self.ai_client = ai_client
    
    def create_mapping_prompt(self) -> str:
        """
        Tworzy prompt systemowy do mapowania inputu na model danych
        
        Returns:
            Prompt systemowy
        """
        return """Jesteś ekspertem ds. kredytów hipotecznych w Platinum Financial.

🎯 TWOJE ZADANIE: Ekstrakcja i strukturyzacja danych kredytobiorcy

Otrzymasz surowy input użytkownika (opis profilu kredytobiorcy w języku naturalnym).
Twoim zadaniem jest ZMAPOWANIE tych danych na predefinowany model JSON.

---

📋 MODEL DANYCH (struktura JSON do wypełnienia):

```json
{
  "borrower": {
    "age": null,  // WYMAGANE: liczba (wiek w latach)
    "income_type": null,  // WYMAGANE: string z listy (patrz INCOME_TYPES)
    "income_amount_monthly": null,  // float (dochód netto PLN)
    "employment_duration_months": null,  // WYMAGANE: liczba (staż w miesiącach)
    "is_polish_citizen": true,  // bool (domyślnie true)
    "has_residence_card": null,  // bool (tylko dla cudzoziemców)
    "residence_card_type": null,  // string: "stały" / "czasowy"
    "additional_income_sources": [],  // lista dodatkowych dochodów
    "is_property_owner": null  // bool
  },
  
  "co_borrower": null,  // Taka sama struktura jak "borrower" lub null
  
  "additional_borrowers": [],  // Lista (max 2) - taka sama struktura
  
  "relationship_status": null,  // string: "malzenstwo" / "zwiazek_nieformalny" / "single" / "rozdzielnosc_majatkowa"
  
  "loan": {
    "loan_purpose": null,  // WYMAGANE: string z listy (patrz LOAN_PURPOSES)
    "property_value": null,  // float (wartość nieruchomości PLN)
    "loan_amount": null,  // float (kwota kredytu PLN) - WYMAGANE jeśli brak property_value
    "down_payment": null,  // float (wkład własny PLN)
    "down_payment_percent": null,  // float (wkład własny %)
    "ltv": null,  // float (Loan-to-Value %)
    "loan_period_months": null,  // int (okres miesięcy)
    "loan_period_years": null,  // int (okres lata)
    "currency": "PLN",  // string: "PLN" / "EUR" / "USD" / "CHF"
    "grace_period_months": null,  // int
    "fixed_rate_period_years": null,  // int
    "eco_friendly": null,  // bool (kredyt EKO)
    "refinancing_period_months": null,  // int
    "existing_mortgage_count": 0,  // int
    "consolidation_amount": null  // float
  },
  
  "property": {
    "property_type": null,  // string z listy (patrz PROPERTY_TYPES)
    "property_location": null,  // string (miasto/województwo)
    "property_area_sqm": null,  // float (powierzchnia m2)
    "plot_area_sqm": null,  // float (działka m2)
    "construction_cost_per_sqm": null,  // float
    "has_building_permit": null,  // bool
    "commercial_space_percent": null,  // float (% komercji)
    "is_city_above_100k": null,  // bool
    "is_family_transaction": null,  // bool
    "is_shared_ownership": null,  // bool
    "ownership_percent": null,  // float
    "is_third_party_collateral": null,  // bool
    "plot_as_down_payment": null  // bool
  },
  
  "raw_input": ""  // Oryginalny input użytkownika (skopiuj tutaj)
}
```

---

📖 SŁOWNIKI WARTOŚCI:

**INCOME_TYPES** (dozwolone wartości dla "income_type"):
- "umowa_o_prace_czas_nieokreslony"
- "umowa_o_prace_czas_okreslony"
- "umowa_na_zastepstwo"
- "kontrakt_menedzerski"
- "umowa_o_dzielo"
- "umowa_zlecenie"
- "dzialalnosc_pelna_ksiegowosc"
- "dzialalnosc_kpir"
- "dzialalnosc_ryczalt"
- "dzialalnosc_karta_podatkowa"
- "dzialalnosc_rolnicza"
- "samozatrudnienie"
- "dochody_z_najmu"
- "emerytura"
- "renta"
- "dywidendy"
- "diety"
- "dochody_marynarzy"
- "urlop_macierzynski"
- "dochod_w_obcej_walucie"
- "powolanie_w_spolce"
- "800_plus"

**LOAN_PURPOSES** (dozwolone wartości dla "loan_purpose"):
- "zakup_mieszkania_domu"
- "budowa_domu_systemem_gospodarczym"
- "budowa_domu_systemem_zleconym"
- "zakup_dzialki_budowlanej"
- "zakup_dzialki_rolnej_pod_zabudowe"
- "zakup_dzialki_rekreacyjnej"
- "siedlisko"
- "zakup_domu_letniskowego"
- "zakup_lokalu_uzytkowego"
- "zakup_kamienicy"
- "zakup_udzialu_w_nieruchomosci"
- "ekspektatywa_cesja"
- "refinansowanie_wydatkow"
- "nieruchomosc_z_komercja"
- "refinansowanie_kredytu"
- "transakcja_rodzinna"
- "tbs"
- "lokal_w_budynku_w_budowie"
- "konsolidacja_niemieszkaniowa"
- "cel_dowolny"

**PROPERTY_TYPES** (dozwolone wartości dla "property_type"):
- "mieszkanie"
- "dom"
- "dzialka_budowlana"
- "dzialka_rolna"
- "dzialka_rekreacyjna"
- "lokal_uzytkowy"
- "kamienica"
- "nieruchomosc_z_komercja"
- "siedlisko"
- "dom_letniskowy"

---

⚠️ WYMAGANE POLA (minimum do analizy):
1. borrower.age
2. borrower.income_type
3. borrower.employment_duration_months
4. loan.loan_purpose
5. loan.property_value LUB loan.loan_amount

---

🔍 ZASADY MAPOWANIA:

1. **Ekstrakcja dokładna**:
   - Czytaj uważnie cały input
   - Wyciągnij WSZYSTKIE informacje
   - Nie zgaduj - jeśli informacji brak, zostaw null

2. **Konwersje**:
   - Wiek: zawsze jako liczba lat (np. 45)
   - Staż pracy: ZAWSZE w miesiącach (np. 5 lat = 60 miesięcy)
   - Okres kredytu: preferuj miesiące (25 lat = 300 miesięcy)
   - Kwoty: zawsze jako liczby (nie stringi), bez separatorów (800000 nie "800 000")
   - Procenty: jako liczby (20 nie "20%")

3. **Inteligentne wnioskowanie**:
   - Jeśli podano "małżeństwo" → relationship_status = "malzenstwo"
   - Jeśli podano współkredytobiorcę → uzupełnij co_borrower
   - Jeśli podano "obywatel Polski" → is_polish_citizen = true
   - Jeśli podano wartość i kwotę → oblicz LTV: (kwota/wartość)*100
   - Jeśli podano wkład % → oblicz down_payment_percent: 100 - LTV
   - Jeśli "dom energooszczędny" lub "EKO" → eco_friendly = true

4. **Typ dochodu - mapowanie synonimów**:
   - "UoP" / "umowa o pracę" / "etat" → rozpoznaj czy czas określony/nieokreślony
   - "działalność gospodarcza" / "firma" / "JDG" → rozpoznaj typ księgowości
   - "emerytura" / "emeryt" → "emerytura"
   - "B2B" → "kontrakt_menedzerski"

5. **Cel kredytu - mapowanie**:
   - "zakup mieszkania" / "kupno mieszkania" → "zakup_mieszkania_domu"
   - "budowa domu" → sprawdź czy "gospodarczy" czy "zlecony"
   - "refinansowanie" → "refinansowanie_kredytu" lub "refinansowanie_wydatkow"

6. **Walidacja**:
   - Sprawdź czy wiek w zakresie 18-100
   - Sprawdź czy LTV w zakresie 0-100%
   - Sprawdź czy kwoty > 0

---

📊 FORMAT ODPOWIEDZI:

Zwróć TYLKO JSON (bez markdown, bez komentarzy, bez ```json).
JSON MUSI być poprawny składniowo i zawierać WSZYSTKIE klucze z modelu.

PRZYKŁAD:

Jeśli input: "Jan Kowalski, 45 lat, UoP na czas nieokreślony, staż 5 lat, zakup mieszkania za 800k, kredyt 640k"

Odpowiedź:
{
  "borrower": {
    "age": 45,
    "income_type": "umowa_o_prace_czas_nieokreslony",
    "income_amount_monthly": null,
    "employment_duration_months": 60,
    "is_polish_citizen": true,
    "has_residence_card": null,
    "residence_card_type": null,
    "additional_income_sources": [],
    "is_property_owner": null
  },
  "co_borrower": null,
  "additional_borrowers": [],
  "relationship_status": null,
  "loan": {
    "loan_purpose": "zakup_mieszkania_domu",
    "property_value": 800000.0,
    "loan_amount": 640000.0,
    "down_payment": 160000.0,
    "down_payment_percent": 20.0,
    "ltv": 80.0,
    "loan_period_months": null,
    "loan_period_years": null,
    "currency": "PLN",
    "grace_period_months": null,
    "fixed_rate_period_years": null,
    "eco_friendly": null,
    "refinancing_period_months": null,
    "existing_mortgage_count": 0,
    "consolidation_amount": null
  },
  "property": {
    "property_type": "mieszkanie",
    "property_location": null,
    "property_area_sqm": null,
    "plot_area_sqm": null,
    "construction_cost_per_sqm": null,
    "has_building_permit": null,
    "commercial_space_percent": null,
    "is_city_above_100k": null,
    "is_family_transaction": null,
    "is_shared_ownership": null,
    "ownership_percent": null,
    "is_third_party_collateral": null,
    "plot_as_down_payment": null
  },
  "raw_input": "Jan Kowalski, 45 lat, UoP na czas nieokreślony, staż 5 lat, zakup mieszkania za 800k, kredyt 640k"
}

---

⚠️ KLUCZOWE:
- Zwróć TYLKO JSON (bez dodatkowego tekstu)
- Wszystkie klucze z modelu MUSZĄ być obecne
- Użyj null dla brakujących danych (nie pomijaj kluczy)
- Liczby jako liczby (nie stringi)
- Użyj TYLKO dozwolonych wartości ze słowników"""
    
    def map_input_to_profile(
        self,
        user_input: str,
        model_name: str = None
    ) -> Tuple[CustomerProfile, Dict]:
        """
        Mapuje surowy input użytkownika na CustomerProfile
        
        Args:
            user_input: Surowy opis profilu kredytobiorcy
            model_name: Opcjonalny model do użycia (domyślnie gpt-4.1)
            
        Returns:
            Tuple (CustomerProfile object, raw_json_dict)
        """
        print("\n" + "="*80)
        print("🔄 MAPOWANIE INPUTU NA MODEL DANYCH")
        print("="*80 + "\n")
        
        mapping_prompt = self.create_mapping_prompt()
        
        messages = [
            {"role": "system", "content": mapping_prompt},
            {"role": "user", "content": f"INPUT UŻYTKOWNIKA:\n\n{user_input}"}
        ]
        
        print("📝 Wysyłam request do LLM...")
        
        # Użyj podanego modelu lub domyślnego
        original_deployment = self.ai_client.deployment_name
        if model_name:
            self.ai_client.deployment_name = model_name
        
        try:
            response = self.ai_client.create_chat_completion(
                messages=messages,
                temperature=0.1,  # Niska temperatura dla precyzji
                max_tokens=3000
            )
        finally:
            # Przywróć oryginalny model
            self.ai_client.deployment_name = original_deployment
        
        # Parsuj JSON
        try:
            # Usuń markdown code blocks jeśli istnieją
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            response_clean = response_clean.strip()
            
            profile_dict = json.loads(response_clean)
            
            print("✅ JSON sparsowany pomyślnie")
            
            # Konwertuj dict na CustomerProfile object
            profile = self._dict_to_profile(profile_dict)
            
            # Walidacja
            is_valid, errors = validate_profile(profile)
            
            if not is_valid:
                print(f"\n⚠️ OSTRZEŻENIA WALIDACJI:")
                for error in errors:
                    print(f"  - {error}")
            
            # Sprawdź wymagane pola
            if not profile.is_complete():
                missing = profile.get_missing_required_fields()
                print(f"\n⚠️ BRAKUJĄCE WYMAGANE POLA: {', '.join(missing)}")
                print("   Analiza może być niepełna!")
            else:
                print("\n✅ Wszystkie wymagane pola wypełnione")
            
            print("\n" + "="*80)
            print("✅ MAPOWANIE ZAKOŃCZONE")
            print("="*80 + "\n")
            
            return profile, profile_dict
            
        except json.JSONDecodeError as e:
            print(f"\n❌ Błąd parsowania JSON: {e}")
            print(f"Odpowiedź LLM (pierwsze 500 znaków):\n{response[:500]}")
            raise ValueError(f"Nie można sparsować odpowiedzi LLM jako JSON: {e}")
    
    def _dict_to_profile(self, data: Dict) -> CustomerProfile:
        """
        Konwertuje dict na CustomerProfile object
        
        Args:
            data: Słownik z danymi profilu
            
        Returns:
            CustomerProfile object
        """
        # Konwertuj string enums na Enum objects
        def str_to_enum(enum_class, value):
            if value is None:
                return None
            try:
                # Znajdź enum po wartości
                for item in enum_class:
                    if item.value == value:
                        return item
                return None
            except:
                return None
        
        # Borrower
        borrower_data = data.get("borrower", {})
        borrower = PersonData(
            age=borrower_data.get("age"),
            income_type=str_to_enum(IncomeType, borrower_data.get("income_type")),
            income_amount_monthly=borrower_data.get("income_amount_monthly"),
            employment_duration_months=borrower_data.get("employment_duration_months"),
            is_polish_citizen=borrower_data.get("is_polish_citizen", True),
            has_residence_card=borrower_data.get("has_residence_card"),
            residence_card_type=borrower_data.get("residence_card_type"),
            additional_income_sources=borrower_data.get("additional_income_sources", []),
            is_property_owner=borrower_data.get("is_property_owner")
        )
        
        # Co-borrower
        co_borrower = None
        co_borrower_data = data.get("co_borrower")
        if co_borrower_data:
            co_borrower = PersonData(
                age=co_borrower_data.get("age"),
                income_type=str_to_enum(IncomeType, co_borrower_data.get("income_type")),
                income_amount_monthly=co_borrower_data.get("income_amount_monthly"),
                employment_duration_months=co_borrower_data.get("employment_duration_months"),
                is_polish_citizen=co_borrower_data.get("is_polish_citizen", True),
                has_residence_card=co_borrower_data.get("has_residence_card"),
                residence_card_type=co_borrower_data.get("residence_card_type"),
                additional_income_sources=co_borrower_data.get("additional_income_sources", []),
                is_property_owner=co_borrower_data.get("is_property_owner")
            )
        
        # Loan
        loan_data = data.get("loan", {})
        loan = LoanParameters(
            loan_purpose=str_to_enum(LoanPurpose, loan_data.get("loan_purpose")),
            property_value=loan_data.get("property_value"),
            loan_amount=loan_data.get("loan_amount"),
            down_payment=loan_data.get("down_payment"),
            down_payment_percent=loan_data.get("down_payment_percent"),
            ltv=loan_data.get("ltv"),
            loan_period_months=loan_data.get("loan_period_months"),
            loan_period_years=loan_data.get("loan_period_years"),
            currency=str_to_enum(Currency, loan_data.get("currency", "PLN")),
            grace_period_months=loan_data.get("grace_period_months"),
            fixed_rate_period_years=loan_data.get("fixed_rate_period_years"),
            eco_friendly=loan_data.get("eco_friendly"),
            refinancing_period_months=loan_data.get("refinancing_period_months"),
            existing_mortgage_count=loan_data.get("existing_mortgage_count", 0),
            consolidation_amount=loan_data.get("consolidation_amount")
        )
        
        # Property
        property_data = data.get("property", {})
        property_obj = PropertyData(
            property_type=str_to_enum(PropertyType, property_data.get("property_type")),
            property_location=property_data.get("property_location"),
            property_area_sqm=property_data.get("property_area_sqm"),
            plot_area_sqm=property_data.get("plot_area_sqm"),
            construction_cost_per_sqm=property_data.get("construction_cost_per_sqm"),
            has_building_permit=property_data.get("has_building_permit"),
            commercial_space_percent=property_data.get("commercial_space_percent"),
            is_city_above_100k=property_data.get("is_city_above_100k"),
            is_family_transaction=property_data.get("is_family_transaction"),
            is_shared_ownership=property_data.get("is_shared_ownership"),
            ownership_percent=property_data.get("ownership_percent"),
            is_third_party_collateral=property_data.get("is_third_party_collateral"),
            plot_as_down_payment=property_data.get("plot_as_down_payment")
        )
        
        # Relationship status
        relationship_status = str_to_enum(RelationshipStatus, data.get("relationship_status"))
        
        # Create profile
        profile = CustomerProfile(
            borrower=borrower,
            co_borrower=co_borrower,
            additional_borrowers=[],  # TODO: Obsługa additional_borrowers
            relationship_status=relationship_status,
            loan=loan,
            property=property_obj,
            raw_input=data.get("raw_input", "")
        )
        
        return profile
