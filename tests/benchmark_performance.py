"""
Benchmark wydajności systemu dwupromptowego
Cel: Czas całkowity < 15 sekund

Mierzy:
1. Czas ładowania bazy wiedzy
2. Czas ETAP 1: Walidacja WYMOGÓW
3. Czas ETAP 2: Ranking JAKOŚCI
4. Czas parsowania JSON
5. Całkowity czas end-to-end
"""

import time
import sys
import os
import json
from datetime import datetime
from typing import Dict, List

# Dodaj src do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.query_engine import QueryEngine
from src.ai_client import AIClient
from src.data_processor import DataProcessor

class PerformanceBenchmark:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "measurements": [],
            "summary": {}
        }
    
    def measure_time(self, operation_name: str, func, *args, **kwargs):
        """Mierzy czas wykonania funkcji"""
        print(f"\n⏱️  測定: {operation_name}...")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            measurement = {
                "operation": operation_name,
                "elapsed_seconds": round(elapsed, 3),
                "status": "success"
            }
            
            self.results["measurements"].append(measurement)
            print(f"✅ {operation_name}: {elapsed:.3f}s")
            
            return result, elapsed
            
        except Exception as e:
            elapsed = time.time() - start_time
            measurement = {
                "operation": operation_name,
                "elapsed_seconds": round(elapsed, 3),
                "status": "error",
                "error": str(e)
            }
            self.results["measurements"].append(measurement)
            print(f"❌ {operation_name}: BŁĄD po {elapsed:.3f}s - {e}")
            return None, elapsed
    
    def benchmark_initialization(self):
        """Test 1: Inicjalizacja systemu"""
        print("\n" + "="*80)
        print("TEST 1: INICJALIZACJA SYSTEMU")
        print("="*80)
        
        # Ładowanie bazy wiedzy
        engine, load_time = self.measure_time(
            "Ładowanie bazy wiedzy",
            QueryEngine,
            "data/processed/knowledge_base.json"
        )
        
        # Ładowanie klasyfikacji parametrów
        _, classif_time = self.measure_time(
            "Ładowanie klasyfikacji parametrów",
            lambda: engine.ai_client._load_parameter_classification()
        )
        
        # Formatowanie kontekstu
        _, format_time = self.measure_time(
            "Formatowanie kontekstu dla AI",
            lambda: engine.data_processor.format_compact_for_context()
        )
        
        total_init = load_time + classif_time + format_time
        print(f"\n📊 Całkowity czas inicjalizacji: {total_init:.3f}s")
        
        return engine
    
    def benchmark_validation_stage(self, engine: QueryEngine, test_query: str):
        """Test 2: ETAP 1 - Walidacja WYMOGÓW"""
        print("\n" + "="*80)
        print("TEST 2: ETAP 1 - WALIDACJA WYMOGÓW (68 parametrów)")
        print("="*80)
        
        knowledge_base = engine.data_processor.format_compact_for_context()
        
        # Tworzenie promptu
        validation_prompt, prompt_time = self.measure_time(
            "Tworzenie promptu walidacyjnego",
            lambda: engine.ai_client.create_validation_prompt()
        )
        
        # Wywołanie API OpenAI - ETAP 1
        validation_result, api_time_1 = self.measure_time(
            "API Call: ETAP 1 (walidacja)",
            engine.ai_client.validate_requirements,
            test_query,
            knowledge_base
        )
        
        # Parsowanie JSON
        if validation_result:
            response_text, parsed_data = validation_result
            _, parse_time = self.measure_time(
                "Parsowanie JSON z ETAP 1",
                lambda: parsed_data
            )
            
            # Wyciągnij listę zakwalifikowanych
            qualified = []
            if parsed_data and "qualified_banks" in parsed_data:
                qualified = [b["bank_name"] for b in parsed_data["qualified_banks"]]
            
            print(f"\n📊 Zakwalifikowane banki: {len(qualified)}")
            print(f"📊 Czas API (ETAP 1): {api_time_1:.3f}s")
            
            return qualified, validation_result, api_time_1
        
        return [], None, api_time_1
    
    def benchmark_ranking_stage(self, engine: QueryEngine, test_query: str, qualified_banks: List[str]):
        """Test 3: ETAP 2 - Ranking JAKOŚCI"""
        print("\n" + "="*80)
        print(f"TEST 3: ETAP 2 - RANKING JAKOŚCI (19 parametrów, {len(qualified_banks)} banków)")
        print("="*80)
        
        if len(qualified_banks) == 0:
            print("⚠️ Brak banków do rankingu")
            return None, 0
        
        knowledge_base = engine.data_processor.format_compact_for_context()
        
        # Tworzenie promptu rankingowego
        ranking_prompt, prompt_time = self.measure_time(
            "Tworzenie promptu rankingowego",
            engine.ai_client.create_ranking_prompt,
            qualified_banks
        )
        
        # Wywołanie API OpenAI - ETAP 2
        ranking_result, api_time_2 = self.measure_time(
            "API Call: ETAP 2 (ranking)",
            engine.ai_client.rank_by_quality,
            test_query,
            knowledge_base,
            qualified_banks
        )
        
        print(f"\n📊 Czas API (ETAP 2): {api_time_2:.3f}s")
        
        return ranking_result, api_time_2
    
    def benchmark_full_pipeline(self, test_profile: Dict):
        """Test 4: Pełny pipeline end-to-end"""
        print("\n" + "="*80)
        print("TEST 4: PEŁNY PIPELINE END-TO-END")
        print("="*80)
        
        print(f"Profil testowy: {test_profile['name']}")
        print(f"Długość zapytania: {len(test_profile['query'])} znaków")
        
        # Inicjalizacja
        engine = self.benchmark_initialization()
        
        if not engine:
            print("❌ Inicjalizacja nie powiodła się")
            return
        
        # ETAP 1: Walidacja
        qualified, validation_result, time_etap1 = self.benchmark_validation_stage(
            engine, 
            test_profile['query']
        )
        
        # ETAP 2: Ranking
        ranking_result, time_etap2 = self.benchmark_ranking_stage(
            engine,
            test_profile['query'],
            qualified
        )
        
        # Oblicz całkowity czas
        total_measurements = [m for m in self.results["measurements"]]
        total_time = sum(m["elapsed_seconds"] for m in total_measurements if m["status"] == "success")
        
        print("\n" + "="*80)
        print("📊 PODSUMOWANIE WYDAJNOŚCI")
        print("="*80)
        
        # Grupuj czasy
        init_time = sum(m["elapsed_seconds"] for m in total_measurements 
                       if "Ładowanie" in m["operation"] or "Formatowanie" in m["operation"])
        
        processing_time = time_etap1 + time_etap2
        
        print(f"\n⏱️  Czasy poszczególnych faz:")
        print(f"   1. Inicjalizacja:     {init_time:.3f}s ({init_time/total_time*100:.1f}%)")
        print(f"   2. ETAP 1 (walidacja): {time_etap1:.3f}s ({time_etap1/total_time*100:.1f}%)")
        print(f"   3. ETAP 2 (ranking):   {time_etap2:.3f}s ({time_etap2/total_time*100:.1f}%)")
        print(f"   ────────────────────────────")
        print(f"   CAŁKOWITY CZAS:       {total_time:.3f}s")
        
        # Ocena względem celu
        target = 15.0
        if total_time <= target:
            status = f"✅ CEL OSIĄGNIĘTY ({total_time:.3f}s ≤ {target}s)"
            color = "green"
        else:
            excess = total_time - target
            status = f"❌ PRZEKROCZENIE ({total_time:.3f}s > {target}s, +{excess:.3f}s)"
            color = "red"
        
        print(f"\n{status}")
        
        # Zapisz podsumowanie
        self.results["summary"] = {
            "total_time_seconds": round(total_time, 3),
            "initialization_time": round(init_time, 3),
            "etap1_time": round(time_etap1, 3),
            "etap2_time": round(time_etap2, 3),
            "target_time": target,
            "within_target": total_time <= target,
            "excess_time": round(max(0, total_time - target), 3),
            "qualified_banks_count": len(qualified)
        }
        
        return self.results
    
    def identify_bottlenecks(self):
        """Identyfikuje wąskie gardła"""
        print("\n" + "="*80)
        print("🔍 ANALIZA WĄSKICH GARDEŁ")
        print("="*80)
        
        measurements = sorted(
            self.results["measurements"],
            key=lambda x: x["elapsed_seconds"],
            reverse=True
        )
        
        print("\n📉 TOP 5 najwolniejszych operacji:")
        for i, m in enumerate(measurements[:5], 1):
            print(f"   {i}. {m['operation']:40s} {m['elapsed_seconds']:.3f}s")
        
        # Rekomendacje
        print("\n💡 REKOMENDACJE OPTYMALIZACJI:")
        
        summary = self.results.get("summary", {})
        etap1_time = summary.get("etap1_time", 0)
        etap2_time = summary.get("etap2_time", 0)
        init_time = summary.get("initialization_time", 0)
        
        recommendations = []
        
        if etap1_time > 8:
            recommendations.append({
                "priority": "HIGH",
                "area": "ETAP 1 (Walidacja)",
                "current_time": f"{etap1_time:.3f}s",
                "suggestions": [
                    "Zmniejsz max_tokens (obecnie 16000)",
                    "Uprość prompt walidacyjny",
                    "Rozważ cache dla powtarzających się zapytań",
                    "Użyj szybszego modelu (gpt-4o-mini zamiast gpt-4o)"
                ]
            })
        
        if etap2_time > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "area": "ETAP 2 (Ranking)",
                "current_time": f"{etap2_time:.3f}s",
                "suggestions": [
                    "Ogranicz ranking do TOP 4 (zamiast wszystkich)",
                    "Zmniejsz szczegółowość opisu",
                    "Rozważ równoległe wywołania API"
                ]
            })
        
        if init_time > 2:
            recommendations.append({
                "priority": "LOW",
                "area": "Inicjalizacja",
                "current_time": f"{init_time:.3f}s",
                "suggestions": [
                    "Cache bazy wiedzy w pamięci",
                    "Lazy loading klasyfikacji parametrów",
                    "Prekompilowane prompty"
                ]
            })
        
        for rec in recommendations:
            print(f"\n   [{rec['priority']}] {rec['area']} - {rec['current_time']}")
            for suggestion in rec['suggestions']:
                print(f"      • {suggestion}")
        
        return recommendations
    
    def save_results(self, filename: str = None):
        """Zapisuje wyniki do pliku JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        filepath = os.path.join("test_results", filename)
        os.makedirs("test_results", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Wyniki zapisane: {filepath}")
        return filepath


def main():
    """Główna funkcja benchmarku"""
    
    # Profile testowe o różnej złożoności
    test_profiles = [
        {
            "name": "Prosty profil (młode małżeństwo)",
            "query": """Klient: Jan Kowalski, 32 lata
