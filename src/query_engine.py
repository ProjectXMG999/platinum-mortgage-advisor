"""
Silnik zapytań - główna logika wyszukiwania produktów
"""
from typing import Dict, List
from src.data_processor import DataProcessor
from src.ai_client import AIClient


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
        
        self.data_processor = DataProcessor(knowledge_base_path)
        self.ai_client = AIClient()
        
        print("\n" + "="*80)
        print("✓ System gotowy do pracy!")
        print("="*80 + "\n")
    
    def process_query(self, user_query: str) -> str:
        """
        Przetwarza zapytanie użytkownika (DWUETAPOWY SYSTEM)
        
        Args:
            user_query: Zapytanie użytkownika w języku naturalnym
            
        Returns:
            Odpowiedź z rekomendacjami produktów
        """
        print(f"\n📝 Zapytanie: {user_query}\n")
        
        # Przygotuj kontekst z bazy wiedzy
        knowledge_context = self.data_processor.format_compact_for_context()
        
        # Dwuetapowe przetwarzanie
        result = self.ai_client.query_two_stage(
            user_query=user_query,
            knowledge_base_context=knowledge_context
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
