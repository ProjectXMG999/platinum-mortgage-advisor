"""
Aplikacja Streamlit - Wyszukiwarka kredytów hipotecznych Platinum Financial
Integracja z systemem dwupromptowym (AI)
"""
import streamlit as st

# Konfiguracja strony - MUSI BYĆ PIERWSZĄ KOMENDĄ STREAMLIT
st.set_page_config(
    page_title="Wyszukiwarka kredytów hipotecznych - Platinum Financial", 
    page_icon="platinum.png",
    layout="wide"
)

import json
import sys
import os
import asyncio

# Dodaj src do ścieżki (kompatybilność z lokalnym i Streamlit Cloud)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import z pełną ścieżką dla pewności
try:
    from query_engine import QueryEngine
    from input_mapper import InputMapper
    from models.customer_profile import CUSTOMER_PROFILE_TEMPLATE
except ImportError:
    from src.query_engine import QueryEngine
    from src.input_mapper import InputMapper
    from src.models.customer_profile import CUSTOMER_PROFILE_TEMPLATE

# Lista banków
banks = [
    "Alior Bank",
    "BNP Paribas",
    "CITI Handlowy",
    "ING Bank Śląski",
    "mBank",
    "Millennium",
    "Pekao SA",
    "PKO BP",
    "Santander",
    "BOŚ BANK",
    "VELO BANK"
]

# Loga banków
bank_logos = {
    "Alior Bank": "banks/Alior Bank-azwdue.png",
    "BNP Paribas": "banks/BNP_Paribas-pp9vtd.png",
    "CITI Handlowy": "banks/CITI-vcqq6w.png",
    "ING Bank Śląski": "banks/ING-uo91sp.png",
    "mBank": "banks/mBank-8y80zh.png",
    "Millennium": "banks/millennium-2oevpq.png",
    "Pekao SA": "banks/Pekao-znylvm.png",
    "PKO BP": "banks/PKO BP-kmc274.png",
    "Santander": "banks/Santander-evlk48.png",
    "BOŚ BANK": "banks/BOŚ-voctnt.jpg",
    "VELO BANK": "banks/velo-aiuy6v.png",
}

# Inicjalizacja session state
if 'engine' not in st.session_state:
    with st.spinner('Inicjalizacja systemu AI...'):
        try:
            st.session_state.engine = QueryEngine("data/processed/knowledge_base.json")
            st.session_state.input_mapper = InputMapper(st.session_state.engine.ai_client)
            st.session_state.engine_ready = True
        except Exception as e:
            st.session_state.engine_ready = False
            st.session_state.engine_error = str(e)

if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
    
if 'ranking_result' not in st.session_state:
    st.session_state.ranking_result = None

if 'qualified_banks' not in st.session_state:
    st.session_state.qualified_banks = []
    
if 'disqualified_banks' not in st.session_state:
    st.session_state.disqualified_banks = []

if 'customer_profile' not in st.session_state:
    st.session_state.customer_profile = None

if 'mapped_profile_json' not in st.session_state:
    st.session_state.mapped_profile_json = None


