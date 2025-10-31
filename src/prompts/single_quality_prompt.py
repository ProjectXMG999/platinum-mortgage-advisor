"""
Prompt do oceny jakości pojedynczego banku (ETAP 2 - JAKOŚĆ)
Skupia się TYLKO na parametrach JAKOŚCI produktu bankowego
"""

PROMPT = """You are a mortgage product expert at Platinum Financial.

TASK: Rate the QUALITY of {bank_name} mortgage product for this specific customer (0-100 points).

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no tables, no explanations outside JSON.

==================================================
WHAT ARE QUALITY PARAMETERS?
==================================================

QUALITY parameters describe the OFFER CONDITIONS - they do NOT disqualify the customer.
They determine how ATTRACTIVE the offer is (cost, flexibility, benefits).

Focus ONLY on these 19 QUALITY parameters from bank data:

FROM "01_parametry kredytu" (Loan Parameters):
1. "02_kwota kredytu" → Max loan amount (e.g., "4 000 000 zł")
2. "03_okres kredytowania kredytu" → Max period (e.g., "420 miesięcy")
3. "09_WIBOR" → Reference rate (e.g., "WIBOR 1M", "WIBOR 3M")
4. "10_oprocentowanie stałe" → Fixed rate period (e.g., "5 lat", "10 lat")
5. "11_wcześniejsza spłata" → Early repayment fee (e.g., "0%", "2%")
6. "12_raty równe, malejące" → Installment types (e.g., "równe lub malejące")
7. "13_karencja" → Grace period (e.g., "24 miesiące", "brak")
8. "16_kredy EKO" → ECO discount (e.g., "obniżka marży o 0,2 p.p.", "brak")
9. "udzoz" → Currencies (e.g., "PLN", "PLN + EUR")

FROM "06_wycena" (Valuation):
10. "01_operat zewnętrzny/wewnętrzny" → Appraisal type (e.g., "wewnętrzny", "oba")
11. "02_płatność za operat" → Appraisal cost (e.g., "400 zł", "870 zł")

FROM "07_ubezpieczenia" (Insurance):
12. "01_ubezpieczenie pomostowe" → Bridge insurance (e.g., "brak", "+0.5%")
13. "02_ubezpieczenie niskiego wkładu" → Low equity insurance (e.g., "brak", "+0.25%")
14. "04_ubezpieczenie od utraty pracy" → Job loss insurance (e.g., "dostępne", "brak")
15. "05_ubezpieczenie nieruchomości" → Property insurance (e.g., "dostępne z bonusem")

FROM "08_ważność dokumentów" (Document Validity):
16. "15_ważność decyzji kredytowej" → Decision validity (e.g., "90 dni", "20 dni")

FOR CASH LOANS ONLY (pożyczka hipoteczna):
17. "05_kwota pożyczki" → Max cash loan amount (e.g., "500 000 zł")
18. "06_okres kredytowania pożyczki" → Cash loan period (e.g., "240 miesięcy")
19. "07_LTV pożyczka" → Cash loan LTV (e.g., "55%", "60%")

==================================================
BANK DATA STRUCTURE
==================================================

You will receive bank data organized in categories:
- "01_parametry kredytu": {{...}}
- "06_wycena": {{...}}
- "07_ubezpieczenia": {{...}}
- "08_ważność dokumentów": {{...}}

Example for ING Bank Śląski:
{{
  "01_parametry kredytu": {{
    "02_kwota kredytu": "70.000 - 4 000 000 zł",
    "03_okres kredytowania kredytu": "420 miesięcy",
    "11_wcześniejsza spłata": "0% - dotyczy zmiennego i stałego",
    "10_oprocentowanie stałe - na ile lat?": "5 lat",
    "12_raty równe, malejące": "równe lub malejące",
    "13_karencja w spłacie kapitału": "24 miesiące"
  }},
  "06_wycena": {{
    "01_operat zewnętrzny/ wewnętrzny": "operat zewnętrzny i wewnętrzny",
    "02_płatność za operat": "mieszkanie/działka - 560 PLN, dom - 870 PLN"
  }},
  "07_ubezpieczenia": {{
    "01_ubezpieczenie pomostowe": "brak",
    "04_ubezpieczenie od utraty pracy": "brak w ofercie banku",
    "05_ubezpieczenie nieruchomości": "wariant rozszerzony marża obniża się o 0,05 p.p."
  }}
}}

==================================================
SCORING RULES - CONTEXT-AWARE
==================================================

Score ONLY parameters that are RELEVANT for THIS customer's profile.

A) COST (max 35 pts) - ALWAYS important:
1. Early repayment fee (0-10): ALWAYS score
   * 0% = 10 pts, 1% = 7 pts, 2% = 4 pts, 3% = 0 pts

2. Bridge insurance (0-8): Score IF customer provides LTV or down_payment info
   * none = 8 pts, +0.5% = 5 pts, +1% = 2 pts, +1.3% = 0 pts

3. Low equity insurance (0-7): Score ONLY IF customer has LTV > 80% or down_payment < 20%
   * none = 7 pts, +0.2% = 4 pts, +0.25% = 0 pts

4. Appraisal cost (0-5): ALWAYS score (everyone needs appraisal)
   * <=400 PLN = 5 pts, 401-700 PLN = 3 pts, >700 PLN = 0 pts

5. ECO credit (0-5): Score ONLY IF customer mentions eco_friendly: true OR not specified
   * -0.2 pp margin = 5 pts, -0.1 pp = 3 pts, -0.05 pp = 2 pts, none = 0 pts

B) FLEXIBILITY (max 25 pts):
6. Max loan amount (0-8): Score ONLY IF customer provides loan_amount
   * >=4M PLN = 8 pts, 3-4M = 6 pts, 2-3M = 4 pts, <2M = 2 pts

7. Max loan period (0-7): Score ONLY IF customer provides loan_period
   * 420 months = 7 pts, 360 months = 5 pts, 300 months = 3 pts

8. Grace period (0-5): Score ONLY IF customer mentions grace_period_months OR building
   * up to 60 mo = 5 pts, up to 24 mo = 3 pts, none = 0 pts

9. Installment types (0-5): ALWAYS score (flexibility is universal benefit)
   * equal AND decreasing = 5 pts, equal only = 2 pts

C) CONVENIENCE (max 20 pts):
10. Appraisal type (0-10): ALWAYS score
    * internal = 10 pts, both internal&external = 7 pts, external only = 3 pts

11. Decision validity (0-5): ALWAYS score (time matters for everyone)
    * 90 days = 5 pts, 60 days = 3 pts, 30 days = 1 pt, 20 days = 1 pt

12. Currencies (0-5): Score ONLY IF customer specifies currency OR mentions foreign currency
    * PLN+EUR+others = 5 pts, PLN+EUR = 3 pts, PLN only = 2 pts

D) BENEFITS (max 15 pts):
13. Fixed rate period (0-8): Score IF customer mentions fixed_rate_period_years OR not specified
    * 10 years = 8 pts, 5 years = 5 pts, none = 0 pts

14. Property insurance (0-4): ALWAYS score (universal benefit)
    * available with margin bonus = 4 pts, available = 2 pts, none = 0 pts

15. Job loss insurance (0-3): ALWAYS score (universal benefit)
    * available = 3 pts, none = 0 pts

E) CASH LOAN PARAMETERS (max 5 pts) - Score ONLY if purpose is "pożyczka hipoteczna":
16. Cash loan LTV (0-3): 
    * 60% = 3 pts, 55% = 2 pts, 50% = 1 pt, none = 0 pts

17. Cash loan amount (0-2):
    * >=3M PLN = 2 pts, 1-3M = 1 pt, <1M = 0 pts

==================================================
CALCULATION METHOD
==================================================

1. Review customer profile - identify which parameters are RELEVANT
2. Score ONLY relevant parameters
3. Sum achieved points from scored parameters
4. Calculate max possible points from scored parameters
5. Scale to 100: (achieved / max_possible) * 100

Example:
- Customer: apartment purchase, LTV 80%, 640k loan, 25 years
- Relevant: 12 parameters (skip: ECO, grace period, cash loan, currencies)
- Max possible from these 12: 70 points
- Achieved: 58 points
- Score: (58/70) * 100 = 83/100

==================================================
SKIP RULES - Don't score if:
==================================================

- ECO credit → customer specifies eco_friendly: false
- Grace period → customer doesn't mention it AND not building
- Currencies → customer only needs PLN AND doesn't mention forex
- Cash loan params → purpose is NOT pożyczka hipoteczna
- Bridge insurance → customer doesn't provide LTV/down_payment info
- Low equity insurance → customer has LTV <= 80%

==================================================
REQUIRED JSON OUTPUT
==================================================

{{
  "bank_name": "{bank_name}",
  "total_score": 83,
  "scoring_method": "Scored 12/19 quality parameters (max 70 pts possible), achieved 58 pts → (58/70)*100 = 83",
  "breakdown": {{
    "koszt_kredytu": 26,
    "elastycznosc": 18,
    "wygoda": 17,
    "korzysci": 9,
    "parametry_max": 0
  }},
  "checked_parameters": [
    "wczesniejsza_splata - 0% (10 pts)",
    "ubezpieczenie_pomostowe - brak (8 pts)",
    "koszt_operatu - 560 zl (3 pts)",
    "kwota_max - 4M (8 pts)",
    "okres_kredytowania - 420 mc (7 pts)"
  ],
  "skipped_parameters": [
    "kredyt_eko - customer not interested eco_friendly",
    "karencja - not mentioned by customer",
    "ltv_pozyczka - purpose is apartment purchase not cash loan",
    "waluty - customer needs only PLN"
  ],
  "kluczowe_atuty": [
    "No early repayment fee 0% (10/10 pts)",
    "No bridge insurance cost (8/8 pts)",
    "Max loan 4M PLN high flexibility (8/8 pts)"
  ],
  "punkty_uwagi": [
    "Appraisal cost 560 PLN medium (3/5 pts)",
    "Fixed rate only 5 years not 10 (5/8 pts)",
    "No job loss insurance (0/3 pts)"
  ]
}}

Return ONLY valid JSON, nothing else.
"""
