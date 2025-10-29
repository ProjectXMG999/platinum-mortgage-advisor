"""
Generator raportów Markdown z wyników testów dopasowania klientów
"""
import json
import sys
from pathlib import Path
from datetime import datetime


def extract_banks_from_response(response_text):
    """Wyodrębnia listę rekomendowanych banków z odpowiedzi AI"""
    banks = []
    lines = response_text.split('\n')
    
    bank_names = [
        'Alior Bank', 'BNP Paribas', 'CITI Handlowy', 'ING Bank Śląski', 'ING',
        'mBank', 'Millennium', 'Pekao SA', 'PKO BP', 'Santander', 'BOŚ Bank', 'VELO BANK'
    ]
    
    for line in lines:
        # Szukaj nagłówków z nazwami banków
        if any(f'**{bank}**' in line or f'### {i}. **{bank}' in line or f'#### {i}. **{bank}' in line 
               for bank in bank_names for i in range(1, 20)):
            for bank in bank_names:
                if bank in line and bank not in banks:
                    banks.append(bank)
                    break
    
    return banks if banks else ["Brak jednoznacznej rekomendacji"]


def extract_best_match(response_text, banks):
    """Określa najlepsze dopasowanie na podstawie odpowiedzi AI"""
    if not banks or banks == ["Brak jednoznacznej rekomendacji"]:
        return {
            'bank': 'Brak rekomendacji',
            'reason': 'AI nie znalazł odpowiedniej oferty dla tego profilu',
            'confidence': 'Niska'
        }
    
    # Pierwszy wymieniony bank jest zwykle najlepszą opcją
    best_bank = banks[0]
    
    # Szukaj uzasadnienia
    lines = response_text.split('\n')
    reason_lines = []
    capture = False
    
    for line in lines:
        if best_bank in line and ('**Dlaczego' in line or 'DLACZEGO' in line):
            capture = True
            continue
        if capture:
            if line.strip().startswith('**Kluczowe') or line.strip().startswith('###') or line.strip().startswith('---'):
                break
            if line.strip():
                reason_lines.append(line.strip())
    
    reason = ' '.join(reason_lines[:3]) if reason_lines else "Bank spełnia wymagania klienta"
    
    # Określ poziom pewności
    confidence = 'Wysoka' if len(banks) >= 3 else 'Średnia' if len(banks) >= 2 else 'Niska'
    
    return {
        'bank': best_bank,
        'reason': reason.replace('- ', '').strip(),
        'confidence': confidence
    }


