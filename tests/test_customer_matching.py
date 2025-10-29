"""
Skrypt do testowania dopasowania profili klientów do produktów bankowych
"""
import sys
from pathlib import Path
import json

# Dodaj ścieżkę do src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import config
from query_engine import QueryEngine


def load_customer_profiles():
    """Wczytuje profile klientów"""
    profiles_path = Path(__file__).parent.parent / "data" / "processed" / "customer_profiles.json"
    with open(profiles_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_profile_query(profile):
    """Formatuje profil klienta na zapytanie w języku naturalnym"""
    
    # Podstawowe informacje
    age = profile['age']
    marital_status = profile['marital_status']
    num_applicants = profile['number_of_applicants']
    
    # Dochód
    income = profile['income']
    income_type = income['type']
    monthly_income = income.get('monthly_gross', 0)
    
    # Szczegóły kredytu
    loan = profile['loan_details']
    purpose = loan['purpose']
    property_value = loan['property_value']
    loan_amount = loan['loan_amount']
    own_contribution = loan['own_contribution']
    own_contribution_pct = loan['own_contribution_percentage']
    
    # Budowanie zapytania
    query_parts = []
    
    # Nagłówek
    query_parts.append(f"Klient: {profile['name']}, {age} lat, {marital_status}")
    
    if num_applicants > 1:
        query_parts.append(f"Liczba wnioskodawców: {num_applicants}")
    
    # Dochód
    if income_type:
        query_parts.append(f"Źródło dochodu: {income_type}, {monthly_income} zł brutto/mies")
        
        if income.get('work_experience_months'):
            years = income['work_experience_months'] // 12
            months = income['work_experience_months'] % 12
            if months > 0:
                query_parts.append(f"Staż pracy: {years} lat {months} miesięcy")
            else:
                query_parts.append(f"Staż pracy: {years} lat")
        
        if income.get('current_employer_months'):
            months = income['current_employer_months']
            if months < 12:
                query_parts.append(f"U obecnego pracodawcy: {months} miesięcy")
            else:
                years = months // 12
                rest_months = months % 12
                if rest_months > 0:
                    query_parts.append(f"U obecnego pracodawcy: {years} lat {rest_months} miesięcy")
                else:
                    query_parts.append(f"U obecnego pracodawcy: {years} lat")
        
        if income.get('additional_income'):
            add_inc = income['additional_income']
            query_parts.append(f"Dochód dodatkowy: {add_inc.get('type', 'nieokreślony')}, {add_inc.get('monthly_amount', 0)} zł/mies")
        
        if income.get('spouse_income_type'):
            query_parts.append(f"Współwnioskodawca: {income.get('spouse_income_type')}, {income.get('spouse_monthly_gross', 0)} zł brutto/mies")
    
    # Cel kredytu
    query_parts.append(f"\nCel: {purpose}")
    query_parts.append(f"Wartość nieruchomości: {property_value:,.0f} zł")
    query_parts.append(f"Kwota kredytu: {loan_amount:,.0f} zł")
    query_parts.append(f"Wkład własny: {own_contribution:,.0f} zł ({own_contribution_pct}%)")
    
    # LTV
    ltv = (loan_amount / property_value) * 100
    query_parts.append(f"LTV: {ltv:.1f}%")
    
    # Dodatkowe informacje
    additional = profile.get('additional_info', {})
    
    if additional.get('has_other_property'):
        query_parts.append(f"Posiada inną nieruchomość: tak")
        if additional.get('other_property_type'):
            query_parts.append(f"  - {additional['other_property_type']}")
    
    if loan.get('collateral_type'):
        query_parts.append(f"Zabezpieczenie: {loan['collateral_type']}")
    
    if additional.get('number_of_dependents'):
        num_deps = additional['number_of_dependents']
        total_members = additional.get('total_household_members', num_deps + num_applicants)
        query_parts.append(f"Gospodarstwo domowe: {total_members} osób (w tym {num_deps} dzieci)")
    
    if profile.get('property', {}).get('has_land_registry') == False:
        query_parts.append("Nieruchomość bez księgi wieczystej")
    
    # Wyzwania
    if profile.get('challenges'):
        query_parts.append(f"\nGłówne wyzwania:")
        for challenge in profile['challenges']:
            query_parts.append(f"  - {challenge}")
    
    return "\n".join(query_parts)


def test_customer_profile(engine, profile, save_result=True):
    """Testuje pojedynczy profil klienta"""
    
    print("\n" + "="*100)
    print(f"PROFIL #{profile['profile_id']}: {profile['category']}")
    print("="*100)
    
    # Formatuj zapytanie
    query = format_profile_query(profile)
    
    print(f"\n📋 ZAPYTANIE:\n{query}\n")
    print("-"*100)
    
    # Przetwórz zapytanie
    try:
        response = engine.process_query(query)
        
        print(f"\n💡 REKOMENDACJA AI:\n")
        print(response)
        print("\n" + "="*100)
        
        if save_result:
            # Zapisz wynik
            result = {
                "profile_id": profile['profile_id'],
                "category": profile['category'],
                "query": query,
                "response": response,
                "challenges": profile.get('challenges', []),
                "expected_criteria": profile.get('expected_matching_criteria', [])
            }
            return result
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {str(e)}")
        return None


def run_selected_profiles(profile_ids=None, auto_save=True, pause_between=False):
    """Uruchamia testy dla wybranych profili
    
    Args:
        profile_ids: Lista ID profili do przetestowania (None = wszystkie)
        auto_save: Automatycznie zapisz wyniki do pliku JSON
        pause_between: Czekaj na ENTER między profilami
    """
    
    print("\n" + "="*100)
    print(" "*30 + "TEST PROFILI KLIENTÓW")
    print("="*100)
    
    # Wczytaj profile
    data = load_customer_profiles()
    profiles = data['customer_profiles']
    
    # Inicjalizuj silnik
    engine = QueryEngine(config.KNOWLEDGE_BASE_PATH)
    
    # Wybierz profile do testowania
    if profile_ids:
        selected_profiles = [p for p in profiles if p['profile_id'] in profile_ids]
    else:
        # Domyślnie testuj wszystkie profile
        selected_profiles = profiles
    
    print(f"\n📊 Testowanie {len(selected_profiles)} profili klientów...")
    if auto_save:
        print(f"💾 Wyniki będą automatycznie zapisywane do pliku JSON\n")
    else:
        print()
    
    results = []
    for i, profile in enumerate(selected_profiles, 1):
        print(f"\n⏳ Przetwarzanie profilu {i}/{len(selected_profiles)}...")
        result = test_customer_profile(engine, profile)
        if result:
            results.append(result)
        
        # Opcjonalna pauza między profilami
        if pause_between and i < len(selected_profiles):
            input("\n⏸  Naciśnij ENTER aby kontynuować do następnego profilu...")
    
    # Podsumowanie
    print("\n" + "="*100)
    print(f"✅ ZAKOŃCZONO TESTOWANIE {len(results)}/{len(selected_profiles)} PROFILI")
    print("="*100)
    
    # Automatyczny zapis lub pytanie
    if auto_save:
        results_path = Path(__file__).parent.parent / "data" / "processed" / "matching_results.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total_profiles_tested": len(results),
                    "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "deployment_model": config.AZURE_OPENAI_DEPLOYMENT_NAME
                },
                "results": results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Wyniki zapisane do: {results_path}")
        print(f"📊 Przetworzono {len(results)} profili z {len([r for r in results if r])} odpowiedziami")
        
        # Automatycznie generuj raport Markdown
        print(f"\n📝 Generowanie raportów Markdown...")
        try:
            import subprocess
            report_script = Path(__file__).parent / "generate_report.py"
            subprocess.run([sys.executable, str(report_script)], check=True)
        except Exception as e:
            print(f"⚠️  Nie udało się wygenerować raportu: {e}")
            print(f"    Możesz go wygenerować ręcznie: python tests\\generate_report.py")
    else:
        save_choice = input("\nCzy zapisać wyniki do pliku JSON? (t/n): ")
        if save_choice.lower() == 't':
            results_path = Path(__file__).parent.parent / "data" / "processed" / "matching_results.json"
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            from datetime import datetime
            
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": {
                        "total_profiles_tested": len(results),
                        "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "deployment_model": config.AZURE_OPENAI_DEPLOYMENT_NAME
                    },
                    "results": results
                }, f, ensure_ascii=False, indent=2)
            print(f"✅ Wyniki zapisane do: {results_path}")
    
    return results


