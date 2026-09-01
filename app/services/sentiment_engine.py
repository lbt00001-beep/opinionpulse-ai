import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime

# ==============================================================================
# SCIENTIFIC SENTIMENT & POLARIZATION ENGINE (VALENCE PARSER & BIMODAL POLARIZATION)
# ==============================================================================

def strip_accents(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ñ", "n")
    )

# 1. INTENSITY BOOSTERS & DAMPENERS
BOOSTERS = {
    "muy": 1.4, "extremadamente": 1.8, "increiblemente": 1.7, "totalmente": 1.5, "absolutamente": 1.6,
    "brutalmente": 1.7, "enormemente": 1.6, "completamente": 1.5, "super": 1.4, "hiper": 1.5,
    "claramente": 1.3, "altamente": 1.4, "enorme": 1.4, "mas": 1.2, "radicalmente": 1.6, "duramente": 1.6,
    "plenamente": 1.3, "rotundamente": 1.5, "categoricamente": 1.5, "ferozmente": 1.6,
    "very": 1.4, "extremely": 1.8, "incredibly": 1.7, "totally": 1.5, "absolutely": 1.6,
    "hugely": 1.6, "completely": 1.5, "highly": 1.4, "deeply": 1.5, "radically": 1.6, "harshly": 1.6,
    "fiercely": 1.6
}

DAMPENERS = {
    "algo": 0.6, "un poco": 0.5, "ligeramente": 0.6, "apenas": 0.4, "relativamente": 0.7,
    "parcialmente": 0.6, "quizas": 0.7, "tal vez": 0.7, "supuestamente": 0.6, "presuntamente": 0.6,
    "somewhat": 0.6, "slightly": 0.5, "barely": 0.4, "hardly": 0.4, "partially": 0.6, "allegedly": 0.6
}

