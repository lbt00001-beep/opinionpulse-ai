import json
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.config import get_default_api_key

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def build_prompt_for_sentiment_report(
    topic: str,
    metrics: Dict[str, Any],
    mentions: List[Dict[str, Any]],
    report_type: str = "executive"
) -> str:
    """Construye un prompt de inteligencia de opinión exhaustivo con ponderación contextual."""
    
    # Take top sample mentions from different platforms
    reddit_samples = [m for m in mentions if m.get("platform") == "Reddit"][:8]
    news_samples = [m for m in mentions if "Medios" in m.get("platform", "") or "Noticias" in m.get("platform", "")][:8]
    social_samples = [m for m in mentions if m.get("platform") not in ["Reddit"] and "Medios" not in m.get("platform", "")][:8]
    
    mentions_text = "### MUESTRAS DE CONVERSACIONES EXTRAÍDAS EN TIEMPO REAL:\n\n"
    
    if reddit_samples:
        mentions_text += "#### [REDDIT - DEBATES Y COMUNIDADES]:\n"
        for i, m in enumerate(reddit_samples, 1):
            mentions_text += f"{i}. [{m.get('source_name', 'Reddit')}] \"{m.get('title', '')}\": {m.get('content', '')} (Sentimiento: {m.get('sentiment_label')}, Peso: {m.get('applied_weight', 1.0)})\n"
            
    if news_samples:
        mentions_text += "\n#### [PRENSA Y MEDIOS DE COMUNICACIÓN]:\n"
        for i, m in enumerate(news_samples, 1):
            mentions_text += f"{i}. [{m.get('source_name', 'Medios')}] \"{m.get('title', '')}\": {m.get('content', '')} (Sentimiento: {m.get('sentiment_label')}, Peso: {m.get('applied_weight', 1.0)})\n"
            
    if social_samples:
        mentions_text += "\n#### [REDES SOCIALES (X/TWITTER, FACEBOOK, FOROS)]:\n"
        for i, m in enumerate(social_samples, 1):
            mentions_text += f"{i}. [{m.get('platform', 'Social')}] \"{m.get('title', '')}\": {m.get('content', '')} (Sentimiento: {m.get('sentiment_label')}, Peso: {m.get('applied_weight', 1.0)})\n"
            
    detected_domain = metrics.get("detected_domain", "General / Multitemático")
    weights = metrics.get("active_weights", {})
    weights_str = ", ".join([f"{k}: {int(v*100)}%" for k, v in weights.items() if isinstance(v, (int, float))])
    trend_info = metrics.get("trend", {})
    trend_str = f"{trend_info.get('direction', 'Estable')} (Variación: {trend_info.get('delta', 0.0)}%)"
    
    polarization_info = metrics.get("polarization", {})
    pi_score = polarization_info.get("score", 0)
    pi_label = polarization_info.get("label", "Consenso")
    pi_desc = polarization_info.get("description", "")
    
    polarization_alert = ""
    if pi_score >= 50:
        polarization_alert = f"""
⚠️ ATENCIÓN ANALÍTICA DE ALTA POLARIZACIÓN (Índice: {pi_score}% - {pi_label}):
Este tema presenta una FRACTURA SOCIAL / BIMODALIDAD SEVERA. No intentes resumir la opinión en un consenso tibio o término medio artificial. 
Debes exponer con total nitidez y rigor:
1. Las tesis, argumentos de defensa y legitimación del BANDO FAVORABLE.
2. Las críticas, acusaciones de ataque y quejas del BANDO DETRACTOR.
3. El choque dialéctico, las palabras de conflicto y la dinámica de trincheras en redes y medios.
"""

    prompt = f"""Eres un analista senior de inteligencia de opinión pública, reputación y análisis de mercado.
Tu tarea es redactar un **Informe Ejecutivo de Estado de Opinión y Sentimiento** riguroso, perspicaz y profesional sobre: **"{topic}"**.

### DATOS CUANTITATIVOS DEL ANÁLISIS:
- **Categoría Temática Detectada:** {detected_domain}
- **Matriz de Ponderación Contextual Aplicada:** {weights_str}
- **Índice de Polarización & Fricción Social (PI):** {pi_score}% ({pi_label}) - {pi_desc}
- **Evolución y Tendencia Temporal:** {trend_str}
- **Total de menciones analizadas:** {metrics.get('total_count', 0)}
- **Índice Neto de Sentimiento Ponderado (NSI):** {metrics.get('weighted_nsi', metrics.get('net_sentiment_index', 0))}% (Escala de -100% rechazo a +100% aprobación)
- **Distribución de Sentimiento Bruta:** {metrics.get('distribution', {}).get('positive', 0)}% Positivo | {metrics.get('distribution', {}).get('neutral', 0)}% Neutral | {metrics.get('distribution', {}).get('negative', 0)}% Negativo
- **Temas y conceptos clave más repetidos:** {', '.join(metrics.get('key_phrases', []))}
{polarization_alert}

{mentions_text}

---

### ESTRUCTURA OBLIGATORIA DEL INFORME (Formato Markdown profesional):

# 📊 Informe de Inteligencia de Opinión: {topic}

## 1. 📌 Resumen Ejecutivo y Tesis Central
- Explicación del clima de opinión actual y balance del **Índice Neto de Sentimiento Ponderado ({metrics.get('weighted_nsi', 0)}%)** según el contexto de **{detected_domain}**.
- Nivel de convicción, volatilidad emocional y **grado de polarización detectada ({pi_score}%)**.

## 2. ⚡ Mapa de Polarización y Choque Dialéctico
- Análisis del grado de enfrentamiento: ¿hay consenso mayoritario o es una **guerra de trincheras** entre dos bloques definidos?
- Principales líneas de ataque y defensa esgrimidas por cada sector.

## 3. 📈 Evolución Temporal y Tendencia
- Análisis de la curva de opinión a lo largo del tiempo: ¿la percepción del público está **mejorando**, **empeorando** o se mantiene **estable**?
- Identificación de posibles **puntos de inflexión** o momentos clave donde cambió el tono de la conversación.

## 4. 🌐 Radiografía Ponderada por Canales y Comunidades
- **En Medios y Prensa Especializada:** Enfoque editorial, cobertura técnica o financiera y datos contrastados.
- **En Comunidades de Debate (Reddit):** Argumentos de fondo, tesis de usuarios y puntos de mayor votación.
- **En Redes Sociales (X/Twitter, Foros):** Reacciones de última hora, sentimiento visceral y tendencias virales.

## 5. ⚖️ Los Principales Argumentos en Debate
- **🟢 Focos de Valoración Positiva / Argumentos de Apoyo:** 3-4 aspectos concretos con mayor respaldo.
- **🔴 Puntos de Fricción, Riesgo o Crítica:** 3-4 objeciones, quejas o denuncias específicas.

## 6. 🚨 Alertas de Riesgo Reputacional / Volatilidad
- Identificación de polémicas activas, riesgos de mercado/regulatorios o cambios bruscos en la narrativa.

## 7. 💡 Conclusiones y Recomendaciones Estratégicas
- 3 o 4 recomendaciones ejecutivas accionables basadas en la ponderación y el nivel de polarización detectado.

Redacta el informe en español, con un tono analítico, neutral y objetivo. Utiliza negritas, listas y llamadas estructuradas."""
    return prompt

