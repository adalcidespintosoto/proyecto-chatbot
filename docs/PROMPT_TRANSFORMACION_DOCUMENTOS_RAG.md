# 📄 Guía y Prompt Maestro para Optimización de Documentos RAG en UniMon
### (Soporta Documentos con Solución Única y Manuales Multi-Solución / Multi-Trámite)

Este documento contiene el **Prompt Maestro** y las **Plantillas Estructuradas (.md)** diseñados para transformar manuales, reglamentos y guías institucionales sin procesar (PDF, Word, etc.) en documentos de máxima precisión semántica para el pipeline RAG de UniMon (ChromaDB + `multilingual-e5-base` / `bge-m3` + Cross-Encoder Reranker + `unimon:8b`).

---

## 🎯 El Desafío: ¿Qué pasa cuando un documento resuelve VARIAS cosas a la vez?

Muchos documentos institucionales son **manuales integrales o reglamentos** que no resuelven una sola cosa, sino varias (ej. un manual del *Portal Estudiantes* que explica cómo consultar notas, cómo descargar certificados y cómo pedir supletorios; o una guía de *TI* que explica Wi-Fi, VPN y correo móvil).

### El Peligro en RAG:
Si el texto original no se estructura adecuadamente:
1. **Contaminación Cruzada de Chunks**: Como UniMon divide el texto en fragmentos de 800 caracteres (`chunk_size=800`), si un usuario pregunta por *"certificados"*, el buscador vectorial podría recuperar un fragmento donde se mezclan los pasos de notas con los de certificados, confundiendo a la IA y al usuario.
2. **Pérdida de Contexto de Encabezado**: Si un paso dice simplemente *"Paso 2: Haz clic en Solicitar"*, el bot no sabe si está solicitando un supletorio o un certificado.
3. **Falsas Alarmas de Redundancia**: Si un documento repite requisitos generales para 5 trámites distintos sin modularizarlos, el auditor de `/admin` marcará el documento como redundante.

### La Solución Arquitectónica: "Módulos Autónomos y Auto-contenidos"
El Prompt Maestro instruye a la IA para:
- **Identificar cada trámite o solución individual** dentro del documento.
- **Convertir cada solución en una sección completamente autónoma** con su propio encabezado explícito (ej. `## 🛠️ Procedimiento 1: Consulta de Calificaciones [Portal Estudiantes]`), sus propios requisitos y su propio paso a paso.
- **Mantener cada solución dentro del rango ideal de 400 a 700 caracteres**, garantizando que cada chunk vectorial contenga el trámite completo sin cortes accidentales.

---

## 🤖 PROMPT MAESTRO DE TRANSFORMACIÓN (Copiar y Pegar en ChatGPT / Claude / Gemini)

> **Instrucciones de uso:** Copia todo el bloque a continuación en tu herramienta de IA preferida, y adjunta o pega al final el texto o archivo del documento original.

```markdown
Eres un Arquitecto de Información Senior y Especialista en Sistemas RAG (Retrieval-Augmented Generation) para Soporte Técnico TI Universitario.

Tu tarea es leer el documento original adjunto (manual, procedimiento, reglamento, circular o guía de usuario) y transformarlo en un documento Markdown (.md) de máxima precisión semántica para el motor RAG de "UniMon", el Asistente Virtual Oficial de la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta).

================================================================================
REGLA FUNDAMENTAL PARA DOCUMENTOS CON MÚLTIPLES SOLUCIONES / TRÁMITES:
================================================================================
Si el documento describe MÁS DE UNA solución, trámite, servicio o procedimiento (ej. un manual de portal que enseña a ver notas, pedir certificados y pagar matrícula; o una guía de TI que explica Wi-Fi, Teams y VPN):

1. DETECCIÓN Y DESCOMPOSICIÓN MODULAR:
   Identifica CADA solución o trámite por separado. NO los mezcles en un solo paso a paso genérico ni dejes pasos sueltos.
   
2. AUTONOMÍA DE CADA SOLUCIÓN (Anti-Contaminación de Chunks):
   Cada solución debe estructurarse como una sección `##` totalmente INDEPENDIENTE y AUTO-CONTENIDA.
   El título de cada sección DEBE incluir el nombre explícito del trámite y la plataforma (ej. "## 🛠️ Procedimiento 1: Consulta de Calificaciones [Portal Estudiantes]"). Así, cuando el motor RAG recupere ese fragmento de 800 caracteres, el bot sabe exactamente a qué trámite pertenece sin confundirlo con los demás.