# 2. CONTEXTUAL N-GRAM IDIOMS (Financieros, Tecnológicos y POLÍTICO-PERIODÍSTICOS)
CONTEXTUAL_PHRASES = {
    # Positive Complex Idioms (+1.0 to +1.8)
    "caida de la inflacion": 1.5,
    "bajada de la inflacion": 1.5,
    "caida del desempleo": 1.6,
    "bajada del paro": 1.6,
    "recorta perdidas": 1.4,
    "reduce perdidas": 1.4,
    "supera estimaciones": 1.7,
    "supera expectativas": 1.8,
    "supera previsiones": 1.8,
    "bate record": 1.7,
    "record historico": 1.7,
    "maximos historicos": 1.6,
    "gana cuota": 1.4,
    "acuerdo historico": 1.6,
    "avance historico": 1.7,
    "mejora de margenes": 1.5,
    "fuerte demanda": 1.5,
    "impulso alcista": 1.6,
    "sube con fuerza": 1.6,
    "flujo positivo": 1.4,
    "libre de deuda": 1.5,
    "recupera terreno": 1.4,
    "supera al mercado": 1.6,
    "liderazgo solido": 1.6,
    "victoria rotunda": 1.7,
    "victoria aplastante": 1.8,
    "victoria electoral": 1.7,
    "respaldo mayoritario": 1.6,
    "respaldo unanime": 1.7,
    "aplauso unanime": 1.7,
    "apoyo masivo": 1.7,
    "lleno absoluto": 1.5,
    "estabilidad institucional": 1.5,
    "crecimiento historico": 1.6,
    "crecimiento del empleo": 1.6,
    "subida de salarios": 1.5,
    "subida del salario": 1.5,
    "pensiones record": 1.6,
    "subida en encuestas": 1.5,
    "subida en las encuestas": 1.5,
    "sube en encuestas": 1.5,
    "saca adelante": 1.5,
    "salva la votacion": 1.4,
    "triunfo parlamentario": 1.7,
    "avala la ley": 1.5,
    "firmeza y liderazgo": 1.6,
    "revalida su liderazgo": 1.6,
    "revalidar el gobierno": 1.5,
    "exito diplomatico": 1.7,
    "acuerdo de legislatura": 1.5,
    "golpe de efecto": 1.5,
    "resiste el ataque": 1.4,
    "resiste la presion": 1.4,
    "defiende su gestion": 1.4,
    "defiende la gestion": 1.4,
    "beats expectations": 1.8,
    "record high": 1.7,
    "strong buy": 1.8,
    "landslide victory": 1.8,
    "cuts losses": 1.4,
    "inflation drops": 1.5,
    "breakthrough achievement": 1.8,
    "surges in polls": 1.6,
    "massive support": 1.7,

    # Negative & Political Conflict Idioms (-1.0 to -1.9)
    "carga duramente contra": -1.7,
    "carga duramente": -1.6,
    "carga contra": -1.5,
    "arremete contra": -1.6,
    "ataca con dureza": -1.6,
    "estalla contra": -1.6,
    "tacha de": -1.4,
    "absoluta estupidez": -1.8,
    "dura critica": -1.6,
    "duras criticas": -1.6,
    "duro golpe": -1.6,
    "reves judicial": -1.7,
    "batacazo electoral": -1.7,
    "contra las cuerdas": -1.6,
    "bajo sospecha": -1.6,
    "investigado por corrupcion": -1.9,
    "imputado por": -1.7,
    "caso koldo": -1.8,
    "trama de corrupcion": -1.9,
    "pide la dimision": -1.6,
    "exige la dimision": -1.7,
    "pide explicaciones": -1.3,
    "acusa de mentir": -1.7,
    "acusa de traicion": -1.8,
    "fuerte abucheo": -1.7,
    "abucheos e insultos": -1.8,
    "gritos de dimision": -1.8,
    "crisis de gobierno": -1.6,
    "guerra interna": -1.7,
    "acusaciones cruzadas": -1.5,
    "fuerte bronca": -1.5,
    "guerra sucia": -1.8,
    "fango politico": -1.8,
    "maquina del fango": -1.8,
    "traicion a espana": -1.9,
    "alta traicion": -1.9,
    "golpe de estado": -1.9,
    "quiebra del estado": -1.8,
    "ataque a la democracia": -1.8,
    "ataque frontal": -1.6,
    "abuso de poder": -1.7,
    "frena el crecimiento": -1.5,
    "frena las ventas": -1.5,
    "aumenta la deuda": -1.5,
    "incremento de deuda": -1.5,
    "rebaja de calificacion": -1.6,
    "rebaja prevision": -1.6,
    "incumple objetivos": -1.7,
    "incumple plazos": -1.5,
    "incumple promesas": -1.7,
    "fuga de usuarios": -1.7,
    "fuga de empresas": -1.7,
    "fuga de cerebros": -1.5,
    "brecha de seguridad": -1.8,
    "vulnerabilidad critica": -1.8,
    "demanda judicial": -1.4,
    "demanda colectiva": -1.7,
    "investigacion judicial": -1.4,
    "imputacion formal": -1.6,
    "despido masivo": -1.7,
    "recorte de plantilla": -1.5,
    "cae en picado": -1.8,
    "se estrella": -1.6,
    "pierde aura": -1.5,
    "embestida contra": -1.5,
    "perdida millonaria": -1.7,
    "quema de caja": -1.6,
    "presion bajista": -1.5,
    "alerta roja": -1.6,
    "crispacion politica": -1.6,
    "farsa politica": -1.7,
    "oposicion destructiva": -1.6,
    "gobierno ilegitimo": -1.8,
    "mentiras continuas": -1.7,
    "fake news": -1.6,
    "noticias falsas": -1.6,
    "guerra de trincheras": -1.7,
    "polarizacion extrema": -1.7,
    "misses estimates": -1.7,
    "security breach": -1.8,
    "mass layoffs": -1.7,
    "witch hunt": -1.7,
    "abuse of power": -1.8,
    "fierce criticism": -1.7,
    "guilty verdict": -1.9
}

