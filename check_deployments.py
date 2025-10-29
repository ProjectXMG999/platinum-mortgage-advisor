"""
Skrypt do sprawdzenia dostępnych deploymentów w Azure OpenAI
"""
from openai import AzureOpenAI
import sys
from pathlib import Path

# Dodaj ścieżkę do src
sys.path.insert(0, str(Path(__file__).parent / "src"))

import config

print("="*80)
print("SPRAWDZANIE DOSTĘPNYCH MODELI W AZURE OPENAI")
print("="*80)
print(f"\nEndpoint: {config.AZURE_OPENAI_ENDPOINT}")
print(f"API Version: {config.AZURE_OPENAI_API_VERSION}")
print(f"Aktualnie skonfigurowany deployment: {config.AZURE_OPENAI_DEPLOYMENT_NAME}")

try:
    client = AzureOpenAI(
        api_version=config.AZURE_OPENAI_API_VERSION,
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        api_key=config.AZURE_OPENAI_API_KEY,
    )
    
    print("\n" + "="*80)
    print("PRÓBA TESTOWEGO ZAPYTANIA Z RÓŻNYMI NAZWAMI DEPLOYMENTÓW")
    print("="*80)
    
    # Lista możliwych nazw deploymentów do przetestowania
    possible_deployments = [
        "gpt-4o",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-35-turbo",
        "gpt-4o-mini",
        "gpt-4-32k",
    ]
    
    working_deployments = []
    
    for deployment_name in possible_deployments:
        print(f"\n🔍 Testuję: {deployment_name}...", end=" ")
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "user", "content": "Odpowiedz krótko: działa?"}
                ],
                max_tokens=10
            )
            print("✅ DZIAŁA!")
            working_deployments.append(deployment_name)
            print(f"   Odpowiedź: {response.choices[0].message.content}")
        except Exception as e:
            error_msg = str(e)
            if "DeploymentNotFound" in error_msg:
                print("❌ Nie znaleziono")
            elif "429" in error_msg:
                print("⚠️  Limit zapytań (ale deployment istnieje!)")
                working_deployments.append(deployment_name)
            else:
                print(f"❌ Błąd: {error_msg[:50]}...")
    
    print("\n" + "="*80)
    print("PODSUMOWANIE")
    print("="*80)
    
    if working_deployments:
        print(f"\n✅ Znalezione działające deploymenty ({len(working_deployments)}):")
        for dep in working_deployments:
            print(f"   - {dep}")
        
        print(f"\n💡 REKOMENDACJA:")
        print(f"   Użyj w config.py: AZURE_OPENAI_DEPLOYMENT_NAME = \"{working_deployments[0]}\"")
    else:
        print("\n❌ Nie znaleziono żadnych działających deploymentów!")
        print("\n🔍 Możliwe przyczyny:")
        print("   1. Nieprawidłowy klucz API")
        print("   2. Nieprawidłowy endpoint")
        print("   3. Brak wdrożonych modeli w Azure OpenAI")
        print("\n💡 Sprawdź w Azure Portal:")
        print("   https://portal.azure.com → Azure OpenAI → Deployments")
        
except Exception as e:
    print(f"\n❌ Błąd połączenia: {str(e)}")
    print("\n🔍 Sprawdź:")
    print("   1. Czy klucz API jest poprawny")
    print("   2. Czy endpoint jest poprawny")
    print("   3. Czy masz dostęp do Azure OpenAI")

print("\n" + "="*80)