3. ESTRUCTURA INTERNA POR CADA SOLUCIÓN:
   Cada solución individual debe contener obligatoriamente:
   - **¿Para qué sirve?** (1-2 líneas).
   - **⚠️ Requisitos Previos Específicos** (documento, fechas, autorizaciones, paz y salvo).
   - **Paso a Paso Cronológico** (Paso 1, Paso 2...) con botones y menús exactos en **negrita**.
   - **Preguntas Frecuentes / Casos de Error de esa solución** (FAQ específica de ese trámite).

4. SI EL DOCUMENTO ES EXCESIVAMENTE GRANDE O DESCONEXO:
   Si el documento original mezcla temas que van a audiencias distintas (ej. una sección para Estudiantes y otra para Profesores) o temas sin relación entre sí, indícalo al inicio y genera bloques de archivos Markdown separados listos para guardar independientemente (ej. `--- ARCHIVO 1: Nombre.md ---` y `--- ARCHIVO 2: Nombre.md ---`).

================================================================================
DIRECTRICES DE CONTENIDO Y TONO:
================================================================================
1. ELIMINAR RUIDO INSTITUCIONAL: Suprime preámbulos legales ("Considerando que..."), firmas, resoluciones introductorias, comités de redacción, membretes y pies de página repetitivos.
2. FIDELIDAD INSTITUCIONAL: Utiliza ÚNICAMENTE nombres de botones, menús, campos y URLs reales [Nombre](URL) que aparezcan en el documento. NUNCA inventes pasos ni supongas opciones ficticias.
3. REGLA DE NO-PARADOJA: Para recuperación de contraseñas, usuarios o acceso a plataformas, NUNCA exijas tener la contraseña activa ni la sesión iniciada. Los requisitos son documento de identidad y correo personal/celular registrado.
4. LENGUAJE NATURAL Y SEO RAG: Agrega variantes de cómo preguntaría un usuario real de forma informal (ej. "no me sale la nota", "bajar sábana de notas", "recuperar clave", "olvidé mi usuario").
5. CANALES OFICIALES DE SOPORTE: Al final incluye siempre los canales oficiales de Soporte TI:
   - Sede Barranquilla: solicitudcomputo@unisimon.edu.co | WhatsApp: 3172683922 | Tel: (605) 3444333 Ext. 8003/8004
   - Sede Cúcuta: helpdesk@unisimon.edu.co | Tel: (607) 5827070 Ext. 129

================================================================================
PLANTILLA DE SALIDA ESPERADA:
================================================================================

# [Título General del Manual o Documento]

## 📌 Metadatos Generales
- **Audiencia / Rol:** [Estudiantes / Profesores / Administrativos / General]
- **Subdirectorio RAG recomendado:** [1_estudiantes / 2_profesores / 3_funcionarios_gestion / 4_general_normativa]
- **Plataforma Principal:** [Nombre del Sistema, Portal o Servicio]
- **Trámites / Soluciones incluidas:**
  1. [Nombre del Trámite o Solución 1]
  2. [Nombre del Trámite o Solución 2]
  3. [Nombre del Trámite o Solución 3...]
- **Palabras Clave Globales:** [Términos de búsqueda informales y formales]

---

## 🛠️ Procedimiento 1: [Nombre Específico del Primer Trámite o Solución]
### 📋 Descripción y Propósito
[Explica en 2 líneas qué problema resuelve este trámite concreto y cuándo se usa].

### ⚠️ Requisitos Previos y Restricciones
- [Requisito 1 para este trámite en particular]
- [Requisito 2 / Fechas permitidas si aplican]

### 📝 Paso a Paso (Autoservicio)
1. **Paso 1: Acceso al módulo.** [Ruta exacta con URLs reales si existen].
2. **Paso 2: Selección de opción.** [Menú o botón en **negrita**].
3. **Paso 3: Ejecución de la acción.** [Qué datos ingresar o qué confirmar].
4. **Paso 4: Resultado final.** [Comprobante generado, descarga de archivo o mensaje de éxito].

### ❓ Preguntas Frecuentes y Errores Comunes de este Trámite
- **¿[Duda frecuente sobre este trámite 1]?:** [Solución directa].
- **¿[Error común al ejecutar este paso]?:** [Forma de destrabarlo].

---

## 🛠️ Procedimiento 2: [Nombre Específico del Segundo Trámite o Solución]
### 📋 Descripción y Propósito
[Explica en 2 líneas qué problema resuelve este segundo trámite].

### ⚠️ Requisitos Previos y Restricciones
- [Requisitos particulares de esta segunda solución]

