from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# 1. Carga de variables de entorno
load_dotenv()

# 2. Configuración de Flask para servir el frontend desde la carpeta 'frontend'
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Usamos el modelo estable 1.5-flash
model = genai.GenerativeModel('gemini-1.5-flash')

# --- RUTA RAÍZ: ESTA ES LA QUE EVITA EL ERROR 404 ---
@app.route('/')
def index():
    """Sirve el archivo index.html desde la carpeta frontend."""
    return send_from_directory(app.static_folder, 'index.html')

# --- ENDPOINTS DE LA API ---

@app.route('/generar-casos', methods=['POST'])
def generar_casos():
    """Genera 5 expedientes extensos basados en leyes colombianas."""
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    prompt = f"""
    Eres un Magistrado de la República de Colombia. 
    Genera 5 casos ficticios detallados de {categoria} en COLOMBIA.
    Nivel: {dificultad}.
    
    Cada 'descripcion' debe ser EXTENSA (mínimo 200 palabras) e incluir:
    1. Hechos: Relato detallado con lugares exactos en Colombia (barrios, ciudades).
    2. Pruebas: Menciona testimonios, documentos o videos disponibles.
    3. Problema Jurídico: La controversia a resolver.

    Responde ÚNICAMENTE con un array JSON.
    [
      {{"id": 1, "titulo": "Nombre del Proceso", "descripcion": "Texto jurídico largo..."}}
    ]
    """
    try:
        # Forzamos respuesta en formato JSON nativo
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error en generación: {e}")
        # Casos de respaldo por seguridad
        backup = [
            {"id": 1, "titulo": "Litigio de Tierras en Urabá", "descripcion": "Relato extenso sobre despojo y restitución de tierras bajo la Ley 1448..."},
            {"id": 2, "titulo": "Responsabilidad Médica en Cali", "descripcion": "Caso detallado sobre presunta mala praxis en procedimiento estético..."}
        ]
        return jsonify(backup), 200

@app.route('/debatir', methods=['POST'])
def debatir():
    """Maneja el debate jurídico."""
    data = request.json
    argumento = data.get('argumento', '')
    caso = data.get('caso', '')
    rol = data.get('rol', '')
    turnos = data.get('turnos', 0)
    dificultad = data.get('dificultad', 'Intermedio')

    finalizar = turnos >= 8
    contraparte = "Fiscalía" if rol == "Abogado Defensor" else "Abogado Defensor"

    prompt = f"""
    Eres un litigante experto en Colombia ({contraparte}). Caso: {caso}.
    El usuario ({rol}) argumenta: "{argumento}".
    Turno actual: {turnos}/8. Responde en JSON con: respuesta_ia, analisis, finalizar, sentencia.
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 200

# 4. Configuración del puerto para Render
if __name__ == '__main__':
    # Render usa la variable PORT. En local usa el 5000 por defecto.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)