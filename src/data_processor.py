"""
Moduł do przetwarzania i ładowania danych z bazy wiedzy
"""
import json
from typing import Dict, List
from pathlib import Path


class DataProcessor:
    """Klasa do zarządzania bazą wiedzy hipotecznej"""
    
    def __init__(self, knowledge_base_path: str):
        """
        Inicjalizacja procesora danych
        
        Args:
            knowledge_base_path: Ścieżka do pliku JSON z bazą wiedzy
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base = None
        self.load_knowledge_base()
    
    def load_knowledge_base(self) -> Dict:
        """Wczytuje bazę wiedzy z pliku JSON"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            print(f"✓ Wczytano bazę wiedzy: {len(self.knowledge_base['products'])} banków")
            return self.knowledge_base
        except FileNotFoundError:
            raise FileNotFoundError(f"Nie znaleziono pliku: {self.knowledge_base_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Błąd parsowania JSON: {self.knowledge_base_path}")
    
    def get_all_banks(self) -> List[str]:
        """Zwraca listę wszystkich banków"""
        return self.knowledge_base.get('banks', [])
    
    def get_bank_data(self, bank_name: str) -> Dict:
        """
        Zwraca dane dla konkretnego banku
        
        Args:
            bank_name: Nazwa banku
            
        Returns:
            Słownik z danymi banku
        """
        for product in self.knowledge_base.get('products', []):
            if product['bank_name'] == bank_name:
                return product
        return None
    
    def format_for_context(self) -> str:
        """
        Formatuje bazę wiedzy do tekstu dla kontekstu AI
        
        Returns:
            Sformatowany string z pełną bazą wiedzy
        """
        if not self.knowledge_base:
            return ""
        
        context_parts = [
            "# BAZA WIEDZY PRODUKTÓW HIPOTECZNYCH PLATINUM FINANCIAL",
            f"\nData aktualizacji: {self.knowledge_base['metadata']['date_updated']}",
            f"\n{self.knowledge_base['metadata']['description']}",
            f"\nLiczba banków: {len(self.knowledge_base['products'])}",
            "\n\n" + "="*80 + "\n"
        ]
        
        for product in self.knowledge_base['products']:
            bank_name = product['bank_name']
            context_parts.append(f"\n## BANK: {bank_name}\n")
            
            for group_name, parameters in product['parameters'].items():
                context_parts.append(f"\n### {group_name}\n")
                for param_name, param_value in parameters.items():
                    context_parts.append(f"- **{param_name}**: {param_value}\n")
            
            context_parts.append("\n" + "-"*80 + "\n")
        
        return "".join(context_parts)
    
    def format_compact_for_context(self) -> str:
        """
        Formatuje bazę wiedzy do kompaktowego JSON dla kontekstu AI
        
        Returns:
            JSON string z bazą wiedzy
        """
        if not self.knowledge_base:
            return ""
        
        return json.dumps(self.knowledge_base, ensure_ascii=False, indent=2)
