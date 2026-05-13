from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# 1. Carga de variables de entorno
load_dotenv()

# 2. Configuración de Flask para servir el HTML desde la carpeta 'frontend'
app = Flask(__name__, static_folder='frontend', static_url_path='')

# CORS configurado para permitir todo
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# --- RUTA PARA MOSTRAR EL SITIO WEB ---
@app.route('/')
def index():
    """Sirve el archivo index.html desde la carpeta frontend."""
    return send_from_directory(app.static_folder, 'index.html')

# --- ENDPOINTS DE LA API ---

@app.route('/generar-casos', methods=['POST'])
def generar_casos():
    """Genera 5 expedientes detallados de Colombia."""
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    prompt = f"""
    Eres un Magistrado experto en el sistema jurídico de COLOMBIA. 
    Genera 5 casos ficticios detallados de {categoria} ambientados en COLOMBIA.
    Nivel de complejidad: {dificultad}.
    
    Cada 'descripcion' debe ser EXTENSA (mínimo 200 palabras) e incluir:
    - Hechos detallados (lugares y fechas en Colombia).
    - Pruebas mencionadas.
    - Problema jurídico.

    Responde EXCLUSIVAMENTE con un array JSON puro:
    [
      {{"id": 1, "titulo": "Nombre del Caso", "descripcion": "Texto jurídico largo..."}}
    ]
    """
    try:
        # Modo JSON nativo para evitar que se rompa
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error en generación: {e}")
        return jsonify([{"id": 1, "titulo": "Error de conexión", "descripcion": "No se pudo generar el caso detallado."}]), 200

@app.route('/debatir', methods=['POST'])
def debatir():
    """Maneja el debate jurídico."""
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
    Eres un litigante de élite ({contraparte}) experto en derecho de COLOMBIA.
    Analiza el argumento del usuario ({rol}): "{argumento}".
    Caso: {caso}.
    Responde ÚNICAMENTE en formato JSON:
    {{
      "respuesta_ia": "Refutación legal...",
      "analisis": {{ "fundamentacion_legal": 0, "coherencia_logica": 0, "persuasion_retorica": 0, "tecnica_procesal": 0, "uso_terminologia": 0, "feedback_sutil": "..." }},
      "finalizar": {str(finalizar).lower()},
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

# 4. CONFIGURACIÓN DEL PUERTO (Explicación abajo)
if __name__ == '__main__':
    # Render usa una variable de entorno llamada PORT. Si no existe, usa el 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)