def show_menu():
    """Wyświetla menu wyboru profili"""
    data = load_customer_profiles()
    profiles = data['customer_profiles']
    
    print("\n" + "="*100)
    print(" "*30 + "PROFILE KLIENTÓW DO TESTOWANIA")
    print("="*100)
    
    # Grupuj po kategoriach
    categories = {}
    for profile in profiles:
        cat = profile['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(profile)
    
    # Wyświetl
    for cat, profs in categories.items():
        print(f"\n{cat}:")
        for p in profs:
            print(f"  [{p['profile_id']:2d}] {p['name']} - {p['age']} lat")
    
    print("\n" + "="*100)
    print("\nOpcje:")
    print("  1. Testuj główne kategorie (profile 1-6) - z pauzami")
    print("  2. Testuj wszystkie profile (1-20) - AUTOMATYCZNIE")
    print("  3. Testuj wszystkie profile (1-20) - z pauzami")
    print("  4. Wybierz konkretne profile")
    print("  5. Wyjście")
    print("="*100)


if __name__ == "__main__":
    show_menu()
    
    choice = input("\nWybierz opcję (1-5): ").strip()
    
    if choice == '1':
        # Główne kategorie z pauzami
        run_selected_profiles(profile_ids=[1, 3, 4, 6, 9, 11], auto_save=True, pause_between=True)
    
    elif choice == '2':
        # Wszystkie profile - AUTOMATYCZNIE
        print("\n🚀 TRYB AUTOMATYCZNY - przetwarzanie wszystkich profili bez przerw...")
        run_selected_profiles(auto_save=True, pause_between=False)
    
    elif choice == '3':
        # Wszystkie profile z pauzami
        run_selected_profiles(auto_save=True, pause_between=True)
    
    elif choice == '4':
        # Wybrane profile
        ids_input = input("Podaj numery profili oddzielone przecinkami (np. 1,5,10): ")
        try:
            ids = [int(x.strip()) for x in ids_input.split(',')]
            pause = input("Chcesz pauzy między profilami? (t/n): ").strip().lower() == 't'
            run_selected_profiles(profile_ids=ids, auto_save=True, pause_between=pause)
        except ValueError:
            print("❌ Nieprawidłowy format!")
    
    elif choice == '5':
        print("\n👋 Do widzenia!")
    
    else:
        print("\n❌ Nieprawidłowa opcja!")
