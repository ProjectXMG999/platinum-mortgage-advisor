"""
Prompt dla porównawczej oceny jakości wszystkich zakwalifikowanych banków
Benchmarking, skalowanie min-max, ranking z kontekstem rynkowym
"""

PROMPT = """
# SYSTEM PORÓWNAWCZEJ OCENY JAKOŚCI KREDYTÓW

## ZADANIE
Otrzymujesz profil klienta oraz parametry JAKOŚCI dla wszystkich zakwalifikowanych banków.
Twoim zadaniem jest:

1. **PORÓWNAĆ** oferty WZGLĘDEM SIEBIE (nie w izolacji!)
2. **ZNALEŹĆ** obiektywne najlepsze i najgorsze rozwiązania w każdej kategorii
3. **OCENIĆ** każdy bank w kontekście RYNKOWYM (nie abstrakcyjnym)
4. **ZASTOSOWAĆ** dynamiczne wagi dostosowane do profilu klienta


## KATEGORIE OCENY (z wagami)

Otrzymasz wagi optymalne dla tego konkretnego klienta. Przykładowo:

### 1. KOSZT KREDYTU (waga: X%)
- Prowizja bankowa
- Oprocentowanie (jeśli podane)
- Ubezpieczenia (wymagane i opcjonalne)
- Opłaty za wycenę nieruchomości
- Opłaty za inspekcję
- Inne koszty dodatkowe

### 2. ELASTYCZNOŚĆ (waga: Y%)
- Wcześniejsza spłata (opłata lub darmowa)
- Wcześniejsza spłata części kapitału
- Zawieszenie spłaty rat
- Karencja kapitałowa
- Karencja kapitału i odsetek
- Opcje spłaty (kapitał i odsetki oddzielnie)

### 3. WYGODA (waga: Z%)
- Proces wyceny (online, inspekcja, certyfikat)
- Liczba wymaganych dokumentów
- Szybkość decyzji
- Dostępność oddziałów / obsługa online
- Prostota warunków

### 4. KORZYŚCI (waga: W%)
- Kredyt EKO (rabat na oprocentowanie)
- Programy lojalnościowe
- Promocje
- Benefity dodatkowe (konta, karty)
- Rabaty za produkty dodatkowe


## METODOLOGIA BENCHMARKINGU

### SKALOWANIE MIN-MAX (dla każdej kategorii osobno)

```
1. Znajdź NAJLEPSZĄ wartość w kategorii = 100 punktów
2. Znajdź NAJGORSZĄ wartość w kategorii = 0 punktów
3. Pozostałe banki skaluj liniowo:

   score = 100 * (wartość_banku - min) / (max - min)
```

### PRZYKŁAD: Prowizja bankowa

```
mBank: 1.5%        → najniższa → 100 pkt
ING: 1.8%          → (2.5-1.8)/(2.5-1.5) = 0.7 → 70 pkt
PKO BP: 2.0%       → (2.5-2.0)/(2.5-1.5) = 0.5 → 50 pkt
Getin: 2.5%        → najwyższa → 0 pkt

W kategorii KOSZT:
- mBank najlepszy (100 pkt)
- Getin najgorszy (0 pkt)
```

### PRZYKŁAD: Wcześniejsza spłata

```
mBank: DARMOWA         → najlepsza → 100 pkt
ING: DARMOWA           → najlepsza → 100 pkt
PKO BP: 2% opłata      → (3-2)/(3-0) = 0.33 → 33 pkt
Santander: 3% opłata   → najgorsza → 0 pkt

W kategorii ELASTYCZNOŚĆ:
- mBank i ING liderzy (100 pkt)
- Santander najgorszy (0 pkt)
```


## ZASADY KONTEKSTOWE

### 1. OCENIAJ TYLKO ISTOTNE PARAMETRY

**NIE oceniaj parametrów nieistotnych dla klienta!**

Przykłady:
- Klient ma LTV=70% → NIE oceniaj "ubezpieczenia niskiego wkładu" (nieistotne)
- Klient NIE buduje → NIE oceniaj "karencja kapitałowa" (nieistotne)
- Klient NIE szuka EKO → NIE oceniaj "kredyt EKO" (nieistotne)

**JAK to zrobić?**
- Pomiń nieistotne parametry w obliczeniach
- Skaluj tylko istotne parametry
- W reasoning zaznacz "parametr X pominięty - nieistotny dla klienta"


### 2. AGREGUJ WYNIKI W KATEGORIACH

Dla każdego banku oblicz średnią punktów w kategorii (tylko z istotnych parametrów).

Przykład kategorii KOSZT:
```
mBank:
  - prowizja: 100 pkt (1.5% - najniższa)
  - wycena: 50 pkt (300 PLN - średnia)
  - ubezpieczenie: POMINIĘTE (LTV<80%)
  
  Średnia KOSZT = (100 + 50) / 2 = 75 pkt
```


### 3. OBLICZ TOTAL SCORE

```
total_score = (koszt_score * waga_koszt) + 
              (elastycznosc_score * waga_elastycznosc) + 
              (wygoda_score * waga_wygoda) + 
              (korzysci_score * waga_korzysci)

Gdzie wagi sumują się do 100%.
```


### 4. RANKING I PERCENTYL

```
rank = pozycja w sortowaniu po total_score (1 = najlepszy)

percentile = 100 * (liczba_banków_gorszych / liczba_wszystkich_banków)

Przykład dla 11 banków:
- Rank 1 (najlepszy) → percentile = 100
- Rank 6 (środek)    → percentile = 50
- Rank 11 (najgorszy)→ percentile = 0
```


## ANALIZA JAKOŚCIOWA

Dla każdego banku podaj:

### STRENGTHS (mocne strony)
Konkretne parametry gdzie bank WYGRYWA z konkurencją:
- "Najniższa prowizja na rynku (1.5% vs średnia 2.1%)"
- "Darmowa wcześniejsza spłata (tylko 3/11 banków)"
- "Wycena online bez opłat (8/11 banków wymaga inspekcji)"

### WEAKNESSES (słabe strony)
Konkretne parametry gdzie bank PRZEGRYWA:
- "Prowizja 2.5% (najwyższa na rynku, średnia 2.0%)"
- "Brak możliwości zawieszenia rat (ma to 7/11 banków)"
- "Opłata 3% za wcześniejszą spłatę (4 banki mają darmową)"

### COMPETITIVE ADVANTAGES (unikalne przewagi)
Coś co TYLKO ten bank ma lub robi ZNACZĄCO lepiej:
- "Jedyny bank z karencją 24 miesiące (reszta max 12)"
- "Najwyższy rabat EKO na rynku (-0.2%, średnia -0.1%)"
- "Tylko bank akceptujący działkę jako wkład własny"

### BETTER_THAN / WORSE_THAN
Listy nazw banków:
- better_than: ["PKO BP", "ING", "Santander", ...]
- worse_than: ["mBank", "Credit Agricole"]


## FORMAT ODPOWIEDZI (JSON)

{{
  "ranking": [
    {{
      "bank_name": "mBank",
      "rank": 1,
      "total_score": 92.5,
      "percentile": 100.0,
      
      "cost_score": 95.0,
      "cost_weight": 40.0,
      "flexibility_score": 88.0,
      "flexibility_weight": 25.0,
      "convenience_score": 92.0,
      "convenience_weight": 25.0,
      "benefits_score": 95.0,
      "benefits_weight": 10.0,
      
      "strengths": [
        "Najniższa prowizja bankowa na rynku (1.5% vs średnia 2.1%)",
        "Darmowa wcześniejsza spłata (tylko 3/11 banków oferuje)",
        "Najwyższy rabat EKO (-0.2%, średnia -0.12%)"
      ],
      "weaknesses": [
        "Brak ubezpieczenia niskiego wkładu (6/11 banków oferuje)"
      ],
      "competitive_advantages": [
        "Jedyny bank z wycena online całkowicie darmową",
        "Najdłuższa karencja kapitałowa na rynku (24 mies. vs średnia 12)"
      ],
      "better_than": ["PKO BP", "ING", "Santander", "Alior", ...],
      "worse_than": [],
      
      "reasoning": "mBank dominuje w kategorii KOSZT (95 pkt) dzięki najniższej prowizji 1.5% i darmowej wycenie online. ELASTYCZNOŚĆ również wysoka (88 pkt) - darmowa wcześniejsza spłata to rzadkość na rynku. KORZYŚCI maksymalne (95 pkt) - kredyt EKO z rabatem -0.2% to najlepsza oferta. Jedyną słabością jest brak ubezpieczenia niskiego wkładu, ale przy LTV=70% klienta to nieistotne. Total score 92.5 wynika z dominacji w kluczowych dla klienta obszarach."
    }},
    {{
      "bank_name": "PKO BP",
      "rank": 2,
      "total_score": 78.3,
      "percentile": 82.0,
      // ... analogicznie
    }},
    // ... pozostałe banki w kolejności rankingu
  ],
  
  "market_statistics": {{
    "total_banks": 11,
    "avg_total_score": 65.4,
    "median_total_score": 68.0,
    "best_bank": "mBank",
    "worst_bank": "Getin Noble Bank",
    "score_range": [42.1, 92.5],
    "applied_weights": {{
      "koszt": 40.0,
      "elastycznosc": 25.0,
      "wygoda": 25.0,
      "korzysci": 10.0
    }}
  }}
}}


## WALIDACJA ODPOWIEDZI

Przed zwróceniem JSON sprawdź:

1. ✅ Wszystkie banki mają unikalne ranki (1, 2, 3, ..., N)
2. ✅ Ranking posortowany malejąco po total_score
3. ✅ Percentile obliczone poprawnie (rank 1 = 100, ostatni = 0)
4. ✅ Total_score = suma ważona 4 kategorii
5. ✅ Wszystkie wagi zgodne z otrzymanymi (suma = 100)
6. ✅ Strengths/weaknesses odnoszą się do KONKRETNYCH wartości
7. ✅ Better_than i worse_than są spójne z rankingiem
8. ✅ Reasoning wyjaśnia DLACZEGO taki wynik (odniesienie do danych)


## PRZYKŁADY DOBRYCH OPISÓW

### ✅ DOBRY STRENGTH:
"Najniższa prowizja na rynku (1.5% vs średnia 2.1%, różnica 0.6%)"

### ❌ ZŁY STRENGTH:
"Niska prowizja"

### ✅ DOBRY WEAKNESS:
"Opłata 3% za wcześniejszą spłatę - najwyższa na rynku (4 banki mają darmową, średnia opłata 1.2%)"

### ❌ ZŁY WEAKNESS:
"Opłata za wcześniejszą spłatę"

### ✅ DOBRE REASONING:
"PKO BP zajmuje 2 miejsce (78.3 pkt) dzięki solidnym wynikom we wszystkich kategoriach. KOSZT (72 pkt) - prowizja 2.0% jest średnia na rynku, ale ubezpieczenia tańsze o 15% od konkurencji. ELASTYCZNOŚĆ (65 pkt) obniża opłata 2% za wcześniejszą spłatę podczas gdy liderzy oferują to darmowo. WYGODA (85 pkt) wysoka - największa sieć oddziałów w Polsce. KORZYŚCI (90 pkt) - kredyt EKO z rabatem -0.15%. Brakuje mu 14 pkt do lidera głównie przez opłaty w kategorii ELASTYCZNOŚĆ."

### ❌ ZŁE REASONING:
"PKO BP ma dobre wyniki w większości kategorii. Dobra oferta dla klienta."


## TWOJA ODPOWIEDŹ

Przeanalizuj otrzymane dane banków i profil klienta, następnie zwróć kompletny JSON z rankingiem.

PAMIĘTAJ:
- Porównuj banki MIĘDZY SOBĄ (skalowanie min-max)
- Używaj konkretnych liczb i porównań
- Oceniaj tylko parametry ISTOTNE dla klienta
- Stosuj otrzymane wagi kategorii
- Dodawaj kontekst rynkowy (X/N banków, średnia, etc.)
"""
