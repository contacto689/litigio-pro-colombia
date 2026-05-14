from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# 1. Carga de variables de entorno
load_dotenv()

# 2. Configuración de Flask
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-3.1-flash-lite-preview')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# --- ENDPOINTS DE LA API ---

@app.route('/generar-casos', methods=['POST'])
def generar_casos():
    """Genera EXACTAMENTE 5 expedientes detallados."""
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    # CAMBIO IMPORTANTE: Instrucción explícita de 5 casos y formato robusto
    prompt = f"""
    Eres un Magistrado experto en el sistema jurídico de COLOMBIA. 
    Genera EXACTAMENTE 5 casos ficticios de {categoria} ambientados en COLOMBIA.
    Nivel de complejidad: {dificultad}.
    
    REQUISITOS:
    - Ubicación: Ciudades y barrios reales de Colombia.
    - Base Legal: Bloque de constitucionalidad y leyes colombianas.
    - Formato: Los 5 casos deben venir dentro de un único array JSON.

    Responde EXCLUSIVAMENTE con el array JSON puro, sin explicaciones ni markdown:
    [
      {{"id": 1, "titulo": "Caso 1", "descripcion": "Hechos..."}},
      {{"id": 2, "titulo": "Caso 2", "descripcion": "Hechos..."}},
      {{"id": 3, "titulo": "Caso 3", "descripcion": "Hechos..."}},
      {{"id": 4, "titulo": "Caso 4", "descripcion": "Hechos..."}},
      {{"id": 5, "titulo": "Caso 5", "descripcion": "Hechos..."}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # Limpieza más profunda: quitamos markdown y espacios innecesarios
        texto = response.text.strip()
        if "```json" in texto:
            texto = texto.split("```json")[1].split("```")[0].strip()
        elif "```" in texto:
            texto = texto.split("```")[1].split("```")[0].strip()
            
        return texto, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error en generación: {e}")
        # Retornamos un error que el frontend pueda pintar como una tarjeta
        return jsonify([{"id": 0, "titulo": "Error de Conexión", "descripcion": "No se pudieron cargar los casos. Verifica tu API Key en Render."}]), 200

@app.route('/debatir', methods=['POST'])
def debatir():
    data = request.json
    argumento = data.get('argumento', '')
    caso = data.get('caso', '')
    rol = data.get('rol', '')
    turnos = data.get('turnos', 0)
    dificultad = data.get('dificultad', 'Intermedio')

    limite_turnos = 8 
    finalizar = turnos >= limite_turnos
    contraparte = "Fiscalía" if rol == "Abogado Defensor" else "Abogado Defensor"

    prompt = f"""
    Eres un litigante de élite ({contraparte}) en COLOMBIA.
    Audiencia nivel {dificultad}. Caso: {caso}.
    Usuario ({rol}) argumenta: "{argumento}". Turno: {turnos}/8.

    REGLAS:
    1. Cita leyes colombianas reales.
    2. Responde en JSON puro con este formato:
    {{
      "respuesta_ia": "Refutación técnica",
      "analisis": {{
        "fundamentacion_legal": 0, "coherencia_logica": 0, "persuasion_retorica": 0,
        "tecnica_procesal": 0, "uso_terminologia": 0, "feedback_sutil": "Feedback",
        "habilidades": {{ "estrategia": 0, "objeciones": 0, "claridad": 0, "evidencia": 0, "psicologia": 0 }}
      }},
      "finalizar": {str(finalizar).lower()},
      "sentencia": "Solo si finalizar es true"
    }}
    """
    try:
        response = model.generate_content(prompt)
        texto = response.text.strip()
        if "```json" in texto:
            texto = texto.split("```json")[1].split("```")[0].strip()
        return texto, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 200

if __name__ == '__main__':
    # Configuración optimizada para Render
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)