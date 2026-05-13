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
    data = request.json
    categoria = data.get('categoria', 'Derecho Penal')
    dificultad = data.get('dificultad', 'Intermedio')

    # Prompt ultra-detallado para obligar a la IA a escribir más
    prompt = f"""
    Actúa como un Magistrado de la República de Colombia.
    Genera 5 expedientes judiciales de {categoria} para nivel {dificultad}.
    
    Cada 'descripcion' debe ser un relato jurídico profesional de al menos 3 párrafos que incluya:
    - Hechos relevantes (Lugar exacto en Colombia, fecha y hora).
    - Pruebas recaudadas (testimonios, dictámenes periciales, grabaciones).
    - El problema jurídico central a resolver.

    IMPORTANTE: Responde EXCLUSIVAMENTE con el array JSON.
    Formato:
    [
      {{"id": 1, "titulo": "Nombre del Proceso", "descripcion": "Relato extenso..."}}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Limpieza avanzada para ignorar cualquier texto que no sea el JSON
        start_idx = raw_text.find('[')
        end_idx = raw_text.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            raw_text = raw_text[start_idx:end_idx]
        
        json_data = json.loads(raw_text)
        return jsonify(json_data)
        
    except Exception as e:
        print(f"Error: {e}")
        # Si falla, estos casos de respaldo ahora son más largos también
        return jsonify([
            {
                "id": 1, 
                "titulo": "Homicidio Preterintencional en Bogotá", 
                "descripcion": "Los hechos ocurrieron en el barrio Chapinero, donde tras una riña recíproca, el indiciado golpeó a la víctima provocando una caída fatal. Se cuenta con videos de seguridad y tres testimonios clave que indican falta de intención de matar."
            },
            {
                "id": 2, 
                "titulo": "Restitución de Tierras en Urabá", 
                "descripcion": "Un grupo de reclamantes solicita la devolución de 50 hectáreas despojadas en 1998. El opositor alega compra de buena fe exenta de culpa. El caso requiere análisis de la Ley 1448 de 2011."
            }
        ])

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