def format_client_data_from_profile(profile):
    """Formatuje pełne dane profilu klienta w czytelny sposób"""
    formatted = []
    
    # Podstawowe dane
    formatted.append("### 👤 Dane Osobowe")
    formatted.append(f"- **Imię i nazwisko:** {profile.get('name', 'N/A')}")
    formatted.append(f"- **Wiek:** {profile.get('age', 'N/A')} lat")
    formatted.append(f"- **Stan cywilny:** {profile.get('marital_status', 'N/A')}")
    formatted.append(f"- **Liczba wnioskodawców:** {profile.get('number_of_applicants', 1)}")
    formatted.append("")
    
    # Dochody
    income = profile.get('income', {})
    formatted.append("### 💼 Dochody")
    formatted.append(f"- **Źródło dochodu:** {income.get('type', 'N/A')}")
    if income.get('monthly_gross'):
        formatted.append(f"- **Dochód miesięczny brutto:** {income['monthly_gross']:,} zł")
    if income.get('work_experience_months'):
        years = income['work_experience_months'] // 12
        months = income['work_experience_months'] % 12
        formatted.append(f"- **Staż pracy:** {years} lat {months} miesięcy" if months else f"- **Staż pracy:** {years} lat")
    if income.get('current_employer_months'):
        months = income['current_employer_months']
        if months >= 12:
            years = months // 12
            rest = months % 12
            formatted.append(f"- **U obecnego pracodawcy:** {years} lat {rest} miesięcy" if rest else f"- **U obecnego pracodawcy:** {years} lat")
        else:
            formatted.append(f"- **U obecnego pracodawcy:** {months} miesięcy")
    
    # Dochód dodatkowy
    if income.get('additional_income'):
        add_inc = income['additional_income']
        formatted.append(f"- **Dochód dodatkowy:** {add_inc.get('type', 'N/A')} - {add_inc.get('monthly_amount', 0):,} zł/mies")
    
    # Współwnioskodawca
    if income.get('spouse_income_type'):
        formatted.append(f"- **Współwnioskodawca - źródło:** {income.get('spouse_income_type', 'N/A')}")
        if income.get('spouse_monthly_gross'):
            formatted.append(f"- **Współwnioskodawca - dochód:** {income['spouse_monthly_gross']:,} zł brutto/mies")
    formatted.append("")
    
    # Szczegóły kredytu
    loan = profile.get('loan_details', {})
    formatted.append("### 🎯 Szczegóły Kredytu")
    formatted.append(f"- **Cel:** {loan.get('purpose', 'N/A')}")
    formatted.append(f"- **Wartość nieruchomości:** {loan.get('property_value', 0):,} zł")
    formatted.append(f"- **Kwota kredytu:** {loan.get('loan_amount', 0):,} zł")
    formatted.append(f"- **Wkład własny:** {loan.get('own_contribution', 0):,} zł ({loan.get('own_contribution_percentage', 0)}%)")
    if loan.get('property_value') and loan.get('loan_amount'):
        ltv = (loan['loan_amount'] / loan['property_value']) * 100
        formatted.append(f"- **LTV:** {ltv:.1f}%")
    formatted.append(f"- **Okres kredytowania:** {loan.get('loan_period_months', 0)} miesięcy")
    formatted.append(f"- **Waluta:** {loan.get('currency', 'PLN')}")
    formatted.append("")
    
    # Nieruchomość
    prop = profile.get('property', {})
    if prop:
        formatted.append("### 🏠 Nieruchomość")
        formatted.append(f"- **Typ:** {prop.get('type', 'N/A')}")
        formatted.append(f"- **Rynek:** {prop.get('market', 'N/A')}")
        formatted.append(f"- **Lokalizacja:** {prop.get('location', 'N/A')}")
        if prop.get('size_sqm'):
            formatted.append(f"- **Powierzchnia:** {prop['size_sqm']} m²")
        if prop.get('plot_size_sqm'):
            formatted.append(f"- **Działka:** {prop['plot_size_sqm']} m²")
        formatted.append("")
    
    # Dodatkowe informacje
    additional = profile.get('additional_info', {})
    if additional:
        formatted.append("### ℹ️ Informacje Dodatkowe")
        if additional.get('has_other_property'):
            formatted.append(f"- **Posiada inną nieruchomość:** Tak")
            if additional.get('other_property_type'):
                formatted.append(f"  - Typ: {additional['other_property_type']}")
            if additional.get('other_property_value'):
                formatted.append(f"  - Wartość: {additional['other_property_value']:,} zł")
        if additional.get('has_life_insurance'):
            formatted.append(f"- **Ubezpieczenie na życie:** Tak")
        if additional.get('credit_history'):
            formatted.append(f"- **Historia kredytowa:** {additional['credit_history']}")
        if additional.get('number_of_dependents'):
            formatted.append(f"- **Dzieci na utrzymaniu:** {additional['number_of_dependents']}")
        if additional.get('total_household_members'):
            formatted.append(f"- **Gospodarstwo domowe:** {additional['total_household_members']} osób")
        formatted.append("")
    
    return '\n'.join(formatted)