### 📝 Paso a Paso (Autoservicio)
1. **Paso 1: [Acción inicial].** [Detalle].
2. **Paso 2: [Acción intermedia].** [Detalle].
3. **Paso 3: [Acción final].** [Detalle].

### ❓ Preguntas Frecuentes y Errores Comunes de este Trámite
- **¿[Duda frecuente sobre el trámite 2]?:** [Solución directa].

---

[Repetir la estructura para cada procedimiento adicional que contenga el documento...]

---

## 📞 Canales Oficiales de Soporte Técnico y Escalado TI
Si al intentar realizar cualquiera de estos procedimientos el sistema arroja un error técnico no contemplado:
- **Sede Barranquilla:**
  - Correo: `solicitudcomputo@unisimon.edu.co`
  - WhatsApp: `3172683922`
  - Teléfono: `(605) 3444333` Ext. `8003` / `8004`
- **Sede Cúcuta:**
  - Correo: `helpdesk@unisimon.edu.co`
  - Teléfono: `(607) 5827070` Ext. `129`

================================================================================
FIN DE LA PLANTILLA. Entrega el resultado en código Markdown limpio (.md).
================================================================================

Documento original a transformar:
```

---

## 💡 EJEMPLO REAL DE DOCUMENTO MULTI-SOLUCIÓN TRANSFORMADO

A continuación puedes ver cómo se vería un manual institucional que contiene 3 soluciones en un solo documento:

```markdown
# Guía Integral de Servicios Académicos en el Portal Estudiantes

## 📌 Metadatos Generales
- **Audiencia / Rol:** Estudiantes (Pregrado y Posgrado)
- **Subdirectorio RAG recomendado:** `1_estudiantes`
- **Plataforma Principal:** Portal Estudiantes UniSimon
- **Trámites / Soluciones incluidas:**
  1. Consulta e Impresión de Calificaciones Parciales y Finales
  2. Solicitud y Descarga de Certificados Académicos
  3. Solicitud de Exámenes Supletorios
- **Palabras Clave Globales:** portal estudiantes, notas, notas parciales, certificados, certificado de estudio, supletorio, examen diferido, promedio, calificaciones

---

## 🛠️ Procedimiento 1: Consulta e Impresión de Calificaciones [Portal Estudiantes]
### 📋 Descripción y Propósito
Permite al estudiante consultar las notas registradas por los docentes durante el semestre en curso (cortes 1, 2 y 3) o imprimir su historial académico acumulado (sábana de notas).

### ⚠️ Requisitos Previos y Restricciones
- Tener la matrícula académica activa en el periodo vigente.
- Estar al día con la evaluación docente (si el periodo de evaluación está activo).

