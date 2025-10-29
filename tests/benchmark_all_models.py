"""
Kompleksowy benchmark wszystkich modeli AI
Cel: Ranking wydajności dla każdego modelu w ETAP 1 i ETAP 2

Testuje:
- 6 modeli: gpt-4.1, gpt-4.1-nano, gpt-5-mini, gpt-5-nano, o1, o4-mini
- 3 profile klientów (simple, medium, complex)
- Osobno ETAP 1 (walidacja) i ETAP 2 (ranking)
- Tryb async parallel vs sequential

Wynik: Ranking modeli według szybkości dla każdego etapu
"""

import time
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
import asyncio

# Dodaj src do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.query_engine import QueryEngine
from src.ai_client import AIClient
from src.data_processor import DataProcessor

# Dostępne modele
AVAILABLE_MODELS = [
    "gpt-4.1",
    "gpt-4.1-nano",
    "gpt-5-mini",
    "gpt-5-nano",
    "o1",
    "o4-mini"
]

# Profile testowe
TEST_PROFILES = {
    "simple": {
        "name": "Młode małżeństwo - zakup mieszkania",
        "query": """Młode małżeństwo (28 i 30 lat) chce kupić mieszkanie za 600,000 zł. 
Wkład własny: 150,000 zł. Oboje na umowie o pracę na czas nieokreślony (staż 4 lata). 
Wspólne dochody: 15,000 zł netto/miesiąc. Brak innych kredytów."""
    },
    "medium": {
        "name": "Senior - zakup działki pod budowę",
        "query": """Klient (55 lat) planuje zakup działki budowlanej (1200 m2) za 250,000 zł 
i budowę domu systemem zleconym (koszt 800,000 zł). Wkład własny: 400,000 zł. 
Dochód z działalności gospodarczej (pełna księgowość, 8 lat): 18,000 zł netto. 
Jeden kredyt konsumpcyjny: 500 zł/mc."""
    },
    "complex": {
        "name": "Inwestor - kamienica z lokalami",
        "query": """Inwestor (42 lata) kupuje kamienicę z 3 lokalami użytkowymi za 2,500,000 zł. 
Wkład własny: 750,000 zł. Dochody: umowa o pracę (12,000 zł) + wynajem 2 mieszkań (6,000 zł) 
+ dywidendy ze spółki (4,000 zł, otrzymywane 3 lata). Transakcja rodzinna (brat sprzedaje). 
Kredyt hipoteczny w PKO BP: 800,000 zł (500 zł/mc pozostało)."""
    }
}


class ModelBenchmark:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "models_tested": AVAILABLE_MODELS,
            "profiles_tested": list(TEST_PROFILES.keys()),
            "etap1_results": {},  # model -> [times]
            "etap2_results": {},  # model -> [times]
            "etap1_ranking": [],
            "etap2_ranking": [],
            "detailed_results": []
        }
        
        # Inicjalizuj QueryEngine raz
        print("\n" + "="*80)
        print("🚀 INICJALIZACJA SYSTEMU")
        print("="*80)
        self.engine = QueryEngine("data/processed/knowledge_base.json")
        print("✅ System gotowy\n")
    
    def test_model_etap1(
        self, 
        model_name: str, 
        profile_name: str, 
        query: str,
        use_async: bool = True
    ) -> Tuple[float, int, bool]:
        """
        Testuje model w ETAP 1 (Walidacja WYMOGÓW)
        
        Returns:
            Tuple[czas, liczba_zakwalifikowanych, success]
        """
        knowledge_base = self.engine.data_processor.format_compact_for_context()
        knowledge_base_dict = self.engine.data_processor.knowledge_base
        
        print(f"  🔍 ETAP 1: {model_name} | {profile_name} | {'ASYNC' if use_async else 'SYNC'}")
        
        start_time = time.time()
        
        try:
            if use_async:
                # Async parallel processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    validation_response, validation_data = loop.run_until_complete(
                        self.engine.ai_client.validate_requirements_async(
                            user_query=query,
                            knowledge_base=knowledge_base_dict,
                            deployment_name=model_name
                        )
                    )
                finally:
                    loop.close()
            else:
                # Sequential processing
                validation_response, validation_data = self.engine.ai_client.validate_requirements(
                    user_query=query,
                    knowledge_base_context=knowledge_base
                )
            
            elapsed = time.time() - start_time
            
            # Zlicz zakwalifikowane banki
            qualified_count = 0
            if validation_data and "qualified_banks" in validation_data:
                qualified_count = len(validation_data["qualified_banks"])
            
            print(f"    ✅ {elapsed:.2f}s | Zakwalifikowane: {qualified_count}/11")
            
            return elapsed, qualified_count, True
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"    ❌ {elapsed:.2f}s | BŁĄD: {str(e)[:100]}")
            return elapsed, 0, False
    
    def test_model_etap2(
        self, 
        model_name: str, 
        profile_name: str, 
        query: str,
        qualified_banks: List[str]
    ) -> Tuple[float, bool]:
        """
        Testuje model w ETAP 2 (Ranking JAKOŚCI)
        
        Returns:
            Tuple[czas, success]
        """
        if len(qualified_banks) == 0:
            print(f"  🏅 ETAP 2: {model_name} | {profile_name} | SKIP (brak banków)")
            return 0, False
        
        knowledge_base = self.engine.data_processor.format_compact_for_context()
        
        print(f"  🏅 ETAP 2: {model_name} | {profile_name} | {len(qualified_banks)} banków")
        
        start_time = time.time()
        
        try:
            ranking_response = self.engine.ai_client.rank_by_quality(
                user_query=query,
                knowledge_base_context=knowledge_base,
                qualified_banks=qualified_banks,
                deployment_name=model_name
            )
            
            elapsed = time.time() - start_time
            print(f"    ✅ {elapsed:.2f}s")
            
            return elapsed, True
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"    ❌ {elapsed:.2f}s | BŁĄD: {str(e)[:100]}")
            return elapsed, False
    
    def run_comprehensive_benchmark(self, use_async: bool = True):
        """
        Uruchamia kompletny benchmark dla wszystkich modeli i profili
        """
        print("\n" + "="*80)
        print("📊 KOMPLEKSOWY BENCHMARK WSZYSTKICH MODELI")
        print("="*80)
        print(f"Modele: {len(AVAILABLE_MODELS)}")
        print(f"Profile: {len(TEST_PROFILES)}")
        print(f"Tryb: {'ASYNC PARALLEL' if use_async else 'SEQUENTIAL'}")
        print(f"Łącznie testów: {len(AVAILABLE_MODELS) * len(TEST_PROFILES) * 2} (ETAP 1 + ETAP 2)")
        print("="*80 + "\n")
        
        # Inicjalizuj wyniki dla każdego modelu
        for model in AVAILABLE_MODELS:
            self.results["etap1_results"][model] = []
            self.results["etap2_results"][model] = []
        
        # Iteruj przez wszystkie kombinacje
        for model in AVAILABLE_MODELS:
            print(f"\n{'='*80}")
            print(f"🤖 TESTOWANIE MODELU: {model}")
            print(f"{'='*80}\n")
            
            for profile_key, profile_data in TEST_PROFILES.items():
                profile_name = profile_data["name"]
                query = profile_data["query"]
                
                print(f"\n📋 Profil: {profile_name}")
                print(f"{'─'*80}")
                
                # ETAP 1: Walidacja
                etap1_time, qualified_count, etap1_success = self.test_model_etap1(
                    model_name=model,
                    profile_name=profile_name,
                    query=query,
                    use_async=use_async
                )
                
                if etap1_success:
                    self.results["etap1_results"][model].append(etap1_time)
                
                # ETAP 2: Ranking (tylko jeśli mamy zakwalifikowane banki)
                if qualified_count > 0 and etap1_success:
                    # Dla uproszczenia używamy TOP 4 banków (symulacja)
                    mock_qualified = ["Alior Bank", "PKO BP", "mBank", "Millennium"][:qualified_count]
                    
                    etap2_time, etap2_success = self.test_model_etap2(
                        model_name=model,
                        profile_name=profile_name,
                        query=query,
                        qualified_banks=mock_qualified
                    )
                    
                    if etap2_success:
                        self.results["etap2_results"][model].append(etap2_time)
                else:
                    etap2_time = 0
                    etap2_success = False
                
                # Zapisz szczegółowe wyniki
                self.results["detailed_results"].append({
                    "model": model,
                    "profile": profile_name,
                    "profile_key": profile_key,
                    "etap1_time": etap1_time,
                    "etap1_success": etap1_success,
                    "qualified_count": qualified_count,
                    "etap2_time": etap2_time,
                    "etap2_success": etap2_success,
                    "total_time": etap1_time + etap2_time,
                    "use_async": use_async
                })
                
                print(f"  💰 TOTAL: {etap1_time + etap2_time:.2f}s (ETAP 1: {etap1_time:.2f}s + ETAP 2: {etap2_time:.2f}s)")
        
        # Oblicz ranking
        self.calculate_rankings()
        
        # Wyświetl wyniki
        self.display_results()
        
        # Zapisz do pliku
        self.save_results()
    
    def calculate_rankings(self):
        """Oblicza rankingi modeli według średniego czasu"""
        print("\n" + "="*80)
        print("📊 OBLICZANIE RANKINGÓW")
        print("="*80 + "\n")
        
        # Ranking ETAP 1
        etap1_avg = []
        for model, times in self.results["etap1_results"].items():
            if len(times) > 0:
                avg_time = sum(times) / len(times)
                etap1_avg.append({
                    "model": model,
                    "avg_time": round(avg_time, 3),
                    "min_time": round(min(times), 3),
                    "max_time": round(max(times), 3),
                    "tests_count": len(times)
                })
        
        self.results["etap1_ranking"] = sorted(etap1_avg, key=lambda x: x["avg_time"])
        
        # Ranking ETAP 2
        etap2_avg = []
        for model, times in self.results["etap2_results"].items():
            if len(times) > 0:
                avg_time = sum(times) / len(times)
                etap2_avg.append({
                    "model": model,
                    "avg_time": round(avg_time, 3),
                    "min_time": round(min(times), 3),
                    "max_time": round(max(times), 3),
                    "tests_count": len(times)
                })
        
        self.results["etap2_ranking"] = sorted(etap2_avg, key=lambda x: x["avg_time"])
    
    def display_results(self):
        """Wyświetla czytelne podsumowanie wyników"""
        print("\n" + "="*80)
        print("🏆 RANKING MODELI - ETAP 1 (WALIDACJA WYMOGÓW)")
        print("="*80 + "\n")
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
        
        for idx, result in enumerate(self.results["etap1_ranking"]):
            medal = medals[idx] if idx < len(medals) else f"{idx+1}."
            print(f"{medal} {result['model']:15} | "
                  f"AVG: {result['avg_time']:6.2f}s | "
                  f"MIN: {result['min_time']:6.2f}s | "
                  f"MAX: {result['max_time']:6.2f}s | "
                  f"Tests: {result['tests_count']}")
        
        print("\n" + "="*80)
        print("🏆 RANKING MODELI - ETAP 2 (RANKING JAKOŚCI)")
        print("="*80 + "\n")
        
        for idx, result in enumerate(self.results["etap2_ranking"]):
            medal = medals[idx] if idx < len(medals) else f"{idx+1}."
            print(f"{medal} {result['model']:15} | "
                  f"AVG: {result['avg_time']:6.2f}s | "
                  f"MIN: {result['min_time']:6.2f}s | "
                  f"MAX: {result['max_time']:6.2f}s | "
                  f"Tests: {result['tests_count']}")
        
        # Najlepsza kombinacja
        print("\n" + "="*80)
        print("💡 REKOMENDOWANE KOMBINACJE")
        print("="*80 + "\n")
        
        if self.results["etap1_ranking"] and self.results["etap2_ranking"]:
            best_etap1 = self.results["etap1_ranking"][0]
            best_etap2 = self.results["etap2_ranking"][0]
            
            print(f"🚀 NAJSZYBSZY CZAS CAŁKOWITY:")
            print(f"   ETAP 1: {best_etap1['model']} ({best_etap1['avg_time']:.2f}s)")
            print(f"   ETAP 2: {best_etap2['model']} ({best_etap2['avg_time']:.2f}s)")
            print(f"   TOTAL:  {best_etap1['avg_time'] + best_etap2['avg_time']:.2f}s")
            
            # Sprawdź czy osiągnięto cel <15s
            total_time = best_etap1['avg_time'] + best_etap2['avg_time']
            if total_time < 15:
                print(f"\n   ✅ CEL OSIĄGNIĘTY! ({15 - total_time:.2f}s poniżej limitu 15s)")
            else:
                print(f"\n   ⚠️ CEL NIEOSIĄGNIĘTY ({total_time - 15:.2f}s powyżej limitu 15s)")
    
    def save_results(self):
        """Zapisuje wyniki do pliku JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/model_benchmark_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Wyniki zapisane: {filename}")
        
        # Zapisz również czytelną wersję markdown
        md_filename = f"test_results/model_benchmark_{timestamp}.md"
        self.save_markdown_report(md_filename)
        print(f"📄 Raport markdown: {md_filename}")
    
    def save_markdown_report(self, filename: str):
        """Zapisuje czytelny raport w markdown"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Benchmark Modeli AI - Platinum Mortgage Advisor\n\n")
            f.write(f"**Data:** {self.results['timestamp']}\n\n")
            
            f.write("## 🏆 Ranking ETAP 1 (Walidacja WYMOGÓW)\n\n")
            f.write("| Pozycja | Model | AVG Time | MIN Time | MAX Time | Testy |\n")
            f.write("|---------|-------|----------|----------|----------|---------|\n")
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
            for idx, result in enumerate(self.results["etap1_ranking"]):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}"
                f.write(f"| {medal} | {result['model']} | {result['avg_time']:.2f}s | "
                       f"{result['min_time']:.2f}s | {result['max_time']:.2f}s | "
                       f"{result['tests_count']} |\n")
            
            f.write("\n## 🏆 Ranking ETAP 2 (Ranking JAKOŚCI)\n\n")
            f.write("| Pozycja | Model | AVG Time | MIN Time | MAX Time | Testy |\n")
            f.write("|---------|-------|----------|----------|----------|---------|\n")
            
            for idx, result in enumerate(self.results["etap2_ranking"]):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}"
                f.write(f"| {medal} | {result['model']} | {result['avg_time']:.2f}s | "
                       f"{result['min_time']:.2f}s | {result['max_time']:.2f}s | "
                       f"{result['tests_count']} |\n")
            
            f.write("\n## 📊 Szczegółowe wyniki\n\n")
            f.write("| Model | Profil | ETAP 1 | ETAP 2 | TOTAL | Status |\n")
            f.write("|-------|--------|--------|--------|-------|---------|\n")
            
            for result in self.results["detailed_results"]:
                status = "✅" if result["etap1_success"] and result["etap2_success"] else "⚠️"
                f.write(f"| {result['model']} | {result['profile'][:30]} | "
                       f"{result['etap1_time']:.2f}s | {result['etap2_time']:.2f}s | "
                       f"{result['total_time']:.2f}s | {status} |\n")


def main():
    """Główna funkcja benchmarku"""
    print("\n" + "="*80)
    print("🚀 KOMPLEKSOWY BENCHMARK MODELI AI")
    print("   Platinum Mortgage Advisor - Performance Testing")
    print("="*80)
    
    benchmark = ModelBenchmark()
    
    # Wybór trybu
    print("\nWybierz tryb testowania:")
    print("1. ASYNC PARALLEL (szybki - rekomendowany)")
    print("2. SEQUENTIAL (wolny - dla porównania)")
    
    choice = input("\nWybór (1/2) [domyślnie 1]: ").strip() or "1"
    use_async = choice == "1"
    
    # Uruchom benchmark
    benchmark.run_comprehensive_benchmark(use_async=use_async)
    
    print("\n" + "="*80)
    print("✅ BENCHMARK ZAKOŃCZONY")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
