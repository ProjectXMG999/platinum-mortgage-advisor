"""
Test systemu dwupromptowego: WALIDACJA WYMOGÓW → RANKING JAKOŚCI
"""
import sys
import os
from datetime import datetime

# Dodaj src do ścieżki
sys.path.insert(0, os.path.dirname(__file__))

from src.query_engine import QueryEngine

def test_two_stage_system():
    """Test główny - system dwupromptowy"""
    
    print("\n" + "="*80)
    print("TEST SYSTEMU DWUPROMPTOWEGO")
    print("="*80 + "\n")
    
    # Inicjalizuj silnik
    engine = QueryEngine("data/processed/knowledge_base.json")
    
    # Test query - profil klienta
    test_query = """
Klient: Jan Kowalski, 45 lat
Współkredytobiorca: Anna Kowalska, 42 lata

DOCHODY:
- Jan: Umowa o pracę na czas nieokreślony, staż 5 lat w obecnej firmie
- Anna: Umowa o pracę na czas nieokreślony, staż 3 lata w obecnej firmie

CEL KREDYTU:
Zakup mieszkania na rynku wtórnym w Warszawie

PARAMETRY:
- Cena mieszkania: 800,000 zł
- Wkład własny: 160,000 zł (20%)
- Kwota kredytu: 640,000 zł
- LTV: 80%
- Okres kredytowania: 25 lat (300 miesięcy)
- Preferowane raty: równe

DODATKOWE INFORMACJE:
- Oboje obywatele Polski
- Związek małżeński (wspólność majątkowa)
- Brak innych kredytów hipotecznych
- Stabilna sytuacja finansowa
- Zainteresowani kredytem EKO (mieszkanie ma certyfikat energetyczny klasy B)

Proszę o rekomendację najlepszych ofert bankowych.
"""
    
    print("📋 PROFIL TESTOWY:")
    print("-" * 80)
    print(test_query)
    print("-" * 80)
    print()
    
    # Uruchom dwuetapową analizę
    result = engine.process_query(test_query)
    
    # Wyświetl wynik
    print("\n" + "="*80)
    print("WYNIK ANALIZY")
    print("="*80 + "\n")
    print(result)
    
    # Zapisz do pliku
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results/two_stage_test_{timestamp}.md"
    
    os.makedirs("test_results", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Test Systemu Dwupromptowego\n\n")
        f.write(f"**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Profil Klienta\n\n")
        f.write(f"```\n{test_query}\n```\n\n")
        f.write(f"## Wynik Analizy\n\n")
        f.write(result)
    
    print(f"\n✅ Wynik zapisany do: {output_file}")
    

def test_validation_only():
    """Test tylko etapu 1 - walidacja"""
    
    print("\n" + "="*80)
    print("TEST ETAPU 1: WALIDACJA WYMOGÓW")
    print("="*80 + "\n")
    
    from src.ai_client import AIClient
    from src.data_processor import DataProcessor
    
    # Inicjalizuj komponenty
    ai_client = AIClient()
    data_processor = DataProcessor("data/processed/knowledge_base.json")
    
    # Profil klienta
    test_query = """
Klient: Senior, 68 lat (emeryt)
Współkredytobiorca: Małżonka, 65 lat (emerytka)

DOCHODY:
- Emerytura: 4,500 zł/mc (łącznie 9,000 zł)

CEL:
Zakup działki rekreacyjnej (1,500 m2) w górach

PARAMETRY:
- Cena działki: 150,000 zł
- Wkład własny: 50,000 zł (33%)
- Kwota kredytu: 100,000 zł
- Okres: 10 lat

Która oferta jest możliwa?
"""
    
    knowledge_context = data_processor.format_compact_for_context()
    
    validation_response, validation_data = ai_client.validate_requirements(
        user_query=test_query,
        knowledge_base_context=knowledge_context
    )
    
    print("\n📊 WYNIK WALIDACJI (JSON):")
    print("-" * 80)
    print(validation_response)
    print("-" * 80)
    
    if validation_data:
        print(f"\n✅ Zakwalifikowane: {len(validation_data.get('qualified_banks', []))}")
        print(f"⚠️ Warunkowo: {len(validation_data.get('conditionally_qualified_banks', []))}")
        print(f"❌ Odrzucone: {len(validation_data.get('disqualified_banks', []))}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test systemu dwupromptowego")
    parser.add_argument('--mode', choices=['full', 'validation'], default='full',
                       help='Tryb testu: full (cały system) lub validation (tylko etap 1)')
    
    args = parser.parse_args()
    
    if args.mode == 'validation':
        test_validation_only()
    else:
        test_two_stage_system()
