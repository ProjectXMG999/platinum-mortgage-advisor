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
from src.services import PromptLoader


class InputMapper:
    """Mapuje surowy input użytkownika na strukturę CustomerProfile"""
    
    def __init__(self, ai_client):
        """
        Inicjalizacja mappera
        
        Args:
            ai_client: Instancja AIClient do komunikacji z LLM
        """
        self.ai_client = ai_client
        self.prompt_loader = PromptLoader(prompts_dir="src/prompts")
    
    def create_mapping_prompt(self) -> str:
        """
        Tworzy prompt systemowy do mapowania inputu na model danych
        
        Returns:
            Prompt systemowy
        """
        return self.prompt_loader.load_prompt("input_mapper_prompt")
    
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
