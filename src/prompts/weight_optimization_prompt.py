"""
Prompt dla dynamicznego dostrajania wag kategorii jakości
Analizuje profil klienta i ustala optymalne wagi dla 4 kategorii
"""

PROMPT = """
# SYSTEM OPTYMALIZACJI WAG KATEGORII JAKOŚCI

## ZADANIE
Przeanalizuj profil kredytobiorcy i ustal optymalne wagi dla 4 kategorii oceny jakości oferty kredytowej.

## KATEGORIE DO OCENY

### 1. KOSZT KREDYTU (domyślnie 35%)
Prowizje, ubezpieczenia, opłaty dodatkowe, spread

### 2. ELASTYCZNOŚĆ (domyślnie 25%)
Wcześniejsza spłata, zawieszenie rat, karencja, opcje dostosowywania

### 3. WYGODA (domyślnie 25%)
Proces, dokumentacja, wycena, czas oczekiwania, obsługa

### 4. KORZYŚCI (domyślnie 15%)
Promocje, rabaty, programy lojalnościowe, dodatkowe benefity


## METODOLOGIA DOSTRAJANIA WAG

### REGUŁY ANALIZY PROFILU

**A. ANALIZA FINANSOWA**

1. **Wysoki dochód + duża kwota kredytu** → KOSZT ważniejszy
   - Duże kwoty = duże różnice w złotówkach
   - Przykład: różnica 0.2% przy 1M PLN = 2000 PLN/rok
   - Waga KOSZT: 40-45%

2. **Niski wkład własny (LTV > 80%)** → KOSZT krytyczny
   - Ubezpieczenie niskiego wkładu = znaczący koszt
   - Różnice w LTV requirements
   - Waga KOSZT: 45-50%

3. **Długi okres kredytowania (> 25 lat)** → KOSZT dominujący
   - Długi czas = zwielokrotnione różnice
   - Przykład: 0.1% różnicy przez 30 lat = dziesiątki tysięcy
   - Waga KOSZT: 45-50%

**B. ANALIZA SYTUACJI ŻYCIOWEJ**

1. **Biznesmen / samozatrudniony** → ELASTYCZNOŚĆ kluczowa
   - Nieprzewidywalne dochody
   - Potrzeba zawieszania rat w słabszych miesiącach
   - Waga ELASTYCZNOŚĆ: 30-35%

2. **Kredyt na budowę / deweloperski** → ELASTYCZNOŚĆ ważna
   - Karencja kapitałowa krytyczna
   - Transze wypłat
   - Waga ELASTYCZNOŚĆ: 30-35%

3. **Refinansowanie** → ELASTYCZNOŚĆ i WYGODA
   - Szybkość procesu ważna
   - Brak opłat za wcześniejszą spłatę starego kredytu
   - Waga ELASTYCZNOŚĆ: 30%, WYGODA: 30%

**C. ANALIZA PREFERENCJI**

1. **Młody klient (< 30 lat)** → KORZYŚCI atrakcyjne
   - Długa perspektywa relacji z bankiem
   - Wrażliwość na benefity (cashback, karty, konta)
   - Waga KORZYŚCI: 20-25%

2. **Kredyt EKO / energooszczędny** → KORZYŚCI kluczowe
   - Rabat na oprocentowanie to główny benefit
   - Może zrównoważyć wyższe koszty
   - Waga KORZYŚCI: 25-30%

3. **Pierwszy kredyt** → WYGODA priorytet
   - Brak doświadczenia
   - Obsługa i prostota procesu ważne
   - Waga WYGODA: 30-35%

**D. ANALIZA RYZYKA**

1. **Niepewna sytuacja (czas określony, próbny okres)** → ELASTYCZNOŚĆ
   - Potrzeba bezpieczeństwa (opcja zawieszenia)
   - Waga ELASTYCZNOŚĆ: 35-40%

2. **Stabilna sytuacja (UoP czas nieokreślony, senior)** → KOSZT główny
   - Brak obaw o spłatę
   - Optymalizacja kosztów priorytet
   - Waga KOSZT: 40-45%


## FORMAT ODPOWIEDZI (JSON)

{{
  "wagi": {{
    "koszt": 35.0,          // 0-100, suma = 100
    "elastycznosc": 25.0,   // 0-100
    "wygoda": 25.0,         // 0-100
    "korzysci": 15.0        // 0-100
  }},
  "uzasadnienie": "Szczegółowe wyjaśnienie dlaczego takie wagi są optymalne dla tego klienta. Odniesienie do konkretnych cech profilu.",
  "kluczowe_czynniki": [
    "Czynnik 1 wpływający na wagi",
    "Czynnik 2 wpływający na wagi",
    "Czynnik 3 wpływający na wagi"
  ],
  "profil_klienta_summary": "Krótkie podsumowanie profilu finansowego i życiowego klienta"
}}


## WALIDACJA

1. **Suma wag MUSI wynosić 100.0**
2. **Żadna waga nie może być < 5%** (każda kategoria ma minimalne znaczenie)
3. **Żadna waga nie może być > 60%** (zachowanie balansu)
4. **Uzasadnienie musi odnosić się do konkretnych danych z profilu**


## PRZYKŁADY

### PRZYKŁAD 1: Młode małżeństwo, pierwszy kredyt na mieszkanie
```json
{{
  "wagi": {{
    "koszt": 40.0,
    "elastycznosc": 20.0,
    "wygoda": 30.0,
    "korzysci": 10.0
  }},
  "uzasadnienie": "Pierwszy kredyt - WYGODA procesu ważna (30%). Stabilne UoP - KOSZT priorytet (40%). Młode osoby - KORZYŚCI mniej istotne (10%). Standardowy kredyt mieszkaniowy - ELASTYCZNOŚĆ standardowa (20%).",
  "kluczowe_czynniki": [
    "Pierwszy kredyt hipoteczny - brak doświadczenia",
    "Stabilne zatrudnienie UoP czas nieokreślony",
    "Standardowy cel - zakup mieszkania"
  ],
  "profil_klienta_summary": "Para 28/30 lat, UoP, łączny dochód 15k PLN, kredyt 500k na mieszkanie, LTV 80%"
}}
```

### PRZYKŁAD 2: Biznesmen budujący dom
```json
{{
  "wagi": {{
    "koszt": 30.0,
    "elastycznosc": 40.0,
    "wygoda": 20.0,
    "korzysci": 10.0
  }},
  "uzasadnienie": "Samozatrudnienie - ELASTYCZNOŚĆ krytyczna (40%) ze względu na zmienne dochody. Budowa domu - karencja kapitałowa kluczowa. KOSZT mniej istotny (30%) przy dużym dochodzie. WYGODA standardowa (20%).",
  "kluczowe_czynniki": [
    "Działalność gospodarcza - zmienne przychody",
    "Budowa domu - potrzeba karencji kapitałowej",
    "Wysoki dochód - mniejsza wrażliwość na koszty"
  ],
  "profil_klienta_summary": "Przedsiębiorca 42 lata, KPIR, dochód 25k PLN, kredyt 800k na budowę, działka własna"
}}
```

### PRZYKŁAD 3: Senior refinansujący kredyt EKO
```json
{{
  "wagi": {{
    "koszt": 35.0,
    "elastycznosc": 25.0,
    "wygoda": 15.0,
    "korzysci": 25.0
  }},
  "uzasadnienie": "Refinansowanie - KOSZT i KORZYŚCI kluczowe (razem 60%). Kredyt EKO - rabat na oprocentowanie to główny benefit (25%). Senior z doświadczeniem - WYGODA mniej istotna (15%). ELASTYCZNOŚĆ standardowa (25%).",
  "kluczowe_czynniki": [
    "Refinansowanie - optymalizacja kosztów głównym celem",
    "Kredyt EKO - znaczący rabat na oprocentowanie",
    "Doświadczony klient - sprawnie przejdzie przez proces"
  ],
  "profil_klienta_summary": "Senior 55 lat, UoP, refinansowanie 600k, dom energooszczędny, LTV 50%"
}}
```


## TWOJA ODPOWIEDŹ

Przeanalizuj otrzymany profil klienta i zwróć JSON z optymalnymi wagami.
Pamiętaj: suma wag = 100, każda waga 5-60%, konkretne uzasadnienie.
"""