### 📝 Paso a Paso (Autoservicio)
1. **Paso 1: Ingreso al portal.** Accede a [Portal Estudiantes](https://estudiantes.unisimon.edu.co) con tu usuario y contraseña institucional.
2. **Paso 2: Menú de calificaciones.** En el menú lateral izquierdo, selecciona **Servicios Académicos** y haz clic en **Consulta de Calificaciones**.
3. **Paso 3: Selección del periodo.** Elige el periodo lectivo en el selector desplegable (ej. `2026-1`).
4. **Paso 4: Visualización e impresión.** Se desplegará la lista de asignaturas, porcentaje de avance y calificaciones por corte. Para imprimir o guardar en PDF, presiona el botón **Imprimir Reporte**.

### ❓ Preguntas Frecuentes y Errores Comunes de este Trámite
- **¿Qué hago si no me aparece la nota de una materia?:** Verifica con el docente si el acta ya fue cerrada o revisa en el calendario académico la fecha límite de cargue de notas del corte.
- **¿Por qué me sale 'Evaluación docente pendiente'?:** Debes completar la encuesta obligatoria de evaluación a profesores en el menú **Evaluación Docente** para desbloquear la vista de notas.

---

## 🛠️ Procedimiento 2: Solicitud y Descarga de Certificados Académicos [Portal Estudiantes]
### 📋 Descripción y Propósito
Permite tramitar y descargar de forma inmediata certificados oficiales (estudio, calificaciones, buena conducta) con firma digital y código QR de verificación.

### ⚠️ Requisitos Previos y Restricciones
- Estar a paz y salvo financiero con la institución.
- Disponer de medio de pago digital (PSE / Tarjeta de crédito) si el certificado tiene costo estipulado.

### 📝 Paso a Paso (Autoservicio)
1. **Paso 1: Módulo de certificados.** En el menú del Portal Estudiantes, dirígete a **Trámites y Solicitudes** > **Certificados en Línea**.
2. **Paso 2: Tipo de certificado.** Selecciona el tipo de certificado requerido (ej. *Certificado de Estudio con Calificaciones* o *Certificado de Matrícula*).
3. **Paso 3: Liquidación y pago.** Revisa el valor liquidado y presiona **Pagar con PSE**. Completa la transacción en la pasarela bancaria.
4. **Paso 4: Descarga del documento.** Una vez aprobado el pago, haz clic en **Descargar Certificado** (formato PDF). El documento cuenta con código QR y es válido legalmente.

### ❓ Preguntas Frecuentes y Errores Comunes de este Trámite
- **¿El certificado digital es válido ante entidades externas?:** Sí, contiene firma digital institucional y código de validación web con verificación QR.
- **¿Qué pasa si el pago fue debitado pero el certificado no se generó?:** Espera 15 minutos a que la pasarela bancaria confirme el estado `APROBADO`. Si persiste, contacta a Soporte TI con el comprobante CUS de PSE.

---

## 🛠️ Procedimiento 3: Solicitud de Examen Supletorio [Portal Estudiantes]
### 📋 Descripción y Propósito
Procedimiento normativo para solicitar la presentación de un examen parcial o final que no se pudo rendir en la fecha ordinaria programada.

### ⚠️ Requisitos Previos y Restricciones
- Radicar la solicitud dentro de los **cinco (5) días hábiles** siguientes a la fecha original del examen.
- Adjuntar soporte documental válido (incapacidad médica validada por Bienestar Universitario o constancia de fuerza mayor).

### 📝 Paso a Paso (Autoservicio)
1. **Paso 1: Radicación de la solicitud.** En el Portal Estudiantes, ve a **Novedades Académicas** > **Solicitud de Examen Supletorio**.
2. **Paso 2: Selección de la asignatura.** Elige la materia y el corte que deseas presentar en supletorio.
3. **Paso 3: Adjuntar justificativo.** Carga el soporte en archivo PDF (ej. incapacidad médica).
4. **Paso 4: Envío y liquidación.** Haz clic en **Radicar Solicitud**. La dirección de programa revisará el caso en un plazo máximo de 3 días hábiles. Si es aprobado, generará el volante de pago en el módulo de pagos.

### ❓ Preguntas Frecuentes y Errores Comunes de este Trámite
- **¿Puedo presentar el supletorio sin haber pagado el derecho pecuniario?:** No, el profesor solo podrá aplicar el examen si en el sistema aparece el estado de la solicitud en `PAGADO / AUTORIZADO`.

---

## 📞 Canales Oficiales de Soporte Técnico y Escalado TI
Para fallas en la plataforma o bloqueos de acceso al Portal:
- **Sede Barranquilla:**
  - Correo: `solicitudcomputo@unisimon.edu.co`
  - WhatsApp: `3172683922`
  - Teléfono: `(605) 3444333` Ext. `8003` / `8004`
- **Sede Cúcuta:**
  - Correo: `helpdesk@unisimon.edu.co`
  - Teléfono: `(607) 5827070` Ext. `129`
```

---

## ⚖️ Criterio Clave: ¿Cuándo dejar un solo archivo vs. cuándo dividir en varios?

| Situación del Documento Original | ¿Qué es mejor para UniMon? | Razón Técnica |
| :--- | :--- | :--- |
| **Trámites dentro del mismo portal o sistema** (ej. Certificados, Notas y Matrícula en Portal Estudiantes) | **Dejarlo en UN SOLO archivo** con secciones `## Procedimiento 1:`, `## Procedimiento 2:`. | Comparten la misma audiencia (`1_estudiantes`) y plataforma. El chunking de 800 caracteres separará cada sección limpiamente sin colisiones. |
| **Temas para diferentes roles** (ej. un reglamento que tiene un capítulo para estudiantes y otro para profesores) | **DIVIDIR en 2 archivos separados** (`Guia_Estudiantes.md` y `Guia_Profesores.md`). | Permite guardarlos en subcarpetas distintas (`1_estudiantes/` y `2_profesores/`), evitando que el bot recomiende opciones de profesor a un estudiante. |
| **Manuales gigantes de más de 30 páginas** con temas no relacionados (ej. ERP Kactus: Nómina, Vacaciones, Contratación, Viáticos) | **DIVIDIR por cada macro-proceso** (un `.md` para Nómina, otro para Vacaciones, etc.). | Los archivos más pequeños y temáticamente puros obtienen puntuaciones de similitud coseno más altas y nunca saturan el vector store. |
