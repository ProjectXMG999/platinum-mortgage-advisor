"""
Response Parser - Parsowanie i walidacja odpowiedzi LLM
Konwersja JSON na strukturyzowane modele
"""
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from src.models.structured_outputs import (
    ValidationResult,
    QualityScore,
    DetailedRanking,
    RequirementCheck,
    ParameterScore,
    ComparativeQualityScore,
    CategoryWeights
)


class ResponseParser:
    """Parsuje i waliduje odpowiedzi LLM do strukturyzowanych modeli"""
    
    def __init__(self):
        """Inicjalizacja parsera"""
        pass
    
    def _clean_json_response(self, response: str) -> str:
        """
        Czyści odpowiedź z markdown i przygotowuje do parsowania JSON
        
        Args:
            response: Surowa odpowiedź z LLM
            
        Returns:
            Wyczyszczony JSON string
        """
        result_clean = response.strip()
        
        # Usuń markdown code blocks
        if result_clean.startswith("```json"):
            result_clean = result_clean[7:]
        elif result_clean.startswith("```"):
            result_clean = result_clean[3:]
        
        if result_clean.endswith("```"):
            result_clean = result_clean[:-3]
        
        result_clean = result_clean.strip()
        
        # NOWA LOGIKA: Jeśli nadal nie wygląda jak JSON, spróbuj wyciągnąć z markdown
        if not result_clean.startswith("{"):
            # Szukaj JSON między ```json...``` lub pierwszego { do ostatniego }
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_clean, re.DOTALL)
            if json_match:
                result_clean = json_match.group(1)
            else:
                # Znajdź pierwszy { i ostatni }
                start_idx = result_clean.find("{")
                end_idx = result_clean.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    result_clean = result_clean[start_idx:end_idx+1]
        
        return result_clean.strip()
    
    def parse_validation_response(
        self,
        response: str,
        bank_name: str = ""
    ) -> Optional[ValidationResult]:
        """
        Parsuje JSON z walidacji do ValidationResult
        
        Args:
            response: Odpowiedź LLM (JSON)
            bank_name: Nazwa banku (fallback)
            
        Returns:
            ValidationResult object lub None przy błędzie
        """
        try:
            # Wyczyść i parsuj JSON
            clean_json = self._clean_json_response(response)
            data = json.loads(clean_json)
            
            # Konwertuj na ValidationResult
            return ValidationResult.from_dict(data)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Błąd parsowania JSON walidacji dla {bank_name}: {e}")
            print(f"   Pierwsze 200 znaków: {response[:200]}")
            
            # Zwróć ERROR result
            return ValidationResult(
                bank_name=bank_name,
                status="ERROR",
                notes=f"JSON parse error: {str(e)}"
            )
        
        except Exception as e:
            print(f"⚠️ Nieoczekiwany błąd parsowania walidacji dla {bank_name}: {e}")
            return ValidationResult(
                bank_name=bank_name,
                status="ERROR",
                notes=f"Parse error: {str(e)}"
            )
    
    def parse_quality_response(
        self,
        response: str,
        bank_name: str = ""
    ) -> Optional[QualityScore]:
        """
        Parsuje JSON z oceny jakości do QualityScore
        
        Args:
            response: Odpowiedź LLM (JSON)
            bank_name: Nazwa banku (fallback)
            
        Returns:
            QualityScore object lub None przy błędzie
        """
        try:
            # Wyczyść i parsuj JSON
            clean_json = self._clean_json_response(response)
            data = json.loads(clean_json)
            
            # Konwertuj na QualityScore
            return QualityScore.from_dict(data)
            
        except json.JSONDecodeError as e:
            print(f"❌ BŁĄD PARSOWANIA JSON dla {bank_name}")
            print(f"   JSONDecodeError: {e}")
            print(f"   Pierwsze 500 znaków odpowiedzi:")
            print(f"   {response[:500]}")
            raise
        
        except Exception as e:
            print(f"❌ BŁĄD parsowania jakości dla {bank_name}: {e}")
            print(f"   Typ błędu: {type(e).__name__}")
            raise
    
    def parse_ranking_response(
        self,
        response: str,
        top_banks: list
    ) -> DetailedRanking:
        """
        Parsuje odpowiedź markdown z rankingu TOP 3
        
        Args:
            response: Odpowiedź LLM (markdown)
            top_banks: Lista nazw TOP banków
            
        Returns:
            DetailedRanking object
        """
        try:
            # Response jest już w markdown - nie parsujemy JSON
            # Wyodrębniamy sekcje
            
            recommendations = {}
            comparison_table = ""
            final_recommendation = ""
            analysis_summary = ""
            
            # Regex dla sekcji
            # Rekomendacje dla każdego banku
            for i, bank_name in enumerate(top_banks[:3]):
                medals = ["🥇", "🥈", "🥉"]
                medal = medals[i]
                
                # Szukaj sekcji dla tego banku
                pattern = rf"##\s*{re.escape(medal)}.*?{re.escape(bank_name)}(.*?)(?=##|$)"
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                
                if match:
                    recommendations[bank_name] = match.group(1).strip()
            
            # Tabela porównawcza
            table_match = re.search(r"##\s*📊\s*TABELA PORÓWNAWCZA(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
            if table_match:
                comparison_table = table_match.group(1).strip()
            
            # Finalna rekomendacja
            final_match = re.search(r"##\s*💡\s*FINALNA REKOMENDACJA(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
            if final_match:
                final_recommendation = final_match.group(1).strip()
            
            # Podsumowanie
            summary_match = re.search(r"##\s*📋\s*PODSUMOWANIE(.*?)$", response, re.DOTALL | re.IGNORECASE)
            if summary_match:
                analysis_summary = summary_match.group(1).strip()
            
            return DetailedRanking(
                top_banks=top_banks[:3],
                recommendations=recommendations,
                comparison_table=comparison_table,
                final_recommendation=final_recommendation,
                analysis_summary=analysis_summary
            )
            
        except Exception as e:
            print(f"⚠️ Błąd parsowania rankingu: {e}")
            
            # Zwróć podstawowy ranking
            return DetailedRanking(
                top_banks=top_banks[:3],
                recommendations={},
                comparison_table="",
                final_recommendation=response[:500],  # Pierwsze 500 znaków
                analysis_summary=f"Parse error: {str(e)}"
            )
    
    def validate_json_schema(self, data: Dict, schema_type: str) -> bool:
        """
        Waliduje czy JSON ma wymagane pola
        
        Args:
            data: Sparsowany JSON
            schema_type: "validation" lub "quality"
            
        Returns:
            True jeśli schema poprawna
        """
        if schema_type == "validation":
            required_fields = ["bank_name", "status"]
            return all(field in data for field in required_fields)
        
        elif schema_type == "quality":
            required_fields = ["bank_name", "total_score"]
            return all(field in data for field in required_fields)
        
        return False
    
    def extract_bank_name_from_response(self, response: str) -> Optional[str]:
        """
        Próbuje wyciągnąć nazwę banku z odpowiedzi (fallback)
        
        Args:
            response: Odpowiedź LLM
            
        Returns:
            Nazwa banku lub None
        """
        try:
            data = json.loads(self._clean_json_response(response))
            return data.get("bank_name")
        except:
            # Regex fallback
            match = re.search(r'"bank_name":\s*"([^"]+)"', response)
            if match:
                return match.group(1)
            return None
    
    def parse_weight_optimization(self, response: str) -> CategoryWeights:
        """
        Parsuje odpowiedź LLM z optymalizacji wag kategorii
        
        Args:
            response: Odpowiedź LLM (JSON)
            
        Returns:
            CategoryWeights z dostrojonymi wagami
        """
        try:
            data = json.loads(self._clean_json_response(response))
            
            # Pobierz wagi
            wagi = data.get("wagi", {})
            
            return CategoryWeights(
                koszt=float(wagi.get("koszt", 35.0)),
                elastycznosc=float(wagi.get("elastycznosc", 25.0)),
                wygoda=float(wagi.get("wygoda", 25.0)),
                korzysci=float(wagi.get("korzysci", 15.0)),
                reasoning=data.get("uzasadnienie", data.get("reasoning", ""))
            )
            
        except Exception as e:
            # Fallback do domyślnych wag
            return CategoryWeights(
                koszt=35.0,
                elastycznosc=25.0,
                wygoda=25.0,
                korzysci=15.0,
                reasoning=f"Błąd parsowania wag: {str(e)}. Użyto wartości domyślnych."
            )
    
    def parse_comparative_quality(
        self,
        response: str,
        weights: Dict[str, float]
    ) -> Tuple[List[ComparativeQualityScore], Dict[str, Any]]:
        """
        Parsuje odpowiedź LLM z porównawczego scoringu jakości
        
        Args:
            response: Odpowiedź LLM (JSON)
            weights: Wagi kategorii {"koszt": 35.0, ...}
            
        Returns:
            (ranking: lista ComparativeQualityScore, market_stats: dict ze statystykami)
        """
        try:
            data = json.loads(self._clean_json_response(response))
            
            ranking_data = data.get("ranking", [])
            market_stats = data.get("market_statistics", {})
            
            # Parsuj ranking
            ranking = []
            for item in ranking_data:
                score = ComparativeQualityScore(
                    bank_name=item.get("bank_name", ""),
                    total_score=float(item.get("total_score", 0.0)),
                    cost_score=float(item.get("cost_score", 0.0)),
                    cost_weight=float(item.get("cost_weight", weights.get("koszt", 35.0))),
                    flexibility_score=float(item.get("flexibility_score", 0.0)),
                    flexibility_weight=float(item.get("flexibility_weight", weights.get("elastycznosc", 25.0))),
                    convenience_score=float(item.get("convenience_score", 0.0)),
                    convenience_weight=float(item.get("convenience_weight", weights.get("wygoda", 25.0))),
                    benefits_score=float(item.get("benefits_score", 0.0)),
                    benefits_weight=float(item.get("benefits_weight", weights.get("korzysci", 15.0))),
                    rank=int(item.get("rank", 0)),
                    percentile=float(item.get("percentile", 0.0)),
                    strengths=item.get("strengths", item.get("zalety", [])),
                    weaknesses=item.get("weaknesses", item.get("wady", [])),
                    competitive_advantages=item.get("competitive_advantages", item.get("przewagi_konkurencyjne", [])),
                    better_than=item.get("better_than", item.get("lepsza_niz", [])),
                    worse_than=item.get("worse_than", item.get("gorsza_niz", [])),
                    reasoning=item.get("reasoning", item.get("uzasadnienie", ""))
                )
                ranking.append(score)
            
            return ranking, market_stats
            
        except Exception as e:
            # Zwróć puste wyniki w przypadku błędu
            return [], {"error": f"Błąd parsowania: {str(e)}"}
