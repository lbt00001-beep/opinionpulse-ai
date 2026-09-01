import os
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel Serverless runs on a read-only filesystem except /tmp
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    DATA_DIR = Path("/tmp/sentiment_data")
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "sentiment_app.db"

# Openrouter key auto-detection paths
POSSIBLE_KEY_PATHS = [
    Path("C:/Users/Gaming/Documents/Openrouter.txt"),
    BASE_DIR.parent.parent.parent / "Openrouter.txt",
    BASE_DIR / "openrouter_key.txt",
]

def get_default_api_key() -> str:
    # Check env var first
    env_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if env_key:
        return env_key
    
    # Check text file
    for path in POSSIBLE_KEY_PATHS:
        try:
            if path.exists():
                content = path.read_text(encoding="utf-8").strip()
                if content and content.startswith("sk-or-"):
                    return content
        except Exception:
            pass
    return ""

RECOMMENDED_MODELS: List[Dict[str, Any]] = [
    {
        "id": "google/gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash Lite",
        "provider": "Google",
        "description": "El modelo más rápido y económico de Google. 1M de contexto, excelente redacción y coste mínimo.",
        "input_cost": "$0.075 / 1M",
        "output_cost": "$0.30 / 1M",
        "is_default": True,
        "badge": "⭐ Recomendado (Por Defecto)"
    },
    {
        "id": "z-ai/glm-5.3-flash",
        "name": "GLM 5.3 Flash",
        "provider": "Zhipu AI (Z.ai)",
        "description": "Modelo de última generación altamente eficiente, excelente capacidad de razonamiento analítico y coste muy bajo.",
        "input_cost": "$0.08 / 1M",
        "output_cost": "$0.20 / 1M",
        "is_default": False,
        "badge": "Muy Popular & Barato"
    },
    {
        "id": "google/gemini-2.5-flash-lite",
        "name": "Gemini 2.5 Flash Lite",
        "provider": "Google",
        "description": "Versión Flash Lite de gran estabilidad y velocidad instantánea para resúmenes ejecutivos.",
        "input_cost": "$0.075 / 1M",
        "output_cost": "$0.30 / 1M",
        "is_default": False,
        "badge": "Económico & Rápido"
    },
    {
        "id": "z-ai/glm-5.2",
        "name": "GLM 5.2",
        "provider": "Zhipu AI (Z.ai)",
        "description": "Gran capacidad de razonamiento y estructuración de informes complejos con ventana de contexto de 1M tokens.",
        "input_cost": "$0.10 / 1M",
        "output_cost": "$0.25 / 1M",
        "is_default": False,
        "badge": "Razonamiento Avanzado"
    },
    {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek V3 / Chat",
        "provider": "DeepSeek",
        "description": "Líder en relación calidad/precio. Redacción impecable y detección fina de matices y opiniones contrapuestas.",
        "input_cost": "$0.14 / 1M",
        "output_cost": "$0.28 / 1M",
        "is_default": False,
        "badge": "Top Calidad/Precio"
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "Llama 3.1 8B Instruct",
        "provider": "Meta",
        "description": "Extremadamente ligero y económico, respuesta casi instantánea para resúmenes rápidos.",
        "input_cost": "$0.05 / 1M",
        "output_cost": "$0.05 / 1M",
        "is_default": False,
        "badge": "Ultra Económico"
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Llama 3.3 70B Instruct",
        "provider": "Meta",
        "description": "Rendimiento similar a GPT-4 a una fracción minúscula de coste.",
        "input_cost": "$0.12 / 1M",
        "output_cost": "$0.30 / 1M",
        "is_default": False,
        "badge": "Alto Rendimiento"
    },
    {
        "id": "google/gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "Google",
        "description": "Versión balanceada con excelente capacidad analítica e instrucciones complejas.",
        "input_cost": "$0.15 / 1M",
        "output_cost": "$0.60 / 1M",
        "is_default": False,
        "badge": "Gran Capacidad"
    },
    {
        "id": "mistralai/mistral-small-24b-instruct-2501",
        "name": "Mistral Small 24B",
        "provider": "Mistral AI",
        "description": "Excelente soporte en español, razonamiento conciso y alta velocidad.",
        "input_cost": "$0.10 / 1M",
        "output_cost": "$0.30 / 1M",
        "is_default": False,
        "badge": "Multilingüe"
    },
    {
        "id": "qwen/qwen-2.5-72b-instruct",
        "name": "Qwen 2.5 72B",
        "provider": "Alibaba Cloud",
        "description": "Gran robustez lógica para análisis comparativo y extracción de hechos.",
        "input_cost": "$0.35 / 1M",
        "output_cost": "$0.40 / 1M",
        "is_default": False,
        "badge": "Lógica & Datos"
    }
]
