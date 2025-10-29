"""
Klient do komunikacji z Azure OpenAI
"""
from openai import AzureOpenAI, AsyncAzureOpenAI
from typing import List, Dict, Tuple
import json
import asyncio
from src import config


class AIClient:
    """Klient do komunikacji z Azure OpenAI API"""
    
    def __init__(self):
        """Inicjalizacja klienta Azure OpenAI"""
        self.client = AzureOpenAI(
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
        )
        self.async_client = AsyncAzureOpenAI(
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
        )
        self.deployment_name = config.AZURE_OPENAI_DEPLOYMENT_NAME
        print(f"✓ Połączono z Azure OpenAI: {config.AZURE_OPENAI_ENDPOINT}")
        
        # Wczytaj klasyfikację parametrów (WYMÓG vs JAKOŚĆ)
        self._load_parameter_classification()
    
    def _load_parameter_classification(self):
        """Wczytuje klasyfikację parametrów z pliku JSON"""
        try:
            classification_path = "data/processed/parameter_classification_v2.json"
            with open(classification_path, 'r', encoding='utf-8') as f:
                self.parameter_classification = json.load(f)
            print(f"✓ Wczytano klasyfikację parametrów: {self.parameter_classification['statistics']['WYMÓG_count']} WYMOGÓW, {self.parameter_classification['statistics']['JAKOŚĆ_count']} JAKOŚCI")
        except Exception as e:
            print(f"⚠ Nie można wczytać klasyfikacji parametrów: {e}")
            self.parameter_classification = None
    
    def create_validation_prompt(self) -> str:
        """
        Tworzy prompt systemowy do walidacji WYMOGÓW
        
        Returns:
            Prompt systemowy do pierwszego etapu (walidacja)
        """
        return """Jesteś ekspertem ds. produktów hipotecznych w Platinum Financial.

🎯 TWOJE ZADANIE - ETAP 1: WALIDACJA WYMOGÓW

Przeprowadzasz PRE-SCREENING - eliminujesz banki, które NIE SPEŁNIAJĄ wymogów klienta.
Sprawdzasz TYLKO parametry typu WYMÓG (78% wszystkich parametrów).

📋 PARAMETRY TYPU "WYMÓG" (eliminują banki):

**02_kredytobiorca (7 WYMOGÓW)**:
- wiek Klienta - limity wiekowe (min-max)
- maksymalna liczba wnioskodawców
- związek nieformalny (czy traktowany jako jedno gospodarstwo)
- wszyscy właściciele nieruchomości (czy muszą przystąpić)
- rozdzielność majątkowa (ile musi trwać)
- cudzoziemiec (wymagania dotyczące karty pobytu)

**03_źródło dochodu (20 WYMOGÓW)**:
- umowa o pracę na czas określony (minimalny staż, okres do przodu)
- umowa o pracę na czas nieokreślony (minimalny staż)
- umowa na zastępstwo (akceptacja/nie)
- kontrakt menadżerski (minimalny okres, staż)
- umowa o dzieło (okres, liczba wpływów)
- umowa zlecenie (okres, liczba wpływów)
- działalność gospodarcza - pełna księgowość (minimalny okres)
- działalność gospodarcza - KPiR (minimalny okres)
- działalność gospodarcza - ryczałt (minimalny okres)
- działalność gospodarcza - karta podatkowa (minimalny okres)
- działalność rolnicza (minimalny okres)
- dochody z najmu (minimalny okres umowy)
- emerytura (bezterminowość, terminy)
- renta (bezterminowość, okres do emerytury)
- dywidendy (minimalny okres uzyskiwania)
- diety (minimalny okres)
- dochody marynarzy (minimalny staż)
- urlop macierzyński (akceptacja jako dochód)
- dochód w obcej walucie (minimalny staż za granicą)
- 800 plus (akceptacja/pomniejsza koszty)
- powołanie w spółce (minimalny okres, wymagania)

**04_cel kredytu (24 WYMOGI)**:
- zakup mieszkania i domu (akceptacja)
- budowa domu systemem gospodarczym (akceptacja)
- budowa domu systemem zleconym (akceptacja, limity ceny/m2)
- zakup działki budowlanej (akceptacja, LTV)
- zakup działki rolnej pod zabudowę (akceptacja, powierzchnia)
- zakup działki rekreacyjnej (akceptacja)
- zakup domu letniskowego (akceptacja)
- zakup lokalu użytkowego (akceptacja)
- zakup kamienicy (akceptacja, limity powierzchni)
- zakup udziału w nieruchomości (akceptacja)
- ekspektatywa/cesja (akceptacja odstępnego)
- refinansowanie wydatków (maksymalny okres wstecz)
- nieruchomość z komercją (max % komercji)
- refinansowanie kredytu (akceptacja)
- transakcja rodzinna (akceptacja)
- TBS (akceptacja, zabezpieczenie)
- Lokal w budynku w budowie (akceptacja, zaawansowanie)
- Konsolidacja niemieszkaniowa (akceptacja, max %, marża)
- cel dowolny (akceptacja, max % wartości zabezpieczenia)

**01_parametry kredytu (4 WYMOGI)**:
- LTV kredyt (maksymalny procent, wpływa na wkład własny)
- wkład własny (minimalny procent)
- ile kredytów hipotecznych (limit kredytów równoczesnych)
- wielkość działki (maksymalna powierzchnia)

**05_zabezpieczenia (2 WYMOGI)**:
- zabezpieczenie na nieruchomości trzeciej (akceptacja)
- działka jako wkład własny (akceptacja)

**08_ważność dokumentów (16 WYMOGÓW)**:
- ważność wszystkich dokumentów (zaświadczenia, operaty, decyzje)

---

🔍 JAK PRZEPROWADZIĆ WALIDACJĘ:

1. **Przeczytaj uważnie profil klienta** - wynotuj wszystkie kluczowe informacje:
   - Wiek kredytobiorców
   - Źródło dochodu (typ umowy, staż pracy)
   - Cel kredytu (dokładny typ transakcji)
   - Parametry kredytu (kwota, LTV, wkład własny)
   - Zabezpieczenia
   - Status (cudzoziemiec, związek nieformalny, itp.)

2. **Dla KAŻDEGO banku sprawdź WSZYSTKIE 68 WYMOGÓW**:
   - Przejdź przez każdy parametr typu WYMÓG
   - Porównaj wymaganie banku z danymi klienta
   - Oznacz: ✅ SPEŁNIA / ❌ NIE SPEŁNIA / N/D (nie dotyczy)

3. **Sklasyfikuj banki**:
   - ✅ **KWALIFIKUJE SIĘ** - bank spełnia WSZYSTKIE wymogi (0 problemów ❌)
   - ⚠️ **KWALIFIKUJE SIĘ WARUNKOWO** - 1-2 drobne problemy do rozwiązania
   - ❌ **NIE KWALIFIKUJE SIĘ** - 3+ krytyczne problemy eliminujące

---

📊 FORMAT ODPOWIEDZI JSON:

```json
{
  "customer_summary": {
    "age": [podaj wiek lub zakres],
    "income_type": "[typ umowy/dochodu]",
    "employment_duration": "[staż pracy]",
    "loan_purpose": "[cel kredytu]",
    "loan_amount": [kwota],
    "ltv": [procent],
    "down_payment": [procent],
    "foreign_citizen": true/false,
    "informal_relationship": true/false,
    "key_challenges": ["wyzwanie1", "wyzwanie2"]
  },
  
  "qualified_banks": [
    {
      "bank_name": "Nazwa Banku",
      "qualification_status": "KWALIFIKUJE_SIĘ",
      "requirements_met": 68,
      "requirements_total": 68,
      "critical_issues": [],
      "minor_issues": [],
      "validation_details": {
        "02_kredytobiorca": {
          "01_wiek_klienta": {
            "status": "✅",
            "bank_requirement": "18-80 lat",
            "customer_value": "45 lat",
            "note": "OK - mieści się w zakresie"
          },
          "07_cudzoziemiec": {
            "status": "N/D",
            "bank_requirement": "karta stałego pobytu",
            "customer_value": "obywatel Polski",
            "note": "Nie dotyczy"
          }
        },
        "03_źródło_dochodu": {
          "02_umowa_o_pracę_na_czas_nieokreślony": {
            "status": "✅",
            "bank_requirement": "minimum 3 miesięczny staż",
            "customer_value": "5 lat stażu",
            "note": "OK - spełnia wymóg"
          }
        },
        "04_cel_kredytu": {
          "01_zakup_mieszkania_domu": {
            "status": "✅",
            "bank_requirement": "tak",
            "customer_value": "zakup mieszkania",
            "note": "Cel akceptowany"
          },
          "13_zakup_kamienicy": {
            "status": "N/D",
            "bank_requirement": "nie",
            "customer_value": "nie dotyczy",
            "note": "Klient nie kupuje kamienicy"
          }
        },
        "01_parametry_kredytu": {
          "04_LTV_kredyt": {
            "status": "✅",
            "bank_requirement": "90%",
            "customer_value": "80%",
            "note": "OK - w limicie"
          },
          "08_wkład_własny": {
            "status": "✅",
            "bank_requirement": "10%",
            "customer_value": "20%",
            "note": "OK - powyżej minimum"
          }
        }
      },
      "summary": "Bank spełnia wszystkie wymogi klienta. Brak problemów eliminujących."
    }
  ],
  
  "conditionally_qualified_banks": [
    {
      "bank_name": "Nazwa Banku",
      "qualification_status": "WARUNKOWO",
      "requirements_met": 66,
      "requirements_total": 68,
      "critical_issues": [],
      "minor_issues": [
        "Wymaga dostarczenia dodatkowego dokumentu X",
        "Preferuje wyższy wkład własny (15% vs 10%)"
      ],
      "validation_details": { },
      "summary": "Bank wymaga spełnienia 2 dodatkowych warunków, ale są one do osiągnięcia."
    }
  ],
  
  "disqualified_banks": [
    {
      "bank_name": "Nazwa Banku",
      "qualification_status": "NIE_KWALIFIKUJE_SIĘ",
      "requirements_met": 63,
      "requirements_total": 68,
      "critical_issues": [
        "❌ WIEK: Bank akceptuje maksymalnie 65 lat, klient ma 70 lat",
        "❌ CEL: Bank nie finansuje kamienic, a klient kupuje kamienicę",
        "❌ STAŻ: Bank wymaga minimum 12 mc działalności, klient ma 6 mc"
      ],
      "minor_issues": [],
      "validation_details": {
        "02_kredytobiorca": {
          "01_wiek_klienta": {
            "status": "❌",
            "bank_requirement": "18-65 lat",
            "customer_value": "70 lat",
            "note": "PROBLEM: Klient przekracza maksymalny wiek"
          }
        },
        "04_cel_kredytu": {
          "13_zakup_kamienicy": {
            "status": "❌",
            "bank_requirement": "nie",
            "customer_value": "zakup kamienicy",
            "note": "PROBLEM: Bank nie finansuje tego celu"
          }
        }
      },
      "summary": "Bank nie spełnia 5 krytycznych wymogów. Dyskwalifikacja."
    }
  ],
  
  "validation_summary": {
    "total_banks_analyzed": 11,
    "qualified_count": 6,
    "conditionally_qualified_count": 2,
    "disqualified_count": 3,
    "next_step": "Przejdź do ETAPU 2: Ranking JAKOŚCI dla 6-8 zakwalifikowanych banków"
  }
}
```

---

⚠️ KRYTYCZNE ZASADY:

1. **Sprawdź WSZYSTKIE 68 WYMOGÓW** dla każdego banku
2. **Jeśli parametr nie dotyczy klienta** → oznacz jako "N/D"
3. **Jeśli bank nie spełnia WYMOGÓW** → dyskwalifikuj (nie przejdzie do etapu 2)
4. **Cytuj dokładnie z bazy** - nie interpretuj, nie zgaduj
5. **Jeden ❌ w kluczowym WYMOGU = dyskwalifikacja** (np. wiek, cel, staż)
6. **Odpowiadaj TYLKO w formacie JSON** - bez dodatkowego tekstu przed/po

Twoim celem jest FILTROWANIE - eliminujesz banki niedopasowane, przekazujesz tylko te które MOGĄ obsłużyć klienta."""
    
    def create_ranking_prompt(self, qualified_banks: List[str]) -> str:
        """
        Tworzy prompt systemowy do rankingu JAKOŚCI
        
        Args:
            qualified_banks: Lista banków zakwalifikowanych z etapu 1
            
        Returns:
            Prompt systemowy do drugiego etapu (ranking)
        """
        banks_list = ", ".join(qualified_banks)
        
        # Dostosuj komunikat do liczby banków
        if len(qualified_banks) == 1:
            ranking_instruction = f"Dokładnie oceniasz JAKOŚĆ jedynego zakwalifikowanego banku (0-100 pkt)."
        elif len(qualified_banks) == 2:
            ranking_instruction = f"Rankujesz 2 banki: 🥇 LEPSZY, 🥈 GORSZY."
        elif len(qualified_banks) == 3:
            ranking_instruction = f"Rankujesz 3 banki: 🥇 NAJLEPSZY, 🥈 DRUGI, 🥉 TRZECI."
        else:
            ranking_instruction = f"Wybierasz TOP 4: 🏆 NAJLEPSZY, 🥈 DRUGI, 🥉 TRZECI, ⚠️ CZWARTY."
        
        return f"""Jesteś ekspertem ds. produktów hipotecznych w Platinum Financial.

🎯 TWOJE ZADANIE - ETAP 2: RANKING JAKOŚCI

Otrzymałeś listę banków zakwalifikowanych z ETAPU 1 (spełniają WYMOGI):
**{banks_list}**

Teraz rankujesz te banki według JAKOŚCI oferty (19 parametrów JAKOŚĆ = 22% wszystkich).
{ranking_instruction}

---

📋 PARAMETRY TYPU "JAKOŚĆ" (rankują banki):

**01_parametry kredytu (12 JAKOŚCI)**:
- udzoz (waluta) - dostępne waluty
- kwota kredytu - limity min/max
- okres kredytowania - maksymalny okres
- kwota pożyczki - limit pożyczki
- okres kredytowania pożyczki - max okres
- LTV pożyczka - max procent dla pożyczki
- WIBOR - stawka referencyjna (1M/3M/6M)
- oprocentowanie stałe - okres (5 lat/10 lat)
- wcześniejsza spłata - opłata (0%/1%/2%/3%)
- raty - równe/malejące/oba
- karencja - okres karencji (elastyczność)
- kredyt EKO - obniżka marży dla domów energooszczędnych

**06_wycena (2 JAKOŚCI)**:
- operat zewnętrzny/wewnętrzny - rodzaj operatu
- płatność za operat - koszt (200-1160 zł)

**07_ubezpieczenia (5 JAKOŚCI)**:
- ubezpieczenie pomostowe - koszt (+0.5% / +1% / brak)
- ubezpieczenie niskiego wkładu - koszt (+0.2% / +0.25% / brak)
- ubezpieczenie na życie - wymagalność i wpływ na marżę
- ubezpieczenie od utraty pracy - dostępność
- ubezpieczenie nieruchomości - dostępność i koszt

---

🏅 KRYTERIA RANKINGU (система punktowa 0-100):

**1. KOSZT KREDYTU (35 punktów)**
   - Opłata za wcześniejszą spłatę (0-10 pkt): 0% = 10 pkt, 1% = 7 pkt, 2% = 4 pkt, 3% = 0 pkt
   - Ubezpieczenie pomostowe (0-8 pkt): brak = 8 pkt, +0.5% = 5 pkt, +1% = 2 pkt, +1.3% = 0 pkt
   - Ubezpieczenie niskiego wkładu (0-7 pkt): brak/na koszt banku = 7 pkt, +0.2% = 4 pkt, +0.25% = 0 pkt
   - Koszt operatu (0-5 pkt): ≤400 zł = 5 pkt, 401-700 zł = 3 pkt, >700 zł = 0 pkt
   - Kredyt EKO (0-5 pkt): obniżka 0.2 p.p. = 5 pkt, 0.1 p.p. = 3 pkt, 0.05 p.p. = 2 pkt, brak = 0 pkt

**2. ELASTYCZNOŚĆ PRODUKTU (25 punktów)**
   - Maksymalna kwota kredytu (0-8 pkt): ≥4 mln = 8 pkt, 3-4 mln = 6 pkt, 2-3 mln = 4 pkt, <2 mln = 2 pkt
   - Okres kredytowania (0-7 pkt): 420 mc = 7 pkt, 360 mc = 5 pkt, 300 mc = 3 pkt
   - Karencja (0-5 pkt): do 60 mc = 5 pkt, do 24 mc = 3 pkt, brak = 0 pkt
   - Typ rat (0-5 pkt): równe i malejące = 5 pkt, tylko równe = 2 pkt

**3. WYGODA PROCESU (20 punktów)**
   - Rodzaj operatu (0-10 pkt): wewnętrzny = 10 pkt, oba = 7 pkt, zewnętrzny = 3 pkt
   - Termin ważności decyzji (0-5 pkt): 90 dni = 5 pkt, 60 dni = 3 pkt, 30 dni = 1 pkt
   - Dostępność walut (0-5 pkt): PLN+EUR+inne = 5 pkt, PLN+EUR = 3 pkt, PLN = 2 pkt

**4. DODATKOWE KORZYŚCI (15 punktów)**
   - Oprocentowanie stałe (0-8 pkt): 10 lat = 8 pkt, 5 lat = 5 pkt, brak = 0 pkt
   - Ubezpieczenie nieruchomości (0-4 pkt): dostępne z bonusem = 4 pkt, dostępne = 2 pkt, brak = 0 pkt
   - Ubezpieczenie od utraty pracy (0-3 pkt): dostępne = 3 pkt, brak = 0 pkt

**5. PARAMETRY MAKSYMALNE (5 punktów)**
   - LTV pożyczka (0-3 pkt): 60% = 3 pkt, 50% = 2 pkt, brak oferty = 0 pkt
   - Kwota pożyczki (0-2 pkt): ≥3 mln = 2 pkt, 1-3 mln = 1 pkt, brak = 0 pkt

---

📊 FORMAT ODPOWIEDZI:

## 🏆 OFERTA #1: [Nazwa Banku] - NAJLEPSZA OPCJA

### 📈 OCENA JAKOŚCI: **[X]/100 punktów**

#### 💰 KOSZT KREDYTU: [X]/35 pkt
- **Wcześniejsza spłata**: Bank: "[wartość z bazy]" → **[X]/10 pkt** - [uzasadnienie]
- **Ubezpieczenie pomostowe**: Bank: "[wartość]" → **[X]/8 pkt** - [uzasadnienie]
- **Ubezpieczenie niskiego wkładu**: Bank: "[wartość]" → **[X]/7 pkt** - [uzasadnienie]
- **Koszt operatu**: Bank: "[wartość]" → **[X]/5 pkt** - [uzasadnienie]
- **Kredyt EKO**: Bank: "[wartość]" → **[X]/5 pkt** - [uzasadnienie]

#### 🔧 ELASTYCZNOŚĆ: [X]/25 pkt
- **Kwota kredytu**: Bank: "[wartość]" → **[X]/8 pkt** - [uzasadnienie]
- **Okres kredytowania**: Bank: "[wartość]" → **[X]/7 pkt** - [uzasadnienie]
- **Karencja**: Bank: "[wartość]" → **[X]/5 pkt** - [uzasadnienie]
- **Typ rat**: Bank: "[wartość]" → **[X]/5 pkt** - [uzasadnienie]

#### ⚡ WYGODA PROCESU: [X]/20 pkt
- **Rodzaj operatu**: Bank: "[wartość]" → **[X]/10 pkt** - [uzasadnienie]
- **Termin decyzji**: Bank: "[wartość]" → **[X]/5 pkt** - [uzasadnienie]
- **Waluty**: Bank: "[wartość]" → **[X]/5 pkt** - [uzasadnienie]

#### 🎁 DODATKOWE KORZYŚCI: [X]/15 pkt
- **Oprocentowanie stałe**: Bank: "[wartość]" → **[X]/8 pkt** - [uzasadnienie]
- **Ubezpieczenie nieruchomości**: Bank: "[wartość]" → **[X]/4 pkt** - [uzasadnienie]
- **Ubezpieczenie utraty pracy**: Bank: "[wartość]" → **[X]/3 pkt** - [uzasadnienie]

#### 📊 PARAMETRY MAX: [X]/5 pkt
- **LTV pożyczka**: Bank: "[wartość]" → **[X]/3 pkt** - [uzasadnienie]
- **Kwota pożyczki**: Bank: "[wartość]" → **[X]/2 pkt** - [uzasadnienie]

### ✨ KLUCZOWE ATUTY:
1. [Konkretny atut z cytatem z bazy i oceną punktową]
2. [Konkretny atut z cytatem z bazy i oceną punktową]
3. [Konkretny atut z cytatem z bazy i oceną punktową]

### ⚠️ PUNKTY UWAGI:
1. [Ewentualne minusy z oceną punktową]

### 💡 DLACZEGO NAJLEPSZY:
[2-3 zdania uzasadniające najwyższy ranking]

---

## 🥈 OFERTA #2: [Nazwa Banku] - DRUGA OPCJA

[DOKŁADNIE TAKA SAMA STRUKTURA JAK POWYŻEJ]

### 📉 RÓŻNICA vs #1:
- **Punkty**: [X] vs [Y] (#1) = **-[różnica] pkt**
- **Główne różnice**: 
  1. [Konkretny parametr] - [bank #2] ma [wartość], podczas gdy [bank #1] ma [wartość]
  2. [Konkretny parametr] - [różnica w punktach i dlaczego]

---

## 🥉 OFERTA #3: [Nazwa Banku] - TRZECIA OPCJA

[DOKŁADNIE TAKA SAMA STRUKTURA]

### 📉 RÓŻNICA vs #1 i #2:
- **Punkty**: [X] vs [Y] (#1) vs [Z] (#2)
- **Dlaczego gorszy**: [wyjaśnienie]

---

## ⚠️ OFERTA #4: [Nazwa Banku] - NAJGORSZA OPCJA (dla kontrastu)

[DOKŁADNIE TAKA SAMA STRUKTURA]

### ❌ DLACZEGO NAJGORSZY:
1. **[Parametr]**: [wartość] - traci [X] punktów vs najlepszy
2. **[Parametr]**: [wartość] - traci [Y] punktów vs najlepszy
3. **Całkowicie gorszy w**: [kategoria] ([różnica] punktów)

### 🚫 CZEGO UNIKAĆ:
[2-3 konkretne powody dlaczego to najgorsza opcja dla tego klienta]

---

## 📊 TABELA PORÓWNAWCZA

| Parametr | 🏆 #1 [Bank] | 🥈 #2 [Bank] | 🥉 #3 [Bank] | ⚠️ #4 [Bank] |
|----------|-------------|-------------|-------------|-------------|
| **Punkty TOTAL** | [X]/100 | [Y]/100 | [Z]/100 | [W]/100 |
| Wcześniejsza spłata | [wartość] | [wartość] | [wartość] | [wartość] |
| Koszt operatu | [wartość] | [wartość] | [wartość] | [wartość] |
| Ubezp. pomostowe | [wartość] | [wartość] | [wartość] | [wartość] |
| Okres kredytu | [wartość] | [wartość] | [wartość] | [wartość] |
| Karencja | [wartość] | [wartość] | [wartość] | [wartość] |
| Kredyt EKO | [wartość] | [wartość] | [wartość] | [wartość] |

---

## 🎯 REKOMENDACJA KOŃCOWA

**Najlepsza opcja**: **[Bank #1]** zdobywa **[X]/100 punktów**
- Wygrywa w kategoriach: [wymień kategorie]
- Oszczędność vs #4: ~[kwota] zł w skali kredytu

**Dla kogo #2 może być lepszy**: [scenariusz, np. "jeśli klient potrzebuje dłuższej karencji"]

**Dla kogo #3 może być lepszy**: [scenariusz]

**Czego unikać**: **[Bank #4]** - [kluczowe powody]

---

⚠️ KRYTYCZNE ZASADY:

1. Rankuj TYLKO banki z listy zakwalifikowanych: {banks_list}
2. Oceń WSZYSTKIE 19 parametrów JAKOŚĆ dla każdego banku
3. Cytuj DOKŁADNE wartości z bazy wiedzy
4. Punktacja musi być zgodna z tabelą (0-100)
5. Uzasadnij KAŻDĄ ocenę punktową konkretnymi danymi
6. Top 3 to najlepsze, #4 to najgorszy dla kontrastu (pokazuje czego unikać)
7. Tabela porównawcza MUSI zawierać kluczowe parametry JAKOŚĆ"""
    
    def validate_requirements(
        self,
        user_query: str,
        knowledge_base_context: str
    ) -> Tuple[str, Dict]:
        """
        ETAP 1: Walidacja WYMOGÓW - pre-screening banków
        
        Args:
            user_query: Zapytanie użytkownika (profil klienta)
            knowledge_base_context: Kontekst z bazy wiedzy
            
        Returns:
            Tuple (odpowiedź JSON jako string, parsed dict)
        """
        validation_prompt = self.create_validation_prompt()
        
        messages = [
            {"role": "system", "content": validation_prompt},
            {"role": "system", "content": f"BAZA WIEDZY BANKÓW:\n\n{knowledge_base_context}"},
            {"role": "user", "content": f"PROFIL KLIENTA:\n\n{user_query}"}
        ]
        
        print("🔍 ETAP 1: Walidacja WYMOGÓW (pre-screening)...")
        response = self.create_chat_completion(
            messages=messages,
            temperature=0.1,  # Niska temperatura dla precyzji
            max_tokens=16000  # Zwiększono z 4000 - JSON dla 11 banków jest długi
        )
        
        # Parsuj JSON
        try:
            # Usuń markdown code blocks jeśli istnieją
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            parsed = json.loads(response_clean.strip())
            return response, parsed
        except json.JSONDecodeError as e:
            print(f"⚠️ Błąd parsowania JSON z etapu 1: {e}")
            return response, {}
    
    async def validate_single_bank_async(
        self,
        bank_name: str,
        bank_data: Dict,
        user_query: str,
        deployment_name: str = None
    ) -> Dict:
        """
        ASYNC: Walidacja pojedynczego banku (WYMOGI)
        
        Args:
            bank_name: Nazwa banku
            bank_data: Dane banku z knowledge base
            user_query: Profil klienta
            deployment_name: Opcjonalny model do użycia (domyślnie self.deployment_name)
            
        Returns:
            Dict z wynikiem walidacji dla tego banku
        """
        # Krótszy prompt dla pojedynczego banku
        validation_prompt = f"""Jesteś ekspertem ds. produktów hipotecznych w Platinum Financial.

🎯 ZADANIE: Sprawdź czy bank **{bank_name}** SPEŁNIA wszystkie WYMOGI klienta.

📋 Sprawdzasz TYLKO parametry typu WYMÓG (eliminatory) - 78% wszystkich parametrów.

**WYMOGI do sprawdzenia:**
- 02_kredytobiorca (7 WYMOGÓW): wiek, liczba wnioskodawców, związek nieformalny, właściciele, rozdzielność, cudzoziemiec
- 03_źródło dochodu (20 WYMOGÓW): wszystkie typy umów i dochodów
- 04_cel kredytu (24 WYMOGI): wszystkie typy transakcji
- 05_zabezpieczenie (14 WYMOGÓW): typy nieruchomości, lokalizacja, stan
- 06_ocena zdolności (13 WYMOGÓW): metody kalkulacji, współczynniki

**FORMAT ODPOWIEDZI (JSON):**
{{
  "bank_name": "{bank_name}",
  "status": "QUALIFIED" lub "DISQUALIFIED",
  "spelnione_wymogi": ["wymóg1", "wymóg2", ...],
  "niespelnione_wymogi": ["wymóg1: powód", "wymóg2: powód", ...],
  "kluczowe_problemy": ["problem1", "problem2"] (jeśli DISQUALIFIED),
  "notatki": "dodatkowe uwagi"
}}

⚠️ Jeśli choć JEDEN WYMÓG nie jest spełniony → status = "DISQUALIFIED"
✅ Jeśli WSZYSTKIE WYMOGI są spełnione → status = "QUALIFIED"
"""

        bank_context = json.dumps(bank_data, ensure_ascii=False, indent=2)
        
        messages = [
            {"role": "system", "content": validation_prompt},
            {"role": "system", "content": f"DANE BANKU {bank_name}:\n\n{bank_context}"},
            {"role": "user", "content": f"PROFIL KLIENTA:\n\n{user_query}"}
        ]
        
        # Użyj podanego modelu lub domyślnego
        model = deployment_name or self.deployment_name
        
        # Przygotuj parametry zgodnie z typem modelu
        completion_params = {
            "model": model,
            "messages": messages,
        }
        
        model_lower = model.lower()
        if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
            completion_params["temperature"] = 1.0
            completion_params["max_completion_tokens"] = 2000  # Mniejsze dla pojedynczego banku
        else:
            completion_params["temperature"] = 0.1
            completion_params["max_tokens"] = 2000
        
        try:
            response = await self.async_client.chat.completions.create(**completion_params)
            result_text = response.choices[0].message.content
            
            # Agresywne czyszczenie dla JSON
            result_clean = result_text.strip()
            
            # Usuń markdown code blocks
            if result_clean.startswith("```json"):
                result_clean = result_clean[7:]
            elif result_clean.startswith("```"):
                result_clean = result_clean[3:]
            
            if result_clean.endswith("```"):
                result_clean = result_clean[:-3]
            
            result_clean = result_clean.strip()
            
            # Próba parsowania
            try:
                result_dict = json.loads(result_clean)
                return result_dict
            except json.JSONDecodeError:
                # Jeśli fail, spróbuj znaleźć JSON w tekście
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_clean)
                if json_match:
                    try:
                        result_dict = json.loads(json_match.group(0))
                        return result_dict
                    except:
                        pass
                
                # Last resort - zwróć pustą odpowiedź z informacją o błędzie
                print(f"⚠️ Nie można sparsować JSONa dla {bank_name}, zwracam pusty wynik")
                print(f"   Pierwsze 200 znaków: {result_text[:200]}")
                return {
                    "bank_name": bank_name,
                    "status": "ERROR",
                    "error": "JSON parsing failed",
                    "raw_response": result_text[:500]
                }
            
        except Exception as e:
            print(f"⚠️ Błąd walidacji {bank_name}: {e}")
            return {
                "bank_name": bank_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    async def validate_requirements_async(
        self,
        user_query: str,
        knowledge_base: Dict,
        deployment_name: str = None
    ) -> Tuple[str, Dict]:
        """
        ASYNC PARALLEL: Walidacja WYMOGÓW dla wszystkich banków równolegle
        
        Args:
            user_query: Zapytanie użytkownika (profil klienta)
            knowledge_base: Pełna baza wiedzy (Dict z listą products)
            deployment_name: Opcjonalny model do użycia
            
        Returns:
            Tuple (odpowiedź JSON jako string, parsed dict)
        """
        print("🔍 ETAP 1: Walidacja WYMOGÓW (PARALLEL MODE)...")
        
        # Przygotuj listę tasków dla każdego banku
        tasks = []
        for product in knowledge_base.get("products", []):
            bank_name = product.get("bank_name")
            if bank_name:
                task = self.validate_single_bank_async(
                    bank_name=bank_name,
                    bank_data=product,
                    user_query=user_query,
                    deployment_name=deployment_name
                )
                tasks.append(task)
        
        # Wykonaj wszystkie równolegle
        print(f"⚡ Uruchamiam {len(tasks)} równoległych requestów...")
        results = await asyncio.gather(*tasks)
        
        # Połącz wyniki
        qualified_banks = []
        disqualified_banks = []
        
        for result in results:
            if result.get("status") == "QUALIFIED":
                qualified_banks.append(result)
            elif result.get("status") == "DISQUALIFIED":
                disqualified_banks.append(result)
            # Ignoruj ERROR results
        
        # Stwórz finalny JSON
        final_result = {
            "etap": "1_WALIDACJA_WYMOGÓW",
            "qualified_banks": qualified_banks,
            "disqualified_banks": disqualified_banks,
            "summary": {
                "total_banks": len(results),
                "qualified": len(qualified_banks),
                "disqualified": len(disqualified_banks)
            }
        }
        
        result_json = json.dumps(final_result, ensure_ascii=False, indent=2)
        print(f"✓ Zakwalifikowane: {len(qualified_banks)}/{len(results)} banków")
        
        return result_json, final_result
    
    async def rank_single_bank_async(
        self,
        bank_name: str,
        bank_data: Dict,
        user_query: str,
        deployment_name: str = None
    ) -> Dict:
        """
        ASYNC: Ocena jakości pojedynczego banku (19 parametrów JAKOŚCI)
        
        Args:
            bank_name: Nazwa banku
            bank_data: Dane banku z knowledge base
            user_query: Profil klienta
            deployment_name: Opcjonalny model do użycia
            
        Returns:
            Dict z oceną jakości banku (0-100 punktów)
        """
        # Krótszy prompt dla pojedynczego banku
        ranking_prompt = f"""Jesteś ekspertem ds. produktów hipotecznych w Platinum Financial.

🎯 ZADANIE: Oceń JAKOŚĆ oferty banku **{bank_name}** dla klienta (system punktowy 0-100).

📋 PARAMETRY JAKOŚCI (19 parametrów oceniających):

**1. KOSZT KREDYTU (35 punktów)**
- Opłata za wcześniejszą spłatę (0-10): 0% = 10, 1% = 7, 2% = 4, 3% = 0
- Ubezpieczenie pomostowe (0-8): brak = 8, +0.5% = 5, +1% = 2, +1.3% = 0
- Ubezpieczenie niskiego wkładu (0-7): brak = 7, +0.2% = 4, +0.25% = 0
- Koszt operatu (0-5): ≤400 zł = 5, 401-700 = 3, >700 = 0
- Kredyt EKO (0-5): -0.2 p.p. = 5, -0.1 = 3, -0.05 = 2, brak = 0

**2. ELASTYCZNOŚĆ PRODUKTU (25 punktów)**
- Maksymalna kwota kredytu (0-8): ≥4 mln = 8, 3-4 mln = 6, 2-3 mln = 4, <2 mln = 2
- Okres kredytowania (0-7): 420 mc = 7, 360 mc = 5, 300 mc = 3
- Karencja (0-5): do 60 mc = 5, do 24 mc = 3, brak = 0
- Typ rat (0-5): równe i malejące = 5, tylko równe = 2

**3. WYGODA PROCESU (20 punktów)**
- Rodzaj operatu (0-10): wewnętrzny = 10, oba = 7, zewnętrzny = 3
- Termin ważności decyzji (0-5): 90 dni = 5, 60 dni = 3, 30 dni = 1
- Dostępność walut (0-5): PLN+EUR+inne = 5, PLN+EUR = 3, PLN = 2

**4. DODATKOWE KORZYŚCI (15 punktów)**
- Oprocentowanie stałe (0-8): 10 lat = 8, 5 lat = 5, brak = 0
- Ubezpieczenie nieruchomości (0-4): dostępne z bonusem = 4, dostępne = 2, brak = 0
- Ubezpieczenie od utraty pracy (0-3): dostępne = 3, brak = 0

**5. PARAMETRY MAKSYMALNE (5 punktów)**
- LTV pożyczka (0-3): 60% = 3, 50% = 2, brak = 0
- Kwota pożyczki (0-2): ≥3 mln = 2, 1-3 mln = 1, brak = 0

---

📊 FORMAT ODPOWIEDZI (JSON):

{{
  "bank_name": "{bank_name}",
  "total_score": 87,
  "breakdown": {{
    "koszt_kredytu": 32,
    "elastycznosc": 23,
    "wygoda": 17,
    "korzysci": 11,
    "parametry_max": 4
  }},
  "details": {{
    "wczesniejsza_splata": {{"value": "0%", "points": 10}},
    "ubezpieczenie_pomostowe": {{"value": "brak", "points": 8}},
    "ubezpieczenie_niskiego_wkladu": {{"value": "+0.25%", "points": 0}},
    "koszt_operatu": {{"value": "400 zł", "points": 5}},
    "kredyt_eko": {{"value": "brak", "points": 0}},
    "kwota_max": {{"value": "3 mln", "points": 6}},
    "okres_kredytowania": {{"value": "420 mc", "points": 7}},
    "karencja": {{"value": "60 mc", "points": 5}},
    "typ_rat": {{"value": "równe i malejące", "points": 5}},
    "rodzaj_operatu": {{"value": "wewnętrzny", "points": 10}},
    "termin_decyzji": {{"value": "90 dni", "points": 5}},
    "waluty": {{"value": "PLN, EUR", "points": 3}},
    "oprocentowanie_stale": {{"value": "5 lat", "points": 5}},
    "ubezpieczenie_nieruchomosci": {{"value": "dostępne", "points": 2}},
    "ubezpieczenie_utraty_pracy": {{"value": "dostępne", "points": 3}},
    "ltv_pozyczka": {{"value": "60%", "points": 3}},
    "kwota_pozyczki": {{"value": "3 mln", "points": 2}}
  }},
  "kluczowe_atuty": [
    "Brak opłaty za wcześniejszą spłatę (10/10 pkt)",
    "Najdłuższy okres kredytowania 420 mc (7/7 pkt)",
    "Karencja do 60 miesięcy (5/5 pkt)"
  ],
  "punkty_uwagi": [
    "Brak kredytu EKO (0/5 pkt)",
    "Ubezpieczenie niskiego wkładu +0.25% (0/7 pkt)"
  ]
}}

⚠️ ZASADY:
- Oceń TYLKO na podstawie danych banku
- Przypisuj punkty DOKŁADNIE wg skali
- Kluczowe atuty = TOP 3 najlepsze parametry (najwyższe punkty)
- Punkty uwagi = 2-3 najgorsze parametry (najniższe punkty lub minusy)
"""

        bank_context = json.dumps(bank_data, ensure_ascii=False, indent=2)
        
        messages = [
            {"role": "system", "content": ranking_prompt},
            {"role": "system", "content": f"DANE BANKU {bank_name}:\n\n{bank_context}"},
            {"role": "user", "content": f"PROFIL KLIENTA:\n\n{user_query}"}
        ]
        
        # Użyj podanego modelu lub domyślnego
        model = deployment_name or self.deployment_name
        
        # Przygotuj parametry zgodnie z typem modelu
        completion_params = {
            "model": model,
            "messages": messages,
        }
        
        model_lower = model.lower()
        if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
            completion_params["temperature"] = 1.0
            completion_params["max_completion_tokens"] = 2500
        else:
            completion_params["temperature"] = 0.2
            completion_params["max_tokens"] = 2500
        
        try:
            response = await self.async_client.chat.completions.create(**completion_params)
            result_text = response.choices[0].message.content
            
            # Agresywne czyszczenie dla JSON
            result_clean = result_text.strip()
            
            # Usuń markdown code blocks
            if result_clean.startswith("```json"):
                result_clean = result_clean[7:]
            elif result_clean.startswith("```"):
                result_clean = result_clean[3:]
            
            if result_clean.endswith("```"):
                result_clean = result_clean[:-3]
            
            result_clean = result_clean.strip()
            
            # Próba parsowania
            try:
                result_dict = json.loads(result_clean)
                return result_dict
            except json.JSONDecodeError:
                # Jeśli fail, spróbuj znaleźć JSON w tekście
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_clean)
                if json_match:
                    try:
                        result_dict = json.loads(json_match.group(0))
                        return result_dict
                    except:
                        pass
                
                # Last resort - zwróć domyślną ocenę
                print(f"⚠️ Nie można sparsować JSONa oceny dla {bank_name}, zwracam wynik 50/100")
                print(f"   Pierwsze 200 znaków: {result_text[:200]}")
                return {
                    "bank_name": bank_name,
                    "total_score": 50,
                    "breakdown": {
                        "koszt_kredytu": 17,
                        "elastycznosc": 12,
                        "wygoda": 10,
                        "korzysci": 7,
                        "parametry_max": 2
                    },
                    "kluczowe_atuty": ["Ocena automatyczna - błąd parsowania"],
                    "punkty_uwagi": ["Nie udało się sparsować odpowiedzi AI"],
                    "error": "JSON parsing failed"
                }
            
        except Exception as e:
            print(f"⚠️ Błąd oceny {bank_name}: {e}")
            return {
                "bank_name": bank_name,
                "total_score": 0,
                "error": str(e)
            }
    
    async def rank_by_quality_async(
        self,
        user_query: str,
        knowledge_base: Dict,
        qualified_banks: List[str],
        deployment_name: str = None
    ) -> str:
        """
        ASYNC PARALLEL: Ranking JAKOŚCI dla wszystkich zakwalifikowanych banków
        
        Args:
            user_query: Zapytanie użytkownika (profil klienta)
            knowledge_base: Pełna baza wiedzy (Dict z listą products)
            qualified_banks: Lista nazw zakwalifikowanych banków
            deployment_name: Opcjonalny model do użycia
            
        Returns:
            Markdown z rankingiem TOP 4 banków
        """
        print(f"🏅 ETAP 2: Ranking JAKOŚCI (PARALLEL MODE - {len(qualified_banks)} banków)...")
        
        # Przygotuj listę tasków dla każdego banku
        tasks = []
        for bank_name in qualified_banks:
            # Znajdź dane banku
            bank_data = None
            for product in knowledge_base.get("products", []):
                if product.get("bank_name") == bank_name:
                    bank_data = product
                    break
            
            if bank_data:
                task = self.rank_single_bank_async(
                    bank_name=bank_name,
                    bank_data=bank_data,
                    user_query=user_query,
                    deployment_name=deployment_name
                )
                tasks.append(task)
        
        # Wykonaj wszystkie równolegle
        print(f"⚡ Uruchamiam {len(tasks)} równoległych requestów oceny jakości...")
        results = await asyncio.gather(*tasks)
        
        # Sortuj po total_score (malejąco)
        valid_results = [r for r in results if "error" not in r]
        valid_results.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        
        print(f"✓ Oceniono {len(valid_results)} banków")
        
        # Formatuj TOP 4 do markdown
        markdown = self._format_ranking_markdown(valid_results[:4], user_query)
        
        return markdown
    
    def _format_ranking_markdown(self, top_banks: List[Dict], user_query: str) -> str:
        """
        Formatuje wyniki rankingu do markdown (TOP 4)
        
        Args:
            top_banks: Lista dict z ocenami banków (max 4)
            user_query: Profil klienta (dla kontekstu)
            
        Returns:
            Markdown z pełnym rankingiem TOP 4
        """
        medals = ["🥇", "🥈", "🥉", "🎖️"]
        positions = ["NAJLEPSZA OPCJA", "DRUGA OPCJA", "TRZECIA OPCJA", "CZWARTA OPCJA"]
        
        lines = []
        lines.append("# 🏆 RANKING JAKOŚCI OFERT HIPOTECZNYCH")
        lines.append("")
        lines.append(f"*Ocena dla profilu: {user_query[:100]}...*")
        lines.append("")
        lines.append("="*80)
        lines.append("")
        
        for i, bank in enumerate(top_banks):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            position = positions[i] if i < len(positions) else f"OPCJA #{i+1}"
            
            lines.append(f"## {medal} OFERTA #{i+1}: **{bank['bank_name']}** – {position}")
            lines.append("")
            lines.append(f"### 📈 OCENA JAKOŚCI: **{bank['total_score']}/100 punktów**")
            lines.append("")
            
            # Breakdown kategorii
            breakdown = bank.get("breakdown", {})
            lines.append(f"#### 💰 KOSZT KREDYTU: {breakdown.get('koszt_kredytu', 0)}/35 pkt")
            
            details = bank.get("details", {})
            if details:
                lines.append(f"- **Wcześniejsza spłata**: {details.get('wczesniejsza_splata', {}).get('value', 'N/D')} → **{details.get('wczesniejsza_splata', {}).get('points', 0)}/10 pkt**")
                lines.append(f"- **Ubezpieczenie pomostowe**: {details.get('ubezpieczenie_pomostowe', {}).get('value', 'N/D')} → **{details.get('ubezpieczenie_pomostowe', {}).get('points', 0)}/8 pkt**")
                lines.append(f"- **Ubezpieczenie niskiego wkładu**: {details.get('ubezpieczenie_niskiego_wkladu', {}).get('value', 'N/D')} → **{details.get('ubezpieczenie_niskiego_wkladu', {}).get('points', 0)}/7 pkt**")
                lines.append(f"- **Koszt operatu**: {details.get('koszt_operatu', {}).get('value', 'N/D')} → **{details.get('koszt_operatu', {}).get('points', 0)}/5 pkt**")
                lines.append(f"- **Kredyt EKO**: {details.get('kredyt_eko', {}).get('value', 'N/D')} → **{details.get('kredyt_eko', {}).get('points', 0)}/5 pkt**")
            lines.append("")
            
            lines.append(f"#### 🔧 ELASTYCZNOŚĆ: {breakdown.get('elastycznosc', 0)}/25 pkt")
            if details:
                lines.append(f"- **Kwota kredytu**: {details.get('kwota_max', {}).get('value', 'N/D')} → **{details.get('kwota_max', {}).get('points', 0)}/8 pkt**")
                lines.append(f"- **Okres kredytowania**: {details.get('okres_kredytowania', {}).get('value', 'N/D')} → **{details.get('okres_kredytowania', {}).get('points', 0)}/7 pkt**")
                lines.append(f"- **Karencja**: {details.get('karencja', {}).get('value', 'N/D')} → **{details.get('karencja', {}).get('points', 0)}/5 pkt**")
                lines.append(f"- **Typ rat**: {details.get('typ_rat', {}).get('value', 'N/D')} → **{details.get('typ_rat', {}).get('points', 0)}/5 pkt**")
            lines.append("")
            
            lines.append(f"#### ⚡ WYGODA PROCESU: {breakdown.get('wygoda', 0)}/20 pkt")
            if details:
                lines.append(f"- **Rodzaj operatu**: {details.get('rodzaj_operatu', {}).get('value', 'N/D')} → **{details.get('rodzaj_operatu', {}).get('points', 0)}/10 pkt**")
                lines.append(f"- **Termin decyzji**: {details.get('termin_decyzji', {}).get('value', 'N/D')} → **{details.get('termin_decyzji', {}).get('points', 0)}/5 pkt**")
                lines.append(f"- **Waluty**: {details.get('waluty', {}).get('value', 'N/D')} → **{details.get('waluty', {}).get('points', 0)}/5 pkt**")
            lines.append("")
            
            lines.append(f"#### 🎁 DODATKOWE KORZYŚCI: {breakdown.get('korzysci', 0)}/15 pkt")
            if details:
                lines.append(f"- **Oprocentowanie stałe**: {details.get('oprocentowanie_stale', {}).get('value', 'N/D')} → **{details.get('oprocentowanie_stale', {}).get('points', 0)}/8 pkt**")
                lines.append(f"- **Ubezpieczenie nieruchomości**: {details.get('ubezpieczenie_nieruchomosci', {}).get('value', 'N/D')} → **{details.get('ubezpieczenie_nieruchomosci', {}).get('points', 0)}/4 pkt**")
                lines.append(f"- **Ubezpieczenie utraty pracy**: {details.get('ubezpieczenie_utraty_pracy', {}).get('value', 'N/D')} → **{details.get('ubezpieczenie_utraty_pracy', {}).get('points', 0)}/3 pkt**")
            lines.append("")
            
            lines.append(f"#### 📊 PARAMETRY MAX: {breakdown.get('parametry_max', 0)}/5 pkt")
            if details:
                lines.append(f"- **LTV pożyczka**: {details.get('ltv_pozyczka', {}).get('value', 'N/D')} → **{details.get('ltv_pozyczka', {}).get('points', 0)}/3 pkt**")
                lines.append(f"- **Kwota pożyczki**: {details.get('kwota_pozyczki', {}).get('value', 'N/D')} → **{details.get('kwota_pozyczki', {}).get('points', 0)}/2 pkt**")
            lines.append("")
            
            # Kluczowe atuty
            atuty = bank.get("kluczowe_atuty", [])
            if atuty:
                lines.append("### ✨ KLUCZOWE ATUTY:")
                for j, atut in enumerate(atuty[:3], 1):
                    lines.append(f"{j}. {atut}")
                lines.append("")
            
            # Punkty uwagi
            uwagi = bank.get("punkty_uwagi", [])
            if uwagi:
                lines.append("### ⚠️ PUNKTY UWAGI:")
                for j, uwaga in enumerate(uwagi, 1):
                    lines.append(f"{j}. {uwaga}")
                lines.append("")
            
            # Różnica vs #1
            if i > 0:
                diff = top_banks[0]["total_score"] - bank["total_score"]
                lines.append(f"### 📉 RÓŻNICA vs #{1}:")
                lines.append(f"- **Punkty**: {bank['total_score']} vs {top_banks[0]['total_score']} (#{1}) = **-{diff} pkt**")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Tabela porównawcza
        if len(top_banks) > 1:
            lines.append("## 📊 TABELA PORÓWNAWCZA")
            lines.append("")
            lines.append("| Parametr | " + " | ".join([f"{medals[i]} {b['bank_name']}" for i, b in enumerate(top_banks)]) + " |")
            lines.append("|----------|" + "|".join(["----------"] * len(top_banks)) + "|")
            lines.append("| **TOTAL** | " + " | ".join([f"**{b['total_score']}/100**" for b in top_banks]) + " |")
            
            breakdown_keys = [
                ("Koszt kredytu", "koszt_kredytu"),
                ("Elastyczność", "elastycznosc"),
                ("Wygoda", "wygoda"),
                ("Korzyści", "korzysci"),
                ("Parametry MAX", "parametry_max")
            ]
            
            for label, key in breakdown_keys:
                values = [str(b.get("breakdown", {}).get(key, 0)) for b in top_banks]
                lines.append(f"| {label} | " + " | ".join(values) + " |")
            
            lines.append("")
        
        # Rekomendacja końcowa
        if top_banks:
            winner = top_banks[0]
            lines.append("## 🎯 REKOMENDACJA KOŃCOWA")
            lines.append("")
            lines.append(f"**Najlepsza opcja**: **{winner['bank_name']}** zdobywa **{winner['total_score']}/100 punktów**")
            lines.append("")
            
            if len(top_banks) > 1:
                lines.append(f"**Oszczędność vs #{len(top_banks)}**: ~{winner['total_score'] - top_banks[-1]['total_score']} punktów przewagi")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def rank_by_quality(
        self,
        user_query: str,
        knowledge_base_context: str,
        qualified_banks: List[str],
        deployment_name: str = None
    ) -> str:
        """
        ETAP 2: Ranking JAKOŚCI - punktacja zakwalifikowanych banków
        
        Args:
            user_query: Zapytanie użytkownika (profil klienta)
            knowledge_base_context: Kontekst z bazy wiedzy
            qualified_banks: Lista banków zakwalifikowanych z etapu 1
            deployment_name: Opcjonalny model do użycia
            
        Returns:
            Ranking TOP 4 banków z oceną punktową
        """
        ranking_prompt = self.create_ranking_prompt(qualified_banks)
        
        messages = [
            {"role": "system", "content": ranking_prompt},
            {"role": "system", "content": f"BAZA WIEDZY BANKÓW (tylko zakwalifikowane):\n\n{knowledge_base_context}"},
            {"role": "user", "content": f"PROFIL KLIENTA:\n\n{user_query}"}
        ]
        
        print(f"🏅 ETAP 2: Ranking JAKOŚCI ({len(qualified_banks)} banków)...")
        
        # Użyj podanego modelu lub domyślnego
        original_deployment = self.deployment_name
        if deployment_name:
            self.deployment_name = deployment_name
        
        try:
            response = self.create_chat_completion(
                messages=messages,
                temperature=0.2,  # Trochę wyższa dla kreatywności w opisach
                max_tokens=6000
            )
        finally:
            # Przywróć oryginalny model
            self.deployment_name = original_deployment
        
        return response
    
    def query_two_stage(
        self,
        user_query: str,
        knowledge_base_context: str,
        etap1_model: str = None,
        etap2_model: str = None,
        use_async: bool = True,
        knowledge_base_dict: Dict = None
    ) -> Dict[str, str]:
        """
        Główna metoda - dwuetapowe przetwarzanie zapytania
        
        Args:
            user_query: Zapytanie użytkownika
            knowledge_base_context: Kontekst z bazy wiedzy (string)
            etap1_model: Model do ETAP 1 (None = domyślny)
            etap2_model: Model do ETAP 2 (None = domyślny)
            use_async: Czy używać async parallel processing
            knowledge_base_dict: Pełna baza wiedzy jako Dict (dla async)
            
        Returns:
            Dict z wynikami obu etapów
        """
        print("\n" + "="*80)
        print("🚀 DWUETAPOWY SYSTEM DOPASOWANIA KREDYTÓW")
        if use_async:
            print("⚡ Tryb: ASYNC PARALLEL")
        print("="*80 + "\n")
        
        # ETAP 1: Walidacja WYMOGÓW
        if use_async and knowledge_base_dict:
            # Async parallel processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                validation_response, validation_data = loop.run_until_complete(
                    self.validate_requirements_async(
                        user_query=user_query,
                        knowledge_base=knowledge_base_dict,
                        deployment_name=etap1_model
                    )
                )
            finally:
                loop.close()
        else:
            # Sequential processing (stara metoda)
            validation_response, validation_data = self.validate_requirements(
                user_query=user_query,
                knowledge_base_context=knowledge_base_context
            )
        
        if not validation_data:
            print("❌ Błąd w etapie 1 - nie można kontynuować")
            return {
                "stage1_validation": validation_response,
                "stage2_ranking": "Błąd: Nie można przejść do etapu 2 bez poprawnej walidacji",
                "error": True
            }
        
        # Wyciągnij listę zakwalifikowanych banków
        qualified = []
        if "qualified_banks" in validation_data:
            qualified.extend([b["bank_name"] for b in validation_data["qualified_banks"]])
        if "conditionally_qualified_banks" in validation_data:
            qualified.extend([b["bank_name"] for b in validation_data["conditionally_qualified_banks"]])
        
        print(f"\n✅ Zakwalifikowane banki ({len(qualified)}): {', '.join(qualified)}\n")
        
        if len(qualified) == 0:
            print("❌ Brak zakwalifikowanych banków")
            return {
                "stage1_validation": validation_response,
                "stage2_ranking": "Niestety, żaden bank nie spełnia wszystkich wymogów dla tego profilu klienta.",
                "error": False,
                "qualified_banks": []
            }
        
        # ETAP 2: Ranking JAKOŚCI
        if use_async and knowledge_base_dict:
            # Async parallel processing dla ETAP 2
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                ranking_response = loop.run_until_complete(
                    self.rank_by_quality_async(
                        user_query=user_query,
                        knowledge_base=knowledge_base_dict,
                        qualified_banks=qualified,
                        deployment_name=etap2_model
                    )
                )
            finally:
                loop.close()
        else:
            # Sequential processing (stara metoda)
            ranking_response = self.rank_by_quality(
                user_query=user_query,
                knowledge_base_context=knowledge_base_context,
                qualified_banks=qualified,
                deployment_name=etap2_model
            )
        
        print("\n" + "="*80)
        print("✅ ANALIZA ZAKOŃCZONA")
        print("="*80 + "\n")
        
        return {
            "stage1_validation": validation_response,
            "stage2_ranking": ranking_response,
            "error": False,
            "qualified_banks": qualified
        }

        
        # Wczytaj klasyfikację parametrów (WYMÓG vs JAKOŚĆ)
        self._load_parameter_classification()
    
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Wysyła zapytanie do modelu AI
        
        Args:
            messages: Lista wiadomości w formacie OpenAI
            temperature: Temperatura modelu (0-1)
            max_tokens: Maksymalna liczba tokenów w odpowiedzi
            
        Returns:
            Odpowiedź od modelu
        """
        try:
            # GPT-5 używa max_completion_tokens zamiast max_tokens
            completion_params = {
                "model": self.deployment_name,
                "messages": messages,
            }
            
            # Modele nowej generacji (GPT-5, O-series) wymagają temperature=1
            model_lower = self.deployment_name.lower()
            if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
                completion_params["temperature"] = 1.0  # Wymagane dla nowych modeli
            else:
                completion_params["temperature"] = temperature or config.TEMPERATURE
            
            # Dodaj odpowiedni parametr w zależności od modelu
            if "gpt-5" in model_lower or "gpt-4.1" in model_lower or "o4" in model_lower or "o1" in model_lower:
                completion_params["max_completion_tokens"] = max_tokens or config.MAX_TOKENS
            else:
                completion_params["max_tokens"] = max_tokens or config.MAX_TOKENS
            
            response = self.client.chat.completions.create(**completion_params)
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"✗ Błąd podczas komunikacji z AI: {str(e)}")
            raise
    
    def query_with_context(
        self,
        user_query: str,
        knowledge_base_context: str
    ) -> str:
        """
        Wysyła zapytanie z kontekstem bazy wiedzy
        
        Args:
            user_query: Zapytanie użytkownika
            knowledge_base_context: Kontekst z bazy wiedzy
            
        Returns:
            Odpowiedź od modelu
        """
        system_prompt = """Jesteś ekspertem ds. produktów hipotecznych w Platinum Financial.
