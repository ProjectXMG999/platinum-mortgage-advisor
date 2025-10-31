"""
Ranking Service - ETAP 3: Szczegółowy ranking TOP 3 banków
"""
from typing import List, Dict
from src.models.structured_outputs import QualityScore, ValidationResult, DetailedRanking
from src.services.response_parser import ResponseParser


class RankingService:
    """Generuje szczegółowy ranking TOP 3 banków z uzasadnieniem"""
    
    def __init__(self, ai_client, prompt_loader):
        """
        Inicjalizacja serwisu rankingu
        
        Args:
            ai_client: Klient Azure OpenAI
            prompt_loader: Loader promptów
        """
        self.ai_client = ai_client
        self.prompt_loader = prompt_loader
        self.response_parser = ResponseParser()
    
    async def generate_detailed_ranking(
        self,
        top_banks: List[str],
        customer_profile,
        validation_results: List[ValidationResult],
        quality_scores: List[QualityScore],
        deployment_name: str = None
    ) -> DetailedRanking:
        """
        ETAP 3: Generuje szczegółowy ranking TOP 3 banków
        
        Args:
            top_banks: Lista nazw TOP 3 banków (w kolejności malejącej)
            customer_profile: CustomerProfile object
            validation_results: Wszystkie wyniki walidacji
            quality_scores: Wszystkie wyniki jakości
            deployment_name: Opcjonalny model do użycia
            
        Returns:
            DetailedRanking object
        """
        print(f"\n🏆 ETAP 3: Szczegółowy ranking TOP {len(top_banks[:3])} banków...")
        
        # Przygotuj dane dla promptu
        validation_dicts = [v.to_dict() for v in validation_results]
        quality_dicts = [q.to_dict() for q in quality_scores]
        
        # Zbuduj messages używając prompt_loader
        messages = self.prompt_loader.build_ranking_messages(
            top_banks=top_banks,
            customer_profile=customer_profile,
            validation_results=validation_dicts,
            quality_scores=quality_dicts
        )
        
        # Wybierz model
        model = deployment_name or self.ai_client.deployment_name
        
        # Przygotuj parametry completion
        completion_params = {
            "model": model,
            "messages": messages,
        }
        
        # Dostosuj parametry do typu modelu
        model_lower = model.lower()
        if "gpt-5" in model_lower or "o4" in model_lower or "o1" in model_lower:
            completion_params["temperature"] = 1.0
            completion_params["max_completion_tokens"] = 4000
        else:
            completion_params["temperature"] = 0.3  # Niższa dla precyzji
            completion_params["max_tokens"] = 4000
        
        try:
            # Wywołaj API
            response = await self.ai_client.async_client.chat.completions.create(**completion_params)
            result_text = response.choices[0].message.content
            
            # Parsuj markdown do DetailedRanking
            ranking = self.response_parser.parse_ranking_response(
                response=result_text,
                top_banks=top_banks
            )
            
            print(f"✓ Wygenerowano szczegółowy ranking dla TOP {len(ranking.top_banks)}")
            
            return ranking
            
        except Exception as e:
            print(f"⚠️ Błąd generowania rankingu: {e}")
            
            # Zwróć fallback ranking
            return DetailedRanking(
                top_banks=top_banks[:3],
                recommendations={},
                comparison_table="",
                final_recommendation=f"Błąd generowania rankingu: {str(e)}",
                analysis_summary=""
            )
    
    def format_ranking_to_markdown(self, ranking: DetailedRanking) -> str:
        """
        Formatuje DetailedRanking do markdown
        
        Args:
            ranking: DetailedRanking object
            
        Returns:
            Markdown string
        """
        return ranking.to_markdown()
