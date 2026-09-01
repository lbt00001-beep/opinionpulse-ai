import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.mcp_collector import harvest_all_mentions
from app.services.sentiment_engine import process_and_score_mentions

async def test_domain_weighting():
    topics = [
        "Acción de SpaceX y valoración de mercado",
        "Lanzamiento DeepSeek R1 y modelos de lenguaje"
    ]
    
    for t in topics:
        print(f"\n==========================================")
        print(f"Probando tema: \"{t}\"")
        mentions = await harvest_all_mentions(topic=t, sources=["reddit", "news", "social_web"])
        res = process_and_score_mentions(mentions, topic=t)
        
        print(f"-> Categoría detectada: {res['detected_domain']}")
        print(f"-> Ponderación activa: {res['active_weights']}")
        print(f"-> NSI Bruto: {res['net_sentiment_index']}% | NSI Ponderado: {res['weighted_nsi']}%")
        print(f"-> Total menciones analizadas: {res['total_count']}")

if __name__ == "__main__":
    asyncio.run(test_domain_weighting())
