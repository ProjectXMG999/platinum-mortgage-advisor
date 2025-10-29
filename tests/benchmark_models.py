"""
Benchmark porównawczy modeli AI - ETAP 1 vs ETAP 2
Testuje wszystkie dostępne modele osobno dla walidacji i rankingu
"""
import sys
import os
import time
import json
from datetime import datetime

# Dodaj src do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.query_engine import QueryEngine

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
    "profile_1_simple": {
        "name": "Młode małżeństwo - zakup mieszkania",
        "query": "Mamy 28 i 30 lat, umowy o pracę na czas nieokreślony (staż 3 lata). Chcemy kupić mieszkanie za 600 tys. zł, mamy wkład własny 150 tys. zł (25%). Kredyt na 25 lat w PLN."
    },
    "profile_2_medium": {
        "name": "Senior - zakup działki",
        "query": "Mam 65 lat, emerytura 4500 zł netto. Chcę kupić działkę budowlaną za 250 tys. zł pod budowę domu. Mam wkład własny 100 tys. zł (40%). Kredyt na 15 lat."
    },
    "profile_3_complex": {
        "name": "Przedsiębiorca - budowa domu",
        "query": "Prowadzę działalność gospodarczą (KPiR, 5 lat), dochód 15 tys. miesięcznie. Chcę refinansować budowę domu rozpoczętą 10 miesięcy temu, koszt 800 tys. zł. Potrzebuję 600 tys. kredytu na 30 lat."
    }
}


