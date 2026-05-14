// --- CONFIGURACIÓN PARA PRODUCCIÓN (RENDER) ---
const URL_BASE = "https://litigio-pro-colombia.onrender.com"; 

console.log("🚀 Sistema conectado al estrado en:", URL_BASE);

// --- ESTADO GLOBAL ---
let casoActual = null;
let rolUsuario = "";
let turnosRealizados = 0;
let radarChart = null;
let segundos = 0;
let cronoInterval = null;

// --- ELEMENTOS DEL DOM ---
const loadingOverlay = document.getElementById('loading-overlay');
const chatAudiencia = document.getElementById('chat-audiencia');
const inputArgumento = document.getElementById('input-argumento');
const btnMicrofono = document.getElementById('btn-microfono');
const seccionPrincipal = document.getElementById('seccion-principal');
const salaAudiencia = document.getElementById('sala-audiencia');

// --- INICIALIZACIÓN DEL GRÁFICO DE RADAR ---
function initRadar() {
    const ctx = document.getElementById('radarHabilidades').getContext('2d');
    if (radarChart) radarChart.destroy(); 
    
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Estrategia', 'Objeciones', 'Claridad', 'Evidencia', 'Psicología'],
            datasets: [{
                label: 'Habilidades Técnicas',
                data: [0, 0, 0, 0, 0],
                backgroundColor: 'rgba(196, 164, 124, 0.2)',
                borderColor: '#c4a47c',
                pointBackgroundColor: '#c4a47c',
                borderWidth: 2
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { color: '#1e293b' },
                    grid: { color: '#1e293b' },
                    pointLabels: { color: '#94a3b8', font: { size: 10 } },
                    ticks: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// --- GENERACIÓN DE CASOS (RENDER LIVE) ---
document.getElementById('btn-generar').onclick = async () => {
    loadingOverlay.classList.remove('hidden');
    const categoria = document.getElementById('select-categoria').value;
    const dificultad = document.getElementById('select-dificultad').value;

    try {
        const res = await fetch(`${URL_BASE}/generar-casos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ categoria, dificultad })
        });
        
        if (!res.ok) throw new Error("Error en el servidor");
        
        const casos = await res.json();
        const contenedor = document.getElementById('contenedor-casos');
        contenedor.innerHTML = "";

        if (casos[0].id === 0) {
            alert("Error de IA: " + casos[0].descripcion);
            return;
        }

        casos.forEach(c => {
            const card = document.createElement('div');
            card.className = "bg-[#161d2f] border border-slate-800 p-8 rounded-[32px] cursor-pointer hover:border-[#c4a47c]/50 transition-all group";
            card.innerHTML = `
                <h3 class="font-serif-legal text-xl mb-3 group-hover:text-[#c4a47c] transition-colors">${c.titulo}</h3>
                <p class="text-slate-500 text-xs line-clamp-3 italic">${c.descripcion}</p>
            `;
            card.onclick = () => {
                casoActual = c;
                document.getElementById('modal-titulo').innerText = c.titulo;
                document.getElementById('modal-descripcion').innerText = c.descripcion;
                document.getElementById('modal-contexto').classList.remove('hidden');
            };
            contenedor.appendChild(card);
        });
    } catch (e) {
        console.error("Fallo de conexión:", e);
        alert("El servidor de Render podría estar iniciando. Intenta de nuevo en 30 segundos.");
    } finally {
        loadingOverlay.classList.add('hidden');
    }
};

// --- SELECCIÓN DE ROL ---
function setRol(rol) {
    rolUsuario = rol;
    document.getElementById('modal-contexto').classList.add('hidden');
    seccionPrincipal.classList.add('hidden');
    
    // --- LÍNEA CLAVE ---
    // Quitamos el "display: none" que pusimos manualmente
    salaAudiencia.style.display = 'grid'; 
    // Y quitamos el hidden por si acaso
    salaAudiencia.classList.remove('hidden');
    
    document.getElementById('contexto-titulo').innerText = casoActual.titulo;
    document.getElementById('contenido-expediente').innerText = casoActual.descripcion;
    
    initRadar();
    const bienvenida = `La sala está en sesión. Usted comparece como ${rolUsuario}. Comience su argumentación.`;
    addBubble('Tribunal', bienvenida, 'ia');
    hablar(bienvenida);
    startCrono();
}

// --- DEBATE ---
async function enviarArgumento() {
    const texto = inputArgumento.value.trim();
    if (!texto) return;
    inputArgumento.value = "";
    addBubble(rolUsuario, texto, 'user');

    try {
        const res = await fetch(`${URL_BASE}/debatir`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                argumento: texto,
                caso: casoActual.descripcion,
                rol: rolUsuario,
                turnos: turnosRealizados,
                dificultad: document.getElementById('select-dificultad').value
            })
        });
        
        const data = await res.json();
        updateUI(data.analisis);
        
        if (data.finalizar) {
            addBubble('Sentencia', data.sentencia, 'ia');
            hablar("Se dicta sentencia definitiva.");
            setTimeout(() => hablar(data.sentencia), 2000);
        } else {
            addBubble('Contraparte', data.respuesta_ia, 'ia');
            hablar(data.respuesta_ia);
        }
        turnosRealizados++;
    } catch (e) {
        console.error("Error en debate:", e);
    }
}

// --- UI Y MÉTRICAS ---
function updateUI(an) {
    if (!an) return;
    const ids = { 'legal': 'fundamentacion_legal', 'logica': 'coherencia_logica', 'retorica': 'persuasion_retorica', 'procesal': 'tecnica_procesal', 'terminos': 'uso_terminologia' };
    for (let k in ids) {
        const valor = an[ids[k]];
        const barra = document.getElementById(`bar-${k}`);
        const texto = document.getElementById(`val-${k}`);
        if (barra && texto) {
            barra.style.width = `${valor}%`;
            texto.innerText = `${valor}%`;
        }
    }
    if (radarChart && an.habilidades) {
        radarChart.data.datasets[0].data = [an.habilidades.estrategia, an.habilidades.objeciones, an.habilidades.claridad, an.habilidades.evidencia, an.habilidades.psicologia];
        radarChart.update();
    }
    document.getElementById('feedback-sutil').innerText = an.feedback_sutil;
}

// --- UTILIDADES ---
function addBubble(per, txt, type) {
    const bubble = document.createElement('div');
    bubble.className = type === 'ia' ? "bg-white/5 border border-slate-800 p-6 rounded-3xl self-start max-w-[85%] shadow-xl" : "bg-[#1e293b] border border-slate-700 p-6 rounded-3xl self-end max-w-[85%] ml-auto shadow-2xl";
    bubble.innerHTML = `<span class="text-[9px] uppercase font-black text-[#c4a47c] block mb-2 tracking-widest">${per}</span><p class="text-lg font-light leading-relaxed">${txt}</p>`;
    chatAudiencia.appendChild(bubble);
    chatAudiencia.scrollTo({ top: chatAudiencia.scrollHeight, behavior: 'smooth' });
}

function hablar(t) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(t);
    utterance.lang = 'es-ES';
    window.speechSynthesis.speak(utterance);
}

function startCrono() {
    cronoInterval = setInterval(() => {
        segundos++;
        const m = Math.floor(segundos / 60).toString().padStart(2, '0');
        const s = (segundos % 60).toString().padStart(2, '0');
        document.getElementById('cronometro').innerText = `${m}:${s}`;
    }, 1000);
}

function toggleContexto() {
    document.getElementById('panel-contexto').classList.toggle('translate-x-full');
}

function abrirInstrucciones() {
    document.getElementById('modal-instrucciones').classList.remove('hidden');
}

function cerrarInstrucciones() {
    document.getElementById('modal-instrucciones').classList.add('hidden');
}

// --- RECONOCIMIENTO DE VOZ ---
const Speech = window.SpeechRecognition || window.webkitSpeechRecognition || window.mozSpeechRecognition || window.msSpeechRecognition;

if (Speech) {
    const rec = new Speech();
    rec.lang = 'es-CO'; // Ajustado a Colombia
    rec.continuous = false;
    rec.interimResults = false;

    btnMicrofono.onclick = () => {
        try {
            btnMicrofono.classList.add('mic-active');
            rec.start();
        } catch (e) {
            console.error("Error al iniciar micro:", e);
            btnMicrofono.classList.remove('mic-active');
        }
    };

    rec.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        // Mostrar visualmente que se capturó algo antes de enviar
        inputArgumento.value = transcript; 
        btnMicrofono.classList.remove('mic-active');
        enviarArgumento();
    };

    rec.onerror = (e) => {
        console.error("Error de Speech:", e.error);
        btnMicrofono.classList.remove('mic-active');
        if(e.error === 'not-allowed') alert("Debes permitir el acceso al micrófono en los ajustes del sitio.");
    };

    rec.onend = () => btnMicrofono.classList.remove('mic-active');
} else {
    btnMicrofono.style.display = 'none';
    alert("Tu navegador no soporta reconocimiento de voz. Prueba con Chrome o Safari actualizado.");
}

// --- CARGA INICIAL ---
window.onload = () => {
    if(!localStorage.getItem('visitado')) {
        abrirInstrucciones();
        localStorage.setItem('visitado', 'true');
    }
};