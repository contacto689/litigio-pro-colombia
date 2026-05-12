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
    """Genera 5 expedientes con un sistema de limpieza de JSON robusto."""
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    prompt = f"""
    Eres un Magistrado de la Corte Suprema de Justicia de COLOMBIA. 
    Genera 5 expedientes judiciales detallados de {categoria} en COLOMBIA.
    Nivel: {dificultad}.

    Cada descripción debe ser EXTENSA (mínimo 150 palabras) e incluir:
    1. CONTEXTO: Lugar exacto en Colombia y fecha.
    2. HECHOS: Relato detallado de lo sucedido.
    3. CARGOS/PRETENSIONES: Qué se busca legalmente.
    4. PRUEBAS: Menciona un par de pruebas (testimonios, videos de seguridad, contratos).

    Responde ÚNICAMENTE un array JSON:
    [
      {{"id": 1, "titulo": "Nombre Impactante", "descripcion": "Texto largo y jurídico aquí..."}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Limpieza de bloques de código markdown si la IA los incluye
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
        
        # Validamos que el JSON sea correcto antes de enviar
        json_data = json.loads(raw_text)
        return jsonify(json_data)
        
    except Exception as e:
        print(f"Error en generación: {e}")
        # Casos de respaldo por si falla la conexión o el formato
        backup = [
            {"id": 1, "titulo": "Litigio en el Barrio Rosales", "descripcion": "Conflicto de propiedad horizontal en Bogotá."},
            {"id": 2, "titulo": "Infracción en Comuna 13", "descripcion": "Caso penal sobre responsabilidad civil en Medellín."},
            {"id": 3, "titulo": "Disputa Comercial en Bocagrande", "descripcion": "Incumplimiento de contrato mercantil en Cartagena."},
            {"id": 4, "titulo": "Proceso Laboral en Cali", "descripcion": "Despido injustificado en planta industrial del Valle."},
            {"id": 5, "titulo": "Restitución en el Eje Cafetero", "descripcion": "Reclamo de linderos en finca cafetera de Quindío."}
        ]
        return jsonify(backup)

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
    2. Si el usuario cita leyes de otros países, castiga su puntuación.

    Responde ÚNICAMENTE en formato JSON puro:
    {{
      "respuesta_ia": "Tu refutación legal (máx 90 palabras)",
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
        raw_text = response.text.strip()
        
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
                
        return raw_text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 200

# 4. Configuración del puerto para Render o Local
if __name__ == '__main__':
    if os.environ.get('RENDER'):
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        app.run(host='127.0.0.1', port=8000, debug=True)