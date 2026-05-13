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

# CORS configurado para permitir todo en desarrollo local
# Modifica la línea de CORS en app.py
# Reemplaza 'tu-usuario.github.io' por tu nombre real de GitHub
# Reemplaza las líneas 16 a 23 de tu app.py por esto:
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Usamos el modelo estándar para asegurar compatibilidad en Render
model = genai.GenerativeModel('gemini-1.5-flash')

# --- RUTA PARA MOSTRAR EL SITIO WEB (Evita el error 404) ---
@app.route('/')
def index():
    """Sirve el archivo index.html cuando entras al enlace principal."""
    return send_from_directory(app.static_folder, 'index.html')

# --- ENDPOINTS DE LA API ---

@app.route('/generar-casos', methods=['POST'])
def generar_casos():
    """Genera 1 expedientes basados en leyes y geografía colombiana."""
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    prompt = f"""
    Eres un Magistrado experto en el sistema jurídico de COLOMBIA. 
    Genera 1 casos ficticios de {categoria} ambientados en COLOMBIA.
    Nivel de complejidad: {dificultad}.
    
    REQUISITOS GEOGRÁFICOS:
    - Los hechos deben ocurrir en ciudades colombianas (ej: Bogotá, Medellín, Barranquilla, Cali, Bucaramanga, etc.)
    - Nombra barrios o lugares icónicos de esas ciudades para dar realismo.

    REQUISITOS JURÍDICOS:
    - Los conflictos deben estar basados en el bloque de constitucionalidad de Colombia y leyes locales (Código Penal Colombiano, Código Civil, etc.)

    Responde EXCLUSIVAMENTE con un array JSON puro, sin bloques de markdown:
    [
      {{"id": 1, "titulo": "Nombre del Caso", "descripcion": "Hechos detallados ocurridos en Colombia"}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        return texto_limpio, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"Error en generación: {e}")
        return jsonify([{"id": 0, "titulo": "Error", "descripcion": "Problema al generar casos colombianos."}]), 200

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
    Estamos en una audiencia en una sala de justicia colombiana.
    Nivel de debate: {dificultad}. Caso: {caso}.
    El usuario ({rol}) argumenta: "{argumento}".
    Turno actual: {turnos}/8.

    REGLAS DE ORO:
    1. Solo puedes citar la Constitución Política de Colombia de 1991 y leyes colombianas.
    2. Si el usuario cita leyes de otros países o principios que no aplican en Colombia, castiga su puntuación en 'Fundamentación Legal'.
    3. Si la dificultad es 'Avanzado', exige citas exactas de artículos (ej: Art. 29 de la Constitución, Ley 906, etc.)

    Responde ÚNICAMENTE en formato JSON puro:
    {{
      "respuesta_ia": "Tu refutación legal basada en ley colombiana (máx 90 palabras)",
      "analisis": {{
        "fundamentacion_legal": 0, "coherencia_logica": 0, "persuasion_retorica": 0,
        "tecnica_procesal": 0, "uso_terminologia": 0, "feedback_sutil": "Una línea de crítica",
        "habilidades": {{ "estrategia": 0, "objeciones": 0, "claridad": 0, "evidencia": 0, "psicologia": 0 }}
      }},
      "finalizar": {str(finalizar).lower()},
      "sentencia": "Si finalizar es true, dicta una sentencia magistral 'En nombre de la República de Colombia y por autoridad de la Ley'."
    }}
    """
    try:
        response = model.generate_content(prompt)
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        return texto_limpio, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 200

# 4. Configuración del puerto para Render o Local
if __name__ == '__main__':
    if os.environ.get('RENDER'):
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        app.run(host='127.0.0.1', port=8000, debug=True)