import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR, RECOMMENDED_MODELS
from app.services.storage import (
    init_db, get_all_settings, set_setting, save_analysis,
    get_history, get_analysis_by_id, delete_analysis
)
from app.services.mcp_collector import harvest_all_mentions
from app.services.sentiment_engine import process_and_score_mentions
from app.services.openrouter_client import (
    generate_openrouter_report, stream_openrouter_report, test_openrouter_key
)

app = FastAPI(title="Opinion & Sentiment Intelligence Hub", version="1.0.1")

# Mount static and template paths
static_dir = BASE_DIR / "app" / "static"
templates_dir = BASE_DIR / "app" / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    settings = get_all_settings()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "models": RECOMMENDED_MODELS,
            "selected_model": settings.get("selected_model", "google/gemini-3.5-flash-lite"),
            "has_api_key": bool(settings.get("openrouter_api_key"))
        }
    )

@app.get("/api/settings")
async def api_get_settings():
    settings = get_all_settings()
    # Mask API key for safety in UI
    raw_key = settings.get("openrouter_api_key", "")
    masked_key = f"{raw_key[:10]}...{raw_key[-6:]}" if len(raw_key) > 16 else raw_key
    
    return {
        "openrouter_api_key_masked": masked_key,
        "has_key": bool(raw_key),
        "selected_model": settings.get("selected_model", "google/gemini-3.5-flash-lite"),
        "mcp_settings": settings.get("mcp_settings", {})
    }

@app.post("/api/settings")
async def api_save_settings(data: Dict[str, Any] = Body(...)):
    if "openrouter_api_key" in data and data["openrouter_api_key"].strip():
        new_key = data["openrouter_api_key"].strip()
        if not new_key.startswith("***"):  # only update if not placeholder
            set_setting("openrouter_api_key", new_key)
            
    if "selected_model" in data and data["selected_model"].strip():
        set_setting("selected_model", data["selected_model"].strip())
        
    if "mcp_settings" in data:
        set_setting("mcp_settings", json.dumps(data["mcp_settings"]))
        
    return {"status": "success", "message": "Ajustes guardados correctamente"}

@app.get("/api/models")
async def api_get_models():
    return {"models": RECOMMENDED_MODELS}

@app.post("/api/test-key")
async def api_test_key(data: Dict[str, Any] = Body(...)):
    key = data.get("api_key", "").strip()
    if not key:
        settings = get_all_settings()
        key = settings.get("openrouter_api_key", "")
        
    if not key:
        return {"valid": False, "error": "No se ha proporcionado ninguna API Key"}
        
    result = await test_openrouter_key(key)
    return result

