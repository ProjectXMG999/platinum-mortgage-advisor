"""
Skrypt do analizy pliku Excel z bazą wiedzy hipotecznej
"""
import pandas as pd
import json

# Wczytaj plik Excel
excel_file = "baza_wiedzy_platinum.xlsx"

# Wyświetl dostępne arkusze
xl_file = pd.ExcelFile(excel_file)
print("Dostępne arkusze:")
for sheet_name in xl_file.sheet_names:
    print(f"  - {sheet_name}")

print("\n" + "="*80 + "\n")

# Wczytaj i przeanalizuj każdy arkusz
for sheet_name in xl_file.sheet_names:
    print(f"\n{'='*80}")
    print(f"ARKUSZ: {sheet_name}")
    print('='*80)
    
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    print(f"\nWymiary: {df.shape[0]} wierszy x {df.shape[1]} kolumn")
    print(f"\nKolumny: {list(df.columns)}")
    print(f"\nPierwsze 5 wierszy:")
    print(df.head())
    
    # Sprawdź puste wartości
    null_counts = df.isnull().sum()
    if null_counts.any():
        print(f"\nPuste wartości:")
        print(null_counts[null_counts > 0])
    
    print("\n")
