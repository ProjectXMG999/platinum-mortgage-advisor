"""
Konwersja danych z Excela do JSON w strukturze pasującej do analizy AI
"""
import pandas as pd
import json
from typing import Dict, List

def convert_excel_to_knowledge_base(excel_file: str, output_file: str) -> Dict:
    """
    Konwertuje Excel z bazą wiedzy hipotecznej do struktury JSON
    """
    xl_file = pd.ExcelFile(excel_file)
    df = pd.read_excel(excel_file, sheet_name=xl_file.sheet_names[0])
    
    # Lista banków (kolumny od 3. do końca)
    banks = df.columns[2:].tolist()
    
    knowledge_base = {
        "metadata": {
            "source": excel_file,
            "date_updated": "2025-04-01",
            "description": "Baza wiedzy produktów hipotecznych Platinum Financial"
        },
        "banks": banks,
        "products": []
    }
    
    # Grupuj dane po bankach
    for bank in banks:
        bank_data = {
            "bank_name": bank,
            "parameters": {}
        }
        
        current_group = None
        
        for idx, row in df.iterrows():
            group = row['Grupa']
            parameter = row['Parametr']
            value = row[bank]
            
            # Pomiń puste wartości
            if pd.isna(value):
                value = "Brak informacji"
            else:
                value = str(value).strip()
            
            # Zapisz grupę
            if pd.notna(group) and group != current_group:
                current_group = group
                if current_group not in bank_data['parameters']:
                    bank_data['parameters'][current_group] = {}
            
            # Dodaj parametr do grupy
            if current_group and pd.notna(parameter):
                bank_data['parameters'][current_group][parameter] = value
        
        knowledge_base['products'].append(bank_data)
    
    # Zapisz do pliku JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Dane zapisane do: {output_file}")
    print(f"✓ Liczba banków: {len(banks)}")
    print(f"✓ Liczba parametrów: {len(df)}")
    
    return knowledge_base

if __name__ == "__main__":
    excel_file = "baza_wiedzy_platinum.xlsx"
    output_file = "../processed/knowledge_base.json"
    
    knowledge_base = convert_excel_to_knowledge_base(excel_file, output_file)
    
    # Wyświetl przykładowe dane
    print("\n" + "="*80)
    print("PRZYKŁADOWE DANE (pierwszy bank):")
    print("="*80)
    print(json.dumps(knowledge_base['products'][0], ensure_ascii=False, indent=2)[:1000] + "...")
