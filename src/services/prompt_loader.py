"""
Serwis do dynamicznego ładowania promptów z plików
Integracja z ContextLoader dla dynamicznego kontekstu
"""
import os
import json
from typing import Dict, Any, List, Optional
from .context_loader import ContextLoader


class PromptLoader:
    """Dynamiczne ładowanie i formatowanie promptów systemowych"""
    
    def __init__(
        self,
        prompts_dir: str = "src/prompts",
        context_loader: Optional[ContextLoader] = None
    ):
        """
        Inicjalizacja loadera promptów
        
        Args:
            prompts_dir: Ścieżka do katalogu z promptami
            context_loader: Opcjonalny ContextLoader (jeśli None, utworzy nowy)
        """
        self.prompts_dir = prompts_dir
        self.context_loader = context_loader or ContextLoader()
        self._cache = {}
    
    def load_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Ładuje i formatuje prompt z pliku
        
        Args:
            prompt_name: Nazwa pliku promptu (bez .py)
            **kwargs: Parametry do formatowania (np. bank_name)
            
        Returns:
            Sformatowany prompt
        """
        # TYMCZASOWO: Wyłączony cache (zawsze ładuj z pliku)
        # cache_key = f"{prompt_name}_{str(kwargs)}"
        # if cache_key in self._cache:
        #     return self._cache[cache_key]
        
        # Ładuj z pliku
        prompt_path = os.path.join(self.prompts_dir, f"{prompt_name}.py")
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt nie znaleziony: {prompt_path}")
        
        # Import modułu dynamicznie
        import importlib.util
        spec = importlib.util.spec_from_file_location(prompt_name, prompt_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Pobierz PROMPT z modułu
        if not hasattr(module, 'PROMPT'):
            raise AttributeError(f"Moduł {prompt_name} nie ma zmiennej PROMPT")
        
        content = module.PROMPT
        
        # Formatuj z parametrami
        if kwargs:
            try:
                content = content.format(**kwargs)
            except KeyError as e:
                print(f"⚠️ Brak parametru {e} w promptcie {prompt_name}")
        
        # TYMCZASOWO: Cache wyłączony
        # self._cache[cache_key] = content
        
        return content
    
    def clear_cache(self):
        """Czyści cache promptów"""
        self._cache = {}
    
    def get_validation_prompt(self, bank_name: str, has_customer_profile: bool = False) -> str:
        """
        Zwraca prompt do walidacji WYMOGÓW
        
        Args:
            bank_name: Nazwa banku
            has_customer_profile: Czy używamy zmapowanego profilu
            
        Returns:
            Prompt systemowy
        """
        return self.load_prompt("single_validation_prompt", bank_name=bank_name)
    
    def get_quality_prompt(self, bank_name: str, has_customer_profile: bool = False) -> str:
        """
        Zwraca prompt do oceny JAKOŚCI
        
        Args:
            bank_name: Nazwa banku
            has_customer_profile: Czy używamy zmapowanego profilu
            
        Returns:
            Prompt systemowy
        """
        return self.load_prompt("single_quality_prompt", bank_name=bank_name)
    
    def get_input_mapper_prompt(self) -> str:
        """
        Zwraca prompt do mapowania inputu użytkownika
        
        Returns:
            Prompt systemowy
        """
        return self.load_prompt("input_mapper_prompt")
    
    def build_validation_messages(
        self,
        bank_name: str,
        customer_profile
    ) -> List[Dict[str, str]]:
        """
        Buduje kompletne messages dla walidacji z dynamicznym kontekstem
        
        Args:
            bank_name: Nazwa banku
            customer_profile: CustomerProfile object
            
        Returns:
            Lista messages gotowych do wysłania do LLM
        """
        # 1. Załaduj szablon promptu
        template = self.get_validation_prompt(bank_name, has_customer_profile=True)
        
        # 2. Pobierz kontekst WYMOGÓW banku (tylko relevantne pola)
        bank_context = self.context_loader.get_validation_context(bank_name)
        bank_json = json.dumps(bank_context, ensure_ascii=False, indent=2)
        
        # 3. Przygotuj profil klienta
        profile_json = json.dumps(
            customer_profile.to_dict() if hasattr(customer_profile, 'to_dict') else customer_profile,
            ensure_ascii=False,
            indent=2
        )
        
        # 4. Zbuduj messages
        messages = [
            {
                "role": "system",
                "content": template
            },
            {
                "role": "system",
                "content": f"# WYMOGI BANKU {bank_name}\n\nPoniżej znajdziesz TYLKO parametry typu WYMÓG dla tego banku:\n\n```json\n{bank_json}\n```"
            },
            {
                "role": "user",
                "content": f"# PROFIL KLIENTA\n\nPoniżej zmapowany profil klienta:\n\n```json\n{profile_json}\n```\n\n⚠️ **PAMIĘTAJ**: Sprawdzaj TYLKO te WYMOGI, które dotyczą danych PODANYCH przez klienta (pola nie-null)!"
            }
        ]
        
        return messages
    
    def build_quality_messages(
        self,
        bank_name: str,
        customer_profile
    ) -> List[Dict[str, str]]:
        """
        Buduje kompletne messages dla oceny jakości z dynamicznym kontekstem
        
        Args:
            bank_name: Nazwa banku
            customer_profile: CustomerProfile object
            
        Returns:
            Lista messages gotowych do wysłania do LLM
        """
        # 1. Załaduj szablon promptu
        template = self.get_quality_prompt(bank_name, has_customer_profile=True)
        
        # 2. Pobierz kontekst JAKOŚCI banku (tylko relevantne pola)
        bank_context = self.context_loader.get_quality_context(bank_name)
        bank_json = json.dumps(bank_context, ensure_ascii=False, indent=2)
        
        # 3. Przygotuj profil klienta
        profile_json = json.dumps(
            customer_profile.to_dict() if hasattr(customer_profile, 'to_dict') else customer_profile,
            ensure_ascii=False,
            indent=2
        )
        
        # 4. Zbuduj messages
        messages = [
            {
                "role": "system",
                "content": template
            },
            {
                "role": "system",
                "content": f"# PARAMETRY JAKOŚCI - {bank_name}\n\nPoniżej znajdziesz TYLKO parametry typu JAKOŚĆ dla tego banku:\n\n```json\n{bank_json}\n```"
            },
            {
                "role": "user",
                "content": f"# PROFIL KLIENTA\n\nPoniżej zmapowany profil klienta:\n\n```json\n{profile_json}\n```\n\n⚠️ **PAMIĘTAJ**: Punktuj TYLKO te parametry JAKOŚCI, które są ISTOTNE dla TEGO klienta!"
            }
        ]
        
        return messages
    
    def build_ranking_messages(
        self,
        top_banks: List[str],
        customer_profile,
        validation_results: List[Dict],
        quality_scores: List[Dict]
    ) -> List[Dict[str, str]]:
        """
        Buduje messages dla szczegółowego rankingu TOP 3
        
        Args:
            top_banks: Lista nazw TOP 3 banków
            customer_profile: CustomerProfile object
            validation_results: Lista wyników walidacji
            quality_scores: Lista wyników jakości
            
        Returns:
            Lista messages dla LLM
        """
        # Prompt dla rankingu (możemy stworzyć nowy plik)
        ranking_template = """Jesteś ekspertem ds. kredytów hipotecznych w Platinum Financial.

