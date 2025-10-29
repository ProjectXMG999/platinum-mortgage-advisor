# System Dwupromptowy - Wizualizacja

## 🎯 Architektura przepływu

```
                    ┌─────────────────────────────────────────┐
                    │      PROFIL KLIENTA (INPUT)            │
                    │  • Wiek: 45 lat                        │
                    │  • Dochód: UoP czas nieokreślony, 5 lat│
                    │  • Cel: Zakup mieszkania               │
                    │  • Kwota: 640,000 zł                   │
                    │  • LTV: 80%, wkład 20%                 │
                    └──────────────────┬──────────────────────┘
                                       │
                                       ▼
        ┌───────────────────────────────────────────────────────────┐
        │        ETAP 1: WALIDACJA WYMOGÓW (Pre-screening)         │
        │                                                           │
        │  📋 Prompt 1: "Sprawdź 68 WYMOGÓW dla każdego banku"     │
        │  📊 Input: knowledge_base.json + classification_v2.json  │
        │  🎯 Cel: Eliminacja banków niedopasowanych               │
        │                                                           │
        │  ┌─────────────────────────────────────────────────┐    │
        │  │ Weryfikacja dla każdego z 11 banków:            │    │
        │  │                                                  │    │
        │  │ ✅ ALIOR BANK                                    │    │
        │  │    • Wiek: ✅ 18-80 (klient: 45)                │    │
        │  │    • Staż UoP: ✅ min 3mc (klient: 5 lat)       │    │
        │  │    • Cel zakup: ✅ Akceptowany                  │    │
        │  │    • LTV: ✅ 90% max (klient: 80%)              │    │
        │  │    → Status: KWALIFIKUJE_SIĘ (68/68 wymogów)    │    │
        │  │                                                  │    │
        │  │ ✅ PKO BP                                        │    │
        │  │    → Status: KWALIFIKUJE_SIĘ (68/68)            │    │
        │  │                                                  │    │
        │  │ ✅ ING                                           │    │
        │  │    → Status: KWALIFIKUJE_SIĘ (68/68)            │    │
        │  │                                                  │    │
        │  │ ❌ VELO BANK                                     │    │
        │  │    • Wiek: ❌ Max 65 lat (klient: 45) ✅        │    │
        │  │    • Cudzoziemiec: ❌ Brak oferty dla obcokraj. │    │
        │  │    → Status: NIE_KWALIFIKUJE (2 krytyczne)      │    │
        │  │                                                  │    │
        │  │ ❌ CITI HANDLOWY                                 │    │
        │  │    • Cel: ❌ Nie finansuje budowy               │    │
        │  │    → Status: NIE_KWALIFIKUJE (1 krytyczny)      │    │
        │  └─────────────────────────────────────────────────┘    │
        │                                                           │
        │  📤 Output JSON:                                         │
        │     {                                                     │
        │       "qualified_banks": [                               │
        │         "Alior Bank", "PKO BP", "ING",                   │
        │         "Millennium", "mBank", "Santander"               │
        │       ],                                                  │
        │       "disqualified_banks": [                            │
        │         "VELO BANK", "CITI", "BNP", "Pekao", "BOŚ"      │
        │       ],                                                  │
        │       "qualified_count": 6                               │
        │     }                                                     │
        └──────────────────────┬────────────────────────────────────┘
                               │
                               ▼
        ┌───────────────────────────────────────────────────────────┐
        │         ETAP 2: RANKING JAKOŚCI (Scoring)                │
        │                                                           │
        │  📋 Prompt 2: "Oceń 19 parametrów JAKOŚĆ (0-100 pkt)"    │
        │  📊 Input: Tylko 6 zakwalifikowanych banków              │
        │  🎯 Cel: Ranking TOP 4 (3 najlepsze + 1 najgorszy)       │
        │                                                           │
        │  ┌─────────────────────────────────────────────────┐    │
        │  │ Punktacja dla 6 banków:                         │    │
        │  │                                                  │    │
        │  │ 🏆 ALIOR BANK: 87/100 pkt                       │    │
        │  │    • Koszt kredytu: 32/35 pkt                   │    │
        │  │      - Wcześniejsza spłata 0%: 10/10 ✅         │    │
        │  │      - Ubezp. pomostowe brak: 8/8 ✅            │    │
        │  │      - Koszt operatu 400zł: 5/5 ✅              │    │
        │  │    • Elastyczność: 23/25 pkt                    │    │
        │  │      - Okres 420mc: 7/7 ✅                      │    │
        │  │      - Karencja 60mc: 5/5 ✅                    │    │
        │  │    • Wygoda: 18/20 pkt                          │    │
        │  │    • Korzyści: 12/15 pkt                        │    │
        │  │    • Parametry max: 4/5 pkt                     │    │
        │  │                                                  │    │
        │  │ 🥈 PKO BP: 83/100 pkt                           │    │
        │  │    • Koszt kredytu: 30/35 pkt                   │    │
        │  │    • Elastyczność: 25/25 pkt ⭐ MAX              │    │
        │  │    • Wygoda: 15/20 pkt                          │    │
        │  │    • Różnica vs #1: -4 pkt (gorszy koszt)       │    │
        │  │                                                  │    │
        │  │ 🥉 ING: 81/100 pkt                              │    │
        │  │    • Kredyt EKO: bonus +5 pkt ⭐                │    │
        │  │    • Różnica vs #1: -6 pkt                      │    │
        │  │                                                  │    │
        │  │ 🥉 MILLENNIUM: 78/100 pkt                       │    │
        │  │                                                  │    │
        │  │ ⚙️ mBANK: 74/100 pkt                            │    │
        │  │                                                  │    │
        │  │ ⚠️ SANTANDER: 65/100 pkt - NAJGORSZY            │    │
        │  │    • Koszt kredytu: 22/35 pkt ⚠️ (-13 vs #1)    │    │
        │  │      - Wcześniejsza spłata 2%: 4/10 ❌          │    │
        │  │      - Ubezp. pomostowe +1%: 2/8 ❌             │    │
        │  │    • Operat zewnętrzny: 3/10 ❌                 │    │
        │  │    • Dlaczego najgorszy: Wysokie koszty +       │    │
        │  │      brak elastyczności                         │    │
        │  └─────────────────────────────────────────────────┘    │
        │                                                           │
        │  📤 Output Markdown:                                     │
        │     - Szczegółowa analiza TOP 4                          │
        │     - Tabela porównawcza wszystkich parametrów           │
        │     - Uzasadnienie każdej oceny punktowej                │
        │     - Rekomendacja końcowa                               │
        └──────────────────────┬────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────────────────────────┐
                    │    RAPORT KOŃCOWY DLA KLIENTA          │
                    │                                         │
                    │  🏆 NAJLEPSZA: Alior Bank (87 pkt)     │
                    │     • Brak opłat za wcześniejszą spłatę│
                    │     • Najdłuższy okres (420 mc)        │
                    │     • Karencja do 60 miesięcy          │
                    │                                         │
                    │  🥈 DRUGA: PKO BP (83 pkt)             │
                    │     • Maksymalna elastyczność          │
                    │     • Duża kwota kredytu               │
                    │                                         │
                    │  🥉 TRZECIA: ING (81 pkt)              │
                    │     • Kredyt EKO (obniżka marży)       │
                    │     • Operat wewnętrzny                │
                    │                                         │
                    │  ⚠️ CZEGO UNIKAĆ: Santander (65 pkt)   │
                    │     • Opłata 2% za wcześniejszą spłatę │
                    │     • Wysokie ubezpieczenie pomostowe  │
                    │                                         │
                    │  💡 REKOMENDACJA:                      │
                    │     Wybierz Alior Bank - oszczędzisz   │
                    │     ~15,000 zł vs Santander            │
                    └─────────────────────────────────────────┘
```

