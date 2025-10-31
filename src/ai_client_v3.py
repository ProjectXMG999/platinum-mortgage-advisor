"""
Klient do komunikacji z Azure OpenAI - Wersja 3.0
Używa modularnych serwisów z dynamicznym ładowaniem promptów
"""
from openai import AzureOpenAI, AsyncAzureOpenAI
from typing import List, Dict, Tuple, Optional
import json
import asyncio
from src import config
from src.services import (
    ContextLoader,
    PromptLoader,
    ValidationService,
    QualityService,
    RankingService,
    ResponseParser
)
from src.services.comparative_quality_service import ComparativeQualityService
from src.services.orchestrator_service import OrchestratorService
from src.models.customer_profile import CustomerProfile
from src.models.structured_outputs import (
    ValidationResult,
    QualityScore,
    DetailedRanking,
    CompleteAnalysis
)


class AIClient:
    """
    Klient do komunikacji z Azure OpenAI API
    
    Architektura V3:
    - Używa serwisów zamiast zahardkodowanych promptów
    - Dynamiczne ładowanie kontekstu (WYMÓG vs JAKOŚĆ)
    - Structured outputs (ValidationResult, QualityScore, etc.)
    - Separacja odpowiedzialności
    """
    
    def __init__(self):
        """Inicjalizacja klienta Azure OpenAI + wszystkich serwisów"""
        # Azure OpenAI clients (sync + async)
        self.client = AzureOpenAI(
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
        )
        self.async_client = AsyncAzureOpenAI(
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
        )
        self.deployment_name = config.AZURE_OPENAI_DEPLOYMENT_NAME
        print(f"✓ Połączono z Azure OpenAI: {config.AZURE_OPENAI_ENDPOINT}")
        
        # Inicjalizacja serwisów z dynamicznym ładowaniem
        print("🔧 Inicjalizacja serwisów...")
        self.context_loader = ContextLoader()
        self.prompt_loader = PromptLoader(
            prompts_dir="src/prompts",
            context_loader=self.context_loader
        )
        self.validation_service = ValidationService(self, self.prompt_loader)
        self.quality_service = QualityService(self, self.prompt_loader)
        self.comparative_quality_service = ComparativeQualityService(
            self,
            self.prompt_loader,
            ResponseParser()
        )
        self.ranking_service = RankingService(self, self.prompt_loader)
        self.response_parser = ResponseParser()
        
        # Orchestrator
        self.orchestrator = OrchestratorService(
            self.validation_service,
            self.quality_service,
            self.comparative_quality_service
        )
        
        print(f"✓ Serwisy gotowe:")
        print(f"  - ContextLoader: {len(self.context_loader.knowledge_base)} banków")
        print(f"  - PromptLoader: dynamiczne ładowanie z prompts/")
        print(f"  - ValidationService: ETAP 1 (WYMÓG - {len(self.context_loader.WYMOG_CATEGORIES)} kategorii)")
        print(f"  - QualityService: ETAP 2 (JAKOŚĆ - indywidualny scoring)")
        print(f"  - ComparativeQualityService: ETAP 2 (JAKOŚĆ - porównawczy scoring)")
        print(f"  - RankingService: ETAP 3 (TOP 3)")
        print(f"  - OrchestratorService: Koordynacja całego procesu")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Wysyła zapytanie do modelu AI (synchroniczne)
        
        Args:
            messages: Lista wiadomości w formacie OpenAI
            temperature: Temperatura modelu (0-1)
            max_tokens: Maksymalna liczba tokenów w odpowiedzi
            
        Returns:
            Odpowiedź od modelu
        """
        try:
            # Przygotuj parametry
            completion_params = {
                "model": self.deployment_name,
                "messages": messages,
            }
            
            # Dostosuj parametry do typu modelu
            model_lower = self.deployment_name.lower()
            if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
                # Modele reasoning - temperatura 1.0, max_completion_tokens
                completion_params["temperature"] = temperature if temperature is not None else 1.0
                if max_tokens:
                    completion_params["max_completion_tokens"] = max_tokens
            else:
                # Standardowe modele
                completion_params["temperature"] = temperature if temperature is not None else 0.7
                if max_tokens:
                    completion_params["max_tokens"] = max_tokens
            
            response = self.client.chat.completions.create(**completion_params)
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Błąd wywołania API: {e}")
            raise
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        response_format: Dict = None
    ) -> str:
        """
        Asynchroniczne wywołanie chat completion (dla nowych serwisów)
        
        Args:
            messages: Lista wiadomości w formacie OpenAI
            model: Nazwa modelu (deployment) lub None = domyślny
            temperature: Temperatura modelu (0-1)
            max_tokens: Maksymalna liczba tokenów w odpowiedzi
            response_format: Format odpowiedzi, np. {"type": "json_object"}
            
        Returns:
            Odpowiedź od modelu
        """
        try:
            # Użyj podanego modelu lub domyślnego
            deployment = model or self.deployment_name
            
            # Przygotuj parametry
            completion_params = {
                "model": deployment,
                "messages": messages,
            }
            
            # Dodaj response_format jeśli podany
            if response_format:
                completion_params["response_format"] = response_format
            
            # Dostosuj parametry do typu modelu
            model_lower = deployment.lower()
            if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
                # Modele reasoning - temperatura 1.0, max_completion_tokens
                completion_params["temperature"] = temperature if temperature is not None else 1.0
                if max_tokens:
                    completion_params["max_completion_tokens"] = max_tokens
            else:
                # Standardowe modele
                completion_params["temperature"] = temperature if temperature is not None else 0.7
                if max_tokens:
                    completion_params["max_tokens"] = max_tokens
            
            response = await self.async_client.chat.completions.create(**completion_params)
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Błąd wywołania API: {e}")
            raise
    
    # =========================================================================
    # ETAP 1: WALIDACJA WYMOGÓW
    # =========================================================================
    
    async def validate_single_bank_async(
        self,
        bank_name: str,
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Waliduje pojedynczy bank (ETAP 1 - WYMÓG)
        
        Args:
            bank_name: Nazwa banku
            customer_profile: Zmapowany profil klienta
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            ValidationResult object
        """
        return await self.validation_service.validate_single_bank(
            bank_name=bank_name,
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
    
    async def validate_all_banks_async(
        self,
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None,
        show_progress: bool = True
    ) -> Tuple[str, Dict]:
        """
        Waliduje wszystkie banki równolegle (ETAP 1 - WYMÓG)
        
        Args:
            customer_profile: Zmapowany profil klienta
            deployment_name: Model do użycia (None = domyślny)
            show_progress: Czy pokazywać progress
            
        Returns:
            Tuple (JSON string, parsed dict)
        """
        return await self.validation_service.validate_all_banks(
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
    
    # =========================================================================
    # ETAP 2: OCENA JAKOŚCI
    # =========================================================================
    
    async def rate_single_bank_async(
        self,
        bank_name: str,
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None
    ) -> QualityScore:
        """
        Ocenia jakość pojedynczego banku (ETAP 2 - JAKOŚĆ)
        
        Args:
            bank_name: Nazwa banku
            customer_profile: Zmapowany profil klienta
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            QualityScore object
        """
        return await self.quality_service.rate_single_bank(
            bank_name=bank_name,
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
    
    async def rate_all_banks_async(
        self,
        qualified_banks: List[str],
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None
    ) -> str:
        """
        Ocenia wszystkie zakwalifikowane banki (ETAP 2 - JAKOŚĆ)
        
        Args:
            qualified_banks: Lista zakwalifikowanych banków
            customer_profile: Zmapowany profil klienta
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            Markdown z rankingiem TOP 4
        """
        return await self.quality_service.rate_all_banks(
            qualified_banks=qualified_banks,
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
    
    # =========================================================================
    # ETAP 3: SZCZEGÓŁOWY RANKING TOP 3
    # =========================================================================
    
    async def generate_detailed_ranking_async(
        self,
        top_banks: List[str],
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None
    ) -> DetailedRanking:
        """
        Generuje szczegółowy ranking TOP 3 banków (ETAP 3)
        
        Args:
            top_banks: Lista TOP banków (max 3)
            customer_profile: Zmapowany profil klienta
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            DetailedRanking object
        """
        return await self.ranking_service.generate_detailed_ranking(
            top_banks=top_banks[:3],  # Max 3 banki
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
    
    # =========================================================================
    # KOMPLETNY PIPELINE (ETAP 1 + 2 + 3)
    # =========================================================================
    
    async def query_complete_pipeline(
        self,
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None
    ) -> CompleteAnalysis:
        """
        Uruchamia kompletny pipeline 3-etapowy
        
        ETAP 1: Walidacja WYMOGÓW (pre-screening)
        ETAP 2: Ocena JAKOŚCI (ranking zakwalifikowanych)
        ETAP 3: Szczegółowy ranking TOP 3
        
        Args:
            customer_profile: Zmapowany profil klienta
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            CompleteAnalysis object z pełnymi wynikami
        """
        import time
        start_time = time.time()
        
        print("\n" + "="*80)
        print("🚀 KOMPLETNY PIPELINE ANALIZY")
        print("="*80)
        
        # ETAP 1: Walidacja
        print("\n📋 ETAP 1: Walidacja WYMOGÓW...")
        validation_json, validation_dict = await self.validate_all_banks_async(
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
        
        qualified_bank_names = [
            b['bank_name'] 
            for b in validation_dict.get('qualified_banks', [])
        ]
        
        if not qualified_bank_names:
            print("❌ Brak zakwalifikowanych banków!")
            processing_time = time.time() - start_time
            return CompleteAnalysis(
                customer_profile=customer_profile,
                validation_results=[],
                quality_scores=[],
                detailed_ranking=None,
                processing_time=processing_time
            )
        
        print(f"✓ Zakwalifikowano: {len(qualified_bank_names)} banków")
        
        # ETAP 2: Ocena jakości
        print(f"\n🏅 ETAP 2: Ocena JAKOŚCI ({len(qualified_bank_names)} banków)...")
        
        # Zbierz QualityScore dla każdego banku
        quality_tasks = [
            self.rate_single_bank_async(
                bank_name=bank_name,
                customer_profile=customer_profile,
                deployment_name=deployment_name
            )
            for bank_name in qualified_bank_names
        ]
        
        quality_scores: List[QualityScore] = await asyncio.gather(*quality_tasks)
        
        # Sortuj po total_score
        quality_scores_sorted = sorted(
            quality_scores, 
            key=lambda x: x.total_score, 
            reverse=True
        )
        
        print(f"✓ Oceniono {len(quality_scores)} banków")
        
        # ETAP 3: Ranking TOP 3
        top_3_banks = [qs.bank_name for qs in quality_scores_sorted[:3]]
        
        print(f"\n🏆 ETAP 3: Szczegółowy ranking TOP 3...")
        print(f"  TOP 3: {', '.join(top_3_banks)}")
        
        detailed_ranking = await self.generate_detailed_ranking_async(
            top_banks=top_3_banks,
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
        
        processing_time = time.time() - start_time
        
        # Zbuduj CompleteAnalysis
        # Przekonwertuj validation_dict do ValidationResult objects
        validation_results = []
        for bank_data in validation_dict.get('qualified_banks', []) + validation_dict.get('disqualified_banks', []):
            validation_results.append(
                self.response_parser.parse_validation_response(
                    json.dumps(bank_data),
                    bank_data.get('bank_name', 'Unknown')
                )
            )
        
        complete_analysis = CompleteAnalysis(
            customer_profile=customer_profile,
            validation_results=validation_results,
            quality_scores=quality_scores_sorted,
            detailed_ranking=detailed_ranking,
            processing_time=processing_time
        )
        
        print("\n" + "="*80)
        print(f"✅ PIPELINE ZAKOŃCZONY ({processing_time:.2f}s)")
        print("="*80)
        
        return complete_analysis
    
    # =========================================================================
    # BACKWARD COMPATIBILITY (stare metody)
    # =========================================================================
    
    async def query_two_stage_async(
        self,
        customer_profile: CustomerProfile,
        deployment_name: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        BACKWARD COMPATIBILITY: Stara metoda 2-etapowa (ETAP 1 + 2)
        
        Returns:
            Tuple (validation_json, ranking_markdown)
        """
        # ETAP 1
        validation_json, validation_dict = await self.validate_all_banks_async(
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
        
        qualified_banks = [
            b['bank_name'] 
            for b in validation_dict.get('qualified_banks', [])
        ]
        
        if not qualified_banks:
            return validation_json, "# ❌ Brak zakwalifikowanych banków"
        
        # ETAP 2
        ranking_markdown = await self.rate_all_banks_async(
            qualified_banks=qualified_banks,
            customer_profile=customer_profile,
            deployment_name=deployment_name
        )
        
        return validation_json, ranking_markdown
    
    def query(
        self,
        user_query: str,
        knowledge_base: Dict,
        top_k: int = 4,
        model: str = None
    ) -> str:
        """
        BACKWARD COMPATIBILITY: Stara synchroniczna metoda
        UWAGA: Używaj query_complete_pipeline() zamiast tego
        """
        print("⚠️ DEPRECATED: Używaj query_complete_pipeline() zamiast query()")
        
        # Prosta implementacja dla backward compatibility
        messages = [
            {"role": "system", "content": "Jesteś ekspertem kredytów hipotecznych."},
            {"role": "user", "content": user_query}
        ]
        
        response = self.client.chat.completions.create(
            model=model or self.deployment_name,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
