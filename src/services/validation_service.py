"""
Serwis do walidacji WYMOGÓW banków (ETAP 1)
Używa ContextLoader i PromptLoader z dynamicznym kontekstem
"""
import json
import asyncio
from typing import Dict, List, Tuple
from .prompt_loader import PromptLoader
from .response_parser import ResponseParser
from src.models.structured_outputs import ValidationResult


class ValidationService:
    """Walidacja WYMOGÓW - pre-screening banków"""
    
    def __init__(self, ai_client, prompt_loader: PromptLoader):
        """
        Inicjalizacja serwisu walidacji
        
        Args:
            ai_client: Klient Azure OpenAI
            prompt_loader: Loader promptów (z ContextLoader)
        """
        self.ai_client = ai_client
        self.prompt_loader = prompt_loader
        self.response_parser = ResponseParser()
    
    async def validate_single_bank(
        self,
        bank_name: str,
        bank_data: Dict = None,  # Deprecated - używamy ContextLoader
        user_query: str = None,
        customer_profile = None,
        deployment_name: str = None
    ) -> ValidationResult:
        """
        Waliduje pojedynczy bank względem WYMOGÓW klienta
        
        Args:
            bank_name: Nazwa banku
            bank_data: DEPRECATED - nie używane (kontekst z ContextLoader)
            user_query: Surowy profil klienta (opcjonalny)
            customer_profile: Zmapowany profil klienta (CustomerProfile object)
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            ValidationResult object
        """
        if not customer_profile:
            raise ValueError("customer_profile jest wymagany (zmapowany profil klienta)")
        
        # Zbuduj messages używając PromptLoader (dynamiczny kontekst)
        messages = self.prompt_loader.build_validation_messages(
            bank_name=bank_name,
            customer_profile=customer_profile
        )
        
        # Wybierz model
        model = deployment_name or self.ai_client.deployment_name
        
        # Przygotuj parametry completion
        completion_params = {
            "model": model,
            "messages": messages,
        }
        
        # Dostosuj parametry do typu modelu
        model_lower = model.lower()
        if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
            completion_params["temperature"] = 1.0
            completion_params["max_completion_tokens"] = 2000
            # o1 NIE obsługuje response_format, ale prompt wymaga JSON
        else:
            completion_params["temperature"] = 0.1
            completion_params["max_tokens"] = 2000
            # TYLKO dla GPT-4: Wymuś JSON mode
            completion_params["response_format"] = {"type": "json_object"}
        
        try:
            # Wywołaj API
            response = await self.ai_client.async_client.chat.completions.create(**completion_params)
            result_text = response.choices[0].message.content
            
            # DEBUG: Pokaż pierwsze 300 znaków odpowiedzi
            print(f"✓ {bank_name}: {result_text[:300]}...")
            
            # Parsuj JSON do ValidationResult
            validation_result = self.response_parser.parse_validation_response(
                response=result_text,
                bank_name=bank_name
            )
            
            print(f"  → Status: {validation_result.status}, Sprawdzone: {len(validation_result.checked_requirements)}")
            
            return validation_result
                
        except Exception as e:
            print(f"⚠️ Błąd walidacji {bank_name}: {e}")
            return ValidationResult(
                bank_name=bank_name,
                status="ERROR",
                notes=f"API error: {str(e)}"
            )
    
    async def validate_all_banks(
        self,
        knowledge_base: Dict = None,  # Deprecated - używamy ContextLoader
        user_query: str = None,
        customer_profile = None,
        deployment_name: str = None
    ) -> Tuple[str, Dict]:
        """
        Waliduje wszystkie banki równolegle
        
        Args:
            knowledge_base: DEPRECATED - nie używane (kontekst z ContextLoader)
            user_query: Surowy profil klienta (opcjonalny)
            customer_profile: Zmapowany profil klienta (CustomerProfile object)
            deployment_name: Model do użycia
            
        Returns:
            Tuple (JSON string, parsed dict)
        """
        print("🔍 ETAP 1: Walidacja WYMOGÓW (PARALLEL MODE)...")
        
        if not customer_profile:
            raise ValueError("customer_profile jest wymagany")
        
        print("📋 Użyto zmapowanego profilu - sprawdzam tylko podane parametry WYMÓG")
        
        # Pobierz listę banków z ContextLoader
        bank_names = list(self.prompt_loader.context_loader.knowledge_base.keys())
        
        # Przygotuj taski dla każdego banku
        tasks = [
            self.validate_single_bank(
                bank_name=bank_name,
                bank_data=None,  # Deprecated
                user_query=user_query,
                customer_profile=customer_profile,
                deployment_name=deployment_name
            )
            for bank_name in bank_names
        ]
        
        # Wykonaj równolegle
        print(f"⚡ Uruchamiam {len(tasks)} równoległych requestów...")
        results: List[ValidationResult] = await asyncio.gather(*tasks)
        
        # Segreguj wyniki
        qualified_banks = []
        disqualified_banks = []
        
        for result in results:
            result_dict = result.to_dict()
            # LLM zwraca "QUALIFIED" lub "DISQUALIFIED"
            if result.status == "QUALIFIED":
                qualified_banks.append(result_dict)
            else:
                disqualified_banks.append(result_dict)
        
        # Stwórz finalny JSON
        final_result = {
            "etap": "1_WALIDACJA_WYMOGÓW",
            "qualified_banks": qualified_banks,
            "disqualified_banks": disqualified_banks,
            "summary": {
                "total_banks": len(results),
                "qualified": len(qualified_banks),
                "disqualified": len(disqualified_banks)
            }
        }
        
        result_json = json.dumps(final_result, ensure_ascii=False, indent=2)
        print(f"✓ Zakwalifikowane: {len(qualified_banks)}/{len(results)} banków")
        
        return result_json, final_result
