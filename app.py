from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash') # Usamos flash estable para consistencia en JSON

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/generar-casos', methods=['POST'])
def generar_casos():
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    # Ajustamos la complejidad de los casos según la dificultad
    guia_casos = {
        "Principiante": "Casos con hechos claros, pruebas directas y una solución jurídica evidente.",
        "Intermedio": "Casos con contradicciones leves entre testimonios y necesidad de citar códigos básicos.",
        "Avanzado": "Casos complejos con vacíos probatorios, conflictos de derechos fundamentales y tecnicismos procesales."
    }

    prompt = f"""
    Eres un Magistrado de Colombia. Genera EXACTAMENTE 5 casos de {categoria} (Nivel: {dificultad}).
    Contexto del nivel: {guia_casos.get(dificultad, "")}
    
    Cada 'descripcion' debe ser de 200 palabras.
    Responde ÚNICAMENTE un array JSON puro:
    [
      {{"id": 1, "titulo": "...", "descripcion": "..."}}
    ]
    """
    try:
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify([{"id": 0, "titulo": "Error", "descripcion": "Fallo al conectar con la IA."}]), 200

@app.route('/debatir', methods=['POST'])
def debatir():
    data = request.json
    argumento = data.get('argumento', '')
    caso = data.get('caso', '')
    rol = data.get('rol', '')
    turnos = data.get('turnos', 0)
    dificultad = data.get('dificultad', 'Principiante') # Valor por defecto

    # --- LÓGICA DE CALIBRACIÓN DE DIFICULTAD ---
    config_dificultad = {
        "Principiante": {
            "personalidad": "Pedagógico y comprensivo. Valora más la intención que la técnica.",
            "exigencia": "Califica generosamente (70-90) si el argumento tiene sentido común.",
            "critica": "Da consejos constructivos y sencillos."
        },
        "Intermedio": {
            "personalidad": "Litigante estándar. Exige coherencia y mención general de leyes.",
            "exigencia": "Califica estrictamente (50-80). Solo da puntaje alto si hay base legal.",
            "critica": "Señala errores lógicos y falta de sustento."
        },
        "Avanzado": {
            "personalidad": "Fiscal implacable de la Corte Suprema. Detecta falacias y errores procedimentales.",
            "exigencia": "Califica con dureza (10-60). Solo da más de 70 si cita artículos exactos y jurisprudencia.",
            "critica": "Es mordaz y técnico. Ataca los puntos débiles del argumento sin piedad."
        }
    }
    
    conf = config_dificultad.get(dificultad, config_dificultad["Principiante"])

    prompt = f"""
    Eres un litigante experto en Colombia. Actúa como contraparte en una audiencia real.
    Nivel de Dificultad: {dificultad}. 
    TU PERSONALIDAD: {conf['personalidad']}
    CRITERIO DE CALIFICACIÓN: {conf['exigencia']}

    Caso: {caso}.
    Usuario ({rol}) argumenta: "{argumento}".
    Turno: {turnos}/8.

    REGLAS DE ORO:
    1. Si el usuario no cita leyes colombianas y el nivel es Avanzado, su puntaje en Fundamentación Legal debe ser inferior a 30.
    2. Tu 'respuesta_ia' debe durar máximo 90 palabras y usar lenguaje jurídico colombiano.
    3. El 'feedback_sutil' debe reflejar la dureza del nivel: {conf['critica']}

    Responde ÚNICAMENTE en JSON:
    {{
      "respuesta_ia": "...",
      "analisis": {{
        "fundamentacion_legal": 0, "coherencia_logica": 0, "persuasion_retorica": 0,
        "tecnica_procesal": 0, "uso_terminologia": 0, "feedback_sutil": "...",
        "habilidades": {{ "estrategia": 0, "objeciones": 0, "claridad": 0, "evidencia": 0, "psicologia": 0 }}
      }},
      "finalizar": {str(turnos >= 8).lower()},
      "sentencia": "..."
    }}
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)