# 3. BASE POLARITY LEXICON (Enriquecido con Política, Prensa, Redes y Finanzas)
LEXICON_VALENCE = {
    # Positive Spanish
    "excelente": 1.5, "increible": 1.4, "genial": 1.3, "fantastico": 1.4, "maravilloso": 1.4,
    "exito": 1.4, "revolucion": 1.3, "innovador": 1.2, "mejora": 1.1, "util": 0.9, "positivo": 1.0,
    "eficiente": 1.1, "calidad": 1.0, "mejor": 1.2, "perfecto": 1.5, "acierto": 1.2, "confianza": 1.1,
    "brillante": 1.3, "prometedor": 1.2, "triunfo": 1.4, "triunfa": 1.4, "triunfan": 1.4, "seguro": 0.9,
    "rapido": 0.8, "solucion": 1.1, "logro": 1.2, "avance": 1.2, "apoyo": 1.1, "rentable": 1.3,
    "crecimiento": 1.2, "solido": 1.1, "solidez": 1.2, "liderazgo": 1.3, "lider": 1.2, "record": 1.3,
    "ganancia": 1.2, "ganador": 1.3, "alcista": 1.3, "beneficio": 1.1, "valioso": 1.1, "estadista": 1.4,
    "progreso": 1.2, "progresista": 1.0, "valiente": 1.1, "firmeza": 1.2, "firme": 1.1, "acuerdo": 1.0,
    "consenso": 1.2, "avala": 1.3, "avalo": 1.3, "avalan": 1.3, "respalda": 1.3, "respaldo": 1.3,
    "respaldan": 1.3, "solvencia": 1.2, "honesto": 1.4, "transparente": 1.3, "integridad": 1.4,
    "victoria": 1.4, "imparable": 1.4, "subida": 1.1, "sube": 1.1, "suben": 1.1, "revalida": 1.3,
    "revalidar": 1.3, "defiende": 1.1, "defensa": 1.0, "crece": 1.1, "aprobacion": 1.2, "aprobado": 1.2,
    "aciertos": 1.2, "favorito": 1.2, "ventaja": 1.1, "reforma": 0.8, "pacto": 1.0,
    # Positive English
    "great": 1.3, "good": 0.9, "amazing": 1.4, "excellent": 1.5, "fantastic": 1.4, "wonderful": 1.4,
    "success": 1.4, "breakthrough": 1.5, "innovative": 1.2, "improvement": 1.1, "useful": 0.9,
    "efficient": 1.1, "promising": 1.2, "awesome": 1.4, "impressive": 1.3, "profitable": 1.3, "growth": 1.2,
    "bullish": 1.3, "solid": 1.1, "gain": 1.1, "upside": 1.2, "love": 1.4, "leader": 1.2, "victory": 1.4,
    "win": 1.3, "wins": 1.3, "boost": 1.2, "lead": 1.2, "surge": 1.3,

    # Negative Spanish (Incluye fuerte vocabulario de enfrentamiento político/social)
    "malo": -1.0, "pesimo": -1.6, "horrible": -1.6, "fracaso": -1.5, "problema": -0.9, "defecto": -1.0,
    "error": -0.9, "estafa": -1.8, "critica": -0.9, "criticas": -1.0, "critico": -0.9, "decepcion": -1.4,
    "lamentable": -1.3, "inutil": -1.2, "peligro": -1.3, "riesgo": -0.8, "grave": -1.2, "caro": -0.8,
    "lento": -0.7, "caida": -1.0, "peor": -1.4, "verguenza": -1.5, "vergonzoso": -1.5, "preocupante": -1.1,
    "fallo": -1.1, "fallos": -1.1, "desastre": -1.6, "queja": -0.9, "quejas": -1.0, "escandalo": -1.5,
    "escandalos": -1.5, "polemica": -1.0, "polemicas": -1.1, "polemico": -1.0, "abuso": -1.5, "descontento": -1.1,
    "burbuja": -1.0, "perdida": -1.2, "perdidas": -1.2, "rechazo": -1.2, "rechaza": -1.2, "rechazan": -1.2,
    "duda": -0.6, "dudas": -0.7, "fraude": -1.8, "conflicto": -1.1, "quiebra": -1.7, "bajista": -1.2,
    "deuda": -0.8, "sancion": -1.2, "demanda": -1.0, "despido": -1.3, "despidos": -1.3, "colapso": -1.7,
    "corrupto": -1.8, "corrupta": -1.8, "corrupcion": -1.8, "corruptela": -1.6, "traidor": -1.8, "traicion": -1.8,
    "mentiroso": -1.7, "mentirosa": -1.7, "mentira": -1.5, "mentiras": -1.5, "bulo": -1.4, "bulos": -1.4,
    "fango": -1.6, "enchufismo": -1.5, "inepto": -1.6, "inepta": -1.6, "incompetente": -1.5, "incompetencia": -1.5,
    "dimision": -1.4, "dimitir": -1.3, "arruinar": -1.6, "ruina": -1.6, "destruccion": -1.6, "lawfare": -1.4,
    "prevaricacion": -1.7, "malversacion": -1.8, "impeachment": -1.5, "censura": -1.4, "sectario": -1.4,
    "sectarismo": -1.4, "radical": -1.2, "radicales": -1.2, "extremista": -1.4, "crispacion": -1.4,
    "chantaje": -1.5, "sumision": -1.4, "tirano": -1.8, "dictador": -1.8, "dictadura": -1.8, "fascista": -1.7,
    "fascismo": -1.7, "comunista": -1.2, "odio": -1.6, "acoso": -1.5, "sanchismo": -1.3, "ultraderecha": -1.4,
    "golpista": -1.8, "golpe": -1.5, "bochorno": -1.4, "arremete": -1.4, "arremeten": -1.4, "estalla": -1.3,
    "abucheo": -1.5, "abucheos": -1.6, "bronca": -1.4, "insulto": -1.5, "insultos": -1.5, "imputacion": -1.6,
    "imputado": -1.6, "imputada": -1.7, "sospechoso": -1.2, "sospechas": -1.3, "sospecha": -1.2, "reves": -1.4,
    "estupidez": -1.6, "ridiculo": -1.5, "desesperacion": -1.4, "indignacion": -1.3, "embestida": -1.4,
    "acusaciones": -1.2, "acusacion": -1.2, "acusa": -1.2, "acusan": -1.2, "senalamiento": -1.3,
    "senalamientos": -1.3, "antidemocracia": -1.8, "antidemocratico": -1.7, "estrella": -1.3, "culpa": -1.2,
    "culpan": -1.2, "culpar": -1.2, "reprobacion": -1.5, "reprobado": -1.5, "deplorable": -1.5, "ilegitimo": -1.7,
    # Negative English
    "bad": -1.0, "terrible": -1.6, "horrible": -1.6, "failure": -1.5, "defect": -1.0, "error": -0.9,
    "scam": -1.8, "disappointment": -1.4, "danger": -1.3, "risk": -0.8, "expensive": -0.8, "slow": -0.7,
    "worst": -1.5, "disaster": -1.6, "complaint": -0.9, "scandal": -1.5, "controversy": -0.9, "loss": -1.2,
    "crash": -1.6, "hate": -1.5, "bearish": -1.2, "lawsuit": -1.2, "layoff": -1.3, "collapse": -1.7,
    "corrupt": -1.8, "traitor": -1.8, "liar": -1.7, "impeach": -1.5, "tyrant": -1.8, "fascist": -1.7,
    "slams": -1.6, "blasts": -1.6, "indicted": -1.8, "accuses": -1.3, "attack": -1.3, "attacks": -1.4
}

