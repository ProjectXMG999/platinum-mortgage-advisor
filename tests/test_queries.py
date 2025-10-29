"""
Testy dla systemu wyszukiwania produktów hipotecznych
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import config
from query_engine import QueryEngine


def test_query(engine: QueryEngine, query: str, test_number: int):
    """Testuje pojedyncze zapytanie"""
    print(f"\n{'='*80}")
    print(f"TEST {test_number}: {query}")
    print('='*80)
    
    try:
        response = engine.process_query(query)
        print(f"\n{response}")
        print(f"\n✓ Test {test_number} zakończony pomyślnie")
    except Exception as e:
        print(f"\n✗ Test {test_number} zakończony błędem: {str(e)}")
    
    print('='*80)


def run_all_tests():
    """Uruchamia wszystkie testy"""
    print("\n" + "="*80)
    print(" "*25 + "TESTY SYSTEMU")
    print("="*80)
    
    # Inicjalizuj silnik
    engine = QueryEngine(config.KNOWLEDGE_BASE_PATH)
    
    # Lista zapytań testowych
    test_queries = [
        "finansowanie wkładu własnego dla osoby powyżej 60 lat",
        "Finansowanie zakupu udziałów we wspólnocie",
        "Kredyt bez wkładu własnego",
        "Kredyt dla osoby z małym stażem pracy",
        "Kredyt dla osoby z niskim dochodem na osobę w rodzinie",
        "Kredyt zabezpieczony inną nieruchomością"
    ]
    
    # Wykonaj testy
    for i, query in enumerate(test_queries, 1):
        test_query(engine, query, i)
    
    print(f"\n{'='*80}")
    print(f"Wykonano {len(test_queries)} testów")
    print('='*80)


if __name__ == "__main__":
    run_all_tests()