Twoim zadaniem jest analiza zapytań klientów i rekomendacja 4 OFERT BANKOWYCH: 3 NAJLEPSZE (od najlepszej do gorszej) + 1 NAJGORSZA OPCJA.

STRUKTURA BAZY WIEDZY - 8 GRUP PARAMETRÓW:
1. "01_parametry kredytu" - waluta, kwota, okres, LTV, wkład własny, WIBOR, karencja, limity kredytów
2. "02_kredytobiorca" - wiek, liczba wnioskodawców, związek nieformalny, cudzoziemcy, właściciele
3. "03_źródło dochodu" - typy umów, staże, samozatrudnienie, emerytury, najmy, 800+
4. "04_cel kredytu" - zakup/budowa, refinansowanie, konsolidacja, transakcje rodzinne, kamienice
5. "05_zabezpieczenia" - zabezpieczenie osoby trzeciej, działka jako wkład
6. "06_wycena" - operat wewnętrzny/zewnętrzny, płatność
7. "07_ubezpieczenia" - pomostowe, niskiego wkładu, na życie, nieruchomości
8. "08_ważność dokumentów" - terminy ważności wszystkich dokumentów

ZASADY ANALIZY:
1. Przeanalizuj dokładnie WSZYSTKIE parametry klienta z zapytania
2. Znajdź 4 banki: 3 najlepsze (🏆🥈🥉) + 1 najgorszą opcję (⚠️)
3. Dla KAŻDEGO banku przeprowadź SZCZEGÓŁOWĄ WERYFIKACJĘ przez WSZYSTKIE 8 grup parametrów
4. Najgorsza opcja (4.) powinna pokazywać dlaczego NIE jest dobrym wyborem

FORMAT ODPOWIEDZI - OBOWIĄZKOWY:

## 🏆 OFERTA #1: [Nazwa Banku]

### ✅ WERYFIKACJA KOMPLETNA

#### 01_parametry kredytu
- **udzoz (waluta)**: ✅/❌ Bank: [np. "PLN, EUR"] → Klient: [np. "PLN"] - [OK/Problem]
- **kwota kredytu (02)**: ✅/❌ Bank: [np. "100 000 - 3 000 000 zł"] → Klient: [np. "960 000 zł"] - [OK/Poza limitem]
- **okres kredytowania kredytu (03)**: ✅/❌ Bank: [np. "420 miesięcy"] → Klient: [np. "300 miesięcy"] - [OK/Przekroczony]
- **LTV kredyt (04)**: ✅/❌ Bank: [np. "90%"] → Klient: [np. "80%"] - [OK/Za wysokie]
- **kwota pożyczki (05)**: ✅/❌/N/D Bank: [limit] → Klient: [wartość] - [komentarz]
- **LTV pożyczka (07)**: ✅/❌/N/D Bank: [limit] → Klient: [wartość] - [komentarz]
- **wkład własny (08)**: ✅/❌ Bank: [np. "10%"] → Klient: [np. "20%"] - [OK/Za niski]
- **WIBOR (09)**: ✅/N/D Bank: [np. "WIBOR 3M"] → [informacyjnie]
- **oprocentowanie stałe (10)**: ✅/N/D Bank: [np. "5 lat"] → [informacyjnie]
- **karencja w spłacie kapitału (13)**: ✅/❌/N/D Bank: [limit] → Klient: [potrzeba] - [komentarz]
- **ile kredytów hipotecznych (14)**: ✅/❌/N/D Bank: [limit] → Klient: [liczba] - [komentarz]
- **wielkość działki (15)**: ✅/❌/N/D Bank: [limit] → Klient: [powierzchnia] - [komentarz]
- **kredyt EKO (16)**: ✅/❌/N/D Bank: [warunki] → Klient: [parametry] - [komentarz]
⚠️ **NOTATKA**: [Jeśli ❌ opisz dokładnie co jest problemem i jakie są konsekwencje]

