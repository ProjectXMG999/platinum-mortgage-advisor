"""
Test wszystkich profili klientów z zapisem wyników do osobnego katalogu
"""
import sys
import os
import json
from datetime import datetime

# Dodaj główny katalog do path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.query_engine import QueryEngine


def format_query_from_profile(profile):
    """Formatuje szczegółowe zapytanie z profilu klienta"""
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
        additional_income_text += f"\nAlimenty: {income['additional_income']['alimony_received']} zł/mies"
    if income['additional_income']['maternity_leave']:
        additional_income_text += f"\nUrlop macierzyński: Tak"
    if income['additional_income']['dividends']:
        additional_income_text += f"\nDywidendy: Tak"
    if income['additional_income']['foreign_currency_income']:
        additional_income_text += f"\nDochód w walucie obcej: Tak"
    
    query = f"""===== DANE KLIENTA =====
Klient: {profile['name']}, {profile['age']} lat, {profile['marital_status']}
Liczba wnioskodawców: {profile['number_of_applicants']}
Obywatelstwo: {profile.get('citizenship', 'polskie')}
Związek nieformalny: {'Tak' if profile.get('informal_relationship', False) else 'Nie'}
Rozdzielność majątkowa: {'Tak, od ' + str(profile.get('property_separation_years', 0)) + ' lat' if profile.get('property_separation', False) else 'Nie'}

===== ŹRÓDŁO DOCHODU =====
Dochód główny: {income['type']}
Kwota brutto/netto: {income['monthly_gross']} zł / {income.get('monthly_net', income['monthly_gross'] * 0.72)} zł
Staż pracy łączny: {income.get('work_experience_months', 0)} miesięcy
Staż u obecnego pracodawcy: {income.get('current_employer_months', income.get('work_experience_months', 0))} miesięcy
Pracodawca: {income.get('employer_name', 'N/D')}
{f"Forma księgowości: {income.get('accounting_type', 'N/D')}" if 'accounting_type' in income else ''}
{f"Branża: {income.get('business_sector', 'N/D')}" if 'business_sector' in income else ''}

Dochód współmałżonka: {income.get('spouse_income_type', 'brak')}
Kwota współmałżonka brutto/netto: {income.get('spouse_monthly_gross', 0)} zł / {income.get('spouse_monthly_net', income.get('spouse_monthly_gross', 0) * 0.72)} zł
Staż współmałżonka: {income.get('spouse_work_experience_months', 0)} miesięcy (u obecnego: {income.get('spouse_current_employer_months', income.get('spouse_work_experience_months', 0))} mies)
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
    
    return query


def main():
    # Utwórz katalog na wyniki
    results_dir = os.path.join(parent_dir, 'test_results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        print(f"\n✓ Utworzono katalog: {results_dir}\n")
    
    # Wczytaj profile
    profiles_path = os.path.join(parent_dir, 'data', 'processed', 'customer_profiles.json')
    with open(profiles_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    profiles = data['customer_profiles']
    total = len(profiles)
    
    print("\n" + "="*80)
    print(f"TEST WSZYSTKICH PROFILI KLIENTÓW")
    print("="*80)
    print(f"Liczba profili do przetestowania: {total}")
    print(f"Katalog wyników: {results_dir}")
    print("="*80 + "\n")
    
    # Inicjalizuj silnik
    print("⏳ Inicjalizacja systemu...\n")
    kb_path = os.path.join(parent_dir, 'data', 'processed', 'knowledge_base.json')
    engine = QueryEngine(kb_path)
    
    # Timestamp dla tej sesji testów
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Przetwórz każdy profil
    results_summary = []
    
    for idx, profile in enumerate(profiles, 1):
        profile_id = profile['profile_id']
        category = profile['category']
        name = profile['name']
        
        print(f"\n{'='*80}")
        print(f"[{idx}/{total}] PROFIL #{profile_id}: {category}")
        print(f"{'='*80}")
        print(f"Klient: {name}, {profile['age']} lat")
        print(f"Cel: {profile['loan_details']['purpose']}")
        print(f"Kwota: {profile['loan_details']['loan_amount']} zł")
        print(f"{'='*80}\n")
        
        # Sformatuj zapytanie
        query = format_query_from_profile(profile)
        
        print(f"🤖 Analiza przez AI - profil #{profile_id}...\n")
        
        try:
            # Przetwórz zapytanie
            response = engine.process_query(query)
            
            # Przygotuj nazwę pliku
            safe_category = category.replace('/', '_').replace(' ', '_').replace('-', '_')
            filename = f"profile_{profile_id:02d}_{safe_category}_{timestamp}.md"
            filepath = os.path.join(results_dir, filename)
            
            # Zapisz do pliku
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# PROFIL #{profile_id}: {category}\n\n")
                f.write(f"**Klient**: {name}, {profile['age']} lat\n")
                f.write(f"**Data testu**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write("## Zapytanie\n\n")
                f.write("```\n")
                f.write(query)
                f.write("\n```\n\n")
                f.write("---\n\n")
                f.write("## Odpowiedź AI\n\n")
                f.write(response)
            
            print(f"✓ Wynik zapisany: {filename}\n")
            
            results_summary.append({
                'profile_id': profile_id,
                'category': category,
                'name': name,
                'status': 'SUCCESS',
                'filename': filename
            })
            
        except Exception as e:
            print(f"✗ BŁĄD podczas przetwarzania profilu #{profile_id}: {str(e)}\n")
            results_summary.append({
                'profile_id': profile_id,
                'category': category,
                'name': name,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Zapisz podsumowanie
    summary_filepath = os.path.join(results_dir, f"test_summary_{timestamp}.json")
    with open(summary_filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'total_profiles': total,
            'successful': sum(1 for r in results_summary if r['status'] == 'SUCCESS'),
            'failed': sum(1 for r in results_summary if r['status'] == 'ERROR'),
            'results': results_summary
        }, f, indent=2, ensure_ascii=False)
    
    # Wyświetl podsumowanie
    print("\n" + "="*80)
    print("📊 PODSUMOWANIE TESTÓW")
    print("="*80)
    print(f"Przetestowano: {total} profili")
    print(f"Sukces: {sum(1 for r in results_summary if r['status'] == 'SUCCESS')} ✓")
    print(f"Błędy: {sum(1 for r in results_summary if r['status'] == 'ERROR')} ✗")
    print(f"\nKatalog wyników: {results_dir}")
    print(f"Plik podsumowania: test_summary_{timestamp}.json")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
