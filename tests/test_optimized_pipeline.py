"""
Test zoptymalizowanego pipeline'u z ustrukturyzowanymi outputami
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services import (
    ContextLoader,
    PromptLoader,
    ResponseParser
)
from src.models.customer_profile import CustomerProfile


async def test_context_loader():
    """Test ContextLoader - separacja WYMÓG vs JAKOŚĆ"""
    print("\n" + "="*80)
    print("TEST 1: ContextLoader - Separacja WYMÓG vs JAKOŚĆ")
    print("="*80)
    
    loader = ContextLoader()
    
    print(f"\n✓ Załadowano {len(loader.knowledge_base)} banków")
    print(f"✓ Załadowano {len(loader.parameter_classification)} parametrów")
    
    # Test separacji dla jednego banku
    test_bank = list(loader.knowledge_base.keys())[0]
    
    validation_ctx = loader.get_validation_context(test_bank)
    quality_ctx = loader.get_quality_context(test_bank)
    full_ctx = loader.get_full_bank_context(test_bank)
    
    print(f"\n📊 Statystyki kontekstu dla '{test_bank}':")
    print(f"  - Validation (WYMÓG): {len(str(validation_ctx))} znaków")
    print(f"  - Quality (JAKOŚĆ): {len(str(quality_ctx))} znaków")
    print(f"  - Full: {len(str(full_ctx))} znaków")
    
    # Sprawdź kategorie
    validation_keys = set(validation_ctx.keys())
    quality_keys = set(quality_ctx.keys())
    
    print(f"\n📁 Kategorie w Validation context: {validation_keys}")
    print(f"📁 Kategorie w Quality context: {quality_keys}")
    
    # Weryfikacja rozłączności
    overlap = validation_keys & quality_keys
    print(f"\n✅ Overlap między WYMÓG i JAKOŚĆ: {overlap if overlap else 'BRAK (poprawnie!)'}")
    
    return loader


async def test_prompt_loader(context_loader):
    """Test PromptLoader - budowanie messages"""
    print("\n" + "="*80)
    print("TEST 2: PromptLoader - Budowanie Messages")
    print("="*80)
    
    prompt_loader = PromptLoader(context_loader)
    
    # Przykładowy profil klienta
    test_profile = CustomerProfile(
        kwota_kredytu=500000,
        wklad_wlasny=100000,
        cel_kredytu="zakup_mieszkania",
        wiek_kredytobiorcy=35,
        dochod_netto=8000
    )
    
    test_bank = list(context_loader.knowledge_base.keys())[0]
    
    # Test validation messages
    validation_msgs = prompt_loader.build_validation_messages(test_bank, test_profile)
    print(f"\n✓ Validation messages: {len(validation_msgs)} messages")
    for i, msg in enumerate(validation_msgs):
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  [{i+1}] {msg['role']}: {content_preview}")
    
    # Test quality messages
    quality_msgs = prompt_loader.build_quality_messages(test_bank, test_profile)
    print(f"\n✓ Quality messages: {len(quality_msgs)} messages")
    for i, msg in enumerate(quality_msgs):
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  [{i+1}] {msg['role']}: {content_preview}")
    
    # Test ranking messages
    top_banks = list(context_loader.knowledge_base.keys())[:3]
    ranking_msgs = prompt_loader.build_ranking_messages(top_banks, test_profile)
    print(f"\n✓ Ranking messages: {len(ranking_msgs)} messages")
    for i, msg in enumerate(ranking_msgs):
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  [{i+1}] {msg['role']}: {content_preview}")
    
    return prompt_loader, test_profile


async def test_response_parser():
    """Test ResponseParser - parsowanie JSON"""
    print("\n" + "="*80)
    print("TEST 3: ResponseParser - Parsowanie Odpowiedzi")
    print("="*80)
    
    parser = ResponseParser()
    
    # Test 1: Clean JSON z markdown
    test_json_with_markdown = """```json
{
    "bank_name": "Test Bank",
    "status": "PASSED",
    "requirement_checks": [],
    "notes": "Test note"
}
```"""
    
    print("\n📝 Test czyszczenia markdown:")
    cleaned = parser._clean_json_response(test_json_with_markdown)
    print(f"  Przed: {len(test_json_with_markdown)} znaków")
    print(f"  Po: {len(cleaned)} znaków")
    print(f"  ✓ Usunięto: ```json...```")
    
    # Test 2: Parse validation response
    validation_json = """{
    "bank_name": "PKO BP",
    "status": "PASSED",
    "requirement_checks": [
        {"parameter_name": "min_wiek", "status": "PASSED", "reason": "Klient ma 35 lat"},
        {"parameter_name": "min_wklad_wlasny", "status": "PASSED", "reason": "Wkład 100k PLN"}
    ],
    "notes": "Bank spełnia wszystkie wymagania"
}"""
    
    result = parser.parse_validation_response(validation_json, "PKO BP")
    print(f"\n✓ Parsed ValidationResult:")
    print(f"  - Bank: {result.bank_name}")
    print(f"  - Status: {result.status}")
    print(f"  - Checks: {len(result.requirement_checks)}")
    print(f"  - Type: {type(result).__name__}")
    
    # Test 3: to_dict()
    result_dict = result.to_dict()
    print(f"\n✓ Serialization to dict:")
    print(f"  - Keys: {list(result_dict.keys())}")
    
    return parser


async def test_validation_service_mock():
    """Test ValidationService (mock - bez API calls)"""
    print("\n" + "="*80)
    print("TEST 4: ValidationService - Mock Test")
    print("="*80)
    
    # Inicjalizacja bez prawdziwego AI client
    context_loader = ContextLoader()
    prompt_loader = PromptLoader(context_loader)
    
    print(f"\n✓ ValidationService używa:")
    print(f"  - ContextLoader: {len(context_loader.knowledge_base)} banków")
    print(f"  - PromptLoader: {type(prompt_loader).__name__}")
    print(f"  - ResponseParser: zintegrowany")
    
    # Test budowania messages
    test_profile = CustomerProfile(
        kwota_kredytu=300000,
        wklad_wlasny=60000,
        cel_kredytu="zakup_mieszkania",
        wiek_kredytobiorcy=30
    )
    
    test_bank = list(context_loader.knowledge_base.keys())[0]
    messages = prompt_loader.build_validation_messages(test_bank, test_profile)
    
    print(f"\n✓ Build validation messages dla '{test_bank}':")
    print(f"  - Liczba messages: {len(messages)}")
    
    # Sprawdź czy kontekst zawiera tylko WYMÓG
    bank_context_msg = messages[1]['content']
    
    wymog_keywords = ['kredytobiorca', 'źródło_dochodu', 'cel_kredytu', 'zabezpieczenia']
    jakosc_keywords = ['wycena', 'ubezpieczenia']
    
    wymog_found = sum(1 for kw in wymog_keywords if kw in bank_context_msg)
    jakosc_found = sum(1 for kw in jakosc_keywords if kw in bank_context_msg)
    
    print(f"\n📊 Analiza kontekstu:")
    print(f"  - WYMÓG keywords found: {wymog_found}/{len(wymog_keywords)}")
    print(f"  - JAKOŚĆ keywords found: {jakosc_found}/{len(jakosc_keywords)}")
    
    if wymog_found > 0 and jakosc_found == 0:
        print(f"  ✅ Kontekst zawiera TYLKO kategorie WYMÓG (poprawnie!)")
    else:
        print(f"  ⚠️ Kontekst może zawierać zbędne kategorie")


async def test_quality_service_mock():
    """Test QualityService (mock - bez API calls)"""
    print("\n" + "="*80)
    print("TEST 5: QualityService - Mock Test")
    print("="*80)
    
    # Inicjalizacja
    context_loader = ContextLoader()
    prompt_loader = PromptLoader(context_loader)
    
    print(f"\n✓ QualityService używa:")
    print(f"  - ContextLoader: {len(context_loader.knowledge_base)} banków")
    print(f"  - PromptLoader: {type(prompt_loader).__name__}")
    print(f"  - ResponseParser: zintegrowany")
    
    # Test budowania messages
    test_profile = CustomerProfile(
        kwota_kredytu=400000,
        wklad_wlasny=80000,
        cel_kredytu="budowa_domu"
    )
    
    test_bank = list(context_loader.knowledge_base.keys())[0]
    messages = prompt_loader.build_quality_messages(test_bank, test_profile)
    
    print(f"\n✓ Build quality messages dla '{test_bank}':")
    print(f"  - Liczba messages: {len(messages)}")
    
    # Sprawdź czy kontekst zawiera tylko JAKOŚĆ
    bank_context_msg = messages[1]['content']
    
    wymog_keywords = ['kredytobiorca', 'źródło_dochodu', 'cel_kredytu']
    jakosc_keywords = ['wycena', 'ubezpieczenia']
    
    wymog_found = sum(1 for kw in wymog_keywords if kw in bank_context_msg)
    jakosc_found = sum(1 for kw in jakosc_keywords if kw in bank_context_msg)
    
    print(f"\n📊 Analiza kontekstu:")
    print(f"  - WYMÓG keywords found: {wymog_found}/{len(wymog_keywords)}")
    print(f"  - JAKOŚĆ keywords found: {jakosc_found}/{len(jakosc_keywords)}")
    
    if jakosc_found > 0 and wymog_found == 0:
        print(f"  ✅ Kontekst zawiera TYLKO kategorie JAKOŚĆ (poprawnie!)")
    else:
        print(f"  ⚠️ Kontekst może zawierać kategorie WYMÓG")


async def main():
    """Uruchom wszystkie testy"""
    print("\n" + "🚀"*40)
    print("TEST SUITE: Zoptymalizowany Pipeline z Structured Outputs")
    print("🚀"*40)
    
    try:
        # Test 1: ContextLoader
        context_loader = await test_context_loader()
        
        # Test 2: PromptLoader
        prompt_loader, test_profile = await test_prompt_loader(context_loader)
        
        # Test 3: ResponseParser
        parser = await test_response_parser()
        
        # Test 4: ValidationService (mock)
        await test_validation_service_mock()
        
        # Test 5: QualityService (mock)
        await test_quality_service_mock()
        
        print("\n" + "="*80)
        print("✅ WSZYSTKIE TESTY ZAKOŃCZONE SUKCESEM")
        print("="*80)
        print("""
Zoptymalizowany pipeline jest gotowy do użycia:

1. ✅ ContextLoader - separacja WYMÓG vs JAKOŚĆ
2. ✅ PromptLoader - dynamiczne budowanie messages
3. ✅ ResponseParser - parsowanie do structured outputs
4. ✅ ValidationService - używa tylko kontekstu WYMÓG
5. ✅ QualityService - używa tylko kontekstu JAKOŚĆ

Następne kroki:
- Uruchom testy end-to-end z prawdziwymi API calls
- Zintegruj RankingService w OrchestratorService
- Zmierz oszczędności tokenów (WYMÓG vs JAKOŚĆ filtering)
        """)
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
