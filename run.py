import threading
import time
import webbrowser
import uvicorn

def launch_browser():
    time.sleep(1.2)
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

if __name__ == "__main__":
    # Lanzar el navegador por defecto automáticamente en segundo plano
    threading.Thread(target=launch_browser, daemon=True).start()
    
    print("================================================================")
    print("   OPINIONPULSE AI - Radar de Opinión y Sentimiento con MCP")
    print("   Abriendo navegador por defecto en: http://localhost:8000")
    print("================================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
