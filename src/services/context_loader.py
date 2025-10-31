"""
Context Loader - Dynamiczne ładowanie kontekstu z baz danych
Separacja WYMÓG vs JAKOŚĆ
"""
import json
from typing import Dict, List, Any, Optional


class ContextLoader:
    """Dynamicznie ładuje i filtruje kontekst z knowledge base"""
    
    # Definicje kategorii i parametrów WYMÓG vs JAKOŚĆ
    WYMOG_CATEGORIES = [
        "02_kredytobiorca",
        "03_źródło_dochodu",
        "04_cel_kredytu",
        "05_zabezpieczenia",
        "08_ważność_dokumentów"
    ]
    
    WYMOG_PARAMS_FROM_KREDYT = [
        "04_LTV_kredyt",
        "08_wkład_własny",
        "14_ile_kredytów_hipotecznych",
        "15_wielkość_działki"
    ]
    
    JAKOSC_CATEGORIES = [
        "06_wycena",
        "07_ubezpieczenia"
    ]
    
    JAKOSC_PARAMS_FROM_KREDYT = [
        "udzoz",
        "02_kwota_kredytu",
        "03_okres_kredytowania_kredytu",
        "05_kwota_pożyczki",
        "06_okres_kredytowania_pożyczki",
        "07_LTV_pożyczka",
        "09_WIBOR_(stawka_referencyjna)",
        "10_oprocentowanie_stałe_-_na_ile_lat?",
        "11_wcześniejsza_spłata",
        "12_raty_równe,_malejące",
        "13_karencja_w_spłacie_kapitału",
        "16_kredy_EKO"
    ]
    
    def __init__(
        self,
        knowledge_base_path: str = "data/processed/knowledge_base.json",
        classification_path: str = "data/processed/parameter_classification_v2.json"
    ):
        """
        Inicjalizacja context loadera
        
        Args:
            knowledge_base_path: Ścieżka do bazy wiedzy banków
            classification_path: Ścieżka do klasyfikacji WYMÓG/JAKOŚĆ
        """
        self.knowledge_base_path = knowledge_base_path
        self.classification_path = classification_path
        
        # Wczytaj dane
        raw_kb = self._load_json(knowledge_base_path)
        self.classification = self._load_json(classification_path)
        
        # Przekształć knowledge_base do struktury {bank_name: bank_data}
        self.knowledge_base = {}
        for product in raw_kb.get("products", []):
            bank_name = product.get("bank_name")
            if bank_name:
                self.knowledge_base[bank_name] = product
        
        print(f"✓ ContextLoader: Wczytano {len(self.knowledge_base)} banków")
        print(f"✓ ContextLoader: Klasyfikacja {self.classification['statistics']['WYMÓG_count']} WYMOGÓW, "
              f"{self.classification['statistics']['JAKOŚĆ_count']} JAKOŚCI")
    
    def _load_json(self, path: str) -> Dict:
        """Wczytuje plik JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Błąd wczytywania {path}: {e}")
            return {}
    
    def _find_bank(self, bank_name: str) -> Optional[Dict]:
        """Znajduje dane banku po nazwie"""
        return self.knowledge_base.get(bank_name)
    
    def get_validation_context(self, bank_name: str) -> Dict:
        """
        Zwraca TYLKO pola WYMÓG dla konkretnego banku
        
        Args:
            bank_name: Nazwa banku
            
        Returns:
            Dict z kontekstem walidacyjnym (tylko WYMOGI)
        """
        bank_data = self._find_bank(bank_name)
        
        if not bank_data:
            return {"bank_name": bank_name, "error": "Bank nie znaleziony"}
        
        context = {
            "bank_name": bank_name,
            "wymogi": {}
        }
        
        # Dodaj pełne kategorie WYMÓG
        for category in self.WYMOG_CATEGORIES:
            if category in bank_data.get("parameters", {}):
                context["wymogi"][category] = bank_data["parameters"][category]
        
        # Dodaj wybrane parametry WYMÓG z "01_parametry_kredytu"
        kredyt_params = bank_data.get("parameters", {}).get("01_parametry_kredytu", {})
        if kredyt_params:
            context["wymogi"]["parametry_kredytu_WYMOGI"] = {
                param: kredyt_params.get(param, "brak danych")
                for param in self.WYMOG_PARAMS_FROM_KREDYT
            }
        
        return context
    
    def get_quality_context(self, bank_name: str) -> Dict:
        """
        Zwraca TYLKO pola JAKOŚĆ dla konkretnego banku
        
        Args:
            bank_name: Nazwa banku
            
        Returns:
            Dict z kontekstem jakościowym (tylko JAKOŚĆ)
        """
        bank_data = self._find_bank(bank_name)
        
        if not bank_data:
            return {"bank_name": bank_name, "error": "Bank nie znaleziony"}
        
        context = {
            "bank_name": bank_name,
            "jakosc": {}
        }
        
        # Dodaj pełne kategorie JAKOŚĆ
        for category in self.JAKOSC_CATEGORIES:
            if category in bank_data.get("parameters", {}):
                context["jakosc"][category] = bank_data["parameters"][category]
        
        # Dodaj wybrane parametry JAKOŚĆ z "01_parametry_kredytu"
        kredyt_params = bank_data.get("parameters", {}).get("01_parametry_kredytu", {})
        if kredyt_params:
            context["jakosc"]["parametry_kredytu_JAKOŚĆ"] = {}
            for param in self.JAKOSC_PARAMS_FROM_KREDYT:
                # Normalizuj nazwy kluczy (spacje, przecinki etc.)
                for key, value in kredyt_params.items():
                    if self._normalize_key(key) == self._normalize_key(param):
                        context["jakosc"]["parametry_kredytu_JAKOŚĆ"][param] = value
                        break
        
        return context
    
    def get_full_bank_context(self, bank_name: str) -> Dict:
        """
        Zwraca pełny kontekst banku (wszystkie dane)
        Używane dla rankingu TOP 3
        
        Args:
            bank_name: Nazwa banku
            
        Returns:
            Dict z pełnymi danymi banku
        """
        bank_data = self._find_bank(bank_name)
        
        if not bank_data:
            return {"bank_name": bank_name, "error": "Bank nie znaleziony"}
        
        return bank_data
    
    def get_all_banks(self) -> List[str]:
        """Zwraca listę nazw wszystkich banków"""
        return [
            product.get("bank_name")
            for product in self.knowledge_base.get("products", [])
            if product.get("bank_name")
        ]
    
    def get_classification_metadata(self) -> Dict:
        """
        Zwraca metadane klasyfikacji WYMÓG vs JAKOŚĆ
        
        Returns:
            Dict z definicjami i statystykami
        """
        return {
            "definitions": self.classification.get("definitions", {}),
            "statistics": self.classification.get("statistics", {}),
            "wymog_categories": self.WYMOG_CATEGORIES,
            "jakosc_categories": self.JAKOSC_CATEGORIES
        }
    
    def get_customer_relevant_wymogi(self, customer_profile) -> List[str]:
        """
        Zwraca listę kategorii WYMOGÓW istotnych dla danego profilu klienta
        
        Args:
            customer_profile: CustomerProfile object
            
        Returns:
            Lista kategorii do sprawdzenia
        """
        relevant = []
        
        # Sprawdź które kategorie są wypełnione w profilu
        if hasattr(customer_profile, 'borrower') and customer_profile.borrower:
            relevant.append("02_kredytobiorca")
            if customer_profile.borrower.income_type:
                relevant.append("03_źródło_dochodu")
        
        if hasattr(customer_profile, 'loan') and customer_profile.loan:
            if customer_profile.loan.loan_purpose:
                relevant.append("04_cel_kredytu")
        
        if hasattr(customer_profile, 'property') and customer_profile.property:
            relevant.append("05_zabezpieczenia")
        
        return relevant
    
    def _normalize_key(self, key: str) -> str:
        """Normalizuje klucz dla porównania (usuwa spacje, podkreślenia, etc.)"""
        return key.lower().replace(" ", "_").replace(",", "").replace("(", "").replace(")", "").replace("?", "")
    
    def get_validation_context_batch(self, bank_names: List[str]) -> Dict[str, Dict]:
        """
        Zwraca konteksty walidacyjne dla wielu banków naraz
        
        Args:
            bank_names: Lista nazw banków
            
        Returns:
            Dict {bank_name: validation_context}
        """
        return {
            bank_name: self.get_validation_context(bank_name)
            for bank_name in bank_names
        }
    
    def get_quality_context_batch(self, bank_names: List[str]) -> Dict[str, Dict]:
        """
        Zwraca konteksty jakościowe dla wielu banków naraz
        
        Args:
            bank_names: Lista nazw banków
            
        Returns:
            Dict {bank_name: quality_context}
        """
        return {
            bank_name: self.get_quality_context(bank_name)
            for bank_name in bank_names
        }