EMOTION_PATTERNS = {
    "Entusiasmo & Respaldo": ["increible", "revolucion", "prometedor", "futuro", "genial", "innovador", "amazing", "great", "liderazgo", "victoria", "triunfo", "respaldo", "subida", "exito"],
    "Confrontación & Furia": ["traicion", "fango", "corrupcion", "golpista", "mentiroso", "escandalo", "verguenza", "dimision", "odio", "scandal", "liar", "corrupt", "arremete", "abucheo", "bronca", "acusaciones", "embestida", "antidemocracia"],
    "Crítica & Decepción": ["decepcion", "estafa", "peor", "fallo", "caro", "terrible", "scam", "disappointment", "crash", "fracaso", "critica", "criticas"],
    "Cautela & Preocupación": ["cuidado", "riesgo", "peligro", "preocupante", "duda", "alerta", "risk", "warning", "burbuja", "crisis", "sospecha"],
    "Debate & Polarización": ["debate", "elecciones", "congreso", "votos", "polarizacion", "encuesta", "pacto", "ley", "tribunal", "politica", "reforma", "postura"],
    "Neutral & Informativo": ["anuncia", "presenta", "informe", "datos", "oficial", "fecha", "report", "news", "reunion"]
}

DOMAIN_KEYWORDS = {
    "Política & Sociedad": [
        "trump", "donald trump", "sanchez", "pedro sanchez", "feijoo", "alberto nunez feijoo", "ayuso",
        "vox", "psoe", "pp", "sumar", "podemos", "biden", "harris", "amnistia", "elecciones",
        "gobierno", "oposicion", "congreso", "senado", "politica", "reforma", "presidente", "ministro",
        "corrupcion", "koldo", "begona", "alvise", "polarizacion", "fango", "bipartidismo", "maga",
        "ley", "tribunal", "fiscalia", "fiscal general", "supremo", "impuestos", "sociedad", "huelga"
    ],
    "Finanzas & Economía": [
        "accion", "acciones", "stock", "stocks", "spacex", "tesla", "nasdaq", "bolsa", "inversion",
        "mercado", "crypto", "bitcoin", "ingresos", "beneficio", "ipo", "dividendo", "finanzas",
        "economia", "valuation", "revenue", "fed", "inflacion", "banco", "venture", "patrimonio"
    ],
    "Tecnología & Software": [
        "ia", "ai", "llm", "software", "hardware", "apple", "iphone", "nvidia", "deepseek", "chatgpt",
        "gemini", "framework", "codigo", "api", "chip", "servidor", "gpu", "app", "linux", "cloud"
    ],
    "Entretenimiento & Marcas B2C": [
        "pelicula", "serie", "juego", "videojuego", "musica", "concierto", "netflix", "spotify",
        "cine", "actor", "cancion", "evento", "viral", "disney", "ps5", "xbox", "trailer"
    ]
}