def generate_markdown_report(results_file, output_file):
    """Generuje raport Markdown z wyników testów"""
    
    # Wczytaj wyniki
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Wczytaj pełne profile klientów
    profiles_file = Path(results_file).parent / 'customer_profiles.json'
    with open(profiles_file, 'r', encoding='utf-8') as f:
        profiles_data = json.load(f)
    
    # Stwórz mapę profile_id -> profile
    profiles_map = {p['profile_id']: p for p in profiles_data['customer_profiles']}
    
    metadata = data['metadata']
    results = data['results']
    
    # Rozpocznij raport
    report = []
    report.append("# 📊 Raport Testów Dopasowania Klientów do Ofert Bankowych")
    report.append("")
    report.append(f"**Data wygenerowania:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Data testów:** {metadata['test_date']}")
    report.append(f"**Model AI:** {metadata['deployment_model']}")
    report.append(f"**Liczba profili:** {metadata['total_profiles_tested']}")
    report.append("")
    report.append("---")
    report.append("")
    
    # Spis treści
    report.append("## 📑 Spis Treści")
    report.append("")
    for result in results:
        profile_id = result['profile_id']
        category = result['category']
        report.append(f"{profile_id}. [{category}](#profil-{profile_id}-{category.lower().replace(' ', '-').replace('ł', 'l').replace('ą', 'a').replace('ę', 'e').replace('ó', 'o').replace('ś', 's').replace('ć', 'c').replace('ń', 'n').replace('ż', 'z').replace('ź', 'z')})")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Szczegóły każdego profilu
    for idx, result in enumerate(results, 1):
        profile_id = result['profile_id']
        category = result['category']
        query = result['query']
        response = result['response']
        
        # Pobierz pełny profil
        full_profile = profiles_map.get(profile_id, {})
        
        # Wyodrębnij banki i najlepsze dopasowanie
        banks = extract_banks_from_response(response)
        best_match = extract_best_match(response, banks)
        
        # Nagłówek profilu
        report.append(f"## Profil #{profile_id}: {category}")
        report.append("")
        
        # Podsumowanie na górze - KLUCZOWA SEKCJA
        report.append("### 🎯 WYNIK ANALIZY")
        report.append("")
        report.append("| Element | Wartość |")
        report.append("|---------|---------|")
        report.append(f"| **🏦 Najlepszy Bank** | **{best_match['bank']}** |")
        report.append(f"| **✅ Uzasadnienie** | {best_match['reason'][:200]}{'...' if len(best_match['reason']) > 200 else ''} |")
        report.append(f"| **📈 Poziom Pewności** | {best_match['confidence']} |")
        report.append(f"| **🏛️ Wszystkie Opcje** | {', '.join(banks[:5])}{'...' if len(banks) > 5 else ''} |")
        report.append(f"| **📊 Liczba Banków** | {len(banks)} {f'z {len([b for b in banks if b in ['Alior Bank', 'BNP Paribas', 'CITI Handlowy', 'ING Bank Śląski', 'mBank', 'Millennium', 'Pekao SA', 'PKO BP', 'Santander', 'BOŚ Bank', 'VELO BANK']])} banków z bazy)' if banks != ['Brak jednoznacznej rekomendacji'] else ''} |")
        report.append("")
        
        # Dane wejściowe - PEŁNY PROFIL
        report.append("### 📥 DANE WEJŚCIOWE KLIENTA")
        report.append("")
        if full_profile:
            report.append(format_client_data_from_profile(full_profile))
        else:
            # Fallback - jeśli nie ma pełnego profilu
            report.append("#### Zapytanie Tekstowe")
            report.append("")
            report.append(query)
            report.append("")
        
        # Pełna odpowiedź AI
        report.append("### 🤖 PEŁNA ANALIZA AI")
        report.append("")
        report.append("<details>")
        report.append("<summary>Kliknij aby rozwinąć szczegółową analizę</summary>")
        report.append("")
        report.append(response)
        report.append("")
        report.append("</details>")
        report.append("")
        
        # Separator
        report.append("---")
        report.append("")
    
    # Zapisz raport
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Raport wygenerowany: {output_file}")
    print(f"📊 Przetworzono {len(results)} profili")


def generate_summary_report(results_file, output_file):
    """Generuje skrócony raport - tylko najważniejsze informacje"""
    
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data['metadata']
    results = data['results']
    
    report = []
    report.append("# 📋 Podsumowanie Wyników Testów")
    report.append("")
    report.append(f"**Data:** {metadata['test_date']} | **Model:** {metadata['deployment_model']}")
    report.append("")
    
    # Tabela wyników
    report.append("| # | Kategoria | Najlepszy Bank | Liczba Opcji | Pewność |")
    report.append("|---|-----------|----------------|--------------|---------|")
    
    for result in results:
        banks = extract_banks_from_response(result['response'])
        best_match = extract_best_match(result['response'], banks)
        
        report.append(f"| {result['profile_id']} | {result['category'][:40]} | **{best_match['bank']}** | {len(banks)} | {best_match['confidence']} |")
    
    report.append("")
    
    # Statystyki
    report.append("## 📈 Statystyki")
    report.append("")
    
    all_banks = []
    for result in results:
        banks = extract_banks_from_response(result['response'])
        all_banks.extend(banks)
    
    from collections import Counter
    bank_counts = Counter(all_banks)
    
    report.append("### Najczęściej Rekomendowane Banki")
    report.append("")
    for bank, count in bank_counts.most_common(5):
        percentage = (count / len(results)) * 100
        report.append(f"- **{bank}**: {count} przypadków ({percentage:.1f}%)")
    
    # Zapisz
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Podsumowanie wygenerowane: {output_file}")


if __name__ == "__main__":
    # Ścieżki
    base_path = Path(__file__).parent.parent
    results_file = base_path / "data" / "processed" / "matching_results.json"
    
    # Generuj oba raporty
    output_full = base_path / "data" / "processed" / "RAPORT_PELNY.md"
    output_summary = base_path / "data" / "processed" / "RAPORT_PODSUMOWANIE.md"
    
    print("🚀 Generowanie raportów...")
    print("")
    
    generate_markdown_report(results_file, output_full)
    generate_summary_report(results_file, output_summary)
    
    print("")
    print("="*80)
    print("✅ GOTOWE!")
    print("="*80)
    print(f"📄 Pełny raport: {output_full}")
    print(f"📋 Podsumowanie: {output_summary}")