def parse_validation_json(json_text):
    """Parsuje JSON z etapu 1 (walidacja)"""
    try:
        # Usuń markdown code blocks
        json_clean = json_text.strip()
        if json_clean.startswith("```json"):
            json_clean = json_clean[7:]
        if json_clean.startswith("```"):
            json_clean = json_clean[3:]
        if json_clean.endswith("```"):
            json_clean = json_clean[:-3]
        
        json_clean = json_clean.strip()
        
        # Próba 1: Standardowe parsowanie
        try:
            return json.loads(json_clean)
        except json.JSONDecodeError as e:
            # Próba 2: Znajdź JSON object w tekście
            import re
            json_match = re.search(r'\{.*\}', json_clean, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise e
            
    except Exception as e:
        st.error(f"⚠️ Błąd parsowania JSON z etapu 1: {e}")
        with st.expander("🔍 Zobacz surową odpowiedź AI"):
            st.code(json_text[:2000], language="json")  # Pokaż pierwsze 2000 znaków
        return None


def extract_bank_score(ranking_text, bank_name):
    """Wyciąga punktację banku z tekstu rankingu"""
    try:
        import re
        
        # Różne wzorce do znalezienia punktacji
        patterns = [
            # "OFERTA #1: ING Bank - 91/100 punktów"
            rf"OFERTA.*?{re.escape(bank_name)}.*?(\d+)/100",
            # "ING Bank Śląski - **91/100 punktów**"
            rf"{re.escape(bank_name)}.*?[:\-].*?(\d+)/100",
            # "**OCENA JAKOŚCI: **91/100 punktów**" (po nazwie banku)
            rf"{re.escape(bank_name)}.*?OCENA JAKOŚCI.*?(\d+)/100",
            # "91/100 punktów" gdziekolwiek po nazwie banku (w ciągu 500 znaków)
            rf"(?s){re.escape(bank_name)}.{{0,500}}?(\d+)/100",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, ranking_text, re.IGNORECASE | re.DOTALL)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:  # Walidacja zakresu
                    return score
        
        # Jeśli nie znaleziono, szukaj sekcji banku i pierwszej punktacji w niej
        # Znajdź sekcję danego banku (np. "## 🥇 OFERTA #1: ING Bank")
        bank_section_pattern = rf"##.*?{re.escape(bank_name)}(.*?)(?=##|$)"
        bank_section = re.search(bank_section_pattern, ranking_text, re.DOTALL | re.IGNORECASE)
        
        if bank_section:
            section_text = bank_section.group(1)
            # Znajdź pierwszą punktację w tej sekcji
            score_match = re.search(r'(\d+)/100', section_text)
            if score_match:
                score = int(score_match.group(1))
                if 0 <= score <= 100:
                    return score
    except Exception as e:
        print(f"Błąd extract_bank_score dla {bank_name}: {e}")
    
    return None


def extract_category_scores(ranking_text, bank_name):
    """Wyciąga breakdown punktacji według kategorii"""
    try:
        import re
        
        # Znajdź sekcję danego banku
        bank_section_pattern = rf"##.*?{re.escape(bank_name)}(.*?)(?=##|$)"
        bank_section = re.search(bank_section_pattern, ranking_text, re.DOTALL | re.IGNORECASE)
        
        if bank_section:
            section = bank_section.group(1)
            
            # Szukaj sekcji "Rozbicie punktacji"
            breakdown_pattern = r"### 📊 Rozbicie punktacji:(.*?)(?=###|$)"
            breakdown_match = re.search(breakdown_pattern, section, re.DOTALL | re.IGNORECASE)
            
            if breakdown_match:
                breakdown_text = breakdown_match.group(1)
                
                # Wyciągnij wszystkie linie typu "- kategoria: X pkt"
                scores = {}
                for line in breakdown_text.split('\n'):
                    # Zmieniony regex - dopasuj również podkreślniki i inne znaki
                    match = re.search(r'-\s*([\w_]+):\s*(\d+)\s*pkt', line)
                    if match:
                        category = match.group(1)
                        score = int(match.group(2))
                        scores[category] = score
                
                if scores:
                    return scores
    except Exception as e:
        print(f"Błąd extract_category_scores dla {bank_name}: {e}")
    
    return {}


def extract_top_reasons(ranking_text, bank_name):
    """Wyciąga główne atuty banku z tekstu rankingu"""
    try:
        import re
        
        # Znajdź sekcję danego banku
        bank_section_pattern = rf"##.*?{re.escape(bank_name)}(.*?)(?=##|$)"
        bank_section = re.search(bank_section_pattern, ranking_text, re.DOTALL | re.IGNORECASE)
        
        if bank_section:
            section = bank_section.group(1)
            
            # Wzorce do znalezienia atutów
            atuty_patterns = [
                r"### ✨ KLUCZOWE ATUTY:(.*?)(?=###|$)",
                r"KLUCZOWE ATUTY:(.*?)(?=###|$)",
                r"Główne atuty:(.*?)(?=###|$)",
                r"Zalety:(.*?)(?=###|$)",
            ]
            
            for pattern in atuty_patterns:
                atuty_match = re.search(pattern, section, re.DOTALL | re.IGNORECASE)
                if atuty_match:
                    atuty_text = atuty_match.group(1)
                    
                    # Wyciągnij listę punktowaną (różne formaty)
                    reasons = []
                    
                    # Format: "1. Tekst"
                    numbered = re.findall(r'(?:^|\n)\s*\d+\.\s*([^\n]+)', atuty_text)
                    if numbered:
                        reasons.extend(numbered)
                    
                    # Format: "- Tekst" lub "* Tekst"
                    if not reasons:
                        bulleted = re.findall(r'(?:^|\n)\s*[-*]\s*([^\n]+)', atuty_text)
                        if bulleted:
                            reasons.extend(bulleted)
                    
                    # Format: "✓ Tekst"
                    if not reasons:
                        checkmarks = re.findall(r'(?:^|\n)\s*[✓✔]\s*([^\n]+)', atuty_text)
                        if checkmarks:
                            reasons.extend(checkmarks)
                    
                    if reasons:
                        return [r.strip() for r in reasons[:3]]  # Max 3 atuty
            
            # Fallback: weź pierwsze 3 linie z punktami z całej sekcji
            all_points = re.findall(r'(?:^|\n)\s*[-*•]\s*([^\n]+)', section)
            if all_points:
                return [p.strip() for p in all_points[:3]]
        
    except Exception as e:
        print(f"Błąd extract_top_reasons dla {bank_name}: {e}")
    
    return ["Zobacz pełny raport poniżej"]

# Logo i tytuł
st.logo("platinum.png")
st.markdown("# 🏦 Wyszukiwarka Kredytów Hipotecznych")
st.markdown("### *System dwupromptowy z AI - precyzyjna analiza 11 banków*")

# Sprawdź czy silnik gotowy
if not st.session_state.engine_ready:
    st.error(f"❌ Błąd inicjalizacji systemu: {st.session_state.get('engine_error', 'Nieznany błąd')}")
    st.info("Upewnij się, że plik `data/processed/knowledge_base.json` istnieje i jest poprawny.")
    st.stop()

# Główny layout - 3 kolumny
col1, col2, col3 = st.columns([2, 3, 3])

with col1:
    st.markdown("### 📝 Profil Klienta")
    
    # Import danych Quick Start
    try:
        from ui_templates.quick_start_data import (
            CONSULTANT_CONVERSATIONS,
            STANDARD_PROFILES,
            FORM_FIELD_TEMPLATES
        )
    except ImportError:
        from src.ui_templates.quick_start_data import (
            CONSULTANT_CONVERSATIONS,
            STANDARD_PROFILES,
            FORM_FIELD_TEMPLATES
        )
    
    # Przycisk pomocy - szablon
    with st.expander("📖 **PRZEWODNIK: Jakie dane mogę podać?**", expanded=False):
        st.markdown("""
        ### ⚠️ **WYMAGANE MINIMUM:**
        1. **Wiek** kredytobiorcy (np. 45 lat)
        2. **Typ dochodu** (np. UoP, działalność, emerytura)
        3. **Staż pracy** (np. 5 lat)
        4. **Cel kredytu** (np. zakup mieszkania)
        5. **Wartość nieruchomości** lub **kwota kredytu**
        
        ### 💡 **OPCJONALNE (podaj jeśli dotyczy):**
        
        **👤 Dane osobowe:**
        - Wiek współkredytobiorcy
        - Obywatelstwo (cudzoziemiec?)
        - Status związku (małżeństwo, konkubinat)
        
        **💰 Dochody:**
        - Wysokość dochodu miesięcznego
        - Dodatkowe źródła dochodu
        - Typ umowy współkredytobiorcy
        
        **💳 Parametry kredytu:**
        - Wkład własny (kwota lub %)
        - LTV
        - Okres kredytowania (lata/miesiące)
        - Waluta (PLN/EUR)
        - Karencja
        - Kredyt EKO
        - Liczba istniejących kredytów
        
        **🏡 Nieruchomość:**
        - Typ (mieszkanie/dom/działka)
        - Lokalizacja
        - Powierzchnia
        - Powierzchnia działki
        - Transakcja rodzinna?
        - Zabezpieczenie osoby trzeciej?
        
        ### 📝 **Przykłady typów dochodu:**
        - Umowa o pracę (określona/nieokreślona)
        - Działalność gospodarcza (KPiR/pełna/ryczałt)
        - Emerytura / Renta
        - Kontrakt menadżerski
        - Umowa zlecenie / o dzieło
        - Dochody z najmu
        
        ### 🎯 **Przykłady celów:**
        - Zakup mieszkania/domu
        - Budowa domu (gospodarczy/zlecony)
        - Zakup działki (budowlana/rolna/rekreacyjna)
        - Refinansowanie
        - Konsolidacja
        - Cel dowolny (pożyczka hipoteczna)
        """)
    
    # ========================================================================
    # 3-TRYBY QUICK START
    # ========================================================================
    st.markdown("#### 🚀 Szybki Start")
    
    quick_start_mode = st.radio(
        "Wybierz sposób wprowadzania danych:",
        options=[
            "💬 Rozmowy konsultant-klient",
            "📋 Gotowe przykłady",
            "✏️ Edytor formularza"
        ],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    user_description = ""  # Zmienna przechowująca ostateczny input
    
    # ------------------------------------------------------------------------
    # TRYB 1: ROZMOWY KONSULTANT-KLIENT
    # ------------------------------------------------------------------------
    if quick_start_mode == "💬 Rozmowy konsultant-klient":
        st.markdown("##### 💬 Przykładowe rozmowy z konsultantem")
        st.caption("Zobacz naturalne dialogi i zrozum, jak wypełniać dane")
        
        conversation_options = ["Wybierz rozmowę..."] + list(CONSULTANT_CONVERSATIONS.keys())
        selected_conversation = st.selectbox(
            "Wybierz scenariusz:",
            options=conversation_options,
            key="conversation_select"
        )
        
        if selected_conversation != "Wybierz rozmowę...":
            user_description = st.text_area(
                "Rozmowa konsultanta z klientem:",
                value=CONSULTANT_CONVERSATIONS[selected_conversation],
                height=450,
                key="conversation_text",
                help="To przykładowa rozmowa - możesz ją edytować lub użyć jako wzór"
            )
        else:
            user_description = st.text_area(
                "Wpisz swoją rozmowę lub wybierz przykład powyżej:",
                value="",
                height=450,
                key="conversation_text_empty",
                placeholder="""KONSULTANT: Dzień dobry! Ile ma Pan lat?
KLIENT: 35 lat.
KONSULTANT: Jakie ma Pan źródło dochodu?
KLIENT: Pracuję na umowę o pracę od 5 lat, zarabiam 10 tysięcy miesięcznie.
...
"""
            )
    
    # ------------------------------------------------------------------------
    # TRYB 2: GOTOWE STANDARDOWE INPUTY
    # ------------------------------------------------------------------------
    elif quick_start_mode == "📋 Gotowe przykłady":
        st.markdown("##### 📋 Gotowe standardowe profile")
        st.caption("Szybkie wczytanie typowych scenariuszy kredytowych")
        
        profile_options = ["Wybierz profil..."] + list(STANDARD_PROFILES.keys())
        selected_profile = st.selectbox(
            "Wybierz przykładowy profil:",
            options=profile_options,
            key="profile_select"
        )
        
        if selected_profile != "Wybierz profil...":
            user_description = st.text_area(
                "Profil klienta (możesz edytować):",
                value=STANDARD_PROFILES[selected_profile],
                height=450,
                key="profile_text",
                help="Przykładowy profil - możesz go modyfikować wedle potrzeb"
            )
        else:
            user_description = st.text_area(
                "Lub wpisz własny profil w dowolnej formie:",
                value="",
                height=450,
                key="profile_text_empty",
                placeholder="""Klient: 45 lat, UoP czas nieokreślony, staż 5 lat, 10000 zł/mc
Cel: Zakup mieszkania
Wartość: 800,000 zł
Wkład własny: 20%
Okres: 25 lat
"""
            )
    
    # ------------------------------------------------------------------------
    # TRYB 3: EDYTOR FORMULARZA
    # ------------------------------------------------------------------------
    else:  # "✏️ Edytor formularza"
        st.markdown("##### ✏️ Interaktywny edytor z szablonami")
        st.caption("Wypełnij formularz pole po polu z podpowiedziami")
        
        with st.form("customer_profile_form"):
            # ================================================================
            # SEKCJA 1: DANE OSOBOWE
            # ================================================================
            st.markdown("### 👤 DANE OSOBOWE")
            
            col_age1, col_age2 = st.columns(2)
            with col_age1:
                age_template = st.selectbox(
                    "Szablon wieku kredytobiorcy:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["age_templates"],
                    key="age_template"
                )
                age_main = st.text_input(
                    "⚠️ Wiek kredytobiorcy (WYMAGANE):",
                    value=age_template.split(" ")[0] if age_template != "Wybierz..." else "",
                    placeholder="np. 35",
                    key="age_main"
                )
            
            with col_age2:
                has_co_borrower = st.checkbox("Współkredytobiorca?", key="has_co")
                age_co = ""
                if has_co_borrower:
                    age_co = st.text_input(
                        "Wiek współkredytobiorcy:",
                        placeholder="np. 33",
                        key="age_co"
                    )
            
            # Status związku
            relationship_status = st.selectbox(
                "Status związku:",
                options=["Wybierz...", "Małżeństwo", "Związek nieformalny", "Single", "Rozdzielność majątkowa"],
                key="relationship_status"
            )
            
            # Obywatelstwo
            col_cit1, col_cit2 = st.columns(2)
            with col_cit1:
                is_polish_citizen = st.checkbox("Obywatel Polski", value=True, key="is_polish")
            with col_cit2:
                if not is_polish_citizen:
                    has_residence_card = st.checkbox("Karta pobytu", key="has_residence")
                    if has_residence_card:
                        residence_type = st.radio("Typ karty:", ["Stały", "Czasowy"], key="residence_type", horizontal=True)
            
            # ================================================================
            # SEKCJA 2: DOCHODY KREDYTOBIORCY
            # ================================================================
            st.markdown("---")
            st.markdown("### 💰 DOCHODY - KREDYTOBIORCA")
            
            income_type_main = st.selectbox(
                "⚠️ Typ dochodu (WYMAGANE):",
                options=["Wybierz..."] + list(FORM_FIELD_TEMPLATES["income_type_templates"].keys()),
                key="income_type_main",
                help="Wybierz rodzaj zatrudnienia/dochodu"
            )
            
            if income_type_main != "Wybierz...":
                st.info(f"💡 {FORM_FIELD_TEMPLATES['income_type_templates'][income_type_main]}")
            
            col_inc1, col_inc2 = st.columns(2)
            with col_inc1:
                duration_template = st.selectbox(
                    "Szablon stażu pracy:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["employment_duration_templates"],
                    key="duration_template"
                )
                employment_duration = st.text_input(
                    "⚠️ Staż pracy w miesiącach (WYMAGANE):",
                    value=duration_template.split(" ")[0] if duration_template != "Wybierz..." else "",
                    placeholder="np. 60 (5 lat)",
                    key="duration_main"
                )
            
            with col_inc2:
                income_template = st.selectbox(
                    "Szablon dochodu:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["income_templates"],
                    key="income_template"
                )
                monthly_income = st.text_input(
                    "Dochód miesięczny netto (zł):",
                    value=income_template.split(" ")[0].replace(",", "") if income_template != "Wybierz..." else "",
                    placeholder="np. 10000",
                    key="income_main"
                )
            
            # ================================================================
            # SEKCJA 3: DOCHODY WSPÓŁKREDYTOBIORCY
            # ================================================================
            if has_co_borrower:
                st.markdown("---")
                st.markdown("### 👥 DOCHODY - WSPÓŁKREDYTOBIORCA")
                
                income_type_co = st.selectbox(
                    "Typ dochodu współkredytobiorcy:",
                    options=["Wybierz..."] + list(FORM_FIELD_TEMPLATES["income_type_templates"].keys()),
                    key="income_type_co"
                )
                
                col_co1, col_co2 = st.columns(2)
                with col_co1:
                    duration_co = st.text_input("Staż pracy (miesiące):", placeholder="np. 36", key="duration_co")
                with col_co2:
                    income_co = st.text_input("Dochód miesięczny (zł):", placeholder="np. 8000", key="income_co")
            
            # ================================================================
            # SEKCJA 4: CEL KREDYTU
            # ================================================================
            st.markdown("---")
            st.markdown("### 🎯 CEL KREDYTU")
            
            loan_purpose = st.selectbox(
                "⚠️ Cel kredytu (WYMAGANE):",
                options=["Wybierz..."] + list(FORM_FIELD_TEMPLATES["loan_purpose_templates"].keys()),
                key="loan_purpose"
            )
            
            if loan_purpose != "Wybierz...":
                st.info(f"💡 {FORM_FIELD_TEMPLATES['loan_purpose_templates'][loan_purpose]}")
            
            # ================================================================
            # SEKCJA 5: PARAMETRY KREDYTU
            # ================================================================
            st.markdown("---")
            st.markdown("### 💳 PARAMETRY KREDYTU")
            
            col_val1, col_val2 = st.columns(2)
            with col_val1:
                value_template = st.selectbox(
                    "Szablon wartości:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["property_value_templates"],
                    key="value_template"
                )
                property_value = st.text_input(
                    "⚠️ Wartość nieruchomości (zł) - WYMAGANE:",
                    value=value_template.split(" ")[0].replace(",", "") if value_template != "Wybierz..." else "",
                    placeholder="np. 800000",
                    key="property_value"
                )
            
            with col_val2:
                down_payment_template = st.selectbox(
                    "Szablon wkładu:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["down_payment_templates"],
                    key="down_payment_template"
                )
                down_payment_pct = st.text_input(
                    "Wkład własny (%):",
                    value=down_payment_template.split("%")[0] if down_payment_template != "Wybierz..." else "",
                    placeholder="np. 20",
                    key="down_payment"
                )
            
            col_per1, col_per2 = st.columns(2)
            with col_per1:
                period_template = st.selectbox(
                    "Okres kredytowania:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["loan_period_templates"],
                    key="period_template"
                )
                loan_period = st.text_input(
                    "Okres (lata):",
                    value=period_template.split(" ")[0] if period_template != "Wybierz..." else "",
                    placeholder="np. 25",
                    key="loan_period"
                )
            
            with col_per2:
                currency = st.selectbox(
                    "Waluta:",
                    options=["PLN", "EUR", "USD", "CHF"],
                    key="currency"
                )
            
            # Dodatkowe parametry
            with st.expander("⚙️ Parametry dodatkowe (opcjonalne)", expanded=False):
                col_add1, col_add2 = st.columns(2)
                with col_add1:
                    grace_period = st.text_input("Karencja (miesiące):", placeholder="np. 12", key="grace_period")
                    fixed_rate_period = st.text_input("Stałe oprocentowanie (lata):", placeholder="np. 5", key="fixed_rate")
                    eco_friendly = st.checkbox("Kredyt EKO (energooszczędny)", key="eco_friendly")
                
                with col_add2:
                    existing_mortgages = st.text_input("Liczba kredytów hipotecznych:", placeholder="np. 0", key="existing_mortgages")
                    refinancing_months = st.text_input("Refinansowanie (miesięcy wstecz):", placeholder="np. 12", key="refinancing_months")
                    consolidation_amount = st.text_input("Konsolidacja (zł):", placeholder="np. 50000", key="consolidation_amount")
            
            # ================================================================
            # SEKCJA 6: NIERUCHOMOŚĆ
            # ================================================================
            st.markdown("---")
            st.markdown("### 🏡 NIERUCHOMOŚĆ")
            
            property_type = st.selectbox(
                "Typ nieruchomości:",
                options=["Wybierz..."] + list(FORM_FIELD_TEMPLATES["property_type_templates"].keys()),
                key="property_type"
            )
            
            if property_type != "Wybierz...":
                st.info(f"💡 {FORM_FIELD_TEMPLATES['property_type_templates'][property_type]}")
            
            col_loc1, col_loc2 = st.columns(2)
            with col_loc1:
                location_template = st.selectbox(
                    "Szablon lokalizacji:",
                    options=["Wybierz..."] + FORM_FIELD_TEMPLATES["location_templates"],
                    key="location_template"
                )
                location = st.text_input(
                    "Lokalizacja:",
                    value=location_template.split(" ")[0] if location_template != "Wybierz..." else "",
                    placeholder="np. Warszawa",
                    key="location"
                )
            
            with col_loc2:
                property_area = st.text_input("Powierzchnia (m²):", placeholder="np. 75", key="property_area")
                plot_area = st.text_input("Powierzchnia działki (m²):", placeholder="np. 1000", key="plot_area")
            
            # Dodatkowe parametry nieruchomości
            with st.expander("🏗️ Parametry dodatkowe nieruchomości (opcjonalne)", expanded=False):
                col_prop1, col_prop2 = st.columns(2)
                with col_prop1:
                    has_building_permit = st.checkbox("Pozwolenie na budowę", key="building_permit")
                    construction_cost = st.text_input("Koszt budowy za m² (zł):", placeholder="np. 3500", key="construction_cost")
                    commercial_percent = st.text_input("% powierzchni komercyjnej:", placeholder="np. 30", key="commercial_percent")
                
                with col_prop2:
                    is_family_transaction = st.checkbox("Transakcja rodzinna", key="family_transaction")
                    is_shared_ownership = st.checkbox("Zakup udziału", key="shared_ownership")
                    ownership_percent = st.text_input("% udziału:", placeholder="np. 50", key="ownership_percent")
                    third_party_collateral = st.checkbox("Zabezpieczenie osoby trzeciej", key="third_party")
                    plot_as_down = st.checkbox("Działka jako wkład własny", key="plot_as_down")
            
            # ================================================================
            # PRZYCISK GENEROWANIA
            # ================================================================
            st.markdown("---")
            submitted = st.form_submit_button("✅ Generuj opis profilu", type="primary", use_container_width=True)
            
            if submitted:
                # ============================================================
                # GENEROWANIE OPISU Z WYPEŁNIONYCH PÓL
                # ============================================================
                description_parts = []
                
                # --------------------------------------------------------
                # DANE OSOBOWE
                # --------------------------------------------------------
                personal_info = []
                if age_main:
                    personal_info.append(f"Kredytobiorca: {age_main} lat")
                if has_co_borrower and age_co:
                    personal_info.append(f"Współkredytobiorca: {age_co} lat")
                if relationship_status != "Wybierz...":
                    personal_info.append(f"Status: {relationship_status}")
                if not is_polish_citizen:
                    personal_info.append("Cudzoziemiec")
                    if has_residence_card:
                        personal_info.append(f"Karta pobytu: {residence_type}")
                
                if personal_info:
                    description_parts.append("\n".join(personal_info))
                
                # --------------------------------------------------------
                # DOCHODY KREDYTOBIORCY
                # --------------------------------------------------------
                if income_type_main != "Wybierz...":
                    income_info = f"\nDOCHÓD KREDYTOBIORCY:\n- Typ: {income_type_main}"
                    if employment_duration:
                        income_info += f"\n- Staż: {employment_duration} miesięcy"
                    if monthly_income:
                        income_info += f"\n- Dochód miesięczny netto: {monthly_income} zł"
                    description_parts.append(income_info)
                
                # --------------------------------------------------------
                # DOCHODY WSPÓŁKREDYTOBIORCY
                # --------------------------------------------------------
                if has_co_borrower and income_type_co and income_type_co != "Wybierz...":
                    co_income_info = f"\nDOCHÓD WSPÓŁKREDYTOBIORCY:\n- Typ: {income_type_co}"
                    if duration_co:
                        co_income_info += f"\n- Staż: {duration_co} miesięcy"
                    if income_co:
                        co_income_info += f"\n- Dochód miesięczny netto: {income_co} zł"
                    description_parts.append(co_income_info)
                
                # --------------------------------------------------------
                # CEL KREDYTU
                # --------------------------------------------------------
                if loan_purpose != "Wybierz...":
                    description_parts.append(f"\nCEL KREDYTU:\n{loan_purpose}")
                
                # --------------------------------------------------------
                # PARAMETRY KREDYTU
                # --------------------------------------------------------
                params_info = "\nPARAMETRY KREDYTU:"
                added_params = False
                
                if property_value:
                    params_info += f"\n- Wartość nieruchomości: {property_value} zł"
                    added_params = True
                
                if down_payment_pct:
                    params_info += f"\n- Wkład własny: {down_payment_pct}%"
                    added_params = True
                    if property_value:
                        try:
                            down_amt = int(property_value) * int(down_payment_pct) / 100
                            loan_amt = int(property_value) - down_amt
                            params_info += f"\n- Kwota wkładu: {int(down_amt):,} zł"
                            params_info += f"\n- Kwota kredytu: {int(loan_amt):,} zł"
                            params_info += f"\n- LTV: {100 - int(down_payment_pct)}%"
                        except:
                            pass
                
                if loan_period:
                    params_info += f"\n- Okres kredytowania: {loan_period} lat"
                    added_params = True
                
                if currency and currency != "PLN":
                    params_info += f"\n- Waluta: {currency}"
                    added_params = True
                
                # Parametry dodatkowe
                if grace_period:
                    params_info += f"\n- Karencja kapitałowa: {grace_period} miesięcy"
                    added_params = True
                if fixed_rate_period:
                    params_info += f"\n- Oprocentowanie stałe: {fixed_rate_period} lat"
                    added_params = True
                if eco_friendly:
                    params_info += f"\n- Kredyt EKO: TAK (energooszczędny)"
                    added_params = True
                if existing_mortgages:
                    params_info += f"\n- Liczba istniejących kredytów hipotecznych: {existing_mortgages}"
                    added_params = True
                if refinancing_months:
                    params_info += f"\n- Refinansowanie wydatków ({refinancing_months} miesięcy wstecz)"
                    added_params = True
                if consolidation_amount:
                    params_info += f"\n- Konsolidacja zobowiązań: {consolidation_amount} zł"
                    added_params = True
                
                if added_params:
                    description_parts.append(params_info)
                
                # --------------------------------------------------------
                # NIERUCHOMOŚĆ
                # --------------------------------------------------------
                property_info = "\nNIERUCHOMOŚĆ:"
                added_property = False
                
                if property_type != "Wybierz...":
                    property_info += f"\n- Typ: {property_type}"
                    added_property = True
                if location:
                    property_info += f"\n- Lokalizacja: {location}"
                    added_property = True
                if property_area:
                    property_info += f"\n- Powierzchnia: {property_area} m²"
                    added_property = True
                if plot_area:
                    property_info += f"\n- Powierzchnia działki: {plot_area} m²"
                    added_property = True
                
                # Parametry dodatkowe nieruchomości
                if has_building_permit:
                    property_info += f"\n- Pozwolenie na budowę: TAK"
                    added_property = True
                if construction_cost:
                    property_info += f"\n- Koszt budowy: {construction_cost} zł/m²"
                    added_property = True
                if commercial_percent:
                    property_info += f"\n- Powierzchnia komercyjna: {commercial_percent}%"
                    added_property = True
                if is_family_transaction:
                    property_info += f"\n- Transakcja rodzinna: TAK"
                    added_property = True
                if is_shared_ownership:
                    property_info += f"\n- Zakup udziału: TAK"
                    added_property = True
                    if ownership_percent:
                        property_info += f"\n- Udział: {ownership_percent}%"
                if third_party_collateral:
                    property_info += f"\n- Zabezpieczenie osoby trzeciej: TAK"
                    added_property = True
                if plot_as_down:
                    property_info += f"\n- Działka jako wkład własny: TAK"
                    added_property = True
                
                if added_property:
                    description_parts.append(property_info)
                
                # --------------------------------------------------------
                # --------------------------------------------------------
                # POŁĄCZ WSZYSTKO
                # --------------------------------------------------------
                user_description = "\n".join(description_parts)
                
                # Zapisz do session state
                st.session_state['generated_description'] = user_description
        
        # Wyświetl wygenerowany opis (poza formularzem)
        if 'generated_description' in st.session_state:
            user_description = st.text_area(
                "Wygenerowany opis profilu (możesz edytować przed analizą):",
                value=st.session_state['generated_description'],
                height=350,
                key="final_description"
            )
    
    # Przycisk analizy
    analyze_button = st.button(
        "🔍 Znajdź pasujące oferty", 
        type="primary",
        use_container_width=True,
        disabled=(not user_description.strip())
    )
    
    if analyze_button and user_description.strip():
        # Pobierz wybrane modele z session state
        mapper_model = st.session_state.get('mapper_model', 'gpt-4.1')
        etap1 = st.session_state.get('etap1_model', 'gpt-4.1')
        etap2 = st.session_state.get('etap2_model', 'gpt-4.1')
        use_async_mode = st.session_state.get('use_async', True)
        
        # ====================================================================
        # KROK 0: MAPOWANIE INPUTU NA MODEL DANYCH
        # ====================================================================
        with st.spinner(f'🔄 KROK 0: Mapowanie danych klienta [{mapper_model}]...'):
            try:
                profile, profile_dict = st.session_state.input_mapper.map_input_to_profile(
                    user_input=user_description,
                    model_name=mapper_model
                )
                
                st.session_state.customer_profile = profile
                st.session_state.mapped_profile_json = profile_dict
                
                # Sprawdź czy profil kompletny
                if not profile.is_complete():
                    missing = profile.get_missing_required_fields()
                    st.warning(f"⚠️ Brakujące wymagane dane: {', '.join(missing)}")
                    st.info("💡 Analiza będzie przeprowadzona, ale może być niepełna.")
                else:
                    st.success("✅ Profil klienta zmapowany pomyślnie!")
                
                # Pokaż zmapowany profil w expander
                with st.expander("🔍 Zobacz zmapowany profil (JSON)", expanded=False):
                    st.json(profile.to_dict())
                
            except Exception as e:
                st.error(f"❌ Błąd mapowania profilu: {str(e)}")
                st.stop()
        
        # ====================================================================
        # KROK 1 i 2: ANALIZA DWUETAPOWA (ze zmapowanym profilem)
        # ====================================================================
        spinner_text = f'🤖 ETAP 1: Walidacja WYMOGÓW [{etap1}] {"⚡ ASYNC" if use_async_mode else ""}...'
        
        with st.spinner(spinner_text):
            try:
                # Pobierz strategię jakości z session state
                quality_strategy = st.session_state.get('quality_strategy', 'individual')
                
                # Uruchom system V3 z orchestratorem (nowa architektura serwisów)
                result = asyncio.run(
                    st.session_state.engine.process_query_v3(
                        user_query=user_description,
                        customer_profile=st.session_state.customer_profile,  # Zmapowany profil
                        etap1_model=etap1,
                        etap2_model=etap2,
                        quality_strategy=quality_strategy  # Nowy parametr!
                    )
                )
                
                if not result.get("error"):
                    # Parsuj wynik etapu 1
                    validation_json = parse_validation_json(result["stage1_validation"])
                    
                    if validation_json:
                        st.session_state.validation_result = validation_json
                        st.session_state.ranking_result = result["stage2_ranking"]
                        
                        # Pobierz surowe dane z orchestratora
                        stage1_data = result.get("stage1_data", validation_json)
                        stage2_data = result.get("stage2_data", {})
                        strategy = result.get("quality_strategy", "individual")
                        
                        # Zapisz strategię do session_state, aby była dostępna w UI
                        st.session_state.used_quality_strategy = strategy
                        
                        # Stwórz mapę quality scores po nazwie banku (obsługuje obie strategie)
                        quality_scores_map = {}
                        
                        if strategy == "comparative":
                            # Nowa strategia: stage2_data = {"ranking": [...], "weights": {...}, "market_stats": {...}}
                            for score_dict in stage2_data.get("ranking", []):
                                bank_name = score_dict.get("bank_name")
                                if bank_name:
                                    quality_scores_map[bank_name] = score_dict
                        else:
                            # Stara strategia: stage2_data = {"scores": [...]}
                            for score_dict in stage2_data.get("scores", []):
                                bank_name = score_dict.get("bank_name")
                                if bank_name:
                                    quality_scores_map[bank_name] = score_dict
                        
                        # DEBUG: Pokaż fragment rankingu w konsoli
                        print("\n" + "="*80)
                        print("🔍 FRAGMENT RANKINGU (pierwsze 500 znaków):")
                        print("="*80)
                        print(result["stage2_ranking"][:500])
                        print("="*80 + "\n")
                        
                        # Wyciągnij listy banków
                        st.session_state.qualified_banks = []
                        st.session_state.disqualified_banks = []
                        
                        for bank in stage1_data.get("qualified_banks", []):
                            bank_name = bank["bank_name"]
                            
                            # Pobierz dane jakości bezpośrednio z stage2_data
                            quality_data = quality_scores_map.get(bank_name, {})
                            
                            bank_info = {
                                "name": bank_name,
                                "status": "qualified",
                                "score": quality_data.get("total_score", 0),
                                "category_breakdown": quality_data.get("breakdown", {}),
                                "key_strengths": quality_data.get("kluczowe_atuty", quality_data.get("strengths", [])),
                                "key_weaknesses": quality_data.get("punkty_uwagi", quality_data.get("weaknesses", [])),
                                "competitive_advantages": quality_data.get("competitive_advantages", []),
                                "checked_parameters": quality_data.get("checked_parameters", []),
                                "scoring_method": quality_data.get("scoring_method", quality_data.get("reasoning", "")),
                                "requirements_count": len(bank.get("sprawdzone_wymogi", [])),
                                "sprawdzone_wymogi": bank.get("sprawdzone_wymogi", []),
                                # Nowe pola z porównawczej strategii
                                "rank": quality_data.get("rank"),
                                "percentile": quality_data.get("percentile"),
                                "better_than": quality_data.get("better_than", []),
                                "worse_than": quality_data.get("worse_than", []),
                                "raw_validation": bank,
                                "raw_quality": quality_data
                            }
                            st.session_state.qualified_banks.append(bank_info)
                        
                        for bank in stage1_data.get("disqualified_banks", []):
                            bank_name = bank["bank_name"]
                            
                            # Nowy format V3
                            sprawdzone = bank.get("sprawdzone_wymogi", [])
                            niespelnione = bank.get("niespelnione_wymogi", [])
                            kluczowe_problemy = bank.get("kluczowe_problemy", [])
                            
                            bank_info = {
                                "name": bank_name,
                                "status": "disqualified",
                                "critical_issues": kluczowe_problemy,
                                "requirements_count": len(sprawdzone),
                                "unmet_count": len(niespelnione),
                                "sprawdzone_wymogi": sprawdzone,
                                "niespelnione_wymogi": niespelnione,
                                "raw_validation": bank
                            }
                            st.session_state.disqualified_banks.append(bank_info)
                        
                        # Sortuj qualified banki po score
                        st.session_state.qualified_banks.sort(
                            key=lambda x: x.get("score", 0) or 0, 
                            reverse=True
                        )
                        
                        st.success(f"✅ Analiza zakończona! Zakwalifikowane: {len(st.session_state.qualified_banks)}/11")
                    else:
                        st.error("❌ Błąd parsowania wyników walidacji")
                else:
                    st.error(f"❌ Błąd analizy: {result.get('stage2_ranking', 'Nieznany błąd')}")
                    
            except Exception as e:
                st.error(f"❌ Błąd podczas analizy: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


with col2:
    st.markdown(f"### ✅ Pasujące oferty ({len(st.session_state.qualified_banks)}/11)")
    
    if st.session_state.qualified_banks:
        for idx, bank_info in enumerate(st.session_state.qualified_banks):
            bank_name = bank_info["name"]
            
            # Emoji dla TOP 3
            if idx == 0:
                emoji = "🏆"
                border_color = "#FFD700"  # Gold
            elif idx == 1:
                emoji = "🥈"
                border_color = "#C0C0C0"  # Silver
            elif idx == 2:
                emoji = "🥉"
                border_color = "#CD7F32"  # Bronze
            else:
                emoji = "✅"
                border_color = "#4CAF50"  # Green
            
            with st.container(border=True):
                cols = st.columns([1, 5, 2])
                
                with cols[0]:
                    # Logo banku
                    logo_path = bank_logos.get(bank_name, "")
                    if logo_path and os.path.exists(logo_path):
                        st.image(logo_path, width=60)
                    else:
                        st.markdown(f"### {emoji}")
                
                with cols[1]:
                    # Nazwa i punktacja
                    if bank_info.get("score"):
                        st.markdown(f"**{emoji} {bank_name}** - **{bank_info['score']}/100 pkt**")
                    else:
                        st.markdown(f"**{emoji} {bank_name}**")
                    
                    # Wymogi sprawdzone
                    req_count = bank_info.get('requirements_count', 0)
                    st.caption(f"✅ Sprawdzono {req_count} wymogów - wszystkie spełnione")
                
                with cols[2]:
                    # Przycisk szczegółów
                    with st.popover("📊 Szczegóły", use_container_width=True):
                        st.markdown(f"### {bank_name}")
                        
                        # ETAP 2: Punktacja jakości
                        if bank_info.get("score"):
                            st.markdown("#### 🏅 ETAP 2: Ocena Jakości")
                            
                            # Punktacja końcowa z emoji
                            score = bank_info['score']
                            if score >= 80:
                                emoji = "🌟"
                            elif score >= 60:
                                emoji = "✅"
                            else:
                                emoji = "⚠️"
                            
                            # Pokaż punktację z percentylem (jeśli dostępny)
                            percentile = bank_info.get("percentile")
                            rank = bank_info.get("rank")
                            used_strategy = st.session_state.get("used_quality_strategy", "individual")
                            
                            if percentile is not None and used_strategy == "comparative":
                                st.metric(
                                    "Punktacja końcowa", 
                                    f"{score}/100 pkt {emoji}",
                                    delta=f"TOP {100-percentile:.0f}% (#{rank})"
                                )
                            else:
                                st.metric("Punktacja końcowa", f"{score}/100 pkt {emoji}")
                            
                            # Breakdown według kategorii
                            if bank_info.get("category_breakdown"):
                                st.markdown("**📊 Rozbicie punktacji:**")
                                breakdown = bank_info["category_breakdown"]
                                
                                for category, score_val in breakdown.items():
                                    st.markdown(f"**{category}**: {score_val} pkt")
                                    st.progress(min(score_val / 50, 1.0))
                            
                            # Kluczowe atuty
                            if bank_info.get("key_strengths"):
                                st.markdown("**✅ Kluczowe atuty:**")
                                for atut in bank_info["key_strengths"][:5]:
                                    st.markdown(f"- {atut}")
                            
                            # Przewagi konkurencyjne (tylko dla strategii comparative)
                            if bank_info.get("competitive_advantages") and used_strategy == "comparative":
                                st.markdown("**⭐ Przewagi konkurencyjne:**")
                                for przewaga in bank_info["competitive_advantages"][:3]:
                                    st.markdown(f"- {przewaga}")
                            
                            # Punkty uwagi
                            if bank_info.get("key_weaknesses"):
                                st.markdown("**⚠️ Punkty uwagi:**")
                                for uwaga in bank_info["key_weaknesses"][:3]:
                                    st.markdown(f"- {uwaga}")
                            
                            # Metodologia
                            if bank_info.get("scoring_method"):
                                with st.expander("🔍 Metodologia oceny"):
                                    st.caption(bank_info["scoring_method"])
                        
                        st.markdown("---")
                        
                        # ETAP 1: Walidacja wymogów
                        st.markdown("#### ✅ ETAP 1: Walidacja Wymogów")
                        sprawdzone = bank_info.get("sprawdzone_wymogi", [])
                        
                        if sprawdzone:
                            st.success(f"**Sprawdzono {len(sprawdzone)} wymogów - wszystkie spełnione** ✅")
                            
                            with st.expander(f"📋 Szczegóły walidacji ({len(sprawdzone)} wymogów)"):
                                for i, wymog in enumerate(sprawdzone, 1):
                                    st.markdown(f"{i}. ✓ {wymog}")
                        else:
                            st.info("Brak szczegółowych danych walidacji")
    else:
        st.info("👈 Wprowadź profil klienta i kliknij 'Znajdź pasujące oferty'")
        st.markdown("""
        **System trzyetapowy analizuje:**
        - ✅ **ETAP 1**: Walidacja WYMOGÓW (kwalifikacja/dyskwalifikacja)
        - 🏅 **ETAP 2**: Ranking JAKOŚCI (punktacja 0-100)
        - 🏆 **ETAP 3**: TOP 4 z pełnym raportem
        
        **Otrzymasz:**
        - Lista zakwalifikowanych banków z punktacją
        - Szczegółową walidację wymogów dla każdego banku
        - Breakdown punktacji według 5 kategorii jakości
        - TOP 4 ranking z uzasadnieniem i rekomendacją
        """)

with col3:
    st.markdown(f"### ❌ Niepasujące oferty ({len(st.session_state.disqualified_banks)}/11)")
    
    if st.session_state.disqualified_banks:
        for bank_info in st.session_state.disqualified_banks:
            bank_name = bank_info["name"]
            
            with st.container(border=True):
                cols = st.columns([1, 5])
                
                with cols[0]:
                    # Logo banku (szare)
                    logo_path = bank_logos.get(bank_name, "")
                    if logo_path and os.path.exists(logo_path):
                        st.image(logo_path, width=60)
                    else:
                        st.markdown("### ⚠️")
                
                with cols[1]:
                    st.markdown(f"**{bank_name}**")
                    
                    # Wymogi niespełnione
                    unmet = bank_info.get('unmet_count', 0)
                    req_count = bank_info.get('requirements_count', 0)
                    st.caption(f"❌ Niespełnione: {unmet} | ✅ Sprawdzono: {req_count}")
                    
                    # Główne problemy
                    critical_issues = bank_info.get("critical_issues", [])
                    if critical_issues:
                        st.markdown("**Powody odrzucenia:**")
                        for issue in critical_issues[:2]:  # Max 2 powody
                            st.markdown(f"<span style='color: #f44336; font-size: 0.9em;'>⚠️ {issue}</span>", 
                                      unsafe_allow_html=True)
                        
                        if len(critical_issues) > 2:
                            with st.expander(f"+ {len(critical_issues) - 2} więcej"):
                                for issue in critical_issues[2:]:
                                    st.markdown(f"⚠️ {issue}")
                        
                        # Pokaż szczegóły walidacji
                        with st.expander("📋 Szczegóły walidacji"):
                            st.markdown("**✅ Spełnione wymogi:**")
                            for wymog in bank_info.get("sprawdzone_wymogi", [])[:5]:
                                st.markdown(f"✓ {wymog}")
                            
                            st.markdown("**❌ Niespełnione wymogi:**")
                            for wymog in bank_info.get("niespelnione_wymogi", []):
                                st.markdown(f"✗ {wymog}")
    else:
        if st.session_state.qualified_banks:
            st.success("🎉 Wszystkie banki zakwalifikowane!")
        else:
            st.info("Tutaj pojawią się banki odrzucone po analizie")

# ============================================================================
# RANKING TOP BANKÓW WEDŁUG JAKOŚCI (ETAP 2)
# ============================================================================
if st.session_state.qualified_banks and st.session_state.ranking_result:
    st.markdown("---")
    
    # Tytuł dostosowany do liczby banków
    num_banks = len(st.session_state.qualified_banks)
    if num_banks == 1:
        st.markdown("## 🏆 OCENA JAKOŚCI OFERTY")
        st.markdown("*Szczegółowa analiza 19 parametrów jakościowych*")
    else:
        st.markdown("## 🏆 RANKING BANKÓW WG JAKOŚCI OFERTY")
        st.markdown(f"*Ocena 19 parametrów jakościowych - TOP {min(num_banks, 4)} z {num_banks} zakwalifikowanych*")
    
    # TOP banki w kartkach (1-4)
    top_banks = st.session_state.qualified_banks[:4]
    
    if len(top_banks) >= 4:
        cols_top = st.columns(4)
    elif len(top_banks) == 3:
        cols_top = st.columns(3)
    elif len(top_banks) == 2:
        cols_top = st.columns(2)
    else:
        cols_top = [st.container()]
    
    medals = ["🥇", "🥈", "🥉", "🎖️"]
    colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#4CAF50"]
    place_names = ["NAJLEPSZA OFERTA", "DRUGIE MIEJSCE", "TRZECIE MIEJSCE", "CZWARTE MIEJSCE"]
    
    for idx, bank_info in enumerate(top_banks):
        with cols_top[idx] if len(top_banks) > 1 else cols_top[0]:
            bank_name = bank_info["name"]
            score = bank_info.get("score", 0)
            
            # Dostosuj komunikat dla jedynego banku
            if num_banks == 1:
                place_text = "JEDYNA ZAKWALIFIKOWANA OFERTA"
            else:
                place_text = f"{place_names[idx]}"
            
            # Karta banku z gradientem
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {colors[idx]}20 0%, {colors[idx]}40 100%);
                border: 2px solid {colors[idx]};
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                min-height: 280px;
            ">
                <div style="font-size: 3em; margin-bottom: 10px;">{medals[idx]}</div>
                <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 8px;">
                    {bank_name}
                </div>
                <div style="font-size: 2.5em; font-weight: bold; color: {colors[idx]}; margin: 15px 0;">
                    {score}<span style="font-size: 0.5em; color: #666;">/100</span>
                </div>
                <div style="font-size: 0.85em; color: #666; margin-bottom: 10px;">
                    {place_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Logo banku pod kartą
            logo_path = bank_logos.get(bank_name, "")
            if logo_path and os.path.exists(logo_path):
                st.image(logo_path, width=80)
            
            # Główne atuty w expander
            reasons = bank_info.get("reasons", [])
            if reasons:
                with st.expander("✨ Kluczowe atuty"):
                    for reason in reasons:
                        st.markdown(f"✓ {reason}")
    
    # Pełny raport AI w ekspandowanym bloku
    st.markdown("---")
    with st.expander("📄 **PEŁNY RAPORT JAKOŚCIOWY (ETAP 2: AI Analysis)**", expanded=False):
        st.markdown(st.session_state.ranking_result)
        
        # Przycisk download
        st.download_button(
            label="💾 Pobierz raport jako Markdown",
            data=st.session_state.ranking_result,
            file_name=f"ranking_kredytowy_{st.session_state.validation_result.get('customer_summary', {}).get('loan_purpose', 'raport')[:30]}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    # Podsumowanie statystyk
    st.markdown("---")
    stat_cols = st.columns(4)
    
    with stat_cols[0]:
        st.metric(
            "📊 Przeanalizowane banki", 
            f"{len(st.session_state.qualified_banks)}/11",
            delta="Zakwalifikowane"
        )
    
    with stat_cols[1]:
        avg_score = sum(b.get("score", 0) for b in st.session_state.qualified_banks if b.get("score")) / max(len([b for b in st.session_state.qualified_banks if b.get("score")]), 1)
        st.metric(
            "📈 Średnia punktacja", 
            f"{avg_score:.1f}/100",
            delta="Jakość ofert"
        )
    
    with stat_cols[2]:
        if top_banks:
            st.metric(
                "🏆 Najlepsza oferta", 
                top_banks[0]["name"],
                delta=f"{top_banks[0].get('score', 0)}/100 pkt"
            )
    
    with stat_cols[3]:
        st.metric(
            "✅ Parametry sprawdzone", 
            "87 total",
            delta="68 WYMOGÓW + 19 JAKOŚCI"
        )

# Sidebar - informacje
with st.sidebar:
    st.markdown("### 🤖 Konfiguracja modeli AI")
    
    # Dostępne modele
    available_models = [
        "gpt-4.1",
        "gpt-4.1-nano", 
        "gpt-5-mini",
        "gpt-5-nano",
        "o1",
        "o4-mini"
    ]
    
    # Wybór modelu dla MAPPER (nowy!)
    mapper_model = st.selectbox(
        "🔄 Model MAPPER (Ekstrakcja danych)",
        available_models,
        index=0,  # domyślnie gpt-4.1
        help="Model do mapowania inputu użytkownika na strukturę danych. Rekomendacja: gpt-4.1 dla precyzji"
    )
    
    # Wybór modelu dla ETAP 1 (Walidacja)
    etap1_model = st.selectbox(
        "🔍 Model ETAP 1 (Walidacja WYMOGÓW)",
        available_models,
        index=0,  # domyślnie gpt-4.1
        help="Model do walidacji parametrów eliminujących. Rekomendacja: gpt-4.1 lub o4-mini dla szybkości"
    )
    
    # Wybór strategii dla ETAP 2 (nowe!)
    st.markdown("#### 🏅 ETAP 2: Scoring JAKOŚCI")
    
    quality_strategy = st.radio(
        "Strategia oceny jakości:",
        options=["individual", "comparative"],
        format_func=lambda x: {
            "individual": "🔢 Indywidualna (każdy bank osobno)",
            "comparative": "🏆 Porównawcza (benchmarking rynkowy)"
        }[x],
        index=1,  # domyślnie comparative
        help="""
**Indywidualna:** Każdy bank oceniany w izolacji (szybsze, ale brak kontekstu).

**Porównawcza (NOWA!):** 
- Wszystkie banki oceniane razem z kontekstem rynkowym
- Dynamiczne wagi dostrojone do profilu klienta
- Benchmarking min-max (najlepszy = 100, najgorszy = 0)
- Percentyle i przewagi konkurencyjne
- 1 wywołanie LLM zamiast 11 (szybciej + taniej)
"""
    )
    
    # Wybór modelu dla ETAP 2 (Ranking)
    etap2_model = st.selectbox(
        "Model do scoringu jakości:",
        available_models,
        index=0,  # domyślnie gpt-4.1
        help="Model do rankingu parametrów jakościowych. Rekomendacja: gpt-4.1 dla najlepszej jakości"
    )
    
    # Async mode toggle
    use_async = st.checkbox(
        "⚡ Async Parallel Processing",
        value=True,
        help="Równoległe przetwarzanie banków = 80-90% szybciej (31s → 3-5s)"
    )
    
    # Zapisz w session state
    st.session_state.mapper_model = mapper_model
    st.session_state.etap1_model = etap1_model
    st.session_state.etap2_model = etap2_model
    st.session_state.quality_strategy = quality_strategy  # Nowe!
    st.session_state.use_async = use_async
    
    st.markdown("---")
    
    st.markdown("### ℹ️ O systemie")
    
    st.markdown("""
    **System Trzyetapowy v3.0**
    
    � **ETAP 0: Mapowanie danych**
    - AI ekstraktuje dane z inputu
    - Strukturyzacja do modelu
    - Walidacja kompletności
    
    �🔍 **ETAP 1: Walidacja WYMOGÓW**
    - Sprawdza tylko podane parametry
    - Precyzyjna kwalifikacja
    - Jasne uzasadnienia
    
    🏅 **ETAP 2: Ranking JAKOŚCI**
    - Punktacja tylko dla podanych cech
    - Scoring 0-100
    - TOP 4 rekomendacje
    
    📊 **Baza wiedzy:**
    - 11 banków
    - 87 parametrów/bank
    - Inteligentne dopasowanie
    """)
    
    st.markdown("---")
    
    # Pokaż zmapowany profil jeśli istnieje
    if st.session_state.customer_profile:
        st.markdown("### � Zmapowany profil")
        
        profile = st.session_state.customer_profile
        
        # Status kompletności
        if profile.is_complete():
            st.success("✅ Profil kompletny")
        else:
            missing = profile.get_missing_required_fields()
            st.warning(f"⚠️ Brak: {len(missing)} pól")
        
        # Podstawowe info
        if profile.borrower.age:
            st.caption(f"👤 Wiek: {profile.borrower.age} lat")
        if profile.borrower.income_type:
            st.caption(f"💼 Dochód: {profile.borrower.income_type.value}")
        if profile.loan.loan_purpose:
            st.caption(f"🎯 Cel: {profile.loan.loan_purpose.value}")
        if profile.loan.loan_amount:
            st.caption(f"💰 Kwota: {profile.loan.loan_amount:,.0f} PLN")
        
        # Przycisk do pełnego widoku
        with st.expander("🔍 Pełny JSON"):
            st.json(profile.to_dict())
    
    st.markdown("---")
    
    if st.session_state.validation_result:
        st.markdown("### 📈 Statystyki analizy")
        
        summary = st.session_state.validation_result.get("validation_summary", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Zakwalifikowane", summary.get("qualified_count", 0))
        with col2:
            st.metric("Odrzucone", summary.get("disqualified_count", 0))
    
    st.markdown("---")
    
    # Download pełnego raportu
    if st.session_state.ranking_result:
        st.download_button(
            label="📥 Pobierz pełny raport",
            data=st.session_state.ranking_result,
            file_name="raport_kredytowy.md",
            mime="text/markdown",
            use_container_width=True
        )