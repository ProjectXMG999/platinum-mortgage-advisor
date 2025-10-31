# -*- coding: utf-8 -*-
"""Skrypt do naprawy UI w main.py"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Znajdź i zamień sekcję ETAP 2
old_etap2 = '''                        # ETAP 2: Punktacja jakości
                        if bank_info.get("score"):
                            st.markdown("#### 🏅 ETAP 2: Ocena Jakości")
                            st.metric("Punktacja końcowa", f"{bank_info['score']}/100 pkt")
                            
                            # Breakdown według kategorii
                            if bank_info.get("category_breakdown"):
                                st.markdown("**Rozbicie punktacji:**")
                                for category, score in bank_info["category_breakdown"].items():
                                    # Pasek postępu
                                    progress_value = score / 100 if score <= 100 else 1.0
                                    st.markdown(f"- **{category}**: {score} pkt")
                                    st.progress(progress_value)
                            
                            st.markdown("**Główne atuty:**")
                            for reason in bank_info.get("reasons", [])[:5]:
                                st.markdown(f"✓ {reason}")'''

new_etap2 = '''                        # ETAP 2: Punktacja jakości
                        if bank_info.get("score"):
                            st.markdown("#### 🏅 ETAP 2: Ocena Jakości")
                            
                            col_a, col_b = st.columns([2, 1])
                            with col_a:
                                st.metric("Punktacja końcowa", f"{bank_info['score']}/100 pkt")
                            with col_b:
                                if bank_info['score'] >= 80:
                                    st.markdown("### 🌟")
                                elif bank_info['score'] >= 60:
                                    st.markdown("### ✅")
                                else:
                                    st.markdown("### ⚠️")
                            
                            if bank_info.get("category_breakdown"):
                                st.markdown("**📊 Rozbicie punktacji:**")
                                breakdown = bank_info["category_breakdown"]
                                
                                cols_breakdown = st.columns(2)
                                items = list(breakdown.items())
                                mid = (len(items) + 1) // 2
                                
                                with cols_breakdown[0]:
                                    for category, score in items[:mid]:
                                        st.markdown(f"**{category}**: {score} pkt")
                                        st.progress(score / 50 if score <= 50 else 1.0)
                                
                                with cols_breakdown[1]:
                                    for category, score in items[mid:]:
                                        st.markdown(f"**{category}**: {score} pkt")
                                        st.progress(score / 50 if score <= 50 else 1.0)
                            
                            if bank_info.get("key_strengths"):
                                st.markdown("**✅ Kluczowe atuty:**")
                                for atut in bank_info["key_strengths"][:5]:
                                    st.markdown(f"- {atut}")
                            
                            if bank_info.get("key_weaknesses"):
                                st.markdown("**⚠️ Punkty uwagi:**")
                                for uwaga in bank_info["key_weaknesses"][:3]:
                                    st.markdown(f"- {uwaga}")
                            
                            if bank_info.get("scoring_method"):
                                with st.expander("🔍 Metodologia oceny"):
                                    st.caption(bank_info["scoring_method"])'''

content = content.replace(old_etap2, new_etap2)

# Znajdź i zamień sekcję ETAP 1
old_etap1 = '''                        # ETAP 1: Walidacja wymogów
                        st.markdown("#### ✅ ETAP 1: Walidacja Wymogów")
                        sprawdzone = bank_info.get("sprawdzone_wymogi", [])
                        st.metric("Sprawdzone wymogi", f"{len(sprawdzone)}")
                        
                        with st.expander("📋 Szczegóły walidacji"):
                            for wymog in sprawdzone:
                                st.markdown(f"✓ {wymog}")'''

new_etap1 = '''                        # ETAP 1: Walidacja wymogów
                        st.markdown("#### ✅ ETAP 1: Walidacja Wymogów")
                        sprawdzone = bank_info.get("sprawdzone_wymogi", [])
                        
                        if sprawdzone:
                            st.success(f"**Sprawdzono {len(sprawdzone)} wymogów - wszystkie spełnione** ✅")
                            
                            with st.expander(f"📋 Szczegóły walidacji ({len(sprawdzone)} wymogów)"):
                                for i, wymog in enumerate(sprawdzone, 1):
                                    st.markdown(f"{i}. ✓ {wymog}")
                        else:
                            st.info("Brak szczegółowych danych walidacji")'''

content = content.replace(old_etap1, new_etap1)

# Zapisz
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Zaktualizowano main.py")
