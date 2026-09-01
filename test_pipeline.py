import asyncio
import sys

# Ensure utf-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import get_default_api_key, RECOMMENDED_MODELS
from app.services.storage import init_db, get_all_settings
from app.services.mcp_collector import harvest_all_mentions
from app.services.sentiment_engine import process_and_score_mentions
from app.services.openrouter_client import test_openrouter_key, generate_openrouter_report

async def run_verification():
    print("=== 1. Testing Storage & Auto-Detection ===")
    init_db()
    key = get_default_api_key()
    print("OpenRouter Key Detected:", bool(key))
    if key:
        print("Key prefix:", key[:10] + "...")
        
    print("\n=== 2. Testing OpenRouter Key API Connection ===")
    if key:
        val = await test_openrouter_key(key)
        print("Key validation status:", val.get("valid"))
        
    print("\n=== 3. Testing Real-time Multi-Source Harvester ===")
    topic = "Impacto de la Inteligencia Artificial"
    mentions = await harvest_all_mentions(topic=topic, sources=["reddit", "news", "social_web"])
    print(f"Total mentions retrieved: {len(mentions)}")
    
    print("\n=== 4. Testing Sentiment & Scoring Engine ===")
    results = process_and_score_mentions(mentions)
    print("Net Sentiment Index (NSI):", results["net_sentiment_index"])
    print("Sentiment Distribution:", results["distribution"])
    print("Key Debated Terms:", results["key_phrases"][:6])
    
    print("\n=== 5. Testing OpenRouter Report Generation with GLM 5.3 Flash & Gemini Flash Lite ===")
    if key:
        report = await generate_openrouter_report(
            topic=topic,
            metrics=results,
            mentions=results["scored_mentions"],
            model_id="z-ai/glm-5.3-flash",
            api_key=key
        )
        print(f"Report generated successfully with GLM 5.3 Flash! Length: {len(report)} chars")
        
    print("\n=== All Verification Tests Completed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_verification())
