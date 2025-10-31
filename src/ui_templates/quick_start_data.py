"""
Dane dla ulepszonego Quick Start - 3 tryby wprowadzania danych
"""

# ============================================================================
# TRYB 1: PRZYKŁADOWE ROZMOWY Z KONSULTANTEM
# ============================================================================

CONSULTANT_CONVERSATIONS = {
    "💬 Młode małżeństwo - pierwszy kredyt": """KONSULTANT: Dzień dobry! Chciałbym pomóc Państwu znaleźć najlepszą ofertę kredytu. Czy mogę zadać kilka pytań?

KLIENT: Dzień dobry, oczywiście!

KONSULTANT: Super! Zacznijmy od podstaw. Ile Państwo macie lat?

KLIENT: Ja mam 28 lat, a moja żona 26.

KONSULTANT: Świetnie. Jakie są Państwa źródła dochodu?

KLIENT: Oboje pracujemy na umowę o pracę na czas nieokreślony. Ja pracuję od 3 lat w IT, zarabiam około 10 tysięcy miesięcznie. Żona pracuje w księgowości 2 lata, ma 7 tysięcy.

KONSULTANT: Doskonale, stabilne dochody. Co Państwo planujecie?

KLIENT: Chcemy kupić nasze pierwsze mieszkanie. Znaleźliśmy fajne 60-metrowe M3 na Mokotowie za 850 tysięcy złotych.

KONSULTANT: Super lokalizacja! A jaki mają Państwo wkład własny?

KLIENT: Odłożyliśmy 170 tysięcy, czyli jakieś 20%.

KONSULTANT: Czyli kredyt będzie na 680 tysięcy złotych. Na jaki okres myślicie?

KLIENT: Myśleliśmy o 30 latach, żeby rata nie była za wysoka.

KONSULTANT: Rozumiem. Czy jesteście zainteresowani kredytem EKO? Mieszkanie ma jakieś certyfikaty energetyczne?

KLIENT: Tak! To nowy budynek z 2023 roku, ma certyfikat energetyczny klasy A.

KONSULTANT: Świetnie, to może dać niższe oprocentowanie! Jesteście obywatelami Polski?

KLIENT: Tak, oboje.

KONSULTANT: Czy macie jakieś inne kredyty hipoteczne?

KLIENT: Nie, to nasz pierwszy kredyt na mieszkanie.

KONSULTANT: Doskonale! Dam Państwu chwilę na sprawdzenie ofert...""",

    "💬 Biznesmen budujący dom": """KONSULTANT: Witam! Chciałbym pomóc w znalezieniu kredytu. Opowie mi Pan o swoich planach?

KLIENT: Dzień dobry. Prowadzę firmę od 5 lat i chcę zbudować dom dla rodziny.

KONSULTANT: Rozumiem. Ile ma Pan lat?

KLIENT: 42 lata. Żona ma 40.

KONSULTANT: A jaką formę działalności Pan prowadzi?

KLIENT: Działalność na KPiR, rozliczam się co miesiąc. Średni dochód to około 20 tysięcy netto miesięcznie. Żona pracuje na etacie, ma 8 tysięcy.

KONSULTANT: Doskonale. Opowie Pan o tym domu?

KLIENT: Mamy już działkę, kupiliśmy ją 2 lata temu za 120 tysięcy. Teraz chcemy budować dom systemem zleconym, kosztorys wychodzi na 700 tysięcy złotych.

KONSULTANT: Czyli łączna wartość inwestycji to 820 tysięcy (działka + budowa)?

KLIENT: Dokładnie tak.

KONSULTANT: Jaki macie wkład własny poza działką?

KLIENT: Mamy odłożone 100 tysięcy gotówki. Działka może być wkładem?

KONSULTANT: Tak, w wielu bankach działka liczy się jako wkład! Czyli łącznie 220 tysięcy wkładu (27%). Kredyt będzie na 600 tysięcy. Na jaki okres?

KLIENT: Myśleliśmy o 25 latach.

KONSULTANT: A pozwolenie na budowę macie już?

KLIENT: Tak, otrzymaliśmy w zeszłym miesiącu.

KONSULTANT: Świetnie! Będziecie potrzebować karencji w spłacie kapitału podczas budowy?

KLIENT: Tak, to byłoby bardzo pomocne przez pierwsze 12 miesięcy.

KONSULTANT: Rozumiem. Sprawdzam dla Państwa oferty...""",

    "💬 Senior refinansujący kredyt": """KONSULTANT: Dzień dobry! Jak mogę pomóc?

KLIENT: Dzień dobry. Mamy z żoną kredyt hipoteczny i słyszeliśmy, że teraz oprocentowanie spadło. Chcemy sprawdzić, czy możemy refinansować.

KONSULTANT: Świetny pomysł! Ile Państwo macie lat?

KLIENT: Ja mam 55, żona 52.

KONSULTANT: A jakie Państwo mają źródła dochodu?

KLIENT: Oboje na umowach o pracę na czas nieokreślony, ja pracuję od 25 lat w firmie, mam 12 tysięcy. Żona 18 lat, ma 9 tysięcy.

KONSULTANT: Doskonałe stażę! Jaki jest stan Państwa obecnego kredytu?

KLIENT: Zostało nam do spłaty około 400 tysięcy złotych. Dom jest wart teraz jakieś 800 tysięcy.

KONSULTANT: Czyli LTV to 50% - bardzo dobrze! Kiedy zaciągaliście ten kredyt?

KLIENT: 8 lat temu.

KONSULTANT: Na ile lat był kredyt?

KLIENT: Na 25 lat, więc zostało nam jeszcze 17 lat.

KONSULTANT: Czy chcieliby Państwo skrócić ten okres, czy zostawić te 17 lat?

KLIENT: Wolałbym zostawić, żeby rata nie była za wysoka.

KONSULTANT: Rozumiem. A dom ma jakieś certyfikaty energetyczne? Robiliście termomodernizację?

KLIENT: Tak! W zeszłym roku wymieniliśmy okna i dociepliliśmy. Mamy certyfikat klasy B.

KONSULTANT: Świetnie, możecie kwalifikować się do kredytu EKO z niższym oprocentowaniem! Dam Państwu chwilę na przygotowanie ofert...""",

    "💬 Młody single - lokal użytkowy": """KONSULTANT: Witam! W czym mogę pomóc?

KLIENT: Cześć. Mam 32 lata, prowadzę małą agencję marketingową i chcę kupić lokal pod biuro zamiast wynajmować.

KONSULTANT: Świetna decyzja! Opowiedz o swojej działalności.

KLIENT: Działalność jednoosobowa na KPiR, mam ją 4 lata. Dochody stabilne, średnio 18 tysięcy miesięcznie.

KONSULTANT: Doskonale. A znalazłeś już jakiś lokal?

KLIENT: Tak, 45 metrów w biurowcu w centrum Krakowa. Cena 550 tysięcy.

KONSULTANT: Jaki masz wkład własny?

KLIENT: Mam odłożone 200 tysięcy, czyli jakieś 36%.

KONSULTANT: Super, to niskie LTV! Kredyt będzie na 350 tysięcy. Na ile lat?

KLIENT: Myślałem o 15 latach.

KONSULTANT: A czy lokal ma jakąś część mieszkalną, czy to czysto biurowy?

KLIENT: Tylko biuro, żadnej części mieszkalnej.

KONSULTANT: Rozumiem. Czy planujesz tam tylko swoją działalność, czy może wynajem części powierzchni?

KLIENT: Na razie tylko moja agencja.

KONSULTANT: Jesteś obywatelem Polski?

KLIENT: Tak.

KONSULTANT: Masz jakieś inne kredyty hipoteczne?

KLIENT: Nie, to będzie mój pierwszy.

KONSULTANT: Świetnie! Sprawdzam oferty dla lokali użytkowych...""",

    "💬 Para 50+ - działka pod dom letniskowy": """KONSULTANT: Dzień dobry! Słucham Państwa.

KLIENT (mężczyzna): Dzień dobry. Z żoną chcemy kupić działkę i postawić mały domek letniskowy na Mazurach.

KONSULTANT: Piękne miejsce! Ile Państwo mają lat?

KLIENT: Ja mam 58, żona 56.

KONSULTANT: A jakie mają Państwo źródła dochodu?

KLIENT (żona): Oboje pracujemy, ja na etacie od 30 lat, mąż 25 lat. Razem mamy około 16 tysięcy miesięcznie.

KONSULTANT: Świetnie. Opowiedzcie o tej działce.

KLIENT: Znaleźliśmy 1200 metrów przy jeziorze. Działka kosztuje 180 tysięcy, a domek letniskowy około 220 tysięcy.

KONSULTANT: Czyli łącznie 400 tysięcy inwestycji. Jaki macie wkład własny?

KLIENT (żona): Mamy odłożone 150 tysięcy.

KONSULTANT: Czyli kredyt na 250 tysięcy złotych. Na jaki okres?

KLIENT: Może 15 lat? Chcielibyśmy spłacić przed emeryturą.

KONSULTANT: Rozsądnie! A domek będziecie budować od razu?

KLIENT: Najpierw chcemy kupić działkę, potem w ciągu roku wybudować domek.

KONSULTANT: Rozumiem. To będzie działka rekreacyjna czy może rolna pod zabudowę?

KLIENT (żona): Działka rekreacyjna, ale pozwolenie na budowę małych domków jest tam możliwe.

KONSULTANT: Czy macie już jakiekolwiek pozwolenia?

KLIENT: Jeszcze nie, dopiero po zakupie będziemy składać wnioski.

KONSULTANT: Rozumiem. Sprawdzam dla Państwa oferty na działki rekreacyjne...""",

    "💬 Zakup kamienicy - inwestycja": """KONSULTANT: Witam! Opowie mi Pan o swoich planach inwestycyjnych?

KLIENT: Dzień dobry. Mam 45 lat i chcę kupić kamienicę w centrum Wrocławia jako inwestycję pod wynajem.

KONSULTANT: Ciekawy pomysł! Jakie ma Pan źródło dochodu?

KLIENT: Prowadzę działalność gospodarczą, pełna księgowość, od 8 lat. Roczne dochody to około 400 tysięcy, czyli jakieś 33 tysiące miesięcznie.

KONSULTANT: Świetnie. Opowie Pan o tej kamienicy?

KLIENT: To przedwojenny budynek, 4 lokale mieszkalne + 1 lokal użytkowy. Cena to 2 miliony złotych. 3 lokale są wynajęte, generują około 9 tysięcy miesięcznie.

KONSULTANT: Czyli kamienica częściowo się spłaca! Jaki ma Pan wkład własny?

KLIENT: Mam 600 tysięcy gotówki.

KONSULTANT: Czyli kredyt na 1.4 miliona, LTV 70%. Na jaki okres?

KLIENT: Myślałem o 20 latach.

KONSULTANT: A kamienica wymaga remontu?

KLIENT: Nie, jest w dobrym stanie. Trzeba będzie wymienić piece, ale to niewielki koszt.

KONSULTANT: Czy wszystkie lokale mają osobne księgi wieczyste?

KLIENT: Tak, każdy lokal ma swoją KW.

KONSULTANT: A czy Pan planuje mieszkać w którymś z tych lokali, czy to czysto inwestycyjne?

KLIENT: Czysto inwestycyjne, wszystko pójdzie pod wynajem.

KONSULTANT: Rozumiem. To będzie traktowane jako cel mieszkaniowy czy komercyjny?

KLIENT: Myślę, że cel mieszkaniowy, bo to kamienica z lokalami mieszkalnymi głównie.

KONSULTANT: Ma Pan rację. Sprawdzam dla Pana oferty..."""
}


