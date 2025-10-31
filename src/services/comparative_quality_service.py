"""
Serwis do porównawczej oceny jakości kredytów (nowa strategia)
Batch scoring z dynamicznymi wagami i kontekstem rynkowym
"""
import asyncio
import logging
from typing import List, Dict, Any, TYPE_CHECKING
from ..models.structured_outputs import ComparativeQualityScore, CategoryWeights
from .prompt_loader import PromptLoader
from .response_parser import ResponseParser

if TYPE_CHECKING:
    from ..ai_client_v3 import AIClient

logger = logging.getLogger(__name__)


class ComparativeQualityService:
    """
    Porównawcza ocena jakości ofert kredytowych
    - Jeden prompt dla wszystkich zakwalifikowanych banków
    - Dynamiczne wagi dostosowane do profilu klienta
    - Benchmarking min-max z kontekstem rynkowym
    """
    
    def __init__(
        self,
        ai_client: "AIClient",  # Type hint jako string
        prompt_loader: PromptLoader,
        response_parser: ResponseParser
    ):
        self.ai_client = ai_client
        self.prompt_loader = prompt_loader
        self.response_parser = response_parser
    
    async def rate_all_banks_comparative(
        self,
        qualified_banks: List[str],
        customer_profile,
        model: str = "gpt-4.1"
    ) -> tuple[List[ComparativeQualityScore], CategoryWeights, Dict[str, Any]]:
        """
        Porównawcza ocena jakości wszystkich zakwalifikowanych banków
        
        Args:
            qualified_banks: Lista nazw banków, które przeszły walidację
            customer_profile: Profil klienta (CustomerProfile)
            model: Model LLM do użycia
            
        Returns:
            (
                ranking: Lista ComparativeQualityScore posortowana wg total_score,
                weights: CategoryWeights z optymalnymi wagami,
                market_stats: Statystyki rynkowe
            )
        """
        logger.info(f"🔄 Rozpoczynam porównawczą ocenę jakości dla {len(qualified_banks)} banków")
        
        if len(qualified_banks) == 0:
            logger.warning("⚠️ Brak zakwalifikowanych banków do oceny")
            return [], CategoryWeights(35.0, 25.0, 25.0, 15.0, "Brak banków"), {}
        
        # KROK 1: Optymalizacja wag dla tego klienta
        logger.info("📊 KROK 1/2: Optymalizacja wag kategorii...")
        weights = await self._optimize_weights(customer_profile, model)
        
        logger.info(f"✅ Wagi zoptymalizowane: Koszt={weights.koszt}%, Elastyczność={weights.elastycznosc}%, Wygoda={weights.wygoda}%, Korzyści={weights.korzysci}%")
        logger.debug(f"Uzasadnienie wag: {weights.reasoning}")
        
        # KROK 2: Porównawczy scoring wszystkich banków
        logger.info(f"🏆 KROK 2/2: Porównawczy scoring {len(qualified_banks)} banków...")
        ranking, market_stats = await self._comparative_scoring(
            qualified_banks,
            customer_profile,
            weights,
            model
        )
        
        logger.info(f"✅ Ranking zakończony. Najlepszy bank: {ranking[0].bank_name if ranking else 'BRAK'}")
        
        return ranking, weights, market_stats
    
    async def _optimize_weights(
        self,
        customer_profile,
        model: str
    ) -> CategoryWeights:
        """
        Optymalizacja wag kategorii na podstawie profilu klienta
        
        Returns:
            CategoryWeights z dostrojonymi wagami
        """
        try:
            # Buduj messages
            messages = self.prompt_loader.build_weight_optimization_messages(customer_profile)
            
            logger.debug(f"Wysyłam request optymalizacji wag. Model: {model}, Messages: {len(messages)}")
            
            # Wywołaj LLM
            response = await self.ai_client.chat_completion(
                messages=messages,
                model=model,
                response_format={"type": "json_object"}
            )
            
            logger.debug(f"Otrzymano response optymalizacji wag. Długość: {len(response)}")
            
            # Parsuj odpowiedź
            weights = self.response_parser.parse_weight_optimization(response)
            
            # Walidacja sum
            total = weights.koszt + weights.elastycznosc + weights.wygoda + weights.korzysci
            if abs(total - 100.0) > 0.1:
                logger.warning(f"⚠️ Suma wag ({total}) != 100. Normalizuję...")
                # Normalizuj
                factor = 100.0 / total
                weights.koszt *= factor
                weights.elastycznosc *= factor
                weights.wygoda *= factor
                weights.korzysci *= factor
            
            return weights
            
        except Exception as e:
            logger.error(f"❌ Błąd optymalizacji wag: {str(e)}")
            logger.warning("⚠️ Używam domyślnych wag (35/25/25/15)")
            # Fallback do domyślnych wag
            return CategoryWeights(
                koszt=35.0,
                elastycznosc=25.0,
                wygoda=25.0,
                korzysci=15.0,
                reasoning=f"Błąd optymalizacji wag: {str(e)}. Użyto wartości domyślnych."
            )
    
    async def _comparative_scoring(
        self,
        qualified_banks: List[str],
        customer_profile,
        weights: CategoryWeights,
        model: str
    ) -> tuple[List[ComparativeQualityScore], Dict[str, Any]]:
        """
        Porównawczy scoring wszystkich banków w jednym wywołaniu LLM
        
        Returns:
            (ranking: lista ComparativeQualityScore, market_stats: dict ze statystykami)
        """
        try:
            # Przygotuj wagi jako dict
            weights_dict = {
                "koszt": weights.koszt,
                "elastycznosc": weights.elastycznosc,
                "wygoda": weights.wygoda,
                "korzysci": weights.korzysci
            }
            
            # Buduj messages
            messages = self.prompt_loader.build_comparative_quality_messages(
                qualified_banks,
                customer_profile,
                weights_dict
            )
            
            logger.debug(f"Wysyłam request porównawczego scoringu. Model: {model}, Banki: {len(qualified_banks)}, Messages: {len(messages)}")
            
            # Wywołaj LLM
            response = await self.ai_client.chat_completion(
                messages=messages,
                model=model,
                response_format={"type": "json_object"},
                temperature=0.3  # Niższa temperatura dla bardziej deterministycznych wyników
            )
            
            logger.debug(f"Otrzymano response scoringu. Długość: {len(response)}")
            
            # Parsuj odpowiedź
            ranking, market_stats = self.response_parser.parse_comparative_quality(response, weights_dict)
            
            # Walidacja
            if len(ranking) != len(qualified_banks):
                logger.warning(f"⚠️ Liczba banków w rankingu ({len(ranking)}) != liczba zakwalifikowanych ({len(qualified_banks)})")
            
            # Sortuj po total_score (malejąco)
            ranking.sort(key=lambda x: x.total_score, reverse=True)
            
            # Upewnij się, że ranki są poprawne
            for i, score in enumerate(ranking, start=1):
                score.rank = i
            
            logger.info(f"✅ Ranking utworzony: {len(ranking)} banków")
            for i, score in enumerate(ranking[:3], start=1):
                logger.info(f"  {i}. {score.bank_name}: {score.total_score:.1f} pkt (percentyl: {score.percentile:.0f})")
            
            return ranking, market_stats
            
        except Exception as e:
            logger.error(f"❌ Błąd porównawczego scoringu: {str(e)}")
            logger.exception(e)
            # Zwróć puste wyniki
            return [], {}
