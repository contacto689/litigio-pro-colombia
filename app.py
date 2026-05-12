from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# 1. Carga de variables de entorno
load_dotenv()

# 2. Configuración de Flask para servir el Frontend
# 'static_folder' le dice a Flask que busque los archivos en la carpeta frontend
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-1.5-flash') # Versión estable y rápida

# --- RUTA PARA SERVIR LA INTERFAZ WEB ---
@app.route('/')
def index():
    """Sirve el archivo index.html desde la carpeta frontend."""
    return send_from_directory(app.static_folder, 'index.html')

# --- RUTAS DE LA API ---

@app.route('/generar-casos', methods=['POST'])
def generar_casos():
    """Genera 5 expedientes basados en leyes y geografía colombiana."""
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    prompt = f"""
    Eres un Magistrado experto en el sistema jurídico de COLOMBIA. 
    Genera 5 casos ficticios de {categoria} ambientados en COLOMBIA.
    Nivel de complejidad: {dificultad}.
    
    REQUISITOS GEOGRÁFICOS:
    - Hechos en ciudades colombianas con barrios icónicos.

    REQUISITOS JURÍDICOS:
    - Basados en el Código Penal, Código Civil o Constitución Política de Colombia.

    Responde EXCLUSIVAMENTE con un array JSON puro, sin bloques de markdown:
    [
      {{"id": 1, "titulo": "Nombre del Caso", "descripcion": "Hechos detallados..."}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        return texto_limpio, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error en generación: {e}")
        return jsonify([{"id": 0, "titulo": "Error", "descripcion": "Problema al generar casos."}]), 200

@app.route('/debatir', methods=['POST'])
def debatir():
    """Maneja el debate enfocándose estrictamente en leyes colombianas."""
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
    Eres un litigante de élite ({contraparte}) experto en el derecho de COLOMBIA.
    Audiencia colombiana. Nivel: {dificultad}. Caso: {caso}.
    El usuario ({rol}) argumenta: "{argumento}".
    Turno: {turnos}/8.

    REGLAS:
    1. Usa la Constitución de 1991 y leyes colombianas.
    2. Castiga si citan leyes extranjeras.

    Responde ÚNICAMENTE en JSON puro:
    {{
      "respuesta_ia": "Refutación legal colombiana (máx 90 palabras)",
      "analisis": {{
        "fundamentacion_legal": 0, "coherencia_logica": 0, "persuasion_retorica": 0,
        "tecnica_procesal": 0, "uso_terminologia": 0, "feedback_sutil": "Crítica breve",
        "habilidades": {{ "estrategia": 0, "objeciones": 0, "claridad": 0, "evidencia": 0, "psicologia": 0 }}
      }},
      "finalizar": {str(finalizar).lower()},
      "sentencia": "Si finalizar es true, dicta sentencia 'En nombre de la República de Colombia'."
    }}
    """
    try:
        response = model.generate_content(prompt)
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        return texto_limpio, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 200

# 4. Ejecución del Servidor
if __name__ == '__main__':
    # Si estamos en Render, usamos su puerto; si no, el 8000
    port = int(os.environ.get('PORT', 8000))
    # En Render host debe ser 0.0.0.0
    app.run(host='0.0.0.0', port=port, debug=not os.environ.get('RENDER'))