# ============================================================================
# TRYB 2: GOTOWE STANDARDOWE INPUTY
# ============================================================================

STANDARD_PROFILES = {
    "👨‍👩‍👧‍👦 Młode małżeństwo - pierwszy kredyt (28/26 lat)": """Klient: 28 lat, UoP czas nieokreślony, staż 3 lata, 10000 zł/mc
Współkredytobiorca: 26 lat, UoP czas nieokreślony, staż 2 lata, 7000 zł/mc

CEL: Zakup mieszkania (rynek wtórny)

PARAMETRY:
- Wartość mieszkania: 850,000 zł
- Wkład własny: 170,000 zł (20%)
- Kwota kredytu: 680,000 zł
- LTV: 80%
- Okres: 30 lat

NIERUCHOMOŚĆ:
- Typ: mieszkanie
- Lokalizacja: Warszawa Mokotów
- Powierzchnia: 60 m2

DODATKOWE:
- Status: małżeństwo
- Obywatele Polski
- Kredyt EKO (certyfikat A)
- Pierwszy kredyt hipoteczny""",

    "👴 Senior - refinansowanie (55/52 lata)": """Klient: 55 lat, UoP czas nieokreślony, staż 25 lat, 12000 zł/mc
Współkredytobiorca: 52 lata, UoP czas nieokreślony, staż 18 lat, 9000 zł/mc

CEL: Refinansowanie kredytu hipotecznego

PARAMETRY:
- Wartość domu: 800,000 zł
- Pozostało do spłaty: 400,000 zł
- LTV: 50%
- Okres: 17 lat (zostało z 25-letniego kredytu sprzed 8 lat)
- Kredyt zaciągnięty: 8 lat temu

NIERUCHOMOŚĆ:
- Typ: dom
- Lokalizacja: miasto >100k
- Certyfikat energetyczny: klasa B (termomodernizacja)

DODATKOWE:
- Status: małżeństwo
- Kredyt EKO (po termomodernizacji)""",

    "👨‍💼 Biznesmen - budowa domu (42/40 lat)": """Klient: 42 lata, działalność KPiR, 5 lat, 20000 zł/mc
Współkredytobiorca: 40 lat, UoP czas nieokreślony, 8000 zł/mc

CEL: Budowa domu systemem zleconym

PARAMETRY:
- Koszt budowy: 700,000 zł
- Działka w posiadaniu: 120,000 zł
- Wkład własny (gotówka): 100,000 zł
- Łączny wkład: 220,000 zł (27%)
- Kwota kredytu: 600,000 zł
- Okres: 25 lat

NIERUCHOMOŚĆ:
- Typ: dom (budowa)
- Powierzchnia działki: 1000 m2
- Pozwolenie na budowę: TAK

DODATKOWE:
- Status: małżeństwo
- Działka jako część wkładu
- Karencja kapitałowa: 12 miesięcy""",

    "👔 Single - lokal użytkowy (32 lata)": """Klient: 32 lata, działalność KPiR, 4 lata, 18000 zł/mc

CEL: Zakup lokalu użytkowego (biuro)

PARAMETRY:
- Wartość lokalu: 550,000 zł
- Wkład własny: 200,000 zł (36%)
- Kwota kredytu: 350,000 zł
- LTV: 64%
- Okres: 15 lat

NIERUCHOMOŚĆ:
- Typ: lokal użytkowy
- Lokalizacja: Kraków centrum
- Powierzchnia: 45 m2

DODATKOWE:
- Status: single
- Obywatel Polski
- Pierwszy kredyt""",

    "🏖️ Para 50+ - działka letniskowa (58/56 lat)": """Klient: 58 lat, UoP czas nieokreślony, 25 lat, 9000 zł/mc
Współkredytobiorca: 56 lat, UoP czas nieokreślony, 30 lat, 7000 zł/mc

CEL: Zakup działki rekreacyjnej + budowa domku letniskowego

PARAMETRY:
- Działka: 180,000 zł (1200 m2)
- Domek letniskowy: 220,000 zł
- Łącznie: 400,000 zł
- Wkład własny: 150,000 zł (37.5%)
- Kwota kredytu: 250,000 zł
- Okres: 15 lat

NIERUCHOMOŚĆ:
- Typ: działka rekreacyjna + dom letniskowy
- Lokalizacja: Mazury (przy jeziorze)

DODATKOWE:
- Status: małżeństwo""",

    "🏢 Inwestor - kamienica (45 lat)": """Klient: 45 lat, działalność pełna księgowość, 8 lat, 33000 zł/mc

CEL: Zakup kamienicy (inwestycja)

PARAMETRY:
- Wartość kamienicy: 2,000,000 zł
- Wkład własny: 600,000 zł (30%)
- Kwota kredytu: 1,400,000 zł
- LTV: 70%
- Okres: 20 lat

NIERUCHOMOŚĆ:
- Typ: kamienica
- Lokalizacja: Wrocław centrum
- Składniki: 4 lokale mieszkalne + 1 lokal użytkowy
- Dochód z najmu: 9,000 zł/mc (3 lokale wynajęte)

DODATKOWE:
- Nieruchomość z komercją
- Osobne księgi wieczyste dla każdego lokalu
- Cel mieszkaniowy (głównie lokale mieszkalne)""",

    "🌱 Młody przedsiębiorca - dom ekologiczny (35/33 lata)": """Klient: 35 lat, działalność ryczałt, 3 lata, 15000 zł/mc
Współkredytobiorca: 33 lata, UoP czas nieokreślony, 5 lat, 10000 zł/mc

CEL: Budowa domu energooszczędnego

PARAMETRY:
- Koszt budowy: 800,000 zł
- Działka w posiadaniu: 150,000 zł
- Wkład własny: 200,000 zł
- Łączny wkład: 350,000 zł (37%)
- Kwota kredytu: 600,000 zł
- Okres: 30 lat

NIERUCHOMOŚĆ:
- Typ: dom (budowa) energooszczędny
- Powierzchnia działki: 1500 m2
- Pozwolenie na budowę: TAK
- Standard: pasywny (klasa A+++)

DODATKOWE:
- Status: małżeństwo
- Kredyt EKO (dom pasywny)
- Karencja: 18 miesięcy
- Działka jako część wkładu"""
}


