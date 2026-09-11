"""
Servicio de Normalización Léxica, Depuración de Ruido y Expansor de Sinónimos para UniMon (Universidad Simón Bolívar).
Normaliza jerga estudiantil, elimina encabezados/ruido de remitente (ej: 'EXALUMNO CARLOS ARDILA:')
y traduce términos coloquiales a la terminología técnica e institucional oficial.
"""

import re

# Patrones de encabezados con nombres propios o remitentes para eliminación de ruido
HEADER_NOISE_PATTERNS = [
    r"^(?:exalumno|egresad[oa]|estudiante|alumno|docente|profesor[a]?|administrativ[oa]|funcionario|usuario|remitente|de|para|nombre|consulta|solicitud|requerimiento)\s+[a-záéíóúñA-ZÁÉÍÓÚÑ\s]+:\s*",
    r"^(?:de|para|att|asunto):\s*",
    r"^(?:informaci[oó]n\s+(?:para|sobre|de)|consulta\s+(?:para|sobre|de)|solicitud\s+(?:para|sobre|de))\s+"
]

SYNONYM_MAP = {
    # Recuperación de Credenciales, Contraseñas y Desbloqueo de Cuentas
    r"\b(restablecer\s+correo|recuperar\s+correo|desbloquear\s+correo|restablecer\s+contrase[ñn]a|recuperar\s+contrase[ñn]a|recuperar\s+clave|restablecer\s+clave|cambiar\s+clave|cambiar\s+contrase[ñn]a|olvid[eé]\s+mi\s+contrase[ñn]a|olvid[eé]\s+la\s+clave|olvido\s+contrase[ñn]a|desbloqueo\s+de\s+cuenta|olvido\s+su\s+contraseña)\b": "activación de usuario contraseña y correo institucional autogestión de contraseñas portal estudiantes passwordreset microsoftonline",

    # Desambiguación de Estudiante Antiguo / Semestres Superiores
    r"\b(estudiante\s+antiguo|estudiante\s+viejo|estudiante\s+regular|semestres?\s+(?:avanzados?|superiores?)|(?:[2-9]|10)\s*(?:do|er|ro|to|mo|vo|no|°)?\s*semestre|(?:segundo|tercer|tercero|cuarto|quinto|sexto|s[eé]ptimo|septimo|octavo|noveno|d[eé]cimo|decimo)\s*semestre|\b(?:2do|3er|4to|5to|6to|7mo|8vo|9no|10mo)\b|\b(?:segundo|tercero|cuarto|quinto|sexto|s[eé]ptimo|septimo|octavo|noveno|d[eé]cimo|decimo)\b)\b": "recuperacion contraseña portal estudiante restablecer clave microsoft passwordreset autogestion",

    # Canales de Atención, Contacto y Soporte TI
    r"\b(canales\s+de\s+atenci[oó]n|canales\s+de\s+atencion|canales\s+de\s+soporte|canales|lineas\s+de\s+atencion|líneas\s+de\s+atención|contacto\s+ti|contacto\s+soporte|wasap|whatsapp|numero\s+de\s+whatsapp|número\s+de\s+whatsapp|cual\s+es\s+el\s+wasap|cuál\s+es\s+el\s+wasap|cual\s+es\s+el\s+whatsapp|cuál\s+es\s+el\s+whatsapp|correo\s+soporte|correo\s+de\s+soporte|telefono\s+soporte|teléfono\s+soporte|directorio\s+ti|escribir\s+a\s+los\s+canales)\b": "directorio canales soporte tecnico whatsapp telefono correo barranquilla cucuta atencion usuarios pbx",

    # Hardware y Dispositivos / Dotación de Cómputo
    r"\b(portatil|portátil|portatiles|portátiles|laptop|laptops)\b": "dotacion equipo de computo portatil mantenimiento computadores",
    r"\b(computador de mesa|pc de escritorio)\b": "dotacion equipo de computo pc mantenimiento",
    r"\b(pedir computador|solicitar pc|solicitar portatil|solicitar portátil|solicitar equipo|pedir pc|pedir portatil|pedir portátil|asignar computador|dotaci[oó]n|solicitar computador|asignar portatil|asignar portátil)\b": "dotacion renovacion equipos de computo jefe dependencia mantenimiento preventivo y correctivo de equipos de computo p-gt-01",
    r"\b(pc|pcs|compu|computadora|ordenador|maquina|máquina|torre)\b": "computador equipo de cómputo",
    r"\b(tablet|tableta|tabletas|ipad)\b": "tableta digital",
    r"\b(videobeam|video beam|beamer|canon|cañon|cañón)\b": "videobeam proyector institucional",
    r"\b(microfono|micrófono|micrófonos|diadema|audifonos|audífonos|auriculares|parlante|altavoz)\b": "micrófono equipo de audio",
    r"\b(cargador|cable de poder|adaptador|fuente de poder)\b": "cargador fuente de poder cable de energía",
    r"\b(pantalla|monitor|display)\b": "pantalla monitor de video",
    
    # Plataformas y Sistemas
    r"\b(aula|campus virtual|moodle|aula virtual|como entro al aula)\b": "instructivo portales estudiantes siaaf acceso plataforma institucional aula extendida",
    r"\b(portal|portal de la u|pagina de la u|portal estudiantil|portal estudiantes|portal docentes|sistema de notas)\b": "instructivo portales estudiantes ingreso plataforma notas",
    r"\b(teams|tim|reuniones virtuales|como entro a teams|como ingreso a team|como voy a teams)\b": "acceso a microsoft teams para estudiantes inicio sesion credenciales institucionales",
    r"\b(correo|mail|email|outlook)\b": "correo institucional office 365",
    r"\b(seven|seben)\b": "sistema seven erp financiero",
    r"\b(kactus|caktus|kaktu)\b": "sistema kactus gestión de talento humano y nómina",
    r"\b(pac)\b": "diligenciamiento de pac profesores plan de actividad académica",
    r"\b(carnet|carné|carnet digital|app unisim[oó]n|app)\b": "carnetización app unisimon carnet estudiante",
    r"\b(supletorio|supletorios|examen supletorio|ex[aá]menes supletorios)\b": "gestión y autorización de exámenes supletorios en siaaf",
    # Elecciones Institucionales y Votaciones
    r"\b(votaci[oó]n|votaciones|[oó]rganos colegiados|votar|elecci[oó]n|elecciones|representante|representantes|candidato|candidatos|sufragio)\b": "aplicativo de elecciones institucionales votaciones votar https://elecciones.unisimon.edu.co/",
    
    # Reclamos y Cambio de Notas (Límite de Dominio Académico)
    r"\b(me\s+clavaron|me\s+clav[oó]|cambiar\s+nota|cambie\s+la\s+nota|subir\s+nota|suba\s+la\s+nota|corregir\s+nota|reclamo\s+calificaci[oó]n|reclamo\s+nota|reclamar\s+nota|nota\s+injusta|calificaci[oó]n\s+injusta|revisi[oó]n\s+de\s+nota)\b": "reclamo calificacion revision docente direccion de programa",
    
    # Errores, Accesos y Fallas Comunes
    r"\b(datos incorrectos|clave incorrecta|clave mala|clave est[aá] mala|clave no sirve|no me deja entrar|no entra|clave invalida|datos invalidos|no me coge la clave|ando embalao)\b": "problemas de acceso restablecimiento de contraseña credenciales incorrectas",
    r"\b(se traba|se congela|se cuelga|lento|muy lento|pesado)\b": "rendimiento bajo fallas de ejecución del sistema",
    r"\b(pantalla azul|se reinicia|se apaga solo)\b": "falla crítica del sistema operativo hardware",
    r"\b(no prende|no enciende|no da video|muerto|no arranca)\b": "falla de encendido hardware equipo de cómputo",
    r"\b(hace mal contacto|toca mover el cable|toca moverle el cable|no carga bien|mal contacto|cable pelado)\b": "falla física de cargador puerto de alimentación"
}


def strip_query_header_noise(query: str) -> str:
    """
    Elimina prefijos de remitente, encabezados tipo correo o nombres propios
    (ej: 'EXALUMNO CARLOS ARDILA: INFORMACION PARA RESTABLECER CORREO' -> 'RESTABLECER CORREO').
    """
    clean_text = query.strip()
    for pat in HEADER_NOISE_PATTERNS:
        clean_text = re.sub(pat, "", clean_text, flags=re.IGNORECASE).strip()
    return clean_text if clean_text else query.strip()


def normalize_and_expand_query(query: str) -> str:
    """
    Limpia el texto, depura ruido de encabezados, expande siglas y traduce términos coloquiales/jerga estudiantil
    a términos técnicos institucionales para una recuperación semántica de alta precisión (>= 90%).
    """
    stripped_text = strip_query_header_noise(query)
    text_lower = stripped_text.lower().strip()
    expanded_terms = []
    
    for pattern, replacement in SYNONYM_MAP.items():
        if re.search(pattern, text_lower):
            expanded_terms.append(replacement)
            
    if expanded_terms:
        # Retorna el query limpio enriquecido con los términos técnicos oficiales
        return f"{text_lower} {' '.join(expanded_terms)}"
    return text_lower
