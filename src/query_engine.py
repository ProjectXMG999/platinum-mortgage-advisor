"""
Silnik zapytań - główna logika wyszukiwania produktów
"""
from typing import Dict, List
import asyncio
from src.data_processor import DataProcessor
from src.ai_client_v3 import AIClient  # ✅ UŻYWAMY V3 (z poprawnymi serwisami)


class QueryEngine:
    """Silnik do przetwarzania zapytań użytkownika"""
    
    def __init__(self, knowledge_base_path: str):
        """
        Inicjalizacja silnika zapytań
        
        Args:
            knowledge_base_path: Ścieżka do bazy wiedzy
        """
        print("\n" + "="*80)
        print("INICJALIZACJA SYSTEMU PLATINUM MORTGAGE ADVISOR")
        print("="*80 + "\n")
        
        # Data processor (backward compatibility)
        self.data_processor = DataProcessor(knowledge_base_path)
        
        # AIClient V3 - zawiera już wszystkie serwisy (ContextLoader, PromptLoader, ValidationService, etc.)
        self.ai_client = AIClient()
        
        # Skróty do serwisów (dla wygody dostępu)
        self.context_loader = self.ai_client.context_loader
        self.prompt_loader = self.ai_client.prompt_loader
        self.validation_service = self.ai_client.validation_service
        self.quality_service = self.ai_client.quality_service
        self.comparative_quality_service = self.ai_client.comparative_quality_service
        self.ranking_service = self.ai_client.ranking_service
        
        # Orchestrator do zarządzania workflow (użyj tego z ai_client - już zawiera comparative_quality_service)
        self.orchestrator = self.ai_client.orchestrator
        
        print("\n" + "="*80)
        print("✓ System gotowy do pracy!")
        print("="*80 + "\n")
    
    async def process_query_v3(
        self,
        user_query: str = None,
        customer_profile = None,
        etap1_model: str = None,
        etap2_model: str = None,
        quality_strategy: str = "individual",
        skip_quality_scoring: bool = False
    ) -> Dict:
        """
        V3: Przetwarza zapytanie używając nowego orchestratora (services architecture)
        
        Args:
            user_query: Zapytanie użytkownika w języku naturalnym (opcjonalne jeśli mamy customer_profile)
            customer_profile: Zmapowany profil klienta (CustomerProfile object)
            etap1_model: Model do ETAP 1 (walidacja), None = domyślny
            etap2_model: Model do ETAP 2 (ranking), None = domyślny
            quality_strategy: "individual" lub "comparative" dla scoringu jakości
            skip_quality_scoring: Jeśli True, pomija ETAP 2 (tylko walidacja)
            
        Returns:
            Dict z wynikami: {"stage1_validation": str, "stage2_ranking": str, "error": bool, "qualified_banks": list}
        """
        print("\n" + "="*80)
        if skip_quality_scoring:
            print("🚀 TRYB: TYLKO WALIDACJA BANKÓW")
        else:
            print("🚀 TRZYETAPOWY SYSTEM DOPASOWANIA KREDYTÓW")
        print("⚡ Tryb: ASYNC PARALLEL")
        print(f"📋 Profil zmapowany: {'TAK' if customer_profile else 'NIE'}")
        if not skip_quality_scoring:
            print(f"🏆 Strategia ETAP 2: {quality_strategy.upper()}")
        print("="*80 + "\n")
        
        # Wywołaj orchestrator
        result = await self.orchestrator.process_query(
            knowledge_base=self.data_processor.knowledge_base,
            user_query=user_query,
            customer_profile=customer_profile,
            etap1_model=etap1_model,
            etap2_model=etap2_model,
            quality_strategy=quality_strategy,
            skip_quality_scoring=skip_quality_scoring  # Nowy parametr!
        )
        
        return result
    
    def process_query(
        self, 
        user_query: str,
        etap1_model: str = None,
        etap2_model: str = None,
        use_async: bool = True
    ) -> str:
        """
        LEGACY: Przetwarza zapytanie użytkownika (DWUETAPOWY SYSTEM) - STARY KOD używający ai_client
        
        Args:
            user_query: Zapytanie użytkownika w języku naturalnym
            etap1_model: Model do ETAP 1 (walidacja), None = domyślny
            etap2_model: Model do ETAP 2 (ranking), None = domyślny
            use_async: Czy używać async parallel processing (True = szybsze)
            
        Returns:
            Odpowiedź z rekomendacjami produktów
        """
        print(f"\n📝 Zapytanie: {user_query}\n")
        
        # Przygotuj kontekst z bazy wiedzy
        knowledge_context = self.data_processor.format_compact_for_context()
        
        # Dwuetapowe przetwarzanie
        result = self.ai_client.query_two_stage(
            user_query=user_query,
            knowledge_base_context=knowledge_context,
            etap1_model=etap1_model,
            etap2_model=etap2_model,
            use_async=use_async,
            knowledge_base_dict=self.data_processor.knowledge_base  # Dodajemy pełny dict dla async
        )
        
        if result.get("error"):
            return result["stage1_validation"] + "\n\n" + result["stage2_ranking"]
        
        # Formatuj wynik
        output = []
        output.append("="*80)
        output.append("ETAP 1: WALIDACJA WYMOGÓW (Pre-screening)")
        output.append("="*80)
        output.append("")
        output.append(result["stage1_validation"])
        output.append("")
        output.append("")
        output.append("="*80)
        output.append("ETAP 2: RANKING JAKOŚCI (Najlepsze oferty)")
        output.append("="*80)
        output.append("")
        output.append(result["stage2_ranking"])
        
        return "\n".join(output)
    
    def process_query_legacy(self, user_query: str) -> str:
        """
        STARA WERSJA: Przetwarza zapytanie jednym promptem (dla kompatybilności)
        
        Args:
            user_query: Zapytanie użytkownika w języku naturalnym
            
        Returns:
            Odpowiedź z rekomendacjami produktów
        """
        print(f"\n📝 Zapytanie: {user_query}\n")
        print("🔍 Szukam pasujących produktów (stary system)...\n")
        
        # Przygotuj kontekst z bazy wiedzy (używamy kompaktowej wersji JSON)
        knowledge_context = self.data_processor.format_compact_for_context()
        
        # Wyślij zapytanie do AI
        response = self.ai_client.query_with_context(
            user_query=user_query,
            knowledge_base_context=knowledge_context
        )
        
        return response
    
    def get_available_banks(self) -> List[str]:
        """Zwraca listę dostępnych banków"""
        return self.data_processor.get_all_banks()
    
    def get_bank_info(self, bank_name: str) -> Dict:
        """
        Pobiera informacje o konkretnym banku
        
        Args:
            bank_name: Nazwa banku
            
        Returns:
            Dane banku
        """
        return self.data_processor.get_bank_data(bank_name)