DOCHODY: UoP na czas nieokreślony, 8,000 zł/mc, staż 5 lat
CEL: Zakup mieszkania 350,000 zł
PARAMETRY: Wkład własny 100,000 zł (28%), kredyt 250,000 zł, okres 25 lat"""
        },
        {
            "name": "Średni profil (senior, działka)",
            "query": """Klient: Senior, 68 lat (emeryt)
Współkredytobiorca: Małżonka, 65 lat (emerytka)
DOCHODY: Emerytura 9,000 zł/mc łącznie
CEL: Zakup działki rekreacyjnej (1,500 m2) w górach
PARAMETRY: Cena działki: 150,000 zł, Wkład własny: 50,000 zł (33%), Kwota kredytu: 100,000 zł, Okres: 10 lat"""
        },
        {
            "name": "Złożony profil (budowa domu)",
            "query": """Klient: Małgorzata Nowak, 34 lata
Współkredytobiorca: Piotr Nowak, 37 lat
DOCHODY:
- Małgorzata: UoP, 8,000 zł/mc, staż 4 lata
- Piotr: Działalność gospodarcza (KPiR), 24 miesiące
CEL: Budowa domu jednorodzinnego
PARAMETRY: Koszt budowy: 600,000 zł, Działka w posiadaniu (wartość 100,000 zł), Wkład własny: 140,000 zł (20%), Kwota kredytu: 560,000 zł, Okres: 30 lat"""
        }
    ]
    
    print("="*80)
    print("🚀 BENCHMARK WYDAJNOŚCI SYSTEMU DWUPROMPTOWEGO")
    print("="*80)
    print(f"Cel: Całkowity czas < 15 sekund")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Profile testowe: {len(test_profiles)}")
    
    all_results = []
    
    for i, profile in enumerate(test_profiles, 1):
        print(f"\n\n{'='*80}")
        print(f"BENCHMARK #{i}/{len(test_profiles)}: {profile['name']}")
        print(f"{'='*80}")
        
        benchmark = PerformanceBenchmark()
        results = benchmark.benchmark_full_pipeline(profile)
        
        if results:
            benchmark.identify_bottlenecks()
            filepath = benchmark.save_results(f"benchmark_{i}_{profile['name'].replace(' ', '_')}.json")
            all_results.append(results)
        
        # Przerwa między testami
        if i < len(test_profiles):
            print("\n⏸️  Przerwa 3 sekundy przed kolejnym testem...")
            time.sleep(3)
    
    # Podsumowanie wszystkich testów
    print("\n\n" + "="*80)
    print("📊 PODSUMOWANIE WSZYSTKICH TESTÓW")
    print("="*80)
    
    for i, result in enumerate(all_results, 1):
        summary = result["summary"]
        status = "✅" if summary["within_target"] else "❌"
        print(f"{status} Test {i}: {summary['total_time_seconds']:.3f}s "
              f"(ETAP1: {summary['etap1_time']:.3f}s, ETAP2: {summary['etap2_time']:.3f}s)")
    
    avg_time = sum(r["summary"]["total_time_seconds"] for r in all_results) / len(all_results)
    print(f"\n📈 Średni czas: {avg_time:.3f}s")
    print(f"🎯 Cel: 15.000s")
    
    if avg_time <= 15.0:
        print(f"✅ SUKCES! Średni czas mieści się w celu")
    else:
        print(f"❌ Wymaga optymalizacji (przekroczenie o {avg_time - 15.0:.3f}s)")


if __name__ == "__main__":
    main()
