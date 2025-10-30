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
    
    # Przykładowe profile
    example_profiles = {
        "Wybierz przykład...": "",
        "👨‍💼 Standardowy (45 lat, zakup mieszkania)": """Klient: Jan Kowalski, 45 lat
Współkredytobiorca: Anna Kowalska, 42 lata

DOCHODY:
- Jan: Umowa o pracę na czas nieokreślony, staż 5 lat, dochód 8000 zł/mc
- Anna: Umowa o pracę na czas nieokreślony, staż 3 lata, dochód 6000 zł/mc

CEL: Zakup mieszkania na rynku wtórnym w Warszawie

PARAMETRY:
- Wartość mieszkania: 800,000 zł
- Wkład własny: 160,000 zł (20%)
- Kwota kredytu: 640,000 zł
- LTV: 80%
- Okres: 25 lat (300 miesięcy)

NIERUCHOMOŚĆ:
- Typ: mieszkanie
- Lokalizacja: Warszawa
- Powierzchnia: 75 m2

DODATKOWE:
- Status: małżeństwo
- Obywatele Polski
- Brak innych kredytów hipotecznych
- Zainteresowani kredytem EKO""",
        
        "👴 Senior (68 lat, działka rekreacyjna)": """Klient: Senior, 68 lat
Współkredytobiorca: Małżonka, 65 lat

DOCHODY:
- Klient: Emerytura, 5000 zł/mc
- Współkredytobiorca: Emerytura, 4000 zł/mc

CEL: Zakup działki rekreacyjnej

PARAMETRY:
- Powierzchnia działki: 1500 m2
- Cena działki: 150,000 zł
- Wkład własny: 50,000 zł (33%)
- Kwota kredytu: 100,000 zł
- Okres: 10 lat

NIERUCHOMOŚĆ:
- Typ: działka rekreacyjna
- Lokalizacja: góry

DODATKOWE:
- Status: małżeństwo""",
        
        "🏗️ Budowa domu (35 lat)": """Klient: Małgorzata Nowak, 35 lat
Współkredytobiorca: Piotr Nowak, 37 lat

DOCHODY:
- Małgorzata: UoP na czas nieokreślony, 8000 zł/mc, staż 4 lata
- Piotr: Działalność gospodarcza KPiR, 24 miesiące

CEL: Budowa domu jednorodzinnego systemem zleconym

PARAMETRY:
- Koszt budowy: 600,000 zł
- Działka w posiadaniu (wartość 100,000 zł)
- Wkład własny: 140,000 zł (20%)
- Kwota kredytu: 560,000 zł
- Okres: 30 lat

NIERUCHOMOŚĆ:
- Typ: dom (budowa)
- Powierzchnia działki: 800 m2
- Pozwolenie na budowę: tak

DODATKOWE:
- Status: małżeństwo
- Działka jako część wkładu własnego""",
        
        "🏢 Lokal użytkowy (40 lat, kontrakt B2B)": """Klient: Przedsiębiorca, 40 lat

DOCHODY:
- Kontrakt menadżerski (B2B), 36 miesięcy, 15000 zł/mc

CEL: Zakup lokalu użytkowego pod biuro

PARAMETRY:
- Wartość lokalu: 500,000 zł
- Wkład własny: 150,000 zł (30%)
- Kwota kredytu: 350,000 zł
- LTV: 70%
- Okres: 20 lat

NIERUCHOMOŚĆ:
- Typ: lokal użytkowy
- Lokalizacja: Kraków (miasto >100k)
- Powierzchnia: 50 m2

DODATKOWE:
- Status: single
- Brak innych kredytów"""
    }
    
    selected_example = st.selectbox(
        "Szybki start - wybierz przykład:",
        options=list(example_profiles.keys()),
        index=0
    )
    
    user_description = st.text_area(
        "Opisz profil klienta (możesz w dowolnej formie - system AI zrozumie):",
        value=example_profiles[selected_example],
        height=400,
        placeholder="""Podaj dane klienta w dowolnej formie, np.:

Jan Kowalski, 45 lat
UoP na stałe, staż 5 lat
Zakup mieszkania za 800k
Wkład własny 20%
Okres 25 lat
"""
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
                # Przekaż zmapowany profil jako context
                profile_context = json.dumps(st.session_state.mapped_profile_json, ensure_ascii=False, indent=2)
                
                # Uruchom system dwupromptowy z wybranymi modelami
                result = st.session_state.engine.ai_client.query_two_stage(
                    user_query=user_description,
                    knowledge_base_context=st.session_state.engine.data_processor.format_compact_for_context(),
                    etap1_model=etap1,
                    etap2_model=etap2,
                    use_async=use_async_mode,
                    knowledge_base_dict=st.session_state.engine.data_processor.knowledge_base,
                    customer_profile=st.session_state.customer_profile  # Przekaż zmapowany profil
                )
                
                if not result.get("error"):
                    # Parsuj wynik etapu 1
                    validation_json = parse_validation_json(result["stage1_validation"])
                    
                    if validation_json:
                        st.session_state.validation_result = validation_json
                        st.session_state.ranking_result = result["stage2_ranking"]
                        
                        # DEBUG: Pokaż fragment rankingu w konsoli
                        print("\n" + "="*80)
                        print("🔍 FRAGMENT RANKINGU (pierwsze 500 znaków):")
                        print("="*80)
                        print(result["stage2_ranking"][:500])
                        print("="*80 + "\n")
                        
                        # Wyciągnij listy banków
                        st.session_state.qualified_banks = []
                        st.session_state.disqualified_banks = []
                        
                        for bank in validation_json.get("qualified_banks", []):
                            bank_name = bank["bank_name"]
                            score = extract_bank_score(result["stage2_ranking"], bank_name)
                            reasons = extract_top_reasons(result["stage2_ranking"], bank_name)
                            
                            # Debug - wyświetl jeśli nie znaleziono score
                            if score is None:
                                print(f"⚠️ Nie znaleziono punktacji dla: {bank_name}")
                                # Fallback - przypisz 0 zamiast None
                                score = 0
                            
                            # Obsługa obu formatów (stary i nowy async)
                            # Nowy format: spelnione_wymogi, niespelnione_wymogi
                            # Stary format: requirements_met, requirements_total
                            if "spelnione_wymogi" in bank:
                                # Nowy format async
                                requirements_met = len(bank.get("spelnione_wymogi", []))
                                requirements_total = requirements_met + len(bank.get("niespelnione_wymogi", []))
                            else:
                                # Stary format
                                requirements_met = bank.get("requirements_met", 0)
                                requirements_total = bank.get("requirements_total", 0)
                            
                            bank_info = {
                                "name": bank_name,
                                "status": "qualified",
                                "score": score,
                                "reasons": reasons,
                                "requirements_met": requirements_met,
                                "requirements_total": requirements_total
                            }
                            st.session_state.qualified_banks.append(bank_info)
                        
                        for bank in validation_json.get("disqualified_banks", []):
                            # Obsługa obu formatów
                            if "kluczowe_problemy" in bank:
                                # Nowy format async
                                critical_issues = bank.get("kluczowe_problemy", [])
                                requirements_met = len(bank.get("spelnione_wymogi", []))
                                requirements_total = requirements_met + len(bank.get("niespelnione_wymogi", []))
                            else:
                                # Stary format
                                critical_issues = bank.get("critical_issues", [])
                                requirements_met = bank.get("requirements_met", 0)
                                requirements_total = bank.get("requirements_total", 0)
                            
                            bank_info = {
                                "name": bank["bank_name"],
                                "status": "disqualified",
                                "critical_issues": critical_issues,
                                "requirements_met": requirements_met,
                                "requirements_total": requirements_total
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
                    
                    # Wymogi spełnione
                    st.caption(f"Wymogi: {bank_info['requirements_met']}/{bank_info['requirements_total']} ✅")
                
                with cols[2]:
                    # Przycisk szczegółów
                    with st.popover("📊 Szczegóły", use_container_width=True):
                        st.markdown(f"### {bank_name}")
                        
                        if bank_info.get("score"):
                            st.metric("Punktacja", f"{bank_info['score']}/100")
                        
                        st.markdown("**Główne atuty:**")
                        for reason in bank_info.get("reasons", []):
                            st.markdown(f"✓ {reason}")
                        
                        # Link do pełnego raportu
                        if st.session_state.ranking_result:
                            with st.expander("📄 Pełny raport"):
                                st.markdown(st.session_state.ranking_result)
    else:
        st.info("👈 Wprowadź profil klienta i kliknij 'Znajdź pasujące oferty'")
        st.markdown("""
        **System dwupromptowy analizuje:**
        - ✅ **ETAP 1**: Walidacja 68 WYMOGÓW (kwalifikacja)
        - 🏅 **ETAP 2**: Ranking 19 JAKOŚCI (punktacja 0-100)
        
        **Otrzymasz:**
        - Lista zakwalifikowanych banków
        - TOP 4 ranking z uzasadnieniem
        - Szczegółowe powody odrzucenia
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
                    unmet = bank_info['requirements_total'] - bank_info['requirements_met']
                    st.caption(f"Niespełnione wymogi: {unmet}")
                    
                    # Główne problemy
                    critical_issues = bank_info.get("critical_issues", [])
                    if critical_issues:
                        st.markdown("**Powody odrzucenia:**")
                        for issue in critical_issues[:2]:  # Max 2 powody
                            st.markdown(f"<span style='color: #f44336; font-size: 0.9em;'>{issue}</span>", 
                                      unsafe_allow_html=True)
                        
                        if len(critical_issues) > 2:
                            with st.expander(f"+ {len(critical_issues) - 2} więcej"):
                                for issue in critical_issues[2:]:
                                    st.markdown(f"- {issue}")
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
    
    # Wybór modelu dla ETAP 2 (Ranking)
    etap2_model = st.selectbox(
        "🏅 Model ETAP 2 (Ranking JAKOŚCI)",
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