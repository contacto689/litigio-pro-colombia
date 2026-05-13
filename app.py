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
        text = response.text.strip()
        
        # LIMPIEZA QUIRÚRGICA: Buscamos el inicio '[' y el final ']' del JSON
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            clean_json = match.group(0)
            # Validamos que cargue como JSON
            data_final = json.loads(clean_json)
            return jsonify(data_final)
        else:
            raise ValueError("No se encontró un formato JSON válido")
            
    except Exception as e:
        print(f"Error detectado: {e}")
        # CASOS DE RESPALDO EXTENSOS (Para que nunca veas textos cortos)
        return jsonify([
            {
                "id": 1, 
                "titulo": "Falsedad en Documento Público - Bogotá", 
                "descripcion": "En la ciudad de Bogotá, específicamente en la Notaría 100, se detectó una red de falsificación de escrituras públicas relacionadas con predios en el norte de la ciudad. El indiciado pretendía traspasar un inmueble valorado en 2.000 millones de pesos usando un poder falso. Las pruebas incluyen el peritaje grafológico de la firma del notario y los videos de las cámaras de seguridad donde se observa al sospechoso realizando el trámite con documentos apócrifos. El problema jurídico radica en determinar la autoría material y el dolo en la conducta."
            },
            {
                "id": 2, 
                "titulo": "Responsabilidad Médica en Barranquilla", 
                "descripcion": "En una clínica de alta complejidad en Barranquilla, se presentó una demanda por presunta mala praxis durante una cirugía estética. La paciente alega que no se le practicaron los exámenes preoperatorios necesarios, lo que derivó en una embolia pulmonar. La defensa del médico sostiene que los riesgos fueron informados y aceptados en el consentimiento informado. Las pruebas consisten en la historia clínica digital, el peritaje de Medicina Legal y el testimonio de la instrumentadora quirúrgica presente en el procedimiento."
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