class ModelBenchmark:
    """Benchmark porównawczy modeli"""
    
    def __init__(self):
        """Inicjalizacja benchmarku"""
        print("\n" + "="*80)
        print("🔬 BENCHMARK MODELI AI - PORÓWNANIE WYDAJNOŚCI")
        print("="*80 + "\n")
        
        self.engine = QueryEngine("data/processed/knowledge_base.json")
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "models_tested": AVAILABLE_MODELS,
            "profiles_tested": len(TEST_PROFILES),
            "etap1_results": {},
            "etap2_results": {},
            "combined_results": {}
        }
    
    def benchmark_etap1_single_model(self, model_name: str, profile_key: str, profile_data: dict) -> dict:
        """
        Testuje pojedynczy model dla ETAP 1 (Walidacja)
        
        Args:
            model_name: Nazwa modelu do testu
            profile_key: Klucz profilu testowego
            profile_data: Dane profilu
            
        Returns:
            Dict z wynikami testu
        """
        print(f"\n{'='*80}")
        print(f"🔍 ETAP 1: {model_name} | {profile_data['name']}")
        print(f"{'='*80}")
        
        try:
            start_time = time.time()
            
            # Uruchom tylko ETAP 1 (async parallel processing)
            result = self.engine.ai_client.query_two_stage(
                user_query=profile_data['query'],
                knowledge_base_context=self.engine.data_processor.format_compact_for_context(),
                etap1_model=model_name,
                etap2_model="gpt-4.1",  # Dummy dla ETAP 2 (nie będzie używany w pomiarze)
                use_async=True,
                knowledge_base_dict=self.engine.data_processor.knowledge_base
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parsuj wyniki ETAP 1
            validation_json = None
            if result.get("stage1_validation"):
                try:
                    validation_text = result["stage1_validation"]
                    if validation_text.startswith("```json"):
                        validation_text = validation_text[7:]
                    if validation_text.startswith("```"):
                        validation_text = validation_text[3:]
                    if validation_text.endswith("```"):
                        validation_text = validation_text[:-3]
                    validation_json = json.loads(validation_text.strip())
                except:
                    pass
            
            qualified_count = len(result.get("qualified_banks", []))
            
            result_data = {
                "model": model_name,
                "profile": profile_key,
                "duration_seconds": round(duration, 2),
                "qualified_banks": qualified_count,
                "total_banks": 11,
                "success": True
            }
            
            print(f"✅ Czas: {duration:.2f}s | Zakwalifikowane: {qualified_count}/11")
            return result_data
            
        except Exception as e:
            print(f"❌ Błąd: {str(e)}")
            return {
                "model": model_name,
                "profile": profile_key,
                "duration_seconds": 0,
                "error": str(e),
                "success": False
            }
    
    def benchmark_etap2_single_model(self, model_name: str, profile_key: str, profile_data: dict) -> dict:
        """
        Testuje pojedynczy model dla ETAP 2 (Ranking)
        Najpierw uruchamia ETAP 1 z domyślnym modelem, potem ETAP 2 z testowanym modelem
        
        Args:
            model_name: Nazwa modelu do testu
            profile_key: Klucz profilu testowego
            profile_data: Dane profilu
            
        Returns:
            Dict z wynikami testu
        """
        print(f"\n{'='*80}")
        print(f"🏅 ETAP 2: {model_name} | {profile_data['name']}")
        print(f"{'='*80}")
        
        try:
            # Najpierw ETAP 1 z domyślnym modelem (żeby mieć zakwalifikowane banki)
            print("  → Przygotowanie: ETAP 1 z gpt-4.1...")
            prep_result = self.engine.ai_client.query_two_stage(
                user_query=profile_data['query'],
                knowledge_base_context=self.engine.data_processor.format_compact_for_context(),
                etap1_model="gpt-4.1",
                etap2_model=model_name,  # Będziemy mierzyć ten ETAP 2
                use_async=True,
                knowledge_base_dict=self.engine.data_processor.knowledge_base
            )
            
            # Teraz zmierz czas tylko ETAP 2
            # Niestety musimy uruchomić cały pipeline, ale odejmiemy czas ETAP 1
            
            start_time = time.time()
            
            result = self.engine.ai_client.query_two_stage(
                user_query=profile_data['query'],
                knowledge_base_context=self.engine.data_processor.format_compact_for_context(),
                etap1_model="gpt-4.1",  # Szybki model dla ETAP 1
                etap2_model=model_name,  # Testowany model dla ETAP 2
                use_async=True,
                knowledge_base_dict=self.engine.data_processor.knowledge_base
            )
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Oszacowanie: ETAP 1 z gpt-4.1 async ~3-5s, ETAP 2 to reszta
            # Dla dokładności uruchomimy tylko ETAP 2
            qualified_banks = result.get("qualified_banks", [])
            
            if len(qualified_banks) > 0:
                # Zmierz czysty czas ETAP 2
                etap2_start = time.time()
                
                ranking_result = self.engine.ai_client.rank_by_quality(
                    user_query=profile_data['query'],
                    knowledge_base_context=self.engine.data_processor.format_compact_for_context(),
                    qualified_banks=qualified_banks,
                    deployment_name=model_name
                )
                
                etap2_end = time.time()
                etap2_duration = etap2_end - etap2_start
            else:
                etap2_duration = 0
                print("  ⚠️ Brak zakwalifikowanych banków - pomijam ETAP 2")
            
            result_data = {
                "model": model_name,
                "profile": profile_key,
                "duration_seconds": round(etap2_duration, 2),
                "qualified_banks": len(qualified_banks),
                "success": True
            }
            
            print(f"✅ Czas ETAP 2: {etap2_duration:.2f}s | Banków: {len(qualified_banks)}")
            return result_data
            
        except Exception as e:
            print(f"❌ Błąd: {str(e)}")
            return {
                "model": model_name,
                "profile": profile_key,
                "duration_seconds": 0,
                "error": str(e),
                "success": False
            }
    
    def run_etap1_benchmark(self):
        """Testuje wszystkie modele dla ETAP 1"""
        print("\n" + "🔍"*40)
        print("BENCHMARK ETAP 1: WALIDACJA WYMOGÓW (ASYNC PARALLEL)")
        print("🔍"*40 + "\n")
        
        for model in AVAILABLE_MODELS:
            model_results = []
            
            for profile_key, profile_data in TEST_PROFILES.items():
                result = self.benchmark_etap1_single_model(model, profile_key, profile_data)
                model_results.append(result)
                time.sleep(1)  # Krótka przerwa między testami
            
            # Oblicz średnią
            successful_results = [r for r in model_results if r.get("success")]
            if successful_results:
                avg_duration = sum(r["duration_seconds"] for r in successful_results) / len(successful_results)
                self.results["etap1_results"][model] = {
                    "average_duration": round(avg_duration, 2),
                    "tests": model_results,
                    "tests_count": len(successful_results)
                }
            
            print(f"\n{'─'*80}")
            print(f"📊 {model} - Średnia ETAP 1: {avg_duration:.2f}s")
            print(f"{'─'*80}\n")
    
    def run_etap2_benchmark(self):
        """Testuje wszystkie modele dla ETAP 2"""
        print("\n" + "🏅"*40)
        print("BENCHMARK ETAP 2: RANKING JAKOŚCI")
        print("🏅"*40 + "\n")
        
        for model in AVAILABLE_MODELS:
            model_results = []
            
            for profile_key, profile_data in TEST_PROFILES.items():
                result = self.benchmark_etap2_single_model(model, profile_key, profile_data)
                model_results.append(result)
                time.sleep(1)  # Krótka przerwa między testami
            
            # Oblicz średnią
            successful_results = [r for r in model_results if r.get("success")]
            if successful_results:
                avg_duration = sum(r["duration_seconds"] for r in successful_results) / len(successful_results)
                self.results["etap2_results"][model] = {
                    "average_duration": round(avg_duration, 2),
                    "tests": model_results,
                    "tests_count": len(successful_results)
                }
            
            print(f"\n{'─'*80}")
            print(f"📊 {model} - Średnia ETAP 2: {avg_duration:.2f}s")
            print(f"{'─'*80}\n")
    
    def generate_rankings(self):
        """Generuje rankingi modeli dla obu etapów"""
        print("\n" + "="*80)
        print("🏆 RANKINGI MODELI")
        print("="*80 + "\n")
        
        # Ranking ETAP 1
        etap1_ranking = sorted(
            [(model, data["average_duration"]) for model, data in self.results["etap1_results"].items()],
            key=lambda x: x[1]
        )
        
        print("🔍 ETAP 1: WALIDACJA WYMOGÓW (szybciej = lepiej)")
        print("─"*80)
        for i, (model, duration) in enumerate(etap1_ranking, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            print(f"{medal} {model:20s} → {duration:6.2f}s")
        
        # Ranking ETAP 2
        etap2_ranking = sorted(
            [(model, data["average_duration"]) for model, data in self.results["etap2_results"].items()],
            key=lambda x: x[1]
        )
        
        print("\n🏅 ETAP 2: RANKING JAKOŚCI (szybciej = lepiej)")
        print("─"*80)
        for i, (model, duration) in enumerate(etap2_ranking, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            print(f"{medal} {model:20s} → {duration:6.2f}s")
        
        # Ranking TOTAL (ETAP 1 + ETAP 2)
        combined_ranking = []
        for model in AVAILABLE_MODELS:
            etap1_time = self.results["etap1_results"].get(model, {}).get("average_duration", 999)
            etap2_time = self.results["etap2_results"].get(model, {}).get("average_duration", 999)
            total_time = etap1_time + etap2_time
            combined_ranking.append((model, total_time, etap1_time, etap2_time))
        
        combined_ranking.sort(key=lambda x: x[1])
        
        print("\n🎯 RANKING TOTAL (ETAP 1 + ETAP 2)")
        print("─"*80)
        for i, (model, total, etap1, etap2) in enumerate(combined_ranking, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            print(f"{medal} {model:20s} → {total:6.2f}s (E1: {etap1:.2f}s + E2: {etap2:.2f}s)")
        
        # Zapisz rankingi do results
        self.results["rankings"] = {
            "etap1": etap1_ranking,
            "etap2": etap2_ranking,
            "combined": combined_ranking
        }
    
    def save_results(self):
        """Zapisuje wyniki do pliku JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/model_benchmark_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Wyniki zapisane: {filename}")
        return filename
    
    def print_summary(self):
        """Wyświetla podsumowanie benchmarku"""
        print("\n" + "="*80)
        print("📊 PODSUMOWANIE BENCHMARKU")
        print("="*80)
        
        print(f"\n✅ Przetestowane modele: {len(AVAILABLE_MODELS)}")
        print(f"✅ Profile testowe: {len(TEST_PROFILES)}")
        print(f"✅ Całkowita liczba testów: {len(AVAILABLE_MODELS) * len(TEST_PROFILES) * 2}")
        
        # Najszybszy model dla każdego etapu
        if self.results.get("rankings"):
            etap1_winner = self.results["rankings"]["etap1"][0]
            etap2_winner = self.results["rankings"]["etap2"][0]
            total_winner = self.results["rankings"]["combined"][0]
            
            print(f"\n🏆 ZWYCIĘZCY:")
            print(f"  🔍 ETAP 1: {etap1_winner[0]} ({etap1_winner[1]:.2f}s)")
            print(f"  🏅 ETAP 2: {etap2_winner[0]} ({etap2_winner[1]:.2f}s)")
            print(f"  🎯 TOTAL:  {total_winner[0]} ({total_winner[1]:.2f}s)")
            
            # Porównanie z celem <15s
            if total_winner[1] < 15:
                print(f"\n✅ CEL OSIĄGNIĘTY! {total_winner[0]} wykonuje full pipeline w {total_winner[1]:.2f}s (<15s)")
            else:
                print(f"\n⚠️ CEL NIE OSIĄGNIĘTY. Najszybszy: {total_winner[1]:.2f}s (cel: <15s)")


def main():
    """Główna funkcja benchmarku"""
    benchmark = ModelBenchmark()
    
    # Test wszystkich modeli dla ETAP 1
    benchmark.run_etap1_benchmark()
    
    # Test wszystkich modeli dla ETAP 2
    benchmark.run_etap2_benchmark()
    
    # Generuj rankingi
    benchmark.generate_rankings()
    
    # Podsumowanie
    benchmark.print_summary()
    
    # Zapisz wyniki
    benchmark.save_results()
    
    print("\n" + "="*80)
    print("✅ BENCHMARK ZAKOŃCZONY")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
