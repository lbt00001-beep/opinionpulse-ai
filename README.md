# 📊 OpinionPulse AI — Radar de Sentimiento y Estado de Opinión con MCP & OpenRouter

Aplicación web integral para monitorizar en tiempo real el estado de opinión, debates y análisis de sentimiento sobre cualquier tema, persona o marca en **Reddit, X/Twitter, Medios de Comunicación (Prensa) y Redes Sociales**, generando informes ejecutivos de inteligencia mediante **OpenRouter** y el protocolo **MCP (Model Context Protocol)**.

---

## 🚀 Características Principales

1. **Recolección Multicanal en Tiempo Real (MCP & Web Harvester)**:
   - **Reddit**: Captura debates, comentarios reales, hilos más votados y métricas comunitarias.
   - **Medios de Comunicación & Prensa Digital**: Conexión a Google News RSS y portales de noticias internacionales.
   - **Redes Sociales & Foros**: Rastreo en X (Twitter), Facebook, LinkedIn y comunidades de debate.
   - **Soporte MCP Neuronal**: Conectores opcionales para Exa AI MCP (`exa-mcp-server`), Apify MCP (`@apify/mcp-server`) y Bright Data MCP.

2. **Motor Cuantitativo de Sentimiento & NSI**:
   - **Net Sentiment Index (NSI)**: Puntuación normalizada de -100% (Rechazo absoluto) a +100% (Consenso positivo).
   - **Distribución %**: Desglose exacto de porcentaje Positivo, Neutral y Negativo.
   - **NLP Emocional**: Detección de emociones dominantes (Entusiasmo, Crítica, Cautela, Curiosidad, Informativo).
   - **Extracción de Focos**: Detección automática de términos y argumentos más repetidos.

3. **Generación de Informes Ejecutivos vía OpenRouter**:
   - **Modelo por Defecto**: ⭐ **Gemini 2.5 Flash Lite** (`google/gemini-2.5-flash-lite`) — Ultra-rápido, 1M de contexto y coste mínimo (~$0.075 / 1M tokens).
   - **Modelos Económicos Incluidos**:
     - **GLM 5.3 Flash** (`z-ai/glm-5.3-flash`) — Gran capacidad de razonamiento analítico a coste ultra bajo.
     - **GLM 5.2** (`z-ai/glm-5.2`) — Razonamiento avanzado Zhipu AI.
     - **DeepSeek V3 / Chat** (`deepseek/deepseek-chat`) — Top calidad/precio.
     - **Llama 3.1 8B Instruct** (`meta-llama/llama-3.1-8b-instruct`) — Ultra económico.
     - **Llama 3.3 70B Instruct** (`meta-llama/llama-3.3-70b-instruct`) — Calidad similar a GPT-4.
     - **Mistral Small 24B** (`mistralai/mistral-small-24b-instruct-2501`) — Rápido y multilingüe.
     - **Qwen 2.5 72B** (`qwen/qwen-2.5-72b-instruct`) — Excelente estructuración lógica.
     - **Selector Personalizado**: Permite escribir cualquier slug de modelo de OpenRouter.

4. **Interfaz Interactiva y Exportación**:
   - Streaming en vivo de la redacción del informe.
   - Gráficos interactivos de distribución y comparativa por plataforma con **Chart.js**.
   - Muro interactivo de citas con enlaces directos a las fuentes originales.
   - Historial persistente en **SQLite**.
   - Exportación a **Markdown (.md)**, **PDF** y **JSON**.

---

## 🛠️ Cómo Iniciar la Aplicación

1. Abre una terminal en la carpeta del proyecto:
   ```bash
   cd "C:\Users\Gaming\Documents\Proyectos_IA\Antigravity\sentiment-opinion-app"
   ```

2. Ejecuta la aplicación:
   ```bash
   py run.py
   ```

3. Abre en tu navegador:
   ```
   http://localhost:8000
   ```

---

## ⚙️ Configuración de Claves de API

- La aplicación detecta automáticamente la clave de **OpenRouter** del archivo `Documents/Openrouter.txt`.
- También puedes gestionarla o probarla en cualquier momento desde el botón **Ajustes & Claves** de la barra superior.