DOMAIN_WEIGHTS = {
    "Política & Sociedad": {
        "Medios / Noticias": 0.40,
        "X / Twitter": 0.35,
        "Reddit": 0.25,
        "Otras Fuentes": 0.10
    },
    "Finanzas & Economía": {
        "Medios / Noticias": 0.45,
        "Reddit": 0.35,
        "X / Twitter": 0.20,
        "Otras Fuentes": 0.10
    },
    "Tecnología & Software": {
        "Reddit": 0.45,
        "X / Twitter": 0.30,
        "Medios / Noticias": 0.25,
        "Otras Fuentes": 0.10
    },
    "Entretenimiento & Marcas B2C": {
        "X / Twitter": 0.45,
        "Reddit": 0.35,
        "Medios / Noticias": 0.20,
        "Otras Fuentes": 0.10
    },
    "General / Multitemático": {
        "Medios / Noticias": 0.35,
        "Reddit": 0.35,
        "X / Twitter": 0.30,
        "Otras Fuentes": 0.15
    }
}

def detect_domain_category(topic: str, mentions: List[Dict[str, Any]]) -> str:
    clean_topic = strip_accents(topic.lower())
    combined_text = (clean_topic + " " + " ".join(strip_accents(m.get("title", "")).lower() for m in mentions[:15]))
    
    scores = {category: 0 for category in DOMAIN_KEYWORDS}
    for category, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            clean_kw = strip_accents(kw.lower())
            if clean_kw in clean_topic:
                scores[category] += 4
            elif re.search(r"\b" + re.escape(clean_kw) + r"\b", combined_text):
                scores[category] += 1
                
    best_category = max(scores, key=scores.get)
    if scores[best_category] > 0:
        return best_category
    return "General / Multitemático"

def analyze_clause_valence(clause_text: str, target_topic: str = "") -> Tuple[float, int, List[str]]:
    """Calcula la valencia semántica de una cláusula considerando N-gramas, intensificadores y negaciones."""
    lower_clause = strip_accents(clause_text.lower().strip())
    score_accumulator = 0.0
    detected_markers = []
    
    # 1. Check Contextual Complex Phrases First (Highest precision)
    for phrase, phrase_score in CONTEXTUAL_PHRASES.items():
        clean_phrase = strip_accents(phrase)
        if clean_phrase in lower_clause:
            score_accumulator += phrase_score
            detected_markers.append(f"Frase: '{phrase}' ({phrase_score:+.1f})")
            lower_clause = lower_clause.replace(clean_phrase, " ")

    words = re.findall(r"\b\w+\b", lower_clause)
    negations = {"no", "nunca", "jamas", "not", "never", "sin", "tampoco", "nada", "nadie"}
    
    current_modifier = 1.0
    negated = False
    negation_window = 0
    
    for i, w in enumerate(words):
        if w in negations:
            negated = True
            negation_window = 3
            continue
            
        if w in BOOSTERS:
            current_modifier = BOOSTERS[w]
            continue
        elif w in DAMPENERS:
            current_modifier = DAMPENERS[w]
            continue
            
        if w in LEXICON_VALENCE:
            base_val = LEXICON_VALENCE[w]
            
            if negated and negation_window > 0:
                final_word_val = -base_val * 0.75
                detected_markers.append(f"Negación: 'no {w}' ({final_word_val:+.2f})")
            else:
                final_word_val = base_val * current_modifier
                detected_markers.append(f"Término: '{w}' ({final_word_val:+.2f})")
                
            score_accumulator += final_word_val
            current_modifier = 1.0
            
        if negation_window > 0:
            negation_window -= 1
            if negation_window == 0:
                negated = False
                
    return score_accumulator, len(words), detected_markers

