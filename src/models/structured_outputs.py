"""
Strukturyzowane modele danych dla wyników każdego etapu procesu
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


@dataclass
class CategoryWeights:
    """Dynamicznie dostrojone wagi kategorii jakości"""
    koszt: float  # 0-100 (zwykle ~35)
    elastycznosc: float  # 0-100 (zwykle ~25)
    wygoda: float  # 0-100 (zwykle ~25)
    korzysci: float  # 0-100 (zwykle ~15)
    reasoning: str  # Dlaczego takie wagi dla tego klienta
    
    def to_dict(self) -> Dict:
        return {
            "koszt": self.koszt,
            "elastycznosc": self.elastycznosc,
            "wygoda": self.wygoda,
            "korzysci": self.korzysci,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CategoryWeights':
        return cls(
            koszt=data.get("koszt", 35.0),
            elastycznosc=data.get("elastycznosc", 25.0),
            wygoda=data.get("wygoda", 25.0),
            korzysci=data.get("korzysci", 15.0),
            reasoning=data.get("reasoning", data.get("uzasadnienie", ""))
        )


@dataclass
class ComparativeQualityScore:
    """Wynik porównawczej oceny jakości (nowa strategia)"""
    bank_name: str
    
    # SCORING ABSOLUTNY (znormalizowany 0-100)
    total_score: float  # Suma ważona kategorii
    
    # BREAKDOWN KATEGORII (z dynamicznymi wagami)
    cost_score: float  # 0-100
    cost_weight: float  # Waga w % (np. 35.0)
    flexibility_score: float  # 0-100
    flexibility_weight: float  # Waga w %
    convenience_score: float  # 0-100
    convenience_weight: float  # Waga w %
    benefits_score: float  # 0-100
    benefits_weight: float  # Waga w %
    
    # KONTEKST PORÓWNAWCZY
    rank: int  # Pozycja w rankingu (1-N)
    percentile: float  # Percentyl na tle rynku (0-100)
    
    # ANALIZA JAKOŚCIOWA
    strengths: List[str] = field(default_factory=list)  # Co wyróżnia pozytywnie
    weaknesses: List[str] = field(default_factory=list)  # Co przegrywa z konkurencją
    competitive_advantages: List[str] = field(default_factory=list)  # Unikalne przewagi
    
    # RELATYWNY KONTEKST
    better_than: List[str] = field(default_factory=list)  # Lista banków gorszych
    worse_than: List[str] = field(default_factory=list)  # Lista banków lepszych
    
    # UZASADNIENIE
    reasoning: str = ""  # Dlaczego taki wynik
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "bank_name": self.bank_name,
            "total_score": self.total_score,
            "cost_score": self.cost_score,
            "cost_weight": self.cost_weight,
            "flexibility_score": self.flexibility_score,
            "flexibility_weight": self.flexibility_weight,
            "convenience_score": self.convenience_score,
            "convenience_weight": self.convenience_weight,
            "benefits_score": self.benefits_score,
            "benefits_weight": self.benefits_weight,
            "rank": self.rank,
            "percentile": self.percentile,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "competitive_advantages": self.competitive_advantages,
            "better_than": self.better_than,
            "worse_than": self.worse_than,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ComparativeQualityScore':
        return cls(
            bank_name=data.get("bank_name", ""),
            total_score=data.get("total_score", 0.0),
            cost_score=data.get("cost_score", 0.0),
            cost_weight=data.get("cost_weight", 35.0),
            flexibility_score=data.get("flexibility_score", 0.0),
            flexibility_weight=data.get("flexibility_weight", 25.0),
            convenience_score=data.get("convenience_score", 0.0),
            convenience_weight=data.get("convenience_weight", 25.0),
            benefits_score=data.get("benefits_score", 0.0),
            benefits_weight=data.get("benefits_weight", 15.0),
            rank=data.get("rank", 0),
            percentile=data.get("percentile", 0.0),
            strengths=data.get("strengths", data.get("zalety", [])),
            weaknesses=data.get("weaknesses", data.get("wady", [])),
            competitive_advantages=data.get("competitive_advantages", data.get("przewagi_konkurencyjne", [])),
            better_than=data.get("better_than", data.get("lepsza_niz", [])),
            worse_than=data.get("worse_than", data.get("gorsza_niz", [])),
            reasoning=data.get("reasoning", data.get("uzasadnienie", ""))
        )


@dataclass
class RequirementCheck:
    """Pojedyncze sprawdzenie wymogu"""
    category: str  # "02_kredytobiorca", "03_źródło_dochodu", etc.
    parameter: str  # Nazwa parametru
    client_value: Any  # Wartość podana przez klienta
    bank_requirement: str  # Wymóg banku
    status: Literal["PASS", "FAIL", "SKIPPED"]
    reasoning: str  # Uzasadnienie decyzji
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "parameter": self.parameter,
            "client_value": self.client_value,
            "bank_requirement": self.bank_requirement,
            "status": self.status,
            "reasoning": self.reasoning
        }


@dataclass
class ValidationResult:
    """Wynik walidacji pojedynczego banku (ETAP 1)"""
    bank_name: str
    status: Literal["QUALIFIED", "DISQUALIFIED", "ERROR"]
    checked_requirements: List[RequirementCheck] = field(default_factory=list)
    skipped_requirements: List[str] = field(default_factory=list)
    disqualification_reasons: List[str] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Nowe pole - oryginalne stringi z LLM
    sprawdzone_wymogi_raw: List[str] = field(default_factory=list)
    niespelnione_wymogi_raw: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "bank_name": self.bank_name,
            "status": self.status,
            "checked_requirements": [req.to_dict() for req in self.checked_requirements],
            "skipped_requirements": self.skipped_requirements,
            "disqualification_reasons": self.disqualification_reasons,
            "statistics": self.statistics,
            "notes": self.notes,
            "timestamp": self.timestamp,
            # Dodaj oryginalne stringi
            "sprawdzone_wymogi": self.sprawdzone_wymogi_raw,
            "niespelnione_wymogi": self.niespelnione_wymogi_raw,
            "kluczowe_problemy": self.disqualification_reasons
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ValidationResult':
        """Tworzy ValidationResult z dict (z LLM JSON response)"""
        # Parsuj checked_requirements
        checked_reqs = []
        raw_checks = data.get("sprawdzone_wymogi", [])
        
        # Zachowaj oryginalne stringi
        sprawdzone_raw = []
        
        for req in raw_checks:
            if isinstance(req, dict):
                # Jeśli to już dict, stwórz RequirementCheck
                checked_reqs.append(RequirementCheck(
                    category=req.get("category", req.get("kategoria", "")),
                    parameter=req.get("parameter", req.get("parametr", "")),
                    client_value=req.get("client_value", req.get("wartosc_klienta", "")),
                    bank_requirement=req.get("bank_requirement", req.get("wymog_banku", "")),
                    status=req.get("status", "SKIPPED"),
                    reasoning=req.get("reasoning", req.get("uzasadnienie", ""))
                ))
                sprawdzone_raw.append(req.get("reasoning", str(req)))
            elif isinstance(req, str):
                # Jeśli to string, zapisz jako prosty check
                checked_reqs.append(RequirementCheck(
                    category="unknown",
                    parameter=req,
                    client_value="",
                    bank_requirement="",
                    status="SKIPPED",
                    reasoning=req
                ))
                sprawdzone_raw.append(req)
        
        # Wyciągnij niespelnione_wymogi
        niespelnione_raw = data.get("niespelnione_wymogi", [])
        
        return cls(
            bank_name=data.get("bank_name", ""),
            status=data.get("status", "ERROR"),
            checked_requirements=checked_reqs,
            skipped_requirements=data.get("pominiete_wymogi", []),
            disqualification_reasons=niespelnione_raw or data.get("kluczowe_problemy", []),
            statistics=data.get("statystyka", {}),
            notes=data.get("notatki", ""),
            sprawdzone_wymogi_raw=sprawdzone_raw,
            niespelnione_wymogi_raw=niespelnione_raw
        )


@dataclass
class ParameterScore:
    """Ocena pojedynczego parametru JAKOŚCI"""
    parameter_name: str
    category: str  # "koszt_kredytu", "elastycznosc", etc.
    value: str  # Wartość w banku
    points: int  # Punkty uzyskane
    max_points: int  # Max możliwe punkty
    checked: bool  # Czy parametr był sprawdzany
    reasoning: str  # Dlaczego taka punktacja
    
    def to_dict(self) -> Dict:
        return {
            "parameter_name": self.parameter_name,
            "category": self.category,
            "value": self.value,
            "points": self.points,
            "max_points": self.max_points,
            "checked": self.checked,
            "reasoning": self.reasoning
        }


@dataclass
class CategoryScore:
    """Punktacja kategorii (koszt, elastyczność, etc.)"""
    category_name: str
    scored: int  # Punkty uzyskane
    max_possible: int  # Max możliwe w tej kategorii
    parameters_checked: int  # Ile parametrów sprawdzono
    parameters: List[ParameterScore] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "category_name": self.category_name,
            "scored": self.scored,
            "max_possible": self.max_possible,
            "parameters_checked": self.parameters_checked,
            "parameters": [p.to_dict() for p in self.parameters]
        }


@dataclass
class QualityScore:
    """Ocena jakości pojedynczego banku (ETAP 2)"""
    bank_name: str
    total_score: int  # 0-100
    scoring_method: str  # Jak liczono (dla przejrzystości)
    category_scores: Dict[str, int] = field(default_factory=dict)  # breakdown
    checked_parameters: List[str] = field(default_factory=list)
    skipped_parameters: List[str] = field(default_factory=list)
    key_strengths: List[str] = field(default_factory=list)
    key_weaknesses: List[str] = field(default_factory=list)
    details: Dict[str, ParameterScore] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "bank_name": self.bank_name,
            "total_score": self.total_score,
            "scoring_method": self.scoring_method,
            "breakdown": self.category_scores,
            "checked_parameters": self.checked_parameters,
            "skipped_parameters": self.skipped_parameters,
            "kluczowe_atuty": self.key_strengths,
            "punkty_uwagi": self.key_weaknesses,
            "details": {k: v.to_dict() for k, v in self.details.items()},
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QualityScore':
        """Tworzy QualityScore z dict (z LLM JSON response)"""
        return cls(
            bank_name=data.get("bank_name", ""),
            total_score=data.get("total_score", 0),
            scoring_method=data.get("scoring_method", ""),
            category_scores=data.get("breakdown", {}),
            checked_parameters=data.get("checked_parameters", []),
            skipped_parameters=data.get("skipped_parameters", []),
            key_strengths=data.get("kluczowe_atuty", []),
            key_weaknesses=data.get("punkty_uwagi", []),
            details={}  # Ignoruj 'details' - struktura nie pasuje, używamy checked_parameters zamiast tego
        )


@dataclass
class DetailedRanking:
    """Szczegółowy ranking TOP 3 (ETAP 3)"""
    top_banks: List[str]  # Nazwy banków w kolejności
    recommendations: Dict[str, str]  # bank_name -> szczegółowa rekomendacja
    comparison_table: str  # Markdown tabela porównawcza
    final_recommendation: str  # Główna rekomendacja
    analysis_summary: str  # Podsumowanie analizy
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "top_banks": self.top_banks,
            "recommendations": self.recommendations,
            "comparison_table": self.comparison_table,
            "final_recommendation": self.final_recommendation,
            "analysis_summary": self.analysis_summary,
            "timestamp": self.timestamp
        }
    
    def to_markdown(self) -> str:
        """Generuje markdown z rankingu"""
        lines = []
        lines.append("# 🏆 SZCZEGÓŁOWY RANKING TOP 3 BANKÓW")
        lines.append("")
        lines.append(f"*Analiza wykonana: {self.timestamp}*")
        lines.append("")
        lines.append("="*80)
        lines.append("")
        
        # Rekomendacje dla każdego banku
        medals = ["🥇", "🥈", "🥉"]
        for i, bank_name in enumerate(self.top_banks[:3]):
            medal = medals[i]
            lines.append(f"## {medal} MIEJSCE: {bank_name}")
            lines.append("")
            if bank_name in self.recommendations:
                lines.append(self.recommendations[bank_name])
            lines.append("")
            lines.append("-"*80)
            lines.append("")
        
        # Tabela porównawcza
        if self.comparison_table:
            lines.append("## 📊 TABELA PORÓWNAWCZA")
            lines.append("")
            lines.append(self.comparison_table)
            lines.append("")
        
        # Finalna rekomendacja
        if self.final_recommendation:
            lines.append("## 💡 FINALNA REKOMENDACJA")
            lines.append("")
            lines.append(self.final_recommendation)
            lines.append("")
        
        # Podsumowanie
        if self.analysis_summary:
            lines.append("## 📋 PODSUMOWANIE ANALIZY")
            lines.append("")
            lines.append(self.analysis_summary)
        
        return "\n".join(lines)


@dataclass
class CompleteAnalysis:
    """Kompletna analiza - wszystkie etapy"""
    customer_profile: Any  # CustomerProfile object
    validation_results: List[ValidationResult]
    quality_scores: List[QualityScore]
    detailed_ranking: Optional[DetailedRanking] = None
    qualified_banks: List[str] = field(default_factory=list)
    disqualified_banks: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "customer_profile": self.customer_profile.to_dict() if hasattr(self.customer_profile, 'to_dict') else str(self.customer_profile),
            "validation_results": [v.to_dict() for v in self.validation_results],
            "quality_scores": [q.to_dict() for q in self.quality_scores],
            "detailed_ranking": self.detailed_ranking.to_dict() if self.detailed_ranking else None,
            "qualified_banks": self.qualified_banks,
            "disqualified_banks": self.disqualified_banks,
            "timestamp": self.timestamp
        }
    
    def get_summary(self) -> str:
        """Zwraca krótkie podsumowanie analizy"""
        lines = [
            f"Przeanalizowano {len(self.validation_results)} banków",
            f"✅ Zakwalifikowane: {len(self.qualified_banks)}",
            f"❌ Odrzucone: {len(self.disqualified_banks)}",
            f"🏆 Oceniono jakość: {len(self.quality_scores)} banków"
        ]
        
        if self.detailed_ranking:
            lines.append(f"📊 Ranking TOP {len(self.detailed_ranking.top_banks)}")
        
        return "\n".join(lines)
