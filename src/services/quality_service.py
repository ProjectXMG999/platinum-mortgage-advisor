"""
Serwis do oceny JAKOŚCI banków (ETAP 2)
Używa ContextLoader i PromptLoader z dynamicznym kontekstem JAKOŚĆ
"""
import json
import asyncio
from typing import Dict, List
from .prompt_loader import PromptLoader
from .response_parser import ResponseParser
from src.models.structured_outputs import QualityScore


class QualityService:
    """Ocena JAKOŚCI - ranking zakwalifikowanych banków"""
    
    def __init__(self, ai_client, prompt_loader: PromptLoader):
        """
        Inicjalizacja serwisu jakości
        
        Args:
            ai_client: Klient Azure OpenAI
            prompt_loader: Loader promptów (z ContextLoader)
        """
        self.ai_client = ai_client
        self.prompt_loader = prompt_loader
        self.response_parser = ResponseParser()
    
    async def rate_single_bank(
        self,
        bank_name: str,
        bank_data: Dict = None,  # Deprecated - używamy ContextLoader
        user_query: str = None,
        customer_profile = None,
        deployment_name: str = None
    ) -> QualityScore:
        """
        Ocenia jakość pojedynczego banku (0-100 pkt)
        
        Args:
            bank_name: Nazwa banku
            bank_data: DEPRECATED - nie używane (kontekst z ContextLoader)
            user_query: Surowy profil klienta (opcjonalny)
            customer_profile: Zmapowany profil klienta (CustomerProfile object)
            deployment_name: Model do użycia (None = domyślny)
            
        Returns:
            QualityScore object
        """
        if not customer_profile:
            raise ValueError("customer_profile jest wymagany (zmapowany profil klienta)")
        
        # Zbuduj messages używając PromptLoader (dynamiczny kontekst JAKOŚĆ)
        messages = self.prompt_loader.build_quality_messages(
            bank_name=bank_name,
            customer_profile=customer_profile
        )
        
        # Wybierz model
        model = deployment_name or self.ai_client.deployment_name
        
        # DEBUG: Pokaż strukturę messages PRZED wysłaniem
        print(f"\n{'='*80}")
        print(f"🔍 DEBUG PRZED API - {bank_name}")
        print(f"{'='*80}")
        print(f"Model: {model}")
        print(f"Liczba messages: {len(messages)}")
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:200]
            print(f"  Message {i}: role={role}, content_preview={content_preview}...")
        print(f"{'='*80}\n")
        
        # Przygotuj parametry completion
        completion_params = {
            "model": model,
            "messages": messages,
        }
        
        # Dostosuj parametry do typu modelu
        model_lower = model.lower()
        if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
            completion_params["temperature"] = 1.0
            completion_params["max_completion_tokens"] = 3000
            # o1 NIE obsługuje response_format, ale prompt wymaga JSON
            print(f"⚙️ Model reasoning ({model}) - NO response_format")
        else:
            completion_params["temperature"] = 0.1
            completion_params["max_tokens"] = 3000
            # TYLKO dla GPT-4: Wymuś JSON mode
            completion_params["response_format"] = {"type": "json_object"}
            print(f"⚙️ Model GPT-4 ({model}) - response_format = json_object")
        
        try:
            print(f"📡 Wysyłam request do Azure OpenAI dla {bank_name}...")
            # Wywołaj API
            response = await self.ai_client.async_client.chat.completions.create(**completion_params)
            print(f"✅ Otrzymano odpowiedź dla {bank_name}")
            print(f"✅ Otrzymano odpowiedź dla {bank_name}")
            result_text = response.choices[0].message.content
            
            # DEBUG: Pokaż co zwrócił model
            print(f"\n{'='*80}")
            print(f"🔍 DEBUG ODPOWIEDŹ - {bank_name}")
            print(f"{'='*80}")
            print(f"Długość odpowiedzi: {len(result_text)} znaków")
            print(f"Pierwsze 800 znaków:")
            print(result_text[:800])
            if len(result_text) > 800:
                print(f"\n... (+ {len(result_text) - 800} znaków)")
            print(f"{'='*80}\n")
            
            # Parsuj JSON do QualityScore
            print(f"🔧 Parsowanie JSON dla {bank_name}...")
            quality_score = self.response_parser.parse_quality_response(
                response=result_text,
                bank_name=bank_name
            )
            print(f"✅ Parsing OK - Score: {quality_score.total_score}/100")
            
            return quality_score
                
        except Exception as e:
            print(f"\n❌ EXCEPTION w rate_single_bank dla {bank_name}!")
            print(f"   Typ błędu: {type(e).__name__}")
            print(f"   Komunikat: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return QualityScore(
                bank_name=bank_name,
                total_score=0,
                scoring_method="ERROR",
                notes=f"API error: {str(e)}"
            )
    
    async def rate_all_banks(
        self,
        knowledge_base: Dict = None,  # Deprecated - używamy ContextLoader
        qualified_banks: List[str] = None,
        user_query: str = None,
        customer_profile = None,
        deployment_name: str = None
    ) -> str:
        """
        Ocenia wszystkie zakwalifikowane banki równolegle
        
        Args:
            knowledge_base: DEPRECATED - nie używane (kontekst z ContextLoader)
            qualified_banks: Lista nazw zakwalifikowanych banków (opcjonalne - wszystkie jeśli None)
            user_query: Surowy profil klienta (opcjonalny)
            customer_profile: Zmapowany profil klienta (CustomerProfile object)
            deployment_name: Model do użycia
            
        Returns:
            Markdown z rankingiem TOP 4
        """
        if not customer_profile:
            raise ValueError("customer_profile jest wymagany")
        
        # Jeśli nie podano qualified_banks, użyj wszystkich banków
        if not qualified_banks:
            qualified_banks = list(self.prompt_loader.context_loader.knowledge_base.keys())
        
        print(f"🏅 ETAP 2: Ranking JAKOŚCI (PARALLEL MODE - {len(qualified_banks)} banków)...")
        
        # Przygotuj taski dla każdego banku
        tasks = [
            self.rate_single_bank(
                bank_name=bank_name,
                bank_data=None,  # Deprecated
                user_query=user_query,
                customer_profile=customer_profile,
                deployment_name=deployment_name
            )
            for bank_name in qualified_banks
        ]
        
        # Wykonaj równolegle
        print(f"⚡ Uruchamiam {len(tasks)} równoległych requestów oceny jakości...")
        results: List[QualityScore] = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtruj błędy (wyjątki)
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Błąd oceny {qualified_banks[i]}: {result}")
            else:
                valid_results.append(result)
        
        # Sortuj po total_score (malejąco)
        valid_results.sort(key=lambda x: x.total_score, reverse=True)
        
        print(f"✓ Pomyślnie oceniono {len(valid_results)}/{len(qualified_banks)} banków")
        
        # Formatuj TOP 4 do markdown
        markdown = self._format_ranking_markdown(
            valid_results[:4],
            user_query or "profil klienta"
        )
        
        # Zwróć markdown oraz surowe dane QualityScore
        return markdown, valid_results
    
    def _format_ranking_markdown(self, top_banks: List[QualityScore], user_query: str) -> str:
        """
        Formatuje wyniki rankingu do markdown (TOP 4)
        
        Args:
            top_banks: Lista QualityScore objects (max 4)
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
            medal = medals[i] if i < len(medals) else "🏅"
            position = positions[i] if i < len(positions) else f"{i+1}. OPCJA"
            
            lines.append(f"## {medal} {position}: {bank.bank_name}")
            lines.append("")
            lines.append(f"**Ocena końcowa: {bank.total_score}/100 pkt**")
            lines.append("")
            
            # Breakdown punktów (Dict[str, int])
            if bank.category_scores:
                lines.append("### 📊 Rozbicie punktacji:")
                lines.append("")
                for category_name, score in bank.category_scores.items():
                    lines.append(f"- {category_name}: {score} pkt")
                lines.append("")
            
            # Kluczowe atuty
            if bank.key_strengths:
                lines.append("### ✅ Kluczowe atuty:")
                lines.append("")
                for atut in bank.key_strengths[:5]:
                    lines.append(f"- {atut}")
                lines.append("")
            
            # Punkty uwagi
            if bank.key_weaknesses:
                lines.append("### ⚠️ Punkty uwagi:")
                lines.append("")
                for uwaga in bank.key_weaknesses[:3]:
                    lines.append(f"- {uwaga}")
                lines.append("")
            
            # Scoring method
            if bank.scoring_method:
                lines.append(f"*Metodologia: {bank.scoring_method}*")
                lines.append("")
            
            lines.append("-"*80)
            lines.append("")
        
        # Tabela porównawcza
        if len(top_banks) > 1:
            lines.append("## 📋 TABELA PORÓWNAWCZA")
            lines.append("")
            lines.append("| Pozycja | Bank | Ocena | Kategorie |")
            lines.append("|---------|------|-------|-----------|")
            
            for i, bank in enumerate(top_banks):
                medal = medals[i] if i < len(medals) else "🏅"
                # category_scores to Dict[str, int]
                categories_str = ", ".join([f"{k}:{v}" for k, v in list(bank.category_scores.items())[:3]]) if bank.category_scores else ""
                lines.append(
                    f"| {medal} | {bank.bank_name} | "
                    f"{bank.total_score}/100 | "
                    f"{categories_str} |"
                )
            
            lines.append("")
        
        # Rekomendacja końcowa
        if top_banks:
            best_bank = top_banks[0]
            lines.append("## 💡 REKOMENDACJA")
            lines.append("")
            lines.append(f"Najlepsza oferta: **{best_bank.bank_name}** "
                        f"({best_bank.total_score}/100 pkt)")
            lines.append("")
            
            if best_bank.key_strengths:
                lines.append("Główne zalety:")
                for atut in best_bank.key_strengths[:3]:
                    lines.append(f"- {atut}")
        
        return "\n".join(lines)