#### 02_kredytobiorca
- **wiek Klienta (01)**: ✅/❌ Bank: [np. "18-67 lat"] → Klient: [np. "42 lata"] - [OK/Za młody/Za stary]
- **maksymalna liczba wnioskodawców (02)**: ✅/❌ Bank: [limit] → Klient: [liczba] - [komentarz]
- **związek nieformalny (03)**: ✅/❌/N/D Bank: [zasady] → Klient: [status] - [komentarz]
- **dowód osobisty (04)**: ✅/N/D Bank: [wymóg] → [informacyjnie]
- **wszyscy właściciele (05)**: ✅/❌/N/D Bank: [wymóg] → Klient: [sytuacja] - [komentarz]
- **rozdzielność majątkowa (06)**: ✅/❌/N/D Bank: [wymóg] → Klient: [status] - [komentarz]
- **cudzoziemiec (07)**: ✅/❌/N/D Bank: [wymogi karty pobytu] → Klient: [status] - [komentarz]
⚠️ **NOTATKA**: [Jeśli ❌ opisz problem]

#### 03_źródło dochodu
- **Typ umowy klienta**: [określ konkretny typ z zapytania]
- **umowa o pracę na czas określony (01)**: ✅/❌/N/D Bank: [wymogi stażu] → Klient: [staż] - [komentarz]
- **umowa o pracę na czas nieokreślony (02)**: ✅/❌/N/D Bank: [wymogi] → Klient: [staż] - [komentarz]
- **kontrakt menadżerski (04)**: ✅/❌/N/D Bank: [wymogi] → Klient: [staż] - [komentarz]
- **umowa o dzieło (05)**: ✅/❌/N/D Bank: [wymogi] → Klient: [staż] - [komentarz]
- **umowa zlecenie (06)**: ✅/❌/N/D Bank: [wymogi] → Klient: [staż] - [komentarz]
- **działalność gospodarcza (07/08/09/10)**: ✅/❌/N/D Bank: [wymogi dla typu księgowości] → Klient: [czas prowadzenia] - [komentarz]
- **samozatrudnienie**: ✅/❌/N/D Bank: [specjalne warunki] → Klient: [status] - [komentarz]
- **dochody z najmu (11)**: ✅/❌/N/D Bank: [wymogi] → Klient: [okres] - [komentarz]
- **emerytura (12)**: ✅/❌/N/D Bank: [akceptacja] → Klient: [status] - [komentarz]
- **renta (13)**: ✅/❌/N/D Bank: [wymogi stałości] → Klient: [status] - [komentarz]
- **dywidendy (14)**: ✅/❌/N/D Bank: [wymogi okresu] → Klient: [okres] - [komentarz]
- **urlop macierzyński (17)**: ✅/❌/N/D Bank: [warunki] → Klient: [status] - [komentarz]
- **dochód w obcej walucie (18)**: ✅/❌/N/D Bank: [warunki] → Klient: [waluta] - [komentarz]
- **800 plus (19)**: ✅/❌/N/D Bank: [akceptacja] → Klient: [czy dotyczy] - [komentarz]
- **Dochód współmałżonka**: ✅/❌/N/D [weryfikacja typu i stażu]
⚠️ **NOTATKA**: [Kluczowe problemy ze źródłem dochodu]

#### 04_cel kredytu
- **Cel klienta**: [określ dokładny cel z zapytania]
- **zakup mieszkania/domu (01)**: ✅/❌/N/D Bank: [LTV dla celu] → Klient: [cel+LTV] - [komentarz]
- **budowa domu (02/03/04)**: ✅/❌/N/D Bank: [warunki, cena/m2] → Klient: [parametry] - [komentarz]
- **zakup działki (05/06/08)**: ✅/❌/N/D Bank: [limity powierzchni, LTV] → Klient: [powierzchnia] - [komentarz]
- **siedlisko (09)**: ✅/❌/N/D Bank: [warunki] → Klient: [powierzchnia] - [komentarz]
- **dom letniskowy (10)**: ✅/❌/N/D Bank: [warunki] → Klient: [typ] - [komentarz]
- **lokal użytkowy (12)**: ✅/❌/N/D Bank: [akceptacja] → Klient: [cel] - [komentarz]
- **kamienica (13)**: ✅/❌/N/D Bank: [warunki] → Klient: [parametry] - [komentarz]
- **zakup udziału (14)**: ✅/❌/N/D Bank: [warunki] → Klient: [udział] - [komentarz]
- **ekspektatywa/cesja (15)**: ✅/❌/N/D Bank: [odstępne?] → Klient: [parametry] - [komentarz]
- **refinansowanie wydatków (16)**: ✅/❌/N/D Bank: [ile miesięcy] → Klient: [okres] - [komentarz]
- **nieruchomość z komercją (17)**: ✅/❌/N/D Bank: [max % komercji] → Klient: [%] - [komentarz]
- **refinansowanie kredytu (18)**: ✅/❌/N/D Bank: [warunki] → Klient: [cel] - [komentarz]
- **transakcja rodzinna (19)**: ✅/❌/N/D Bank: [akceptacja] → Klient: [rodzaj] - [komentarz]
- **konsolidacja (22)**: ✅/❌/N/D Bank: [max %, marża] → Klient: [kwota] - [komentarz]
- **cel dowolny (23)**: ✅/❌/N/D Bank: [max %] → Klient: [kwota] - [komentarz]
⚠️ **NOTATKA**: [Problemy z realizacją celu]

