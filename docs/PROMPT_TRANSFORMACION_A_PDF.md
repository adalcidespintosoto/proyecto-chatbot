# 📄 Prompt Maestro: Transformación de Documentos a Formato PDF Institucional para UniMon

Este prompt está diseñado para que le entregues cualquier manual, procedimiento o reglamento desordenado a una IA (ChatGPT, Claude, Gemini) y te devuelva un **documento formal maquetado**, listo para copiar en **Microsoft Word** o **Google Docs** y exportar como **PDF**, optimizado para el motor RAG de UniMon.

---

## 🤖 PROMPT MAESTRO (Copiar y pegar en ChatGPT / Claude / Gemini)

> **Instrucciones:** Copia todo el bloque siguiente en tu IA y al final pega o adjunta el documento original.

```text
Eres un Especialista en Documentación Técnica Universitaria y Arquitectura de Sistemas RAG (Retrieval-Augmented Generation).

Tu tarea es leer el documento original adjunto (manual, procedimiento, reglamento o circular) y transformarlo en un DOCUMENTO INSTITUCIONAL FORMAL, listo para ser copiado en Microsoft Word o Google Docs y exportado a PDF, garantizando que el motor RAG de "UniMon" (el Asistente Virtual Oficial de la Universidad Simón Bolívar) lo interprete con 100% de precisión y sin confundir pasos ni cortar palabras.

================================================================================
REGLAS OBLIGATORIAS DE MAQUETACIÓN Y CONTENIDO PARA PDF:
================================================================================

1. DISEÑO DE COLUMNA SIMPLE (CRUCIAL PARA EL LECTOR DE PDF):
   - Redacta en flujo continuo de una sola columna. NUNCA uses columnas dobles, cuadros de texto flotantes ni texto dentro de imágenes, ya que rompen la extracción automática de texto.

2. SOPORTE PARA MÚLTIPLES TRÁMITES / PROCEDIMIENTOS:
   - Si el documento contiene MÁS DE UNA solución o trámite (ej. ver notas, pedir certificados y examen supletorio):
     * Separa cada trámite como un módulo independiente con un título claro: "PROCEDIMIENTO 1: [Nombre]", "PROCEDIMIENTO 2: [Nombre]", etc.
     * En el título de cada trámite DEBE mencionarse el nombre del proceso y la plataforma (ej. "PROCEDIMIENTO 1: Consulta de Calificaciones en el Portal Estudiantes").
     * Cada trámite debe ser auto-contenido: debe tener su propio objetivo, sus requisitos previos, su paso a paso y sus preguntas frecuentes.

3. ELIMINAR RUIDO:
   - Suprime preámbulos legales extensos ("Considerando que..."), decretos introductorios, firmas escaneadas, membretes de página repetitivos y tablas de control de versiones. Ve directo a la información operativa útil.

4. PRECISIÓN EN EL AUTOSERVICIO:
   - Usa numeración estricta para los pasos: "Paso 1:", "Paso 2:", etc.
   - Resalta en NEGRITA todos los nombres exactos de botones, menús, pestañas y campos de texto (ej. haz clic en Servicios Académicos).
   - Coloca las URLs institucionales completas y legibles: https://estudiantes.unisimon.edu.co.

5. REGLA DE NO-PARADOJA PARA CLAVES Y ACCESOS:
   - Si el trámite trata de recuperar contraseña o usuario, NUNCA pidas tener la contraseña activa ni la sesión iniciada. Los requisitos son el documento de identidad y el correo personal o celular registrado.

6. OPTIMIZACIÓN DE BÚSQUEDA (SEO RAG / RERANKER):
   - Al final de cada procedimiento o del documento, incluye una sección de "Preguntas Frecuentes y Variantes de Consulta" que responda dudas con el lenguaje informal que usa la gente (ej. "no puedo ver las notas", "olvidé mi clave", "quién aprueba el computador").

7. CANALES OFICIALES DE SOPORTE TI:
   - Incluye siempre al final los canales oficiales de ambas sedes:
     * Sede Barranquilla: solicitudcomputo@unisimon.edu.co | WhatsApp: 3172683922 | Tel: (605) 3444333 Ext. 8003/8004
     * Sede Cúcuta: helpdesk@unisimon.edu.co | Tel: (607) 5827070 Ext. 129

================================================================================
ESTRUCTURA EXACTA DE SALIDA QUE DEBES ENTREGAR:
================================================================================

[TÍTULO INSTITUCIONAL DEL DOCUMENTO EN MAYÚSCULAS]
Universidad Simón Bolívar - Dirección de Tecnología e Información (TI)

FICHA TÉCNICA DEL DOCUMENTO
• Audiencia y Rol: [Estudiantes / Profesores / Administrativos / General]
• Carpeta RAG recomendada: [1_estudiantes / 2_profesores / 3_funcionarios_gestion / 4_general_normativa]
• Plataforma o Sistema: [Nombre de la plataforma]
• Trámites incluidos:
  1. [Nombre del trámite 1]
  2. [Nombre del trámite 2]
• Términos de búsqueda / Palabras clave: [Lista de 6 a 10 sinónimos y frases comunes de consulta]

--------------------------------------------------------------------------------

PROCEDIMIENTO 1: [NOMBRE DEL PRIMER TRÁMITE O SOLUCIÓN]

1. Descripción y Objetivo:
[Párrafo breve explicando qué resuelve y para qué casos aplica este trámite].

2. Requisitos Previos y Restricciones:
• [Requisito 1 particular de este trámite]
• [Requisito 2 / Fechas permitidas si aplican]

3. Paso a Paso para el Usuario (Autoservicio):
Paso 1: Acceso a la plataforma. Ingresa a [Enlace oficial: https://...] e inicia sesión.
Paso 2: Navegación. En el menú principal, haz clic en [Nombre de Menú] y selecciona [Opción].
Paso 3: Diligenciamiento. Selecciona [Dato] y presiona el botón [Nombre del Botón].
Paso 4: Finalización. Guarda o descarga el comprobante [o mensaje de confirmación].

4. Preguntas Frecuentes y Errores Comunes de este Trámite:
• Pregunta: ¿[Pregunta típica en lenguaje cotidiano]?
  Respuesta: [Solución directa en 1-2 líneas].
• Pregunta: ¿[Error común que suele salir]?
  Respuesta: [Instrucción de cómo solucionarlo].

--------------------------------------------------------------------------------

PROCEDIMIENTO 2: [NOMBRE DEL SEGUNDO TRÁMITE O SOLUCIÓN]
(Repetir la misma estructura si el documento tiene más trámites...)

--------------------------------------------------------------------------------

CANALES OFICIALES DE SOPORTE TÉCNICO TI
Si durante la ejecución de cualquiera de estos pasos se presenta un bloqueo de plataforma o error no contemplado, comunícate con la Mesa de Ayuda TI:
• Sede Barranquilla:
  - Correo: solicitudcomputo@unisimon.edu.co
  - WhatsApp: 3172683922
  - Teléfono: (605) 3444333 Ext. 8003 / 8004
• Sede Cúcuta:
  - Correo: helpdesk@unisimon.edu.co
  - Teléfono: (607) 5827070 Ext. 129

================================================================================
FIN DE LA PLANTILLA. Entrega el texto limpio y perfectamente jerarquizado.
================================================================================

Documento original a procesar:
```

---

## 📝 Pasos para convertir la respuesta de la IA en tu PDF final:

1. **Copia el texto** que te devuelva la IA.
2. **Pégalo en Microsoft Word o Google Docs**:
   - Al título principal colócale estilo **Título 1**.
   - A cada `PROCEDIMIENTO 1: ...` colócale estilo **Título 2**.
   - A los pasos y requisitos déjalos con sus viñetas y negritas.
3. **Exporta a PDF**:
   - En Word: Ve a `Archivo` > `Guardar como` > Selecciona `PDF (*.pdf)` (o `Exportar a PDF`).
   - En Google Docs: Ve a `Archivo` > `Descargar` > `Documento PDF (.pdf)`.
4. **Nombra el archivo sin caracteres especiales**:
   - Ejemplo: `Manual_Tramites_Portal_Estudiantes.pdf` o `Procedimiento_Mantenimiento_Equipos_PGT01.pdf`.
5. **Cárgalo al sistema UniMon**:
   - Puedes guardarlo directamente en `data/docs/[carpeta]/` o cargarlo desde la interfaz web en `http://localhost:8000/admin` (pestaña **Base de Conocimiento RAG**).
