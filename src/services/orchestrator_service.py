"""
Serwis orkiestrujący cały proces dopasowania kredytów
Koordynuje walidację i ocenę jakości
"""
from typing import Dict, List, Optional, Literal
from .validation_service import ValidationService
from .quality_service import QualityService
from .comparative_quality_service import ComparativeQualityService


class OrchestratorService:
    """Orkiestrator dwuetapowego procesu dopasowania kredytów"""
    
    def __init__(
        self,
        validation_service: ValidationService,
        quality_service: QualityService,
        comparative_quality_service: Optional[ComparativeQualityService] = None
    ):
        """
        Inicjalizacja orkiestratora
        
        Args:
            validation_service: Serwis walidacji WYMOGÓW
            quality_service: Serwis oceny JAKOŚCI (indywidualny)
            comparative_quality_service: Serwis oceny JAKOŚCI (porównawczy)
        """
        self.validation_service = validation_service
        self.quality_service = quality_service
        self.comparative_quality_service = comparative_quality_service
    
    async def process_query(
        self,
        knowledge_base: Dict,
        user_query: str = None,
        customer_profile = None,
        etap1_model: str = None,
        etap2_model: str = None,
        quality_strategy: Literal["individual", "comparative"] = "individual",
        skip_quality_scoring: bool = False
    ) -> Dict[str, str]:
        """
        Główna metoda - dwuetapowe przetwarzanie zapytania (z opcją pominięcia ETAP 2)
        
        Args:
            knowledge_base: Pełna baza wiedzy (Dict z listą products)
            user_query: Surowy profil klienta (opcjonalny)
            customer_profile: Zmapowany profil klienta (CustomerProfile object)
            etap1_model: Model do ETAP 1 (None = domyślny)
            etap2_model: Model do ETAP 2 (None = domyślny)
            quality_strategy: Strategia scoringu jakości:
                - "individual": Każdy bank osobno (domyślnie)
                - "comparative": Porównawczy batch scoring
            skip_quality_scoring: Jeśli True, pomija ETAP 2 (tylko walidacja)
            
        Returns:
            Dict z wynikami obu etapów (lub tylko ETAP 1 jeśli skip_quality_scoring=True)
        """
        print("\n" + "="*80)
        if skip_quality_scoring:
            print("🚀 TRYB: TYLKO WALIDACJA BANKÓW (szybki)")
        else:
            print("🚀 DWUETAPOWY SYSTEM DOPASOWANIA KREDYTÓW")
        if customer_profile:
            print("📋 Tryb: ZMAPOWANY PROFIL (inteligentna walidacja)")
        else:
            print("📋 Tryb: SUROWY INPUT (pełna walidacja)")
        if not skip_quality_scoring:
            print(f"⚙️  Strategia ETAP 2: {quality_strategy.upper()}")
        print("="*80 + "\n")
        
        # ETAP 1: Walidacja WYMOGÓW (równolegle dla wszystkich banków)
        validation_response, validation_data = await self.validation_service.validate_all_banks(
            knowledge_base=knowledge_base,
            user_query=user_query,
            customer_profile=customer_profile,
            deployment_name=etap1_model
        )
        
        if not validation_data:
            return {
                "stage1_validation": validation_response,
                "stage2_ranking": "Błąd w etapie 1 - brak danych walidacji",
                "error": True,
                "qualified_banks": []
            }
        
        # Wyciągnij listę zakwalifikowanych banków
        qualified = []
        if "qualified_banks" in validation_data:
            qualified = [b.get("bank_name") for b in validation_data["qualified_banks"] if b.get("bank_name")]
        
        print(f"\n✅ Zakwalifikowane banki ({len(qualified)}): {', '.join(qualified)}\n")
        
        if len(qualified) == 0:
            return {
                "stage1_validation": validation_response,
                "stage2_ranking": "❌ Żaden bank nie spełnia wymogów klienta",
                "error": False,
                "qualified_banks": [],
                "quality_strategy": quality_strategy,
                "skip_quality_scoring": skip_quality_scoring
            }
        
        # Jeśli tryb tylko walidacji - zakończ tutaj
        if skip_quality_scoring:
            print("\n" + "="*80)
            print("✅ WALIDACJA ZAKOŃCZONA (tryb szybki - bez oceny jakości)")
            print("="*80 + "\n")
            
            return {
                "stage1_validation": validation_response,
                "stage1_data": validation_data,
                "stage2_ranking": None,  # Brak etapu 2
                "stage2_data": None,
                "error": False,
                "qualified_banks": qualified,
                "quality_strategy": None,
                "skip_quality_scoring": True
            }
        
        # ETAP 2: Ranking JAKOŚCI (wybór strategii)
        if quality_strategy == "comparative" and self.comparative_quality_service:
            # NOWA STRATEGIA: Porównawczy batch scoring
            print(f"🏆 ETAP 2: PORÓWNAWCZY SCORING dla {len(qualified)} banków\n")
            
            ranking, weights, market_stats = await self.comparative_quality_service.rate_all_banks_comparative(
                qualified_banks=qualified,
                customer_profile=customer_profile,
                model=etap2_model or "gpt-4.1"
            )
            
            # Formatuj markdown response
            ranking_response = self._format_comparative_ranking_markdown(ranking, weights, market_stats)
            
            # Strukturyzowane dane
            stage2_data = {
                "ranking": [score.to_dict() for score in ranking],
                "weights": weights.to_dict(),
                "market_stats": market_stats,
                "strategy": "comparative"
            }
            
        else:
            # STARA STRATEGIA: Indywidualny scoring każdego banku
            print(f"📊 ETAP 2: INDYWIDUALNY SCORING dla {len(qualified)} banków\n")
            
            ranking_response, quality_scores = await self.quality_service.rate_all_banks(
                knowledge_base=knowledge_base,
                qualified_banks=qualified,
                user_query=user_query,
                customer_profile=customer_profile,
                deployment_name=etap2_model
            )
            
            # Strukturyzowane dane
            stage2_data = {
                "scores": [score.to_dict() for score in quality_scores],
                "strategy": "individual"
            }
        
        print("\n" + "="*80)
        print("✅ ANALIZA ZAKOŃCZONA")
        print("="*80 + "\n")
        
        return {
            "stage1_validation": validation_response,
            "stage1_data": validation_data,  # Dict z qualified_banks, disqualified_banks
            "stage2_ranking": ranking_response,
            "stage2_data": stage2_data,
            "error": False,
            "qualified_banks": qualified,
            "quality_strategy": quality_strategy
        }
    
    def _format_comparative_ranking_markdown(
        self,
        ranking: List,
        weights,
        market_stats: Dict
    ) -> str:
        """
        Formatuje wyniki porównawczego rankingu do Markdown
        
        Args:
            ranking: Lista ComparativeQualityScore
            weights: CategoryWeights
            market_stats: Statystyki rynkowe
            
        Returns:
            Markdown string z rankingiem
        """
        if not ranking:
            return "❌ Brak wyników rankingu"
        
        lines = []
        lines.append("# 🏆 RANKING JAKOŚCI (Porównawczy)\n")
        lines.append(f"**Strategia:** Benchmarking wszystkich {len(ranking)} banków z dynamicznymi wagami\n")
        lines.append(f"**Wagi kategorii:**")
        lines.append(f"- 💰 Koszt: {weights.koszt:.0f}%")
        lines.append(f"- 🔄 Elastyczność: {weights.elastycznosc:.0f}%")
        lines.append(f"- ⚡ Wygoda: {weights.wygoda:.0f}%")
        lines.append(f"- 🎁 Korzyści: {weights.korzysci:.0f}%\n")
        lines.append(f"_{weights.reasoning}_\n")
        lines.append("---\n")
        
        # TOP 3 szczegółowo
        for i, score in enumerate(ranking[:3], start=1):
            emoji = ["🥇", "🥈", "🥉"][i-1]
            lines.append(f"## {emoji} MIEJSCE {i}: {score.bank_name}\n")
            lines.append(f"**Ocena:** {score.total_score:.1f}/100 pkt (TOP {100-score.percentile:.0f}%)\n")
            
            lines.append(f"### Breakdown:")
            lines.append(f"- 💰 Koszt: {score.cost_score:.0f}/100 (waga {score.cost_weight:.0f}%)")
            lines.append(f"- 🔄 Elastyczność: {score.flexibility_score:.0f}/100 (waga {score.flexibility_weight:.0f}%)")
            lines.append(f"- ⚡ Wygoda: {score.convenience_score:.0f}/100 (waga {score.convenience_weight:.0f}%)")
            lines.append(f"- 🎁 Korzyści: {score.benefits_score:.0f}/100 (waga {score.benefits_weight:.0f}%)\n")
            
            if score.strengths:
                lines.append(f"### ✅ Mocne strony:")
                for strength in score.strengths:
                    lines.append(f"- {strength}")
                lines.append("")
            
            if score.competitive_advantages:
                lines.append(f"### ⭐ Przewagi konkurencyjne:")
                for advantage in score.competitive_advantages:
                    lines.append(f"- {advantage}")
                lines.append("")
            
            if score.weaknesses:
                lines.append(f"### ⚠️ Słabsze niż konkurencja:")
                for weakness in score.weaknesses:
                    lines.append(f"- {weakness}")
                lines.append("")
            
            lines.append(f"**Uzasadnienie:** {score.reasoning}\n")
            lines.append("---\n")
        
        # Pozostałe banki (tabela)
        if len(ranking) > 3:
            lines.append(f"## 📊 Pozostałe banki\n")
            lines.append("| Pozycja | Bank | Ocena | Percentyl |")
            lines.append("|---------|------|-------|-----------|")
            for score in ranking[3:]:
                lines.append(f"| #{score.rank} | {score.bank_name} | {score.total_score:.1f} | TOP {100-score.percentile:.0f}% |")
            lines.append("")
        
        # Statystyki rynku
        if market_stats:
            lines.append(f"## 📈 Statystyki rynku\n")
            if "avg_total_score" in market_stats:
                lines.append(f"- Średnia ocena: {market_stats['avg_total_score']:.1f}/100")
            if "median_total_score" in market_stats:
                lines.append(f"- Mediana: {market_stats['median_total_score']:.1f}/100")
            if "best_bank" in market_stats and "worst_bank" in market_stats:
                lines.append(f"- Najlepszy: {market_stats['best_bank']}")
                lines.append(f"- Najgorszy: {market_stats['worst_bank']}")
            lines.append("")
        
        return "\n".join(lines)