---

## 📊 Porównanie: Stary vs Nowy System

### Stary system (1 prompt)

```
PROFIL → [PROMPT JEDYNY] → RANKING TOP 4
           ↓
    Analizuje wszystkie 87 parametrów
    jednocześnie dla wszystkich 11 banków
    
    ❌ Problemy:
    • Miesza WYMOGI z JAKOŚCIĄ
    • Brak transparentności eliminacji
    • Trudno zrozumieć dlaczego bank #4 jest gorszy
    • Długi czas analizy (11 banków × 87 param)
```

### Nowy system (2 prompty)

```
PROFIL → [PROMPT 1: WYMOGI] → [PROMPT 2: JAKOŚĆ] → RANKING TOP 4
           ↓                      ↓
    Eliminuje niedopasowane    Rankuje dopasowane
    (68 wymogów, 11 banków)    (19 jakości, 6 banków)
    
    ✅ Korzyści:
    • Rozdziela kwalifikację od optymalizacji
    • Jasne powody eliminacji (JSON)
    • Precyzyjna punktacja (0-100)
    • Szybsze (mniej banków w etapie 2)
    • Audytowalne (każdy krok udokumentowany)
```

---

## 🔍 Przykład analizy krok po kroku

### Wejście: Profil seniora

```
Klient: 68 lat, emeryt
Cel: Zakup działki rekreacyjnej 1,500 m2
Kwota: 100,000 zł
Wkład: 50,000 zł (50%)
```

### ETAP 1: Walidacja WYMOGÓW

```
┌─────────────────────────────────────────────────────────────────┐
│ Bank 1: ALIOR                                                   │
│  ✅ Wiek: 18-80 (klient: 68) → OK                              │
│  ❌ CEL: Nie finansuje działek rekreacyjnych → DYSKWALIFIKACJA │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Bank 2: PKO BP                                                  │
│  ✅ Wiek: 18-80 (klient: 68) → OK                              │
│  ❌ CEL: Nie finansuje działek rekreacyjnych → DYSKWALIFIKACJA │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Bank 3: BOŚ BANK                                                │
│  ✅ Wiek: 18-75 (klient: 68) → OK                              │
│  ✅ CEL: TAK, finansuje działki rekreacyjne (LTV 60%)          │
│  ✅ DOCHÓD: Emerytura akceptowana                              │
│  ✅ LTV: Klient 50% < Bank 60% → OK                            │
│  → Status: KWALIFIKUJE_SIĘ (68/68) ✅                           │
└─────────────────────────────────────────────────────────────────┘

Wynik: Tylko 1 bank (BOŚ) → Brak możliwości rankingu
```

### ETAP 2: Pominięty

```
System: "Tylko 1 bank spełnia wymogi - BOŚ Bank.
        Nie można stworzyć rankingu TOP 4.
        
        Rekomendacja: BOŚ Bank (jedyna opcja)
        LTV: 60% max, klient ma 50% → Zaakceptowany
        Oprocentowanie: Według tabeli BOŚ dla działek"
```

---

## 🎨 Legenda symboli

| Symbol | Znaczenie |
|--------|-----------|
| ✅ | Wymóg spełniony / Pozytywna ocena |
| ❌ | Wymóg niespełniony / Dyskwalifikacja |
| ⚠️ | Warunkowo / Najgorsza opcja (dla kontrastu) |
| 🏆 | #1 - Najlepsza opcja |
| 🥈 | #2 - Druga opcja |
| 🥉 | #3 - Trzecia opcja |
| N/D | Nie dotyczy klienta |
| ⭐ | Wyjątkowa korzyść / Maksymalna punktacja |

---

**Autor**: System Dwupromptowy Platinum Financial  
**Wersja**: 1.0  
**Data**: 2025-01-27