#### 05_zabezpieczenia
- **zabezpieczenie na nieruchomości osoby trzeciej (01)**: ✅/❌/N/D Bank: [warunki] → Klient: [sytuacja] - [komentarz]
- **działka jako wkład własny (02)**: ✅/❌/N/D Bank: [warunki] → Klient: [czy dotyczy] - [komentarz]
⚠️ **NOTATKA**: [Problemy z zabezpieczeniem]

#### 06_wycena
- **operat (01)**: ✅/N/D Bank: [wewnętrzny/zewnętrzny] → [informacyjnie]
- **płatność za operat (02)**: ✅/N/D Bank: [kwoty] → [informacyjnie]

#### 07_ubezpieczenia
- **ubezpieczenie pomostowe (01)**: ✅/❌/N/D Bank: [wymóg/brak] → [komentarz]
- **ubezpieczenie niskiego wkładu (02)**: ✅/❌/N/D Bank: [podwyżka marży] → Klient: [wkład] - [komentarz]
- **ubezpieczenie na życie (03)**: ✅/❌/N/D Bank: [wymóg/wpływ na marżę] → [komentarz]
- **ubezpieczenie nieruchomości (05)**: ✅/N/D Bank: [dostępność] → [informacyjnie]
⚠️ **NOTATKA**: [Wpływ ubezpieczeń na koszty]

