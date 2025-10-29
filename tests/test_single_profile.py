"""
Test pojedynczego profilu z nowym formatem odpowiedzi
"""
import sys
import json
sys.path.insert(0, '..')

from src.query_engine import QueryEngine


def format_query_from_profile(profile):
    """Formatuje profil klienta do zapytania tekstowego"""
    
    # Podstawowe info
    query_parts = [
        f"Klient: {profile['name']}, {profile['age']} lat, {profile['marital_status']}",
        f"Liczba wnioskodawców: {profile['number_of_applicants']}"
    ]
    
    # Dochód
    income = profile['income']
    if income['type']:
        income_text = f"Dochód: {income['type']}, {income['monthly_gross']} zł brutto/mies"
        if income.get('work_experience_months'):
            income_text += f", staż pracy: {income['work_experience_months']} mies"
        if income.get('current_employer_months'):
            income_text += f", u obecnego pracodawcy: {income['current_employer_months']} mies"
        if income.get('business_duration_months'):
            income_text += f", działalność od: {income['business_duration_months']} mies"
        query_parts.append(income_text)
    
    # Dochód współmałżonka
    if income.get('spouse_income_type'):
        spouse_text = f"Współmałżonek: {income['spouse_income_type']}, {income.get('spouse_monthly_gross', 0)} zł brutto/mies"
        if income.get('spouse_work_experience_months'):
            spouse_text += f", staż: {income['spouse_work_experience_months']} mies"
        query_parts.append(spouse_text)
    
    # Dodatkowy dochód
    if income.get('additional_income'):
        add_income = income['additional_income']
        query_parts.append(f"Dochód dodatkowy: {add_income.get('type', 'nieokreślony')}, {add_income.get('monthly_amount', 0)} zł/mies")
    
    # Kredyt
    loan = profile['loan_details']
    loan_text = f"Cel kredytu: {loan['purpose']}"
    loan_text += f"\nWartość nieruchomości: {loan['property_value']} zł"
    loan_text += f"\nKwota kredytu: {loan['loan_amount']} zł"
    loan_text += f"\nWkład własny: {loan['own_contribution']} zł ({loan['own_contribution_percentage']*100}%)"
    loan_text += f"\nOkres kredytowania: {loan['loan_period_months']} miesięcy"
    loan_text += f"\nWaluta: {loan.get('currency', 'PLN')}"
    query_parts.append(loan_text)
    
    # Nieruchomość
    prop = profile['property']
    prop_text = f"Nieruchomość: {prop['type']}, {prop['market']}, {prop['location']}"
    if prop.get('size_sqm'):
        prop_text += f", {prop['size_sqm']} m2"
    if prop.get('plot_size_sqm'):
        prop_text += f", działka {prop['plot_size_sqm']} m2"
    query_parts.append(prop_text)
    
    # Dodatkowe info
    additional = profile.get('additional_info', {})
    if additional.get('has_other_property'):
        query_parts.append(f"Posiada inną nieruchomość: {additional.get('other_property_type', 'tak')}")
    
    if additional.get('citizenship'):
        query_parts.append(f"Obywatelstwo: {additional['citizenship']}")
        if additional.get('residence_permit'):
            query_parts.append(f"Karta pobytu: {additional['residence_permit']}")
    
    return "\n".join(query_parts)


def main():
    # Wczytaj profile
    with open('../data/processed/customer_profiles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    profiles = data['customer_profiles']
    
    print("\n" + "="*80)
    print("TEST NOWEGO FORMATU ODPOWIEDZI - WYBIERZ PROFIL")
    print("="*80)
    
    # Pokaż listę profili
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile['category']} - {profile['name']}")
    
    # Wybierz profil
    try:
        choice = int(input("\nWybierz numer profilu (1-25): "))
        if choice < 1 or choice > len(profiles):
            print("Nieprawidłowy numer!")
            return
    except ValueError:
        print("Nieprawidłowy input!")
        return
    
    profile = profiles[choice - 1]
    
    print("\n" + "="*80)
    print(f"TESTOWANIE PROFILU #{choice}: {profile['category']}")
    print("="*80)
    
    # Sformatuj zapytanie
    query = format_query_from_profile(profile)
    print("\n📝 ZAPYTANIE:")
    print("-" * 80)
    print(query)
    print("-" * 80)
    
    # Inicjalizuj silnik
    engine = QueryEngine('../data/processed/knowledge_base.json')
    
    # Przetwórz zapytanie
    print("\n🤖 Przetwarzanie przez AI...\n")
    response = engine.process_query(query)
    
    # Wyświetl odpowiedź
    print("\n" + "="*80)
    print("ODPOWIEDŹ AI Z WERYFIKACJĄ WYMOGÓW:")
    print("="*80)
    print(response)
    print("\n" + "="*80)
    
    # Opcjonalnie zapisz do pliku
    save = input("\nCzy zapisać wynik do pliku? (t/n): ").lower()
    if save == 't':
        filename = f'test_result_profile_{choice}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"PROFIL #{choice}: {profile['category']}\n")
            f.write("="*80 + "\n\n")
            f.write("ZAPYTANIE:\n")
            f.write("-" * 80 + "\n")
            f.write(query + "\n")
            f.write("-" * 80 + "\n\n")
            f.write("ODPOWIEDŹ AI:\n")
            f.write("="*80 + "\n")
            f.write(response + "\n")
            f.write("="*80 + "\n")
        print(f"✓ Zapisano do: {filename}")


if __name__ == "__main__":
    main()