def analyze_text_sentiment(text: str, target_topic: str = "") -> Tuple[float, str, str, float, str]:
    if not text or not text.strip():
        return 0.0, "Neutral", "Neutral & Informativo", 0.5, "Texto vacío"
        
    lower_text = strip_accents(text.lower())
    
    contrast_match = re.split(r"\b(pero|sin embargo|no obstante|aunque|yet|but|however)\b", lower_text)
    
    if len(contrast_match) >= 3:
        clause_1 = contrast_match[0]
        clause_2 = "".join(contrast_match[2:])
        
        score_1, len_1, markers_1 = analyze_clause_valence(clause_1, target_topic)
        score_2, len_2, markers_2 = analyze_clause_valence(clause_2, target_topic)
        
        raw_score = (score_1 * 0.3) + (score_2 * 0.7)
        total_len = len_1 + len_2
        all_markers = markers_1 + markers_2
        method_desc = "Análisis Cláusula Contrastiva ('pero' / 'sin embargo')"
    else:
        raw_score, total_len, all_markers = analyze_clause_valence(lower_text, target_topic)
        method_desc = "Parsed Contextual de Valencia & Modificadores"
        
    normalized_score = math.tanh(raw_score * 0.65)
    normalized_score = round(normalized_score, 3)
    
    marker_count = len(all_markers)
    if marker_count >= 3:
        confidence = min(0.96, 0.75 + (marker_count * 0.05))
    elif marker_count >= 1:
        confidence = min(0.85, 0.65 + (marker_count * 0.08))
    else:
        confidence = 0.60
        
    confidence = round(confidence, 2)
    
    if normalized_score >= 0.12:
        label = "Positivo"
    elif normalized_score <= -0.12:
        label = "Negativo"
    else:
        label = "Neutral"
        
    detected_emotion = "Neutral & Informativo"
    max_emotion_hits = 0
    for emotion, kws in EMOTION_PATTERNS.items():
        hits = sum(1 for kw in kws if kw in lower_text)
        if hits > max_emotion_hits:
            max_emotion_hits = hits
            detected_emotion = emotion
            
    if max_emotion_hits == 0:
        if label == "Positivo":
            detected_emotion = "Entusiasmo & Respaldo"
        elif label == "Negativo":
            detected_emotion = "Crítica & Decepción"
            
    if all_markers:
        method_summary = f"{method_desc}: {', '.join(all_markers[:2])}"
    else:
        method_summary = "Factual / Informativo sin carga polarizada"
        
    return normalized_score, label, detected_emotion, confidence, method_summary

def calculate_polarization_index(pos_pct: float, neu_pct: float, neg_pct: float, total_count: int) -> Dict[str, Any]:
    """
    Calcula el ÍNDICE DE POLARIZACIÓN & CONTROVERSIA SOCIAL (PI).
    Mide la bimodalidad (enfrentamiento directo de dos bandos extremos sin término medio).
    """
    if total_count == 0 or (pos_pct + neg_pct) == 0:
        return {
            "score": 0,
            "label": "Consenso / Sin Fricción",
            "level": "low",
            "description": "No se detecta polarización apreciable en la muestra analizada.",
            "badge_color": "text-slate-300 bg-slate-800 border-slate-700",
            "icon": "fa-handshake"
        }
        
    stance_ratio = (pos_pct + neg_pct) / 100.0
    imbalance = abs(pos_pct - neg_pct) / max(pos_pct + neg_pct, 1.0)
    balance_factor = 1.0 - imbalance
    
    # Mathematical Bimodality Formula
    raw_pi = (balance_factor ** 0.7) * (stance_ratio ** 0.35) * 100.0
    
    if pos_pct >= 10.0 and neg_pct >= 10.0:
        raw_pi = max(raw_pi, 50.0 + (min(pos_pct, neg_pct) * 1.5))
        
    pi_score = min(100, max(0, round(raw_pi, 1)))
    
    if pi_score >= 70:
        return {
            "score": pi_score,
            "label": "🔥 Guerra de Trincheras / Polarización Extrema",
            "level": "extreme",
            "description": f"Debate altamente fracturado: Fuertes núcleos de defensores ({pos_pct}%) y detractores ({neg_pct}%) enfrentados sin consenso central.",
            "badge_color": "text-rose-400 bg-rose-500/10 border-rose-500/30 animate-pulse",
            "icon": "fa-fire-flame-curved"
        }
    elif pi_score >= 45:
        return {
            "score": pi_score,
            "label": "⚡ Fuerte Enfrentamiento / Alta Polarización",
            "level": "high",
            "description": f"Opinión dividida en dos bloques notorios ({pos_pct}% a favor vs {neg_pct}% en contra). Fricción constante en redes.",
            "badge_color": "text-amber-400 bg-amber-500/10 border-amber-500/30",
            "icon": "fa-bolt"
        }
    elif pi_score >= 20:
        return {
            "score": pi_score,
            "label": "⚖️ Debate Plural / Polarización Moderada",
            "level": "moderate",
            "description": f"Existe diversidad de criterios ({neu_pct}% neutralidad/análisis), con debate activo pero sin crispación extrema.",
            "badge_color": "text-sky-400 bg-sky-500/10 border-sky-500/30",
            "icon": "fa-scale-balanced"
        }
    else:
        return {
            "score": pi_score,
            "label": "🤝 Consenso / Baja Controversia",
            "level": "low",
            "description": f"Percepción mayoritariamente alineada en una misma dirección ({max(pos_pct, neg_pct, neu_pct)}% en la opción predominante).",
            "badge_color": "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
            "icon": "fa-handshake"
        }