@app.post("/api/analyze")
async def api_analyze(data: Dict[str, Any] = Body(...)):
    topic = data.get("topic", "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="El tema no puede estar vacío")
        
    sources = data.get("sources", ["reddit", "news", "social_web"])
    time_range = data.get("time_range", "all")
    settings = get_all_settings()
    
    model_id = data.get("model_id") or settings.get("selected_model", "google/gemini-3.5-flash-lite")
    api_key = settings.get("openrouter_api_key", "")
    
    # 1. Harvest mentions with time range filtering
    raw_mentions = await harvest_all_mentions(
        topic=topic,
        sources=sources,
        time_range=time_range,
        mcp_settings=settings.get("mcp_settings", {})
    )
    
    # 2. Process & score with contextual domain weighting
    analysis_results = process_and_score_mentions(raw_mentions, topic=topic)
    
    # 3. Generate AI Report via OpenRouter
    report_markdown = ""
    if api_key:
        report_markdown = await generate_openrouter_report(
            topic=topic,
            metrics=analysis_results,
            mentions=analysis_results["scored_mentions"],
            model_id=model_id,
            api_key=api_key
        )
    else:
        report_markdown = "⚠️ **Atención**: No se ha configurado la API Key de OpenRouter en los Ajustes. Para generar el informe redactado por IA, por favor introduce tu clave en el panel de Ajustes."
        
    # 4. Save to Database
    analysis_id = str(uuid.uuid4())
    save_analysis(
        analysis_id=analysis_id,
        topic=topic,
        model_used=model_id,
        total_mentions=analysis_results["total_count"],
        sentiment_summary=f"{analysis_results['distribution']['positive']}% Positivo, {analysis_results['distribution']['neutral']}% Neutral, {analysis_results['distribution']['negative']}% Negativo (NSI: {analysis_results['net_sentiment_index']}%)",
        metrics=analysis_results,
        report_markdown=report_markdown,
        mentions_sample=analysis_results["scored_mentions"][:50]
    )
    
    return {
        "id": analysis_id,
        "topic": topic,
        "model_used": model_id,
        "metrics": analysis_results,
        "report_markdown": report_markdown,
        "mentions_sample": analysis_results["scored_mentions"][:50]
    }

@app.get("/api/analyze/stream")
async def api_analyze_stream(
    topic: str,
    sources: Optional[str] = "reddit,news,social_web",
    time_range: Optional[str] = "all",
    model: Optional[str] = None
):
    """Endpoint de Server-Sent Events (SSE) para streaming en vivo del análisis e informe."""
    async def event_generator():
        settings = get_all_settings()
        api_key = settings.get("openrouter_api_key", "")
        model_id = model or settings.get("selected_model", "google/gemini-3.5-flash-lite")
        selected_sources = [s.strip() for s in sources.split(",") if s.strip()] if sources else ["reddit", "news", "social_web"]
        range_val = time_range or "all"
        
        # Step 1: Harvesting
        yield f"data: {json.dumps({'stage': 'harvesting', 'message': f'Recolectando menciones en tiempo real en Reddit, Prensa y Redes para \"{topic}\"...'})}\n\n"
        
        raw_mentions = await harvest_all_mentions(
            topic=topic,
            sources=selected_sources,
            time_range=range_val,
            mcp_settings=settings.get("mcp_settings", {})
        )
        
        yield f"data: {json.dumps({'stage': 'scoring', 'message': f'Procesando {len(raw_mentions)} menciones y calculando métricas de sentimiento...'})}\n\n"
        
        # Step 2: Sentiment scoring with dynamic domain weighting
        analysis_results = process_and_score_mentions(raw_mentions, topic=topic)
        
        yield f"data: {json.dumps({'stage': 'metrics_ready', 'metrics': analysis_results, 'mentions_sample': analysis_results['scored_mentions'][:50]})}\n\n"
        
        # Step 3: Stream Report from OpenRouter
        analysis_id = str(uuid.uuid4())
        full_report = ""
        
        if not api_key:
            error_msg = "\n\n⚠️ **Nota:** No se detectó una API Key de OpenRouter en los Ajustes. Ve a la pestaña de Ajustes para configurar tu clave y generar informes completos con IA."
            yield f"data: {json.dumps({'stage': 'report_chunk', 'chunk': error_msg})}\n\n"
            full_report = error_msg
        else:
            yield f"data: {json.dumps({'stage': 'report_start', 'model': model_id, 'message': f'Generando síntesis ejecutiva con {model_id}...'})}\n\n"
            
            async for chunk in stream_openrouter_report(
                topic=topic,
                metrics=analysis_results,
                mentions=analysis_results["scored_mentions"],
                model_id=model_id,
                api_key=api_key
            ):
                full_report += chunk
                yield f"data: {json.dumps({'stage': 'report_chunk', 'chunk': chunk})}\n\n"
                
        # Step 4: Save & Complete
        save_analysis(
            analysis_id=analysis_id,
            topic=topic,
            model_used=model_id,
            total_mentions=analysis_results["total_count"],
            sentiment_summary=f"{analysis_results['distribution']['positive']}% Positivo, {analysis_results['distribution']['neutral']}% Neutral, {analysis_results['distribution']['negative']}% Negativo (NSI: {analysis_results['net_sentiment_index']}%)",
            metrics=analysis_results,
            report_markdown=full_report,
            mentions_sample=analysis_results["scored_mentions"][:50]
        )
        
        yield f"data: {json.dumps({'stage': 'done', 'analysis_id': analysis_id})}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/history")
async def api_get_history():
    history = get_history(limit=50)
    return {"history": history}

@app.get("/api/history/{analysis_id}")
async def api_get_history_item(analysis_id: str):
    item = get_analysis_by_id(analysis_id)
    if not item:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    return item

@app.delete("/api/history/{analysis_id}")
async def api_delete_history_item(analysis_id: str):
    delete_analysis(analysis_id)
    return {"status": "success", "message": "Análisis eliminado del historial"}

@app.get("/api/export/{analysis_id}")
async def api_export(analysis_id: str, format: str = "markdown"):
    item = get_analysis_by_id(analysis_id)
    if not item:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
        
    if format == "json":
        return JSONResponse(content=item)
    elif format == "markdown":
        filename = f"informe_sentimiento_{item['topic'].replace(' ', '_')}.md"
        headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
        return PlainTextResponse(content=item["report_markdown"], headers=headers)
    else:
        return PlainTextResponse(content=item["report_markdown"])