# ============================================================================
# TRYB 3: SZABLONY DLA EDYTORA FORMULARZA
# ============================================================================

FORM_FIELD_TEMPLATES = {
    # OSOBY - wiek
    "age_templates": [
        "28 lat (młody klient)",
        "35 lat (trzydziestolatek)",
        "45 lat (klient w średnim wieku)",
        "55 lat (senior przed emeryturą)",
        "65 lat (emeryt)"
    ],
    
    # TYP DOCHODU
    "income_type_templates": {
        "UoP czas nieokreślony": "Najlepsza opcja - stabilne zatrudnienie",
        "UoP czas określony": "Może wymagać dłuższego stażu",
        "Działalność KPiR": "Księga przychodów i rozchodów",
        "Działalność pełna księgowość": "Dla większych firm",
        "Działalność ryczałt": "Zryczałtowany podatek",
        "Kontrakt menadżerski": "B2B dla kadry zarządzającej",
        "Emerytura": "Stały dochód dla seniorów",
        "Renta": "Dochód rentowy",
        "Umowa zlecenie": "Może wymagać dodatkowych dokumentów"
    },
    
    # STAŻ PRACY
    "employment_duration_templates": [
        "12 miesięcy (minimum dla większości banków)",
        "24 miesiące (dla działalności)",
        "36 miesięcy (standardowy staż)",
        "60 miesięcy (5 lat - bardzo dobry)",
        "120 miesięcy (10 lat - doskonały)"
    ],
    
    # DOCHÓD MIESIĘCZNY
    "income_templates": [
        "5,000 zł (minimalna)",
        "7,000 zł (średnia krajowa)",
        "10,000 zł (dobra)",
        "15,000 zł (bardzo dobra)",
        "20,000+ zł (wysoka)"
    ],
    
    # CEL KREDYTU
    "loan_purpose_templates": {
        "Zakup mieszkania/domu": "Najpopularniejszy cel",
        "Budowa domu gospodarczy": "Budowa we własnym zakresie",
        "Budowa domu zlecony": "Budowa przez firmę budowlaną",
        "Zakup działki budowlanej": "Pod przyszłą zabudowę",
        "Zakup działki rekreacyjnej": "Działka letniskowa",
        "Zakup lokalu użytkowego": "Biuro, lokal handlowy",
        "Zakup kamienicy": "Inwestycja wielorodzinna",
        "Refinansowanie kredytu": "Spłata istniejącego kredytu",
        "Refinansowanie wydatków": "Zwrot kosztów (do 18 mies.)",
        "Konsolidacja niemieszkaniowa": "Spłata innych zobowiązań",
        "Cel dowolny": "Pożyczka hipoteczna"
    },
    
    # WARTOŚĆ / KWOTA
    "property_value_templates": [
        "300,000 zł (małe mieszkanie)",
        "500,000 zł (średnie mieszkanie)",
        "800,000 zł (duże mieszkanie/mały dom)",
        "1,200,000 zł (dom)",
        "2,000,000+ zł (duża nieruchomość)"
    ],
    
    # WKŁAD WŁASNY
    "down_payment_templates": [
        "10% (minimum, wymaga ubezpieczenia)",
        "20% (standard, bez ubezpieczenia niskiego wkładu)",
        "30% (bardzo dobry)",
        "40%+ (doskonały, niższe oprocentowanie)"
    ],
    
    # OKRES
    "loan_period_templates": [
        "10 lat (krótki, wyższa rata)",
        "15 lat (średni)",
        "20 lat (optymalny dla wielu)",
        "25 lat (długi, niższa rata)",
        "30 lat (maksymalny, najniższa rata)"
    ],
    
    # TYP NIERUCHOMOŚCI
    "property_type_templates": {
        "Mieszkanie": "Standardowy lokal mieszkalny",
        "Dom": "Dom jednorodzinny",
        "Działka budowlana": "Pod zabudowę mieszkaniową",
        "Działka rekreacyjna": "Letniskowa, ROD",
        "Lokal użytkowy": "Biuro, sklep, usługi",
        "Kamienica": "Budynek wielorodzinny",
        "Nieruchomość z komercją": "Mieszkanie + lokal użytkowy"
    },
    
    # LOKALIZACJA
    "location_templates": [
        "Warszawa (duże miasto)",
        "Kraków (duże miasto)",
        "Wrocław (duże miasto)",
        "Poznań (duże miasto)",
        "Miasto >100k mieszkańców",
        "Miasto średnie (50-100k)",
        "Małe miasto / wieś"
    ]
}