async def stream_openrouter_report(
    topic: str,
    metrics: Dict[str, Any],
    mentions: List[Dict[str, Any]],
    model_id: str,
    api_key: str
) -> AsyncGenerator[str, None]:
    """Genera el informe en streaming vía OpenRouter API."""
    prompt = build_prompt_for_sentiment_report(topic, metrics, mentions)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Opinion & Sentiment Intelligence Hub",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": "Eres un asistente experto en análisis de sentimiento, inteligencia de mercado y síntesis de opinión pública. Genera análisis estructurados y profundos con formato Markdown."
            },
            {"role": "user", "content": prompt}
        ],
        "stream": True,
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", OPENROUTER_API_URL, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    yield f"Error al conectar con OpenRouter ({response.status_code}): {error_body.decode('utf-8')}"
                    return
                    
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            choices = data_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except Exception:
                            continue
        except Exception as e:
            yield f"\n\n[Excepción en conexión OpenRouter: {str(e)}]"

async def generate_openrouter_report(
    topic: str,
    metrics: Dict[str, Any],
    mentions: List[Dict[str, Any]],
    model_id: str,
    api_key: str
) -> str:
    """Genera el informe de manera síncrona/completa."""
    prompt = build_prompt_for_sentiment_report(topic, metrics, mentions)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Opinion & Sentiment Intelligence Hub",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": "Eres un analista experto en inteligencia de opinión y síntesis de datos sociales y mediáticos."
            },
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                return f"Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"Excepción de conexión con OpenRouter: {str(e)}"
    return "No se pudo generar el informe."

async def test_openrouter_key(api_key: str) -> Dict[str, Any]:
    """Valida la clave de OpenRouter consultando los modelos disponibles."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return {"valid": True, "info": data.get("data", {})}
            else:
                return {"valid": False, "error": f"Status {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