🎯 ZADANIE: Stwórz szczegółowy ranking i rekomendację dla TOP 3 banków.

Otrzymujesz:
1. Profil klienta
2. Wyniki walidacji wszystkich banków
3. Oceny jakości TOP banków

Twoim zadaniem jest:
1. Przeanalizować mocne i słabe strony każdego z TOP 3 banków
2. Stworzyć szczegółowe rekomendacje dla każdego banku
3. Porównać banki w formie tabeli
4. Wskazać NAJLEPSZĄ opcję z uzasadnieniem

FORMAT ODPOWIEDZI (Markdown):

## 🥇 MIEJSCE 1: [Nazwa Banku]

**Ocena: XX/100 pkt**

### Dlaczego ten bank?
[Szczegółowe uzasadnienie - 3-4 zdania]

### Kluczowe zalety:
- [Zaleta 1 z konkretną wartością]
- [Zaleta 2 z konkretną wartością]
- [Zaleta 3 z konkretną wartością]

### Punkty uwagi:
- [Uwaga 1]
- [Uwaga 2]

---

[Analogicznie dla 🥈 i 🥉]

## 📊 TABELA PORÓWNAWCZA

| Kryterium | 🥇 Bank 1 | 🥈 Bank 2 | 🥉 Bank 3 |
|-----------|-----------|-----------|-----------|
| Ocena | XX/100 | XX/100 | XX/100 |
| Koszt kredytu | ... | ... | ... |
| Elastyczność | ... | ... | ... |
| ... | ... | ... | ... |

