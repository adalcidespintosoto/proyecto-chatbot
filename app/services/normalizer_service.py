"""
Servicio de Normalización Léxica y Expansor de Sinónimos para UniMon (Universidad Simón Bolívar).
Normaliza jerga estudiantil, variantes fonéticas, modismos regionales y siglas informales
a la terminología técnica e institucional oficial de los manuales y procedimientos (P-GT, Moodle, Seven, Kactus).
"""

import re

SYNONYM_MAP = {
    # Hardware y Dispositivos
    r"\b(pc|pcs|compu|computadora|ordenador|maquina|máquina|torre|laptop)\b": "computador equipo de cómputo",
    r"\b(portatil|portátil|portatiles|portátiles)\b": "computador portátil",
    r"\b(tablet|tableta|tabletas|ipad)\b": "tableta digital",
    r"\b(videobeam|video beam|beamer|canon|cañon|cañón)\b": "videobeam proyector institucional",
    r"\b(microfono|micrófono|micrófonos|diadema|audifonos|audífonos|auriculares|parlante|altavoz)\b": "micrófono equipo de audio",
    r"\b(cargador|cable de poder|adaptador|fuente de poder)\b": "cargador fuente de poder cable de energía",
    r"\b(pantalla|monitor|display)\b": "pantalla monitor de video",
    
    # Plataformas y Sistemas
    r"\b(aula|campus virtual|moodle|aula virtual)\b": "aula extendida plataforma educativa",
    r"\b(portal|portal de la u|pagina de la u|portal estudiantil|portal estudiantes|portal docentes|sistema de notas)\b": "instructivo portales estudiantes ingreso plataforma notas",
    r"\b(teams|tim|reuniones virtuales)\b": "microsoft teams reuniones grupos institucionales",
    r"\b(correo|mail|email|outlook)\b": "correo institucional office 365",
    r"\b(seven|seben)\b": "sistema seven erp financiero",
    r"\b(kactus|caktus|kaktu)\b": "sistema kactus gestión de talento humano y nómina",
    r"\b(pac)\b": "diligenciamiento de pac profesores plan de actividad académica",
    r"\b(carnet|carné|carnet digital|app unisim[oó]n|app)\b": "carnetización app unisimon carnet estudiante",
    
    # Errores, Accesos y Fallas Comunes
    r"\b(datos incorrectos|clave incorrecta|no me deja entrar|no entra|clave invalida|datos invalidos|no me coge la clave)\b": "problemas de acceso restablecimiento de contraseña credenciales incorrectas",
    r"\b(se traba|se congela|se cuelga|lento|muy lento|pesado)\b": "rendimiento bajo fallas de ejecución del sistema",
    r"\b(pantalla azul|se reinicia|se apaga solo)\b": "falla crítica del sistema operativo hardware",
    r"\b(no prende|no enciende|no da video|muerto|no arranca)\b": "falla de encendido hardware equipo de cómputo",
    r"\b(hace mal contacto|toca mover el cable|toca moverle el cable|no carga bien|mal contacto|cable pelado)\b": "falla física de cargador puerto de alimentación"
}


def normalize_and_expand_query(query: str) -> str:
    """
    Limpia el texto, expande siglas y traduce términos coloquiales/jerga estudiantil
    a términos técnicos institucionales para una recuperación semántica de alta precisión (>= 90%).
    """
    text = query.lower().strip()
    expanded_terms = []
    
    for pattern, replacement in SYNONYM_MAP.items():
        if re.search(pattern, text):
            expanded_terms.append(replacement)
            
    if expanded_terms:
        # Retorna el query original enriquecido con los términos técnicos oficiales
        return f"{text} {' '.join(expanded_terms)}"
    return text
