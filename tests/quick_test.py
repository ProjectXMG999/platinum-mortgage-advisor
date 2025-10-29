"""
Szybki test pierwszego profilu
"""
import sys
import os
import json

# Dodaj główny katalog do path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.query_engine import QueryEngine


def main():
    # Wczytaj profile
    profiles_path = os.path.join(parent_dir, 'data', 'processed', 'customer_profiles.json')
    with open(profiles_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Wybierz profil #1 (kamienica)
    profile = data['customer_profiles'][0]
    
    print("\n" + "="*80)
    print(f"TEST PROFILU #1: {profile['category']}")
    print("="*80)
    print(f"Klient: {profile['name']}, {profile['age']} lat")
    print(f"Cel: {profile['loan_details']['purpose']}")
    print(f"Kwota: {profile['loan_details']['loan_amount']} zł")
    print("="*80)
    
    # Sformatuj zapytanie
    income = profile['income']
    loan = profile['loan_details']
    prop = profile['property']
    add_info = profile['additional_info']
    insurance = profile['insurance']
    collateral = profile['collateral']
    
    # Formatowanie szczegółów dodatkowych dochodów
    additional_income_text = ""
    if income['additional_income']['rental_income']:
        additional_income_text += f"\nDochód z najmu: {income['additional_income']['rental_income_monthly']} zł/mies, od {income['additional_income']['rental_duration_months']} miesięcy"
    if income['additional_income']['child_benefit_800']:
        additional_income_text += f"\n800+: Tak, {income['additional_income']['number_of_children']} dzieci"
    if income['additional_income'].get('alimony_received', 0) > 0:
        additional_income_text += f"\nalimenty: {income['additional_income']['alimony_received']} zł/mies"
    if income['additional_income']['maternity_leave']:
        additional_income_text += f"\nUrlop macierzyński: Tak"
    if income['additional_income']['dividends']:
        additional_income_text += f"\nDywidendy: Tak"
    if income['additional_income']['foreign_currency_income']:
        additional_income_text += f"\nDochód w walucie obcej: Tak"
    
    query = f"""===== DANE KLIENTA =====
Klient: {profile['name']}, {profile['age']} lat, {profile['marital_status']}
Liczba wnioskodawców: {profile['number_of_applicants']}
Obywatelstwo: {profile['citizenship']}
Związek nieformalny: {'Tak' if profile['informal_relationship'] else 'Nie'}
Rozdzielność majątkowa: {'Tak, od ' + str(profile.get('property_separation_years', 0)) + ' lat' if profile['property_separation'] else 'Nie'}

===== ŹRÓDŁO DOCHODU =====
Dochód główny: {income['type']}
Kwota brutto/netto: {income['monthly_gross']} zł / {income['monthly_net']} zł
Staż pracy łączny: {income['work_experience_months']} miesięcy
Staż u obecnego pracodawcy: {income['current_employer_months']} miesięcy
Pracodawca: {income.get('employer_name', 'N/D')}
{f"Forma księgowości: {income.get('accounting_type', 'N/D')}" if 'accounting_type' in income else ''}
{f"Branża: {income.get('business_sector', 'N/D')}" if 'business_sector' in income else ''}

Dochód współmałżonka: {income.get('spouse_income_type', 'brak')}
Kwota współmałżonka brutto/netto: {income.get('spouse_monthly_gross', 0)} zł / {income.get('spouse_monthly_net', 0)} zł
Staż współmałżonka: {income.get('spouse_work_experience_months', 0)} miesięcy (u obecnego: {income.get('spouse_current_employer_months', 0)} mies)
{f"Pracodawca współmałżonka: {income.get('spouse_employer_name', 'N/D')}" if income.get('spouse_employer_name') else ''}

Dodatkowe dochody:{additional_income_text if additional_income_text else ' Brak'}

===== PARAMETRY KREDYTU =====
Cel kredytu: {loan['purpose']}
Wartość nieruchomości: {loan['property_value']} zł
Kwota kredytu: {loan['loan_amount']} zł
Wkład własny: {loan['own_contribution']} zł ({loan['own_contribution_percentage']}%)
Źródło wkładu: {loan['own_contribution_source']}
Okres kredytowania: {loan['loan_period_months']} miesięcy
Waluta: {loan.get('currency', 'PLN')}
Oprocentowanie: {loan['interest_rate_type']}{f' (stałe na {loan["interest_rate_fixed_years"]} lat)' if loan['interest_rate_type'] == 'stałe' else ''}
Rodzaj rat: {loan['installment_type']}
Karencja: {loan['grace_period_months']} miesięcy
Wcześniejsza spłata: {'Planowana' if loan['early_repayment_planned'] else 'Nie planowana'}
Liczba istniejących kredytów hipotecznych: {loan['existing_mortgages']}
Kredyt EKO: {'Tak - ' + loan.get('eco_loan_details', '') if loan.get('eco_loan') else 'Nie'}
{f"Refinansowanie: Tak, wydatki sprzed {loan.get('refinancing_period_months', 0)} miesięcy" if loan.get('refinancing_period_months') else ''}
{f"Konsolidacja: Tak, {loan.get('consolidation_amount', 0)} zł na spłatę zobowiązań" if loan.get('consolidation_amount') else ''}
{f"Wykup udziału: {loan.get('purchased_share', 'N/D')}" if loan.get('share_purchase') else ''}

===== NIERUCHOMOŚĆ =====
Typ: {prop['type']}
Rynek: {prop['market']}
Lokalizacja: {prop['location']}
Powierzchnia: {prop['size_sqm']} m2
{f"Powierzchnia działki: {prop['plot_size_sqm']} m2" if prop.get('plot_size_sqm', 0) > 0 else ''}
{f"Rok budowy: {prop.get('building_year', 'N/D')}" if prop.get('building_year') else ''}
{f"Stan: {prop.get('condition', 'N/D')}" if prop.get('condition') else ''}
{f"Liczba mieszkań: {prop.get('number_of_apartments', 'N/D')}" if prop.get('number_of_apartments') else ''}
Lokale użytkowe: {'Nie' if not prop.get('commercial_space') else f"Tak, {prop.get('commercial_sqm', 0)} m2 ({prop.get('commercial_percentage', 0)}%)"}
{f"Decyzja WZ: {'Tak' if prop.get('has_wz_decision') else 'Nie'}" if 'has_wz_decision' in prop else ''}
{f"Pozwolenie na budowę: {'Tak' if prop.get('has_building_permit') else 'Nie'}" if 'has_building_permit' in prop else ''}
Uwagi: {prop.get('note', 'Brak')}

===== ZABEZPIECZENIA =====
Zabezpieczenie na nieruchomości osoby trzeciej: {'Tak - ' + collateral.get('third_party_relationship', '') if collateral['collateral_on_third_party_property'] else 'Nie'}
{f"Osoba trzecia: {collateral.get('third_party_owner_name', 'N/D')}" if collateral['collateral_on_third_party_property'] else ''}
Działka jako wkład własny: {'Tak, wartość ' + str(collateral.get('plot_value', 0)) + ' zł' if collateral['owned_plot_as_contribution'] else 'Nie'}

===== WYCENA =====
Preferowany typ operatu: {profile['valuation']['valuation_type_preference']}

===== UBEZPIECZENIA =====
Ubezpieczenie pomostowe: {'Tak' if insurance['bridge_insurance'] else 'Nie'}
Ubezpieczenie niskiego wkładu: {'Tak' if insurance['low_contribution_insurance'] else 'Nie'}
Ubezpieczenie na życie: {'Tak - ' + insurance.get('life_insurance_provider', '') + f", suma {insurance.get('life_insurance_sum', 0)} zł" if insurance['life_insurance'] else 'Nie'}
Ubezpieczenie od utraty pracy: {'Tak' if insurance['job_loss_insurance'] else 'Nie'}
Ubezpieczenie nieruchomości: {'Tak - ' + insurance.get('property_insurance_provider', '') if insurance['property_insurance'] else 'Nie'}

===== DOKUMENTY =====
Zaświadczenie o zarobkach: {profile['documents'].get('employment_certificate_date', 'N/D')}
Zaświadczenie z US: {profile['documents'].get('tax_office_certificate_date', 'N/D')}
Zaświadczenie z ZUS: {profile['documents'].get('zus_certificate_date', 'N/D')}
Wyciągi bankowe: {profile['documents']['bank_statement_months']} miesięcy
{f"PIT za rok ubiegły: {'Tak' if profile['documents'].get('pit_last_year') else 'Nie'}" if 'pit_last_year' in profile['documents'] else ''}
{f"KPiR rok bieżący: {'Tak' if profile['documents'].get('kpir_current_year') else 'Nie'}" if 'kpir_current_year' in profile['documents'] else ''}

===== DODATKOWE INFORMACJE =====
Historia kredytowa: {add_info['credit_history']}
Obecny czynsz/kredyt: {add_info.get('current_rental_cost', 0)} zł/mies
{f"Inne nieruchomości: {add_info.get('other_property_details', 'Brak')}" if add_info.get('has_other_property') else 'Inne nieruchomości: Brak'}
{f"Transakcja rodzinna: {add_info.get('family_transaction_details', 'Tak')}" if add_info.get('family_transaction') else ''}
Motywacja: {add_info.get('motivation', 'N/D')}
Termin: {add_info.get('timeline', 'N/D')}"""
    
    print("\n📝 ZAPYTANIE:")
    print("-" * 80)
    print(query)
    print("-" * 80)
    
    # Inicjalizuj silnik
    print("\n⏳ Inicjalizacja systemu...\n")
    kb_path = os.path.join(parent_dir, 'data', 'processed', 'knowledge_base.json')
    engine = QueryEngine(kb_path)
    
    # Przetwórz zapytanie
    print("\n🤖 Analiza przez AI - to może potrwać chwilę...\n")
    response = engine.process_query(query)
    
    # Wyświetl odpowiedź
    print("\n" + "="*80)
    print("🎯 ODPOWIEDŹ AI Z KOMPLETNĄ WERYFIKACJĄ:")
    print("="*80 + "\n")
    print(response)
    print("\n" + "="*80)
    
    # Zapisz do pliku
    with open('test_result_kamienica.md', 'w', encoding='utf-8') as f:
        f.write("# TEST PROFILU #1: Zakup kamienicy - cel mieszkaniowy\n\n")
        f.write("## Zapytanie\n\n")
        f.write("```\n")
        f.write(query)
        f.write("\n```\n\n")
        f.write("## Odpowiedź AI\n\n")
        f.write(response)
    
    print("\n✓ Wynik zapisany do: test_result_kamienica.md")


if __name__ == "__main__":
    main()