def extract_key_phrases(mentions: List[Dict[str, Any]], top_n: int = 8) -> List[str]:
    stop_words = {
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "no", "una",
        "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o", "este", "si", "porque", "esta", "entre",
        "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos",
        "the", "and", "to", "of", "a", "in", "is", "it", "you", "that", "he", "was", "for", "on", "are", "as", "with"
    }
    words_list = []
    for m in mentions:
        text = f"{m.get('title', '')} {m.get('content', '')}".lower()
        words = re.findall(r"\b[a-záéíóúñ]{4,}\b", text)
        for w in words:
            if w not in stop_words and not w.isdigit():
                words_list.append(w)
    counts = Counter(words_list)
    return [word.capitalize() for word, _ in counts.most_common(top_n)]

def compute_chronological_timeline(scored_mentions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not scored_mentions:
        return [], {"direction": "Estable", "delta": 0.0, "icon": "fa-arrow-right", "color": "text-slate-300"}
        
    date_groups = defaultdict(lambda: {"pos": 0, "neu": 0, "neg": 0, "weighted_sum": 0.0, "weight_total": 0.0, "count": 0})
    
    for m in scored_mentions:
        iso_d = m.get("iso_date", "") or datetime.now().strftime("%Y-%m-%d")
        lbl = m.get("sentiment_label", "Neutral")
        w = m.get("applied_weight", 1.0)
        s = m.get("sentiment_score", 0.0)
        c = m.get("confidence", 0.7)
        
        effective_w = w * c
        date_groups[iso_d]["count"] += 1
        date_groups[iso_d]["weighted_sum"] += (s * effective_w)
        date_groups[iso_d]["weight_total"] += effective_w
        
        if lbl == "Positivo":
            date_groups[iso_d]["pos"] += 1
        elif lbl == "Negativo":
            date_groups[iso_d]["neg"] += 1
        else:
            date_groups[iso_d]["neu"] += 1
            
    sorted_dates = sorted(date_groups.keys())
    timeline_points = []
    
    for d in sorted_dates:
        grp = date_groups[d]
        total_w = grp["weight_total"] or 1.0
        avg_nsi = round((grp["weighted_sum"] / total_w) * 100, 1)
        timeline_points.append({
            "date": d,
            "display_date": d[5:] if len(d) >= 10 else d,
            "nsi": avg_nsi,
            "positive_count": grp["pos"],
            "neutral_count": grp["neu"],
            "negative_count": grp["neg"],
            "count": grp["count"]
        })
        
    if len(timeline_points) >= 2:
        mid = len(timeline_points) // 2
        early_nsi = sum(p["nsi"] for p in timeline_points[:mid]) / max(mid, 1)
        recent_nsi = sum(p["nsi"] for p in timeline_points[mid:]) / max(len(timeline_points) - mid, 1)
        delta = round(recent_nsi - early_nsi, 1)
        
        if delta >= 8.0:
            trend_info = {
                "direction": "Tendencia Alcista (Mejorando)",
                "delta": delta,
                "icon": "fa-arrow-trend-up",
                "color": "text-emerald-400",
                "badge": "bg-emerald-500/10 border-emerald-500/30"
            }
        elif delta <= -8.0:
            trend_info = {
                "direction": "Tendencia Bajista (Deteriorándose)",
                "delta": delta,
                "icon": "fa-arrow-trend-down",
                "color": "text-rose-400",
                "badge": "bg-rose-500/10 border-rose-500/30"
            }
        else:
            trend_info = {
                "direction": "Tendencia Estable / Consolidada",
                "delta": delta,
                "icon": "fa-arrows-left-right",
                "color": "text-slate-300",
                "badge": "bg-slate-700/40 border-slate-600/30"
            }
    else:
        trend_info = {
            "direction": "Tendencia Estable",
            "delta": 0.0,
            "icon": "fa-arrows-left-right",
            "color": "text-slate-300",
            "badge": "bg-slate-700/40 border-slate-600/30"
        }
        
    return timeline_points, trend_info

def process_and_score_mentions(mentions: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
    """
    Procesa y clasifica menciones con PONDERACIÓN BAYESIANA CONTEXTUAL,
    VALENCIA CONTINUA, ÍNDICE DE POLARIZACIÓN Y CONFIANZA ESTADÍSTICA.
    """
    if not mentions:
        return {
            "total_count": 0,
            "detected_domain": "General / Multitemático",
            "active_weights": DOMAIN_WEIGHTS["General / Multitemático"],
            "net_sentiment_index": 0,
            "weighted_nsi": 0,
            "polarization": {"score": 0, "label": "Sin Datos", "level": "low", "description": ""},
            "distribution": {"positive": 0, "neutral": 100, "negative": 0},
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "platform_breakdown": {},
            "emotion_breakdown": {},
            "key_phrases": [],
            "top_positive_quotes": [],
            "top_negative_quotes": [],
            "timeline": [],
            "trend": {"direction": "Estable", "delta": 0.0, "icon": "fa-arrows-left-right", "color": "text-slate-300"},
            "scored_mentions": []
        }
        
    detected_domain = detect_domain_category(topic, mentions)
    active_weights = DOMAIN_WEIGHTS.get(detected_domain, DOMAIN_WEIGHTS["General / Multitemático"])
    
    scored = []
    pos_count = 0
    neu_count = 0
    neg_count = 0
    
    weighted_sentiment_sum = 0.0
    total_effective_weight = 0.0
    
    platform_data: Dict[str, Dict[str, int]] = {}
    emotion_counts: Dict[str, int] = {}
    
    for m in mentions:
        full_text = f"{m.get('title', '')} {m.get('content', '')}"
        
        # 1. Scientific Semantic Analysis
        score, label, emotion, confidence, method_info = analyze_text_sentiment(full_text, target_topic=topic)
        
        # 2. Source Authority Weight
        plat = m.get("platform", "Otras Fuentes")
        plat_weight = active_weights.get(plat, active_weights.get("Otras Fuentes", 0.10))
        if "Medios" in plat or "Noticias" in plat:
            plat_weight = active_weights.get("Medios / Noticias", 0.35)
        elif "Reddit" in plat:
            plat_weight = active_weights.get("Reddit", 0.35)
        elif "Twitter" in plat or "X" in plat or "Redes" in plat or "Facebook" in plat:
            plat_weight = active_weights.get("X / Twitter", 0.30)
            
        # 3. Engagement Multiplier
        raw_score = m.get("score", 1)
        engagement_factor = 1.0 + min(2.0, math.log10(max(raw_score, 1) + 1))
        
        # 4. Final Composite Weight: w = W_source * Engagement * Confidence
        final_mention_weight = round(plat_weight * engagement_factor * confidence, 3)
        
        weighted_sentiment_sum += (score * final_mention_weight)
        total_effective_weight += final_mention_weight
        
        m_copy = dict(m)
        m_copy["sentiment_score"] = score
        m_copy["sentiment_label"] = label
        m_copy["detected_emotion"] = emotion
        m_copy["confidence"] = int(confidence * 100)
        m_copy["method_info"] = method_info
        m_copy["applied_weight"] = final_mention_weight
        scored.append(m_copy)
        
        if label == "Positivo":
            pos_count += 1
        elif label == "Negativo":
            neg_count += 1
        else:
            neu_count += 1
            
        if plat not in platform_data:
            platform_data[plat] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
        platform_data[plat]["total"] += 1
        if label == "Positivo":
            platform_data[plat]["positive"] += 1
        elif label == "Negativo":
            platform_data[plat]["negative"] += 1
        else:
            platform_data[plat]["neutral"] += 1
            
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
    total_count = len(scored)
    pos_pct = round((pos_count / total_count) * 100, 1)
    neu_pct = round((neu_count / total_count) * 100, 1)
    neg_pct = round((neg_count / total_count) * 100, 1)
    
    simple_nsi = round(pos_pct - neg_pct, 1)
    weighted_nsi = round((weighted_sentiment_sum / total_effective_weight) * 100, 1) if total_effective_weight > 0 else simple_nsi
    
    # 5. Scientific Polarization Index (PI)
    polarization_data = calculate_polarization_index(pos_pct, neu_pct, neg_pct, total_count)
    
    sorted_by_pos = sorted([m for m in scored if m["sentiment_label"] == "Positivo"], key=lambda x: x["sentiment_score"], reverse=True)
    sorted_by_neg = sorted([m for m in scored if m["sentiment_label"] == "Negativo"], key=lambda x: x["sentiment_score"])
    
    top_positive = sorted_by_pos[:4]
    top_negative = sorted_by_neg[:4]
    key_phrases = extract_key_phrases(scored, top_n=10)
    
    timeline_points, trend_info = compute_chronological_timeline(scored)
    
    return {
        "total_count": total_count,
        "detected_domain": detected_domain,
        "active_weights": active_weights,
        "net_sentiment_index": simple_nsi,
        "weighted_nsi": weighted_nsi,
        "polarization": polarization_data,
        "distribution": {
            "positive": pos_pct,
            "neutral": neu_pct,
            "negative": neg_pct
        },
        "positive_count": pos_count,
        "neutral_count": neu_count,
        "negative_count": neg_count,
        "platform_breakdown": platform_data,
        "emotion_breakdown": emotion_counts,
        "key_phrases": key_phrases,
        "top_positive_quotes": top_positive,
        "top_negative_quotes": top_negative,
        "timeline": timeline_points,
        "trend": trend_info,
        "scored_mentions": scored
    }