#### 08_ważność dokumentów
- **wniosek o kredyt (02)**: ✅/N/D Bank: [termin] → [informacyjnie]
- **zaświadczenie o zarobkach (03)**: ✅/N/D Bank: [termin] → [informacyjnie]
- **ważność decyzji kredytowej (15)**: ✅/N/D Bank: [termin] → [informacyjnie]

### 📊 OCENA KOŃCOWA
**Dopasowanie**: [X/10] ([Y] wymogów spełnionych, [Z] problemów)
**Główne atuty**: 
1. [konkretny atut z cytatem z bazy]
2. [konkretny atut z cytatem z bazy]

**Główne ryzyka**: 
1. [konkretne ryzyko z cytatem z bazy]
2. [konkretne ryzyko z cytatem z bazy]

**Uzasadnienie rankingu**: [2-3 zdania dlaczego ten bank jest najlepszy/drugi/trzeci]

---

## 🥈 OFERTA #2: [Nazwa Banku]
[DOKŁADNIE TAKA SAMA STRUKTURA JAK POWYŻEJ - wszystkie 8 grup parametrów]

---

## 🥉 OFERTA #3: [Nazwa Banku]
[DOKŁADNIE TAKA SAMA STRUKTURA JAK POWYŻEJ - wszystkie 8 grup parametrów]

