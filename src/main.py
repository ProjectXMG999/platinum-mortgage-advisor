"""
Platinum Mortgage Advisor - Główny moduł aplikacji
System wyszukiwania produktów hipotecznych oparty na AI
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do modułu config
sys.path.insert(0, str(Path(__file__).parent))

import config
from query_engine import QueryEngine


def print_header():
    """Wyświetla nagłówek aplikacji"""
    print("\n" + "="*80)
    print(" "*20 + "PLATINUM MORTGAGE ADVISOR")
    print(" "*15 + "System wyszukiwania produktów hipotecznych")
    print("="*80)


def print_menu():
    """Wyświetla menu aplikacji"""
    print("\n" + "-"*80)
    print("OPCJE:")
    print("  1. Zadaj zapytanie")
    print("  2. Zobacz przykładowe zapytania")
    print("  3. Lista dostępnych banków")
    print("  4. Wyjście")
    print("-"*80)


def show_example_queries():
    """Wyświetla przykładowe zapytania"""
    examples = [
        "finansowanie wkładu własnego dla osoby powyżej 60 lat",
        "Finansowanie zakupu udziałów we wspólnocie (jak mieszkanie w kamienicy bez księgi wieczystej)",
        "Kredyt bez wkładu własnego",
        "Kredyt dla osoby z małym stażem pracy",
        "Kredyt dla osoby z niskim dochodem na osobę w rodzinie",
        "Kredyt zabezpieczony inną nieruchomością"
    ]
    
    print("\n" + "="*80)
    print("PRZYKŁADOWE ZAPYTANIA:")
    print("="*80)
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print("="*80)


def run_interactive_mode(engine: QueryEngine):
    """
    Uruchamia aplikację w trybie interaktywnym
    
    Args:
        engine: Instancja QueryEngine
    """
    while True:
        print_menu()
        choice = input("\nWybierz opcję (1-4): ").strip()
        
        if choice == '1':
            # Zadaj zapytanie
            print("\n" + "="*80)
            query = input("Wpisz swoje zapytanie: ").strip()
            
            if not query:
                print("❌ Zapytanie nie może być puste!")
                continue
            
            try:
                response = engine.process_query(query)
                print("\n" + "="*80)
                print("📊 WYNIKI WYSZUKIWANIA:")
                print("="*80)
                print(response)
                print("="*80)
            except Exception as e:
                print(f"\n❌ Błąd podczas przetwarzania zapytania: {str(e)}")
        
        elif choice == '2':
            # Pokaż przykłady
            show_example_queries()
        
        elif choice == '3':
            # Lista banków
            banks = engine.get_available_banks()
            print("\n" + "="*80)
            print(f"DOSTĘPNE BANKI ({len(banks)}):")
            print("="*80)
            for i, bank in enumerate(banks, 1):
                print(f"{i}. {bank}")
            print("="*80)
        
        elif choice == '4':
            # Wyjście
            print("\n👋 Do widzenia!")
            break
        
        else:
            print("\n❌ Nieprawidłowa opcja! Wybierz 1-4.")


def main():
    """Główna funkcja aplikacji"""
    print_header()
    
    try:
        # Inicjalizuj silnik zapytań
        engine = QueryEngine(config.KNOWLEDGE_BASE_PATH)
        
        # Uruchom tryb interaktywny
        run_interactive_mode(engine)
    
    except FileNotFoundError as e:
        print(f"\n❌ Błąd: {str(e)}")
        print("Upewnij się, że plik z bazą wiedzy istnieje w: data/processed/knowledge_base.json")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n👋 Przerwano przez użytkownika. Do widzenia!")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