## 💡 FINALNA REKOMENDACJA

[2-3 zdania wskazujące NAJLEPSZY wybór z głównym uzasadnieniem]

## 📋 PODSUMOWANIE

[Krótkie podsumowanie całej analizy]
"""
        
        # Przygotuj kontekst TOP banków (pełne dane)
        banks_context = {}
        for bank_name in top_banks[:3]:
            banks_context[bank_name] = self.context_loader.get_full_bank_context(bank_name)
        
        banks_json = json.dumps(banks_context, ensure_ascii=False, indent=2)
        
        # Profil klienta
        profile_json = json.dumps(
            customer_profile.to_dict() if hasattr(customer_profile, 'to_dict') else customer_profile,
            ensure_ascii=False,
            indent=2
        )
        
        # Wyniki walidacji i jakości
        results_summary = {
            "validation": validation_results,
            "quality": quality_scores
        }
        results_json = json.dumps(results_summary, ensure_ascii=False, indent=2)
        
        messages = [
            {
                "role": "system",
                "content": ranking_template
            },
            {
                "role": "system",
                "content": f"# DANE TOP 3 BANKÓW\n\n```json\n{banks_json}\n```"
            },
            {
                "role": "system",
                "content": f"# WYNIKI ANALIZY\n\n```json\n{results_json}\n```"
            },
            {
                "role": "user",
                "content": f"# PROFIL KLIENTA\n\n```json\n{profile_json}\n```\n\nPrzeanalizuj i stwórz szczegółowy ranking TOP 3 banków."
            }
        ]
        
        return messages
    
    def build_weight_optimization_messages(
        self,
        customer_profile
    ) -> List[Dict[str, str]]:
        """
        Buduje messages dla dynamicznego dostrajania wag kategorii
        
        Args:
            customer_profile: Profil klienta (CustomerProfile lub dict)
            
        Returns:
            Lista messages dla LLM (system prompt + user data)
        """
        # Załaduj template promptu
        weight_template = self.load_prompt("weight_optimization_prompt")
        
        # Profil klienta
        profile_json = json.dumps(
            customer_profile.to_dict() if hasattr(customer_profile, 'to_dict') else customer_profile,
            ensure_ascii=False,
            indent=2
        )
        
        messages = [
            {
                "role": "system",
                "content": weight_template
            },
            {
                "role": "user",
                "content": f"# PROFIL KLIENTA DO ANALIZY\n\n```json\n{profile_json}\n```\n\nPrzeanalizuj profil i zwróć optymalne wagi kategorii w formacie JSON."
            }
        ]
        
        return messages
    
    def build_comparative_quality_messages(
        self,
        qualified_banks: List[str],
        customer_profile,
        weights: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """
        Buduje messages dla porównawczego scoringu jakości
        
        Args:
            qualified_banks: Lista nazw zakwalifikowanych banków
            customer_profile: Profil klienta (CustomerProfile lub dict)
            weights: Wagi kategorii {"koszt": 35.0, "elastycznosc": 25.0, ...}
            
        Returns:
            Lista messages dla LLM (system prompt + banks data + user profile)
        """
        # Załaduj template promptu
        comparative_template = self.load_prompt("comparative_quality_prompt")
        
        # Zbierz parametry JAKOŚĆ dla zakwalifikowanych banków
        banks_quality_data = {}
        for bank_name in qualified_banks:
            banks_quality_data[bank_name] = self.context_loader.get_quality_context(bank_name)
        
        banks_json = json.dumps(banks_quality_data, ensure_ascii=False, indent=2)
        
        # Profil klienta
        profile_json = json.dumps(
            customer_profile.to_dict() if hasattr(customer_profile, 'to_dict') else customer_profile,
            ensure_ascii=False,
            indent=2
        )
        
        # Wagi
        weights_json = json.dumps(weights, ensure_ascii=False, indent=2)
        
        messages = [
            {
                "role": "system",
                "content": comparative_template
            },
            {
                "role": "system",
                "content": f"# PARAMETRY JAKOŚCI ZAKWALIFIKOWANYCH BANKÓW\n\n```json\n{banks_json}\n```"
            },
            {
                "role": "system",
                "content": f"# WAGI KATEGORII (dostrojone do klienta)\n\n```json\n{weights_json}\n```"
            },
            {
                "role": "user",
                "content": f"# PROFIL KLIENTA\n\n```json\n{profile_json}\n```\n\nPorównaj banki i zwróć ranking w formacie JSON."
            }
        ]
        
        return messages