---

## ⚠️ OFERTA #4: [Nazwa Banku] - NAJGORSZA OPCJA

### ❌ WERYFIKACJA KOMPLETNA Z PROBLEMAMI

[DOKŁADNIE TAKA SAMA STRUKTURA JAK POWYŻEJ - wszystkie 8 grup parametrów]
[PODKREŚL wszystkie ❌ i problemy, które sprawiają że to najgorsza opcja]

### � OCENA KOŃCOWA
**Dopasowanie**: X/10 (ile wymogów spełnionych / WYJAŚNIJ PROBLEMY)
**Główne problemy**: 
1. [konkretny problem z cytatem z bazy - DLACZEGO TO WYKLUCZA]
2. [konkretny problem z cytatem z bazy - DLACZEGO TO JEST GORSZE]

**Dlaczego najgorsza opcja**: [2-3 zdania jasno tłumaczące dlaczego NIE polecamy tego banku dla tego klienta]

---

## �📌 PODSUMOWANIE PORÓWNAWCZE
**Najlepsza opcja**: [Bank] - [dlaczego]
**Główne różnice między bankami**: [tabela porównawcza kluczowych parametrów]
**Czego unikać**: [Bank #4] - [kluczowe powody dyskwalifikacji]
**Rekomendacja końcowa**: [konkretne kroki dla klienta]

KRYTYCZNE ZASADY:
1. Weryfikuj KAŻDY parametr z KAŻDEJ z 8 grup dla KAŻDEGO banku (wszystkie 4)
2. Jeśli parametr nie dotyczy klienta → "N/D" (nie dotyczy)
3. Przy KAŻDYM ❌ MUSISZ dodać notatkę z wyjaśnieniem problemu
4. Cytuj DOKŁADNE wartości z bazy wiedzy (nie interpretuj, nie uogólniaj)
5. Rankinguj banki według: liczby spełnionych wymogów → jakości dopasowania → kosztów
6. Analizuj DOKŁADNIE 4 banki: 3 najlepsze + 1 najgorsza (pokazująca co NIE pasuje)"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"BAZA WIEDZY:\n\n{knowledge_base_context}"},
            {"role": "user", "content": user_query}
        ]
        
        return self.create_chat_completion(messages)
