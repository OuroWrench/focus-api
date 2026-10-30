# Gap analysis · FOCUS! Web (Figma e1–e47) vs. Focus! API

> **Fuente de UI:** Figma `FOCUS!` → canvas `★ Web nuevo ordenado` → frame **«FOCUS! · Web nuevo ordenado (e1–e48) — ACTUAL»** (`571:10004`).
> El frame contiene **47 pantallas (e1–e47)**; no existe ningún frame `e48`.
> **Fuente de backend:** este repo (rama `claude/focus-gap-analysis-tech-3d80bf`, commit `8b4745d`): 14 controladores, unas 70 rutas y 1 Azure Function HTTP (`ajuste-semanal`).
> **Alcance:** solo la versión Web. En el archivo no hay frames de la app móvil en este canvas; la app Android es el *productor* de datos (eventos, pausas, intentos).

Leyenda de estado: ✅ existe y alcanza · 🟡 existe pero le faltan campos/filtros · ❌ no existe

---

## 0. Brechas transversales (bloquean a casi todas las pantallas)

| # | Brecha | Hoy en la API | Qué se necesita | Prioridad |
|---|---|---|---|---|
| T1 | **Autenticación real** | `X-Usuario-Id: <int>` en header (`app/dependencies.py`). Cualquier cliente puede leer los datos de otro usuario cambiando el número (BOLA/IDOR). `POST /auth/login` devuelve el *nombre del header*, no un token. | JWT de acceso (15 min) + refresh token rotatorio (cookie `HttpOnly`/`SameSite=Strict` en web). Solo cambia `usuario_actual()`, como ya anticipa su docstring. | **P0** |
| T2 | Versionado | Rutas en la raíz (`/planes`, `/riesgo`) | Prefijo `/api/v1` (router padre). Mantener alias sin prefijo durante la migración de la app Android. | P1 |
| T3 | Envelope de error uniforme | `{"detail": "..."}` en 404/409/503; 422 con el formato nativo de FastAPI | `{"error": {"code": "plan_sin_ajustes", "message": "...", "fields": [{"loc": "...", "msg": "..."}]}}`. La UI necesita **códigos estables** para elegir el estado (e14 «Sin datos suficientes» ≠ 404 real). | P1 |
| T4 | Paginación | Ningún `GET` de colección pagina (`/eventos` puede devolver miles de filas) | `?limit=&cursor=` (cursor por `numero`/`inicio`), respuesta `{"items": [], "next_cursor": "..."}`. | P1 |
| T5 | Zona horaria del usuario | Todo se guarda en UTC naive; `Usuario` no tiene `zona_horaria` | `usuario.zona_horaria` (IANA, p. ej. `America/Mexico_City`), `inicio_semana`, `formato_hora`, `idioma` (e38). Toda agregación por día/hora (heatmap, «uso nocturno 22–06», cierre «lunes 00:00») depende de esto. | **P0** |
| T6 | Agregados precalculados | `/estadisticas` suma al vuelo; `/riesgo` recorre todos los eventos de la semana en Python | Tablas materializadas `uso_hora` / `uso_dia` (ver §3, job J2). Sin esto el heatmap y el panel no escalan. | P1 |
| T7 | Dispositivo como entidad | Solo `token_dispositivo` (token FCM) | Tabla `dispositivo` (modelo, versión de la app, último heartbeat, batería, permisos, versión de config aplicada). La usan e6, e20–e32 («última sincronización con Pixel 7 Pro»), e38 (sesiones), e41 y e43. | P1 |
| T8 | Idempotencia en escrituras | No | Header `Idempotency-Key` en `POST`/`PUT` de configuración: e32 «No se pudo guardar · Reintentar» reintenta sin duplicar. | P2 |
| T9 | Concurrencia optimista | No | `ETag` / `If-Match` en los documentos de configuración (web y teléfono editan lo mismo) → `412 Precondition Failed`. | P2 |
| T10 | Arranque en frío | ✅ `DBAPIError → 503 + Retry-After: 30` | Ya cubre e3 «La primera vez del día puede tardar hasta 1 minuto». La UI debe reintentar respetando `Retry-After`. | — |

---

## 1. Matriz de cobertura de endpoints por pantalla

> Las rutas sugeridas ya incluyen `/api/v1`. Las rutas existentes se escriben como están hoy.

### 1.1 Acceso (e1–e5)

| Pantalla / componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| e1 Formulario de inicio de sesión + «Mantener la sesión iniciada» | `POST /api/v1/auth/login` (hoy `POST /auth/login`) | 🟡 | `{"email": str, "password": str, "recordar": bool}` | `200 {"access_token": str, "token_type": "bearer", "expires_in": 900, "usuario": {"id": int, "nombre": str, "foto_url": str\|null}}` + cookie `refresh_token` (7 d si `recordar`, sesión si no) |
| e2 «Correo o contraseña incorrectos · Quedan 4 intentos» + error en el campo | mismo | ❌ | — | `401 {"error": {"code": "credenciales_invalidas", "intentos_restantes": 4}}`; al agotarse, `429 {"code": "cuenta_bloqueada_temporal", "reintentar_en_seg": 900}` + `Retry-After`. Requiere un contador por email+IP (tabla `intento_login` o Redis). |
| e3 «Entrando…» | mismo | ✅ | — | `503 + Retry-After` mientras Azure SQL despierta (T10) |
| e1 Google / Apple / Facebook | `POST /api/v1/auth/oauth/{proveedor}` | ❌ | `{"id_token": str}` (flujo PKCE en el front) | igual que login. **Decidir** si el piloto lo necesita (ver C1). |
| e1 «Ver demo sin cuenta» | `POST /api/v1/auth/demo` | ❌ | — | token de solo lectura sobre un usuario semilla; las escrituras devuelven `403 {"code": "modo_demo"}` |
| e1 «Créala desde la app» | `POST /auth/registro` | ✅ | — | La web no registra; sin cambios. |
| e4 Recupera tu contraseña | `POST /api/v1/auth/password/olvido` | ❌ | `{"email": str}` | `202` **siempre** (no revela si el correo existe). Token de un solo uso, caduca en 30 min (texto de e4). |
| e5 «Reenviar en 0:45» | mismo endpoint | ❌ | — | `429 {"code": "reenvio_muy_pronto", "reintentar_en_seg": 45}` + `Retry-After` |
| (enlace del correo) Nueva contraseña | `POST /api/v1/auth/password/restablecer` | ❌ | `{"token": str, "password": str}` | `204`; revoca todos los refresh tokens. `410 {"code": "token_expirado"}` si ya caducó. |
| Renovar el token (transversal, e46) | `POST /api/v1/auth/refresh` | ❌ | cookie `refresh_token` | `200 {"access_token": ..., "expires_in": 900}` · `401 {"code": "sesion_expirada"}` |

### 1.2 Inicio · Panel General (e6–e8)

> Las 3 pantallas llevan la etiqueta **«(original)»** y un lenguaje de *portal de investigación* (telemetría, clústeres Big Data, «Buscar métrica o usuario»). Ver C2 antes de construir.

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| Selector de periodo «Hoy / 7D / 30D / Semestre Piloto» | parámetro común | ❌ | `?periodo=hoy\|7d\|30d\|piloto` o `?desde=&hasta=` | — |
| Estado «Nube sincronizada · 857 eventos» / «Sincronizando…» / «0 eventos» | `GET /api/v1/dashboard/resumen` (BFF que agrega las tarjetas en 1 llamada) | ❌ | `?periodo=7d` | `{"sync": {"estado": "sincronizado"\|"sincronizando"\|"sin_dispositivo", "eventos_periodo": int, "ultimo_evento": datetime}, "tarjetas": {...}}` (cada tarjeta trae `estado: "ok"\|"sin_datos"\|"insuficiente"` + `motivo`) |
| Tarjeta «Android Cloud Sync · Telemetry Pipeline» (Pixel 7 Pro, Android 14, v1.8.2, heartbeat, cola local) | `GET /api/v1/dispositivos/actual` | ❌ | — | `{"modelo": str, "so": str, "version_app": str, "vinculado": bool, "servicio_activo": bool, "ultimo_heartbeat": datetime, "cola_local": int}` |
| «12.4 KB/s · 98.9 % uptime · 42 ms latency» | — | ❌ | — | Métricas de infraestructura (App Insights), no del usuario. **No exponer** (C2). |
| «Clústeres de comportamiento» (Night Scrollers 31 %, Compulsive Openers 44 %, Focused Students 25 %, 15.2 M puntos) | `GET /api/v1/analitica/clusteres` | ❌ | `?periodo=` | `{"puntos": int, "clusteres": [{"id": "A", "nombre": str, "pct": float}], "cluster_usuario": "B"}`. **No hay modelo de clustering en el backend** (C3). Estado vacío e7: «Se necesitan al menos 3 días». |
| «Mapa de riesgo de recaída · Mamdani · 87.4 % confianza» (barras por hora 00–23, «Ventana crítica 22:00–00:00») | `GET /api/v1/analitica/riesgo-por-hora` | ❌ | `?periodo=7d` | `{"horas": [{"hora": 0..23, "indice": 0..100}], "ventana_critica": {"inicio": "22:00", "fin": "00:00"}, "confianza": float}`. **Ningún modelo produce riesgo por hora** (C4). |
| «Motor de inferencia · Regla activa #07 IF unlock_count > 15 AND time = 23:00 THEN Fricción 3 · μ = 0.88» | `GET /api/v1/friccion/inferencia/actual` | ❌ | — | Las reglas del código usan `adherencia` y `pct_ignoradas`, no `unlock_count` ni la hora (C4). |
| «Hábito semanal · Tiempo vs. Objetivo · −18.6 %» (Lun–Dom, uso real vs. objetivo) | `GET /api/v1/analitica/uso-diario` | ❌ | `?desde=&hasta=` | `{"dias": [{"fecha": date, "uso_min": float, "limite_min": float, "cumplio": bool}], "variacion_pct": float, "delta_promedio_min": float}` |
| «Apps restringidas · 3 h 42 m uso total · Social 52 % / Video / Gaming 17 %» | `GET /api/v1/analitica/uso-por-categoria` | ❌ | `?periodo=` | `{"total_min": float, "categorias": [{"categoria": str, "min": float, "pct": float}]}` |
| «Frecuencia de sesiones · últimas 12 h» | `GET /api/v1/analitica/aperturas` | ❌ | `?horas=12&bucket=1h` | `{"serie": [{"inicio": datetime, "aperturas": int}]}`. **`evento_uso` no distingue aperturas de tiempo** (C5). |
| «Intervenciones · Éxito por nivel · 79 % global · 323 recaídas prevenidas · +12 % vs. semana anterior» (Nivel 1 Timer 5 s 184 / 72 %, Nivel 2 Respiración 96 / 81 %, Nivel 3 Chatbot IA 89 %) | `GET /api/v1/intervenciones/resumen` | ❌ | `?periodo=7d&comparar=periodo_anterior` | `{"exito_global_pct": float, "prevenidas": int, "variacion_pct": float, "niveles": [{"nivel": 1, "nombre": str, "mostradas": int, "exito_pct": float}]}`. Éxito = pausa con `ignorada=false`. `pausa.tipo` (`leve\|media\|alta`) tiene que mapearse 1:1 a Nivel 1/2/3. |
| «Exportar datos CSV/JSON» | ver e37 | ❌ | — | — |
| «Buscar métrica o usuario ⌘K» | — | ❌ | — | Supone un rol de investigador que busca usuarios. **No hay roles** (C2). |

### 1.3 Mi plan (e9–e12)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| «Límite actual 2 h 21 min al día, desde el lunes» | `GET /planes/activo` | 🟡 | — | Agregar `limite_actual_min` (= `limite_base` × Π(1 + cambio/100)), `vigente_desde: date` |
| «Avance del plan · Semana 5 de 8 · meta final 2 h 00 min» | mismo | 🟡 | — | `Plan` no tiene `semanas_totales` ni `meta_final_min` → **migración** |
| «Cambio de esta semana −5.9 % · adherencia buena, pocas pausas ignoradas» | `GET /planes/{n}/ajustes/{semana}` | 🟡 | — | Agregar `nivel_adherencia`, `nivel_ignoradas`, `pct_ignoradas` y `mensaje`. `ajuste_plan` **no guarda `pct_ignoradas` ni `uso_real`**: el ajuste histórico no se puede volver a explicar (C7). |
| Gráficas de membresía (Adherencia 86 % → Baja 0 / Regular 0 / Buena 90 / Excelente 10; Pausas ignoradas 22 % → Pocas 92 / Muchas 0) + tabla de reglas con **fuerza** + «Cambio final de tu límite →» | `GET /api/v1/planes/{n}/ajustes/{semana}/explicacion` | ❌ | — | ver §2.1 |
| «Historial de ajustes» (S4 … S1 con %) | `GET /planes/{n}/ajustes` | ✅ | — | ya devuelve `semana`, `cambio_pct`, `fecha` |
| «Próximo ajuste: lunes 19 · 00:00 · Tu límite bajará a 2 h 13 min si mantienes…» | `GET /api/v1/planes/{n}/proyeccion` | ❌ | — | `{"proximo_ajuste": datetime (tz usuario), "limite_proyectado_min": float, "supuesto": {"adherencia": float, "pct_ignoradas": float}}` |
| e10 «Sensibilidad del ajuste» (Suave / Normal / Estricta) + «Permitir que el plan relaje el límite» | `PATCH /api/v1/planes/{n}` (hoy `PUT`) | ❌ | `{"sensibilidad": "suave"\|"normal"\|"estricta", "permitir_relajar": bool, "meta_final_min": int}` | `PlanRespuesta` + `cambios_pendientes: {"aplican_desde_semana": int, ...}` («Los cambios se aplican desde la próxima semana») |
| e10 «Así cambiaría tu límite» (tabla S6–S9 × 3 perfiles) + «Proyección con Normal · llegarías a tu meta en la semana 7» | `POST /api/v1/planes/{n}/simulacion` | ❌ | `{"perfiles": ["suave","normal","estricta"], "semanas": 4, "adherencia": 0.86?, "pct_ignoradas": 0.22?}` (por defecto toma los valores actuales) | `{"perfiles": [{"perfil": str, "semanas": [{"semana": 6, "limite_min": 134}], "semana_meta": 7}]}`. Cálculo puro, sin escribir en BD. |
| e11 «Sin semana completa» (4 de 7 días con datos; Lun 2 h 05 cumplió / Mar 2 h 40 se pasó / Vie sin datos; promedio 2 h 14; días cumplidos 3 de 4; faltan 3 días; «El lunes 19 de mayo verás tu primer ajuste») | `GET /api/v1/planes/{n}/semana-actual` | ❌ | — | `{"semana": int, "rango": {"desde": date, "hasta": date}, "dias": [{"fecha": date, "uso_min": float\|null, "estado": "cumplio"\|"se_paso"\|"sin_datos"\|"futuro"}], "promedio_min": float, "dias_cumplidos": int, "dias_con_datos": int, "primer_ajuste": date}` |
| e12 «Calculando con los datos de la semana…» | — | ✅ | — | Estado de carga del front. |

### 1.4 Riesgo de recaída (e13–e16)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| Nivel, probabilidad 48 %, «línea de alerta 42 %» | `GET /riesgo` | ✅ | — | `probabilidad`, `nivel`, `umbral` |
| «Desde 60 %: alto» | mismo | 🟡 | — | Agregar `umbral_alto` (hoy está fijo en `nivel()`). |
| «Qué tan confiable es 85 % · acierta en 85 de cada 100» / «Alertas acertadas 7 de 10» | `GET /api/v1/riesgo/modelo` | ❌ | — | `{"version": str, "entrenado_en": date, "n_variables": 7, "exactitud": 0.77, "precision": 0.77, "auc_roc": 0.85}`. **El 85 % es el AUC, no la exactitud** (C8). |
| «IA · Regresión logística entrenada desde…» | mismo | ❌ | — | `entrenado_en`, `datos: "sinteticos"\|"piloto"` |
| «Probabilidad por semana S1–S8» + «Valores por semana» | `GET /api/v1/riesgo/historial` | ❌ | `?plan=&limit=8` | `{"semanas": [{"semana": int, "desde": date, "hasta": date, "probabilidad": float, "nivel": str}]}`. Hoy solo se calcula la última semana. Requiere la tabla `riesgo_semanal` que llena el job J1. |
| «Contribución de cada factor» (7 variables con valor y sube/baja) | `GET /riesgo` | ✅ | — | `factores[]` ya ordenados por peso |
| «Qué puedes hacer» (2 recomendaciones) | `GET /riesgo` | 🟡 | — | Agregar `recomendaciones: [{"factor": str, "titulo": str, "texto": str}]` a partir de los 2 factores que más **suben** el riesgo (tabla fija en el backend, sin LLM). |
| e14 «Sin datos suficientes» (semanas con datos 1 de 2, días 7 de 14, qué variables están listas) | `GET /riesgo` | ❌ | — | Hoy responde **404** «El plan activo aún no tiene ajustes». Cambiar a `200 {"estado": "insuficiente", "progreso": {"semanas": {"actual": 1, "requeridas": 2}, "dias": {"actual": 7, "requeridos": 14}}, "variables": [{"variable": str, "lista": bool, "falta": str\|null}]}` |
| e15 Cargando | — | ✅ | — | — |
| e16 «Detalle de semana» (clic en S6: 9–15 jun, S5 vs. S6 en adherencia 84→91, uso de noche 29→24, pausas saltadas 20→15; «Lo que más pesó»; «Lo que te funcionó · Cumpliste 6 de 7 días») | `GET /api/v1/riesgo/semanas/{semana}` | ❌ | `?comparar=anterior` | `{"semana": int, "rango": {...}, "probabilidad": float, "delta_vs_umbral_pts": float, "factores": [...], "comparacion": [{"variable": str, "antes": float, "despues": float}], "logros": [{"titulo": str, "detalle": str}], "dias_cumplidos": int}` |

### 1.5 Uso por app (e17–e19 · e45/e46 usan la misma pantalla de fondo)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| Encabezado «Uso · 12 al 18 de mayo» + navegación por semana | parámetro común | ❌ | `?semana=2026-W20` o `?desde=&hasta=` | — |
| «Tiempo por app» (nombre, categoría, minutos, % vs. semana anterior) | `GET /api/v1/analitica/uso-por-app` | ❌ | `?desde=&hasta=&comparar=periodo_anterior&limit=` | `{"apps": [{"app_numero": int, "nombre": str, "paquete": str, "categoria": str, "min": float, "variacion_pct": float\|null}]}`. Hoy solo existe `GET /eventos` (filas crudas, sin paginar): **agregar en el cliente no es viable**. |
| «Por categoría» (8 h 22 · 52 %, …) | `GET /api/v1/analitica/uso-por-categoria` | ❌ | igual | ver 1.2 |
| «Mapa de calor · día × hora» + «Pico: vie 23:00 · 48 min» + leyenda «Sin uso … 48+ min» | `GET /api/v1/analitica/heatmap` | ❌ | `?desde=&hasta=&bucket=1h` (tz del usuario, T5) | `{"dias": ["lun",…], "horas": [0..23], "celdas": [[int × 24] × 7], "max_min": 48, "pico": {"dia": "vie", "hora": 23, "min": 48}}`. Los eventos que cruzan de hora **se reparten** entre buckets. La tabla `franja` (catálogo global de 2 h) **no sirve** para buckets de 1 h (C6). |
| «Horas pico» (top 3) + «Tu uso se concentra de 22:00 a 01:00…» | mismo | ❌ | — | `{"top": [{"dia": str, "hora": int, "min": float}], "ventana_pico": {"inicio": "22:00", "fin": "01:00"}}` |
| Responsive 1920 / 1024 (e18, e19) | — | — | — | Sin impacto en la API. |

### 1.6 Apps y sitios · reglas, apps, límites, sitios, privacidad (e20–e32)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| Encabezado «Cambios protegidos y auditados · Todo guardado» + pie «Cambios locales pendientes · La última sincronización con Pixel 7 Pro fue hace…» | `GET /api/v1/configuracion/estado` | ❌ | — | `{"version": int, "guardado_en": datetime, "dispositivo": {"nombre": str, "version_aplicada": int, "ack_en": datetime}}` |
| «Guardar y enviar al teléfono» (guarda **varias** secciones a la vez, ver e30) | `PUT /api/v1/configuracion` | ❌ | Documento completo `{"friccion": {...}, "modo_foco": {...}, "limites": {...}}` + `If-Match: <version>` + `Idempotency-Key` | `200 {"version": int}` y un push al teléfono por FCM (job J9). `412` si el teléfono cambió algo antes. |
| «Restablecer valores por defecto» | `POST /api/v1/configuracion/restablecer` | ❌ | `{"secciones": ["friccion"]}` | nueva versión |
| e31 «Guardado y enviado al teléfono · **Deshacer**» | `POST /api/v1/configuracion/revertir` | ❌ | `{"a_version": int}` | nueva versión con el contenido anterior. Requiere el historial `configuracion_version`, que además cumple «auditados». |
| e31 «Solo guardado en este navegador · Los niveles de fricción todavía no se pueden cambiar desde aquí» | `GET /api/v1/configuracion/capacidades` | ❌ | — | `{"editable_web": ["limites", "sitios"], "solo_telefono": ["friccion.niveles"]}` (C10) |
| e31 «Guardando… Descargando 12 eventos nuevos del dispositivo» | — | ❌ | — | La web no descarga eventos; texto engañoso (C10). |
| e32 «No se pudo guardar · Sin conexión · Reintentar» | — | 🟡 | — | Error de red del cliente; con `Idempotency-Key` (T8) el reintento es seguro. |
| **e20 Reglas de fricción**: «Calibración del sistema · Adaptativo», duración del temporizador 3/9/15 s, tipo de ejercicio del Nivel 2 (respiración / pregunta / retraso), niveles 1–3 con espera 5/9/15 s, «Progresión sugerida» S1–S4, «Personalizar tiempos de espera» | `GET`/`PUT /api/v1/configuracion/friccion` (subdocumento) | ❌ | `{"adaptativo": bool, "temporizador_seg": 3..15, "ejercicio_nivel2": "respiracion"\|"pregunta"\|"retraso", "niveles": [{"nivel": 1, "espera_seg": 5}], "progresion": [{"semana": 1, "nivel": 1, "espera_seg": 5}]}` | igual al request + `version`. **No hay ninguna tabla para esto.** |
| e20 «Modo Foco programado» (días L–D, hora de inicio/fin, «6 h por día · 5 días activos 08:00–14:00») | `GET`/`PUT /api/v1/configuracion/modo-foco` | ❌ | `{"activo": bool, "dias": ["lun",…], "inicio": "08:00", "fin": "14:00"}` | `+ horas_por_dia`. No es lo mismo que `sesion_foco` (sesiones ad hoc) → C11. |
| **e21 Catálogo de apps restringidas**: buscador, filtro por categoría, columnas Fricción (Nivel 1–3) / Límite diario (min) / Uso hoy «22 / 30 min», «5 activas» | `GET /apps` | 🟡 | agregar `?q=&categoria=&activa=&incluir=uso_hoy` + paginación | `App` + `nivel_friccion: 1..3`, `limite_diario_min: int`, `activa: bool`, `uso_hoy_min: float`. **Hoy solo existe `limite_aperturas`** (C9). |
| e21 «Las aplicaciones desactivadas conservan su historial» | `PATCH /api/v1/apps/{n}` | 🟡 | `{"activa": false}` | Hoy `DELETE /apps/{n}` borra la fila y deja huérfanos `evento_uso`/`pausa`, o falla por la FK. → usar `activa`. |
| e21 «Resumen de intervenciones · Fricción activa hoy» (47 mostradas / 29 abandonaron / 18 continuaron, distribución por nivel, apps con más pausas) | `GET /api/v1/intervenciones/resumen` | ❌ | `?fecha=hoy` | `{"mostradas": int, "abandonaron": int, "continuaron": int, "por_nivel": [{"nivel": int, "apps": [str]}], "top_apps": [{"app_numero": int, "nombre": str, "pausas": int}]}` |
| **e22 Diálogo «Agregar app restringida»** (nombre, paquete Android, categoría, límite de aperturas por día con −/+, «Activar fricción progresiva (niveles 1 → 3)») | `POST /apps` | 🟡 | `{"nombre": str, "paquete": str, "categoria": enum, "limite_aperturas": int, "friccion_progresiva": bool}` | `201 AppRespuesta`; `409 {"code": "paquete_duplicado"}` (hoy no hay unique `(usuario_id, paquete)`); `422` si el paquete no cumple `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$` |
| **e23 Límite diario global** (3 h 00, hoy 1 h 12 = 40 %, −/+ con paso de 30 min, «Meta final de tu plan: 2 h 30») | `GET`/`PUT /api/v1/configuracion/limites` | ❌ | `{"global_min": 180, "por_categoria": [{"categoria": str, "min": int}], "por_dia": [{"dia": "lun", "min": int}], "descanso_nocturno": {"activo": bool, "inicio": "23:00", "fin": "07:00"}, "reduccion_gradual": {"activa": bool}}` | + `uso_hoy_min`, `uso_hoy_pct`. **Choca con `plan.limite_base`** (C12). |
| e23 «Límite por categoría» (Redes 42 / 60, Video 31 / 45, Juegos 25 / 25, Mensajería 9 / 30) | mismo + `GET /api/v1/analitica/uso-por-categoria?fecha=hoy` | ❌ | — | — |
| e23 «Límite por día de la semana · Uso real vs. límite» | `GET /api/v1/analitica/uso-diario` | ❌ | `?desde=&hasta=` | ver 1.2 |
| e23 «Reducción gradual · El límite baja 10 % cada semana · Próximo ajuste: lunes 12 oct» | — | ❌ | — | **Contradice** al controlador difuso, que da −10…+5 % (C12). |
| e23 «Días de examen y entregas · + Agregar excepción» | `GET`/`POST`/`DELETE /api/v1/configuracion/limites/excepciones` | ❌ | `{"fecha": date, "fecha_fin": date?, "limite_min": int, "motivo": str}` | lista |
| **e24 Sitios bloqueados**: input «ejemplo.com» + horario «Siempre» / rango; tabla con Sitio / Horario / Intentos 7 d / Estado (Activo / Pausado «En pausa hasta mañana») | `GET`/`POST /dominios` | 🟡 | `POST {"dominio": str, "horario": {"tipo": "siempre"} \| {"tipo": "rango", "inicio": "22:00", "fin": "06:00"}}` | `DominioRespuesta` + `horario`, `estado: "activo"\|"pausado"`, `pausado_hasta: datetime\|null`, `intentos_7d: int`. Hoy solo hay `dominio` y `activo`. |
| e24 Pausar un sitio | `PATCH /api/v1/dominios/{n}` | 🟡 | `{"pausado_hasta": datetime}` | — |
| e24 «Intentos de esta semana» (Lun–Dom) + «Más intentos esta semana» | `GET /api/v1/dominios/intentos` | ❌ | `?desde=&hasta=&agrupar=dia\|dominio` | `{"por_dia": [{"fecha": date, "intentos": int}], "por_dominio": [{"dominio": str, "intentos": int}]}`. Requiere que el teléfono **reporte** intentos: `POST /api/v1/dominios/intentos:lote` (tabla nueva `intento_dominio`). |
| e24 «Sugerencias para bloquear» (instagram.com, twitch.tv…) | `GET /api/v1/dominios/sugerencias` | ❌ | — | Lista fija por ahora; no hay historial de navegación (y la política de privacidad dice que no se recopila). |
| e24 «Tu teléfono se actualizó hace 2 min» | `GET /api/v1/dispositivos/actual` | ❌ | — | ver T7 |
| e25 Sin sitios | `GET /dominios` → `[]` | ✅ | — | — |
| e26 «Sitio no válido» | `POST /dominios` | 🟡 | — | `422 {"code": "dominio_invalido", "fields": [{"loc": "dominio"}]}`. Hoy acepta cualquier string. Normalizar (quitar esquema, `www.` y ruta; minúsculas; IDNA) + unique `(usuario_id, dominio)` → `409 dominio_duplicado`. |
| e27 Confirmar borrado | `DELETE /dominios/{n}` | ✅ | — | `204` |
| e28 «Aviso con deshacer» | `POST /api/v1/dominios/{n}/restaurar` | ❌ | — | Hoy el borrado es definitivo y volver a crearlo con `POST` cambia el `numero`. → soft delete (`eliminado_en`) + restaurar durante unos 10 s (o diferir el `DELETE` en el cliente). |
| **e29 Privacidad académica** (5 toggles, nivel de anonimización, retención 30 / 90 / fin del estudio) | `GET`/`PUT /api/v1/privacidad/preferencias` | ❌ | `{"compartir_agregadas": bool, "participar_clustering": bool, "incluir_nocturno": bool, "compartir_intervenciones": bool, "reportes_tecnicos": bool, "anonimizacion": "sin_nombre"\|"anonimo"\|"agregado", "retencion": "30d"\|"90d"\|"fin_estudio"}` | igual + `actualizado_en` |
| e29 «Consentimiento informado · 12 sep 2026 · versión 1.2 · Firmado · Ver documento · Retirar» | `GET /api/v1/consentimientos/actual`, `POST /api/v1/consentimientos/{version}/firmar`, `POST /api/v1/consentimientos/retirar` | ❌ | — | `{"version": "1.2", "firmado_en": datetime, "documento_url": str (SAS de Blob, caduca)}` |
| e29 «Descargar mis datos» | ver e37 | ❌ | — | — |
| e29 «Solicitar eliminación de mis datos · Procesamos las solicitudes en…» | `POST /api/v1/privacidad/solicitudes-eliminacion` | ❌ | `{"motivo": str?}` | `202 {"id": int, "estado": "recibida", "fecha_limite": date}` → job J6 |
| e30 «Cambios sin guardar» (diff: límite global 3 h → 2 h 30, Instagram aperturas 8, Fricción Nivel 2 pausa 10 s) | `PUT /api/v1/configuracion` | ❌ | — | El diff mezcla `limites`, `apps` y `friccion`: si se guardan con 3 llamadas distintas, el guardado deja de ser atómico (C13). |

### 1.7 Foqui (e33–e35)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| Resumen «Tu semana con Foqui · Semana del 12 al 18 de mayo» (mensaje inicial) | `GET /api/v1/resumenes/semanales/actual` | 🟡 | — | Hoy se obtiene con `POST /companero/mensaje` y `mensaje` vacío, **generando con el LLM en cada carga**. Debe leerse ya generado (job J3): `{"semana": int, "rango": {...}, "texto": str, "estado_foqui": str, "fuente": "llm"\|"respaldo", "generado_en": datetime, "kpis": {...}}` |
| Estado de Foqui «Atenta / Escribiendo… / Sin conexión» | `estado_foqui` | ✅ | — | «Escribiendo» y «Sin conexión» son estados del cliente. |
| KPIs «Promedio diario 2 h 18 min −34 % vs. semana anterior · Adherencia 86 % 6 de 7 días · Ajuste −5.9 % · Riesgo medio 48 %» | `kpis` del resumen | 🟡 | — | `ContextoCompanero` trae `minutos_semana`, `adherencia`, `cambio_pct` y `riesgo_*`; **faltan** `promedio_diario_min`, `variacion_pct` y `dias_cumplidos`. |
| Chips «¿Cómo cuido la noche? · Dame un consejo para la noche · ¿Por qué subió mi riesgo? · Resúmeme mi semana» | `sugerencias` en la respuesta | ❌ | — | `sugerencias: [str]` (máx. 4), elegidas por reglas según el factor principal |
| Input «Escribe a Foqui…» | `POST /companero/mensaje` | ✅ | `{"mensaje": str, "historial": [...]}` | `RespuestaCompanero` |
| e34 «Escribiendo… · Espera a que Foqui termine o **detén la respuesta**» | `POST /api/v1/companero/mensajes:stream` (SSE) | ❌ | igual | `text/event-stream`, ver §2.3 |
| e35 «Sin conexión» + resumen automático con viñetas (promedio, 6 de 7 días, límite −5.9 %, riesgo 48 %) | `fuente: "respaldo"` | 🟡 | — | El respaldo ya existe; falta devolver `viñetas: [str]` estructuradas y un `codigo: "llm_no_disponible"` para que la UI muestre «Reintentar». |
| e35 «Lo que pasó antes de la caída sigue guardado» | — | ❌ | — | La API **no guarda conversaciones** (`historial` va en cada request, máx. 10). Si el texto se refiere al historial del chat: guardarlo en `sessionStorage` del cliente o crear `conversacion` en la BD (C14). |
| «Lo que Foqui sabe de ti» (Sí recibe / Nunca recibe) | — | ✅ | — | Coincide con `ContextoCompanero` (solo agregados). |
| «Tu semana · Uso por día» | `GET /api/v1/analitica/uso-diario` | ❌ | — | ver 1.2 |

### 1.8 Reportes (e36–e37)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| Lista «Resúmenes semanales» (rango, «2 h 18 min · riesgo medio», badge «Nuevo», «Semana inicial · sin riesgo», «Antes del plan · 3 h 55 min») | `GET /api/v1/resumenes/semanales` | ❌ | `?limit=&cursor=` | `{"items": [{"semana": int\|null, "rango": {...}, "uso_promedio_min": float, "riesgo_nivel": str\|null, "tipo": "linea_base"\|"inicial"\|"normal", "leido": bool}]}` |
| Detalle «Escrito por Foqui el lunes 19 de mayo a las…» + «Uso diario de esa semana» | `GET /api/v1/resumenes/semanales/{semana}` | ❌ | — | texto + `generado_en` + `dias[]`. Al abrirlo: `POST …/{semana}/leido` (quita el badge «Nuevo»). |
| «Descargas recientes» (Mis datos · 4 semanas (tabla) · 19 may; Resumen (PDF) · 12 may) | `GET /api/v1/exportaciones` | ❌ | — | `{"items": [{"id": uuid, "tipo": str, "formato": str, "creado_en": datetime, "estado": str, "url": str\|null, "expira_en": datetime}]}` |
| e37 «Exportar métricas» — periodo, formato (Tabla CSV / PDF con gráficas / JSON) e «Incluir» con conteos (28 días, 214 pausas, 4 semanas, 4 textos) + «≈ 1.2 MB · seudonimizado» | `GET /api/v1/exportaciones/vista-previa` | ❌ | `?desde=&hasta=&incluir=uso,pausas,plan,riesgo,resumenes` | `{"conteos": {"dias_uso": 28, "pausas": 214, "semanas_plan": 4, "resumenes": 4}, "tamano_estimado_bytes": int}` |
| e37 Botón «Descargar» | `POST /api/v1/exportaciones` | ❌ | `{"desde": date, "hasta": date, "formato": "csv"\|"pdf"\|"json", "incluir": [str]}` | `202 {"id": uuid, "estado": "en_cola"}` + `Location`; luego `GET /api/v1/exportaciones/{id}` → `{"estado": "lista", "url": SAS de Blob, 15 min}`. Lo procesa el job J5. |

### 1.9 Ajustes (e38–e41)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| e38 Perfil (iniciales «DR», nombre, «Estudiante · UAQ») | `GET /usuarios/me` | 🟡 | — | Agregar `rol`, `institucion`, `programa` («Piloto Focus! · UAQ»). |
| e38 «Contraseña · Último cambio: hace 3 meses» | mismo | ❌ | — | Agregar `password_cambiado_en`. El cambio de contraseña debería ser `POST /api/v1/auth/password/cambiar {"actual", "nueva"}` (hoy viaja en `PUT /usuarios/me` **sin pedir la contraseña actual**). |
| e38 «Preferencias»: idioma, zona horaria, la semana empieza, formato de hora | `PATCH /api/v1/usuarios/me` | ❌ | `{"idioma": "es-MX", "zona_horaria": "America/Mexico_City", "inicio_semana": "lunes", "formato_hora": "24h"}` | T5 |
| e38 «Tu cuenta · Tipo, Miembro desde, Programa» | `GET /usuarios/me` | 🟡 | — | `fecha_registro` ✅; faltan `rol` y `programa`. |
| e38 «Sesiones abiertas» (Este navegador · Chrome en Windows · Querétaro · Activa ahora; Pixel 7 Pro · App 1.8 · hace 2 min) + cerrar cada una | `GET /api/v1/auth/sesiones`, `DELETE /api/v1/auth/sesiones/{id}` | ❌ | — | `{"items": [{"id": uuid, "tipo": "web"\|"app", "agente": str, "ubicacion_aprox": str, "ultima_actividad": datetime, "actual": bool}]}`. Depende de T1 (tabla `refresh_token`). |
| e39 Avisos: cambio de límite, 80 % del límite, recordatorio de Modo Foco 23:30, resumen de Foqui lun 08:00, riesgo alto, copia por correo, horario silencioso, fines de semana | `GET`/`PUT /api/v1/notificaciones/preferencias` | ❌ | `{"cambio_limite": bool, "cerca_limite": {"activo": bool, "umbral_pct": 80}, "recordatorio_foco": {"activo": bool, "hora": "23:30"}, "resumen_semanal": {"activo": bool, "dia": "lun", "hora": "08:00"}, "riesgo_alto": bool, "correo_resumen": bool, "silencio": {"activo": bool, "inicio": str, "fin": str, "fines_semana": bool}}` | igual. Lo consume el job J4. |
| e39 «Así se ven en tu teléfono» (previews) | — | ✅ | — | Plantillas estáticas del front. |
| e40 Estudio de hábitos: «Participar en el estudio», «Compartir mis respuestas de Foqui» | `GET`/`PUT /api/v1/privacidad/preferencias` | ❌ | `{"participar_estudio": bool, "compartir_respuestas_foqui": bool}` | **Se cruza con e29** (C15). |
| e40 «Historial de permisos · Aceptaste participar en el estudio · 7 abr» | `GET /api/v1/privacidad/historial` | ❌ | `?limit=&cursor=` | `{"items": [{"evento": str, "detalle": str, "fecha": datetime}]}` (tabla de auditoría, append-only) |
| e40 «Qué guardamos y por cuánto tiempo» (uso por app 12 meses, resúmenes 6 meses, sitios mientras los uses) | `GET /api/v1/privacidad/retencion` | ❌ | — | Tabla fija servida por la API para que coincida con lo que **realmente** purga J6. Hoy **nada se purga**. |
| e41 Dispositivo (Pixel 7 Pro, App 1.8, Wi-Fi, «Conectado», última actualización hace 2 min, batería 78 %) | `GET /api/v1/dispositivos/actual` | ❌ | — | T7 + `red: "wifi"\|"datos"`, `bateria_pct` |
| e41 «Permisos del teléfono» (Uso de apps · Concedido, Accesibilidad, Mostrar sobre otras apps) | mismo | ❌ | — | `permisos: {"uso_apps": "concedido"\|"denegado", "accesibilidad": ..., "superposicion": ...}`. El teléfono los manda con `POST /api/v1/dispositivos/{id}/heartbeat`. |
| e41 «Protecciones activas» (bloqueo de sitios 3 activos, pausas 6 apps, Modo Foco 23:30) | `GET /api/v1/dispositivos/actual/protecciones` | ❌ | — | Conteos derivados de `dominios`, `apps` y `configuracion.modo_foco`. ⚠ e20 dice Modo Foco 08:00–14:00 y e41 dice 23:30 (C11). |
| e41 «Actividad de hoy · Cuándo tu teléfono envió tu uso» (timeline 00–18) | `GET /api/v1/dispositivos/{id}/actividad` | ❌ | `?fecha=` | `{"envios": [{"en": datetime, "eventos": int}]}` (log de heartbeat/ingesta) |

### 1.10 Cuenta (e42–e47)

| Componente | Endpoint | Estado | Request | Response |
|---|---|---|---|---|
| e42 Menú (nombre, correo, «Participante · usuario 1») | `GET /usuarios/me` | 🟡 | — | `rol`, `codigo_participante` (se muestra un **id interno**; usar el seudónimo) |
| e42 «Ayuda y soporte» | — | ❌ | — | Sin endpoint; definir `mailto:` o `POST /api/v1/soporte/tickets`. |
| e43 Editar perfil: **Nombre + Apellidos**, foto «JPG o PNG de hasta 2 MB», «Quitar», correo «No editable», miembro desde, «Plan activo · Semana 3 de 8», «Dispositivo · Pixel 7». El diseño anota literalmente `PUT /usuarios/me` | `PUT /usuarios/me`, `POST /usuarios/me/foto/archivo` | 🟡 | `{"nombre": str, "apellidos": str}` | `Usuario` tiene un solo `nombre` (C16). Límite de foto: la API acepta 5 MB y WEBP, el diseño dice 2 MB y JPG/PNG. |
| e43 «Quitar» foto | `DELETE /api/v1/usuarios/me/foto` | ❌ | — | `204` + borrar el blob |
| e44 «¿Desactivar tu cuenta? · Escribe DESACTIVAR» | `DELETE /usuarios/me` | ✅ | — | Ya pone `activo=false` (soft delete). Faltan: revocar los refresh tokens (T1), desactivar los tokens FCM y anonimizar según e44 («Tus registros se conservan de forma anónima»). La confirmación DESACTIVAR es del cliente. |
| e44 «Podrás reactivarla escribiendo al equipo» | `POST /api/v1/admin/usuarios/{id}/reactivar` | ❌ | — | Requiere un rol admin/investigador (C2). |
| e45 «¿Cerrar sesión? Tu teléfono seguirá aplicando tus límites» | `POST /api/v1/auth/logout` | ❌ | cookie refresh | `204`; revoca **solo** la sesión web. |
| e46 «Tu sesión terminó · Por seguridad cerramos tu sesión después de…» | cualquier ruta privada | ❌ | — | `401 {"code": "sesion_expirada"}` + `WWW-Authenticate: Bearer error="invalid_token"`. El cliente intenta `/auth/refresh` una vez y, si falla, muestra e46. |
| e47 Página no encontrada | — | ✅ | — | Ruta del front. Para recursos: `404 {"code": "no_encontrado"}`. |

---

## 2. Endpoints especiales de algoritmos

### 2.1 Controlador difuso (Mamdani) · Mi plan

**Qué existe:** `app/utils/reglas_plan.py` (fusificación trapezoidal → min → max → centroide), que usan `POST /planes/{n}/ajustes` (si no mandas `cambio_pct`) y una **copia** en `serverless/reglas_plan.py` (`GET|POST /api/ajuste-semanal`).

**Qué pide la UI y no existe:**

1. **Explicación de un ajuste (e9).** `GET /api/v1/planes/{n}/ajustes/{semana}/explicacion`
   ```json
   {
     "entradas": {"adherencia": 0.86, "pct_ignoradas": 0.22},
     "membresias": {
       "adherencia": {"baja": 0.0, "regular": 0.0, "buena": 0.9, "excelente": 0.1},
       "ignoradas": {"pocas": 0.92, "muchas": 0.0}
     },
     "reglas": [
       {"si_adherencia": "excelente", "y_ignoradas": "pocas", "entonces": "reducir_mucho", "salida_pct": -10, "fuerza": 0.10},
       {"si_adherencia": "buena", "y_ignoradas": "pocas", "entonces": "reducir_poco", "salida_pct": -5, "fuerza": 0.90}
     ],
     "salida": {"centroide_pct": -5.9, "conjunto_agregado": [[-15.0, 0.0], [-14.9, 0.0]]},
     "limite": {"antes_min": 150, "despues_min": 141}
   }
   ```
   Requisito de datos: `ajuste_plan` debe **guardar las entradas** (`pct_ignoradas`, `uso_real_min`, `sensibilidad`) para que la explicación de semanas pasadas no cambie si después se editan pausas (C7). Las funciones `trapecio()`/`REGLAS` ya bastan; falta una función `explicar()` que devuelva los pasos intermedios en lugar de solo el centroide.
2. **Calibración por el usuario (e10).** No se exponen las funciones de membresía (son del modelo, no del usuario). La UI calibra con `sensibilidad` (`suave | normal | estricta`), que **escala los conjuntos de salida** (−5 / −10 / −15 % máximo) y con `permitir_relajar` (que apaga la regla `baja → relajar`). Se guarda en `plan` con efecto a partir de la próxima semana (`PATCH /api/v1/planes/{n}`).
3. **Simulación (e10).** `POST /api/v1/planes/{n}/simulacion` recorre N semanas con los 3 perfiles, suponiendo la adherencia y las pausas actuales. Es cálculo puro, no toca la BD y responde en milisegundos (no necesita background).
4. **Proyección (e9).** `GET /api/v1/planes/{n}/proyeccion` = simulación de 1 semana con el perfil vigente.
5. **Una sola fuente de reglas.** Hoy las reglas están duplicadas entre `app/utils` y `serverless/`. Propuesta: el job de cierre semanal (J1) llama a la API (o importa un paquete compartido) en lugar de mantener una copia.
6. ⚠ **Segundo controlador difuso que no existe:** e6 («Regla activa #07 IF unlock_count > 15 AND time = 23:00 THEN Fricción Nivel 3 · μ = 0.88») y e20 («Calibración del sistema · Adaptativo») describen un controlador **de fricción en tiempo real** con entradas `unlock_count` y hora. Ese controlador, si existe, vive en el teléfono; el backend no lo tiene (C4).

### 2.2 Regresión logística · riesgo de recaída

**Cuándo consulta la UI:**

| Momento | Endpoint | Por qué |
|---|---|---|
| Al abrir *Riesgo* (e13) | `GET /riesgo` + `GET /api/v1/riesgo/historial?limit=8` + `GET /api/v1/riesgo/modelo` (este último cacheable 24 h) | Pinta el nivel, la serie S1–S8 y la confiabilidad |
| Al hacer clic en una semana (e16) | `GET /api/v1/riesgo/semanas/{s}?comparar=anterior` | Detalle bajo demanda |
| Panel (e6), Foqui (e33), Reportes (e36) | Leen `riesgo_*` del resumen o del BFF, **sin recalcular** | — |
| Push «Riesgo alto» (e39) | Lo decide el job J1, no la UI | — |

**Cómo:** el riesgo predice la **semana siguiente** y solo cambia al cerrar una semana. Por eso:
- El job J1 guarda un snapshot en `riesgo_semanal (plan_id, semana, probabilidad, nivel, variables JSON, factores JSON, modelo_version)` con unique `(plan_id, semana)`.
- `GET /riesgo` lee el último snapshot (`ETag` + `Cache-Control: private, max-age=3600`) y solo recalcula al vuelo si falta (primera semana o backfill).
- Datos insuficientes → `200 {"estado": "insuficiente", ...}` (e14), **no 404**.
- `modelo_version` en cada respuesta, para que el historial no mezcle versiones sin aviso.
- **Reentrenamiento:** hoy `ia/entrenar.py` es offline y usa datos sintéticos (2000 usuarios). En producción: job J7 mensual y manual que entrena con datos reales consentidos (e29 «Participar en el análisis…») y publica `modelo_riesgo.json` en Blob versionado. La API carga la versión indicada en `RIESGO_MODELO_VERSION` (app setting), sin redeploy.

### 2.3 Agente LLM «Foqui»

| Uso | Transporte | Endpoint | Justificación |
|---|---|---|---|
| **Resumen semanal** (e33 primer mensaje, e36 lista y detalle, correo e39) | JSON estándar, **ya generado** | `GET /api/v1/resumenes/semanales[/actual\|/{semana}]` | Se genera una vez el lunes (J3); cargar la pantalla no debe costar tokens ni esperar 5–20 s. «Escrito por Foqui el lunes 19 de mayo a las…» confirma que es un artefacto persistido. |
| **Chat** (e33 → e34) | **SSE** (`text/event-stream`) sobre `POST` | `POST /api/v1/companero/mensajes:stream` | e34 muestra «Escribiendo…» y un botón para **detener la respuesta**: hace falta streaming token a token y poder cancelar. Basta con que el cliente aborte el `fetch` (`AbortController`); el servidor detecta la desconexión y cancela el stream del SDK de Anthropic (deja de consumir tokens). WebSocket no hace falta (la comunicación es unidireccional) y el polling no da la UX de e34. |
| **Fallback** | JSON | `POST /companero/mensaje` (existente) | Se mantiene para la app Android y para clientes sin SSE. |

Eventos SSE propuestos:
```
event: meta     data: {"estado_foqui":"Atenta","fuente":"llm"}
event: delta    data: {"texto":"Tu uso nocturno es 31 % "}
event: delta    data: {"texto":"del total y casi…"}
event: fin      data: {"sugerencias":["¿Cómo voy esta semana?"],"tokens":182}
event: error    data: {"code":"llm_no_disponible","respaldo":{"texto":"…","vinetas":["…"]}}
```
- Timeout de 20 s (ya configurado en `app/utils/llm.py`) → emite `error` con el respaldo (e35) en lugar de cortar la conexión.
- Rate limit por usuario (p. ej. 20 mensajes/hora) → `429 {"code":"limite_mensajes"}`.
- El historial sigue viajando en el request (máx. 10 turnos). Si se decide guardarlo (C14): tabla `conversacion` + `mensaje`, con la retención de e40 («Resúmenes de Foqui · 6 meses»).
- En Azure App Service con gunicorn/uvicorn, SSE funciona con `StreamingResponse`; hay que desactivar el buffering (`X-Accel-Buffering: no`) y considerar que el timeout de inactividad del front-end de App Service es de 230 s.

---

## 3. Tareas asíncronas y cron jobs (Azure Functions)

> Hoy solo existe `ajuste-semanal` con **HTTP trigger**: no hay ningún timer, así que **nada ocurre solo**. Hoy los ajustes semanales los crea alguien llamando a `POST /planes/{n}/ajustes` y mandando la `adherencia` calculada por el cliente.

| ID | Job | Trigger | Qué hace | Lo consumen las pantallas | Notas |
|---|---|---|---|---|---|
| **J1** | **Cierre semanal** | Timer cada hora (`0 0 * * * *`) que procesa a los usuarios cuyo **lunes 00:00 local** ya pasó (T5) | 1) Calcula `uso_real` y `adherencia` (días cumplidos / días con datos) y `pct_ignoradas` desde `uso_dia`/`pausa`. 2) Corre el controlador difuso con la `sensibilidad` vigente → inserta `ajuste_plan` (guardando las entradas) y avanza `semana_actual`. 3) Calcula y guarda `riesgo_semanal`. 4) Encola J3 y J4. | e9, e11, e13, e16, e33, e36 | **Idempotente**: el unique `(plan_id, semana)` ya existe; usar `INSERT … ON CONFLICT DO NOTHING` / `MERGE`. Activa la Azure SQL serverless: agrupar el trabajo en un solo despertar. |
| **J2** | Agregación de uso | Queue trigger por cada lote ingerido desde el teléfono (o timer cada 15 min) | Reparte `evento_uso` en buckets de 1 h en la tz del usuario → `uso_hora (usuario_id, fecha_local, hora, app_id, segundos, aperturas)` y `uso_dia`. Tolera eventos tardíos (re-agrega el día afectado). | e6, e11, e17, e23, e33, e37, e41 | Sustituye a la tabla `franja` de 2 h para la analítica (C6). |
| **J3** | Resumen semanal de Foqui | Queue trigger (lo encola J1) | Arma `ContextoCompanero`, llama al LLM (con reintentos y backoff) y guarda `resumen_semanal (usuario_id, semana, texto, vinetas, estado_foqui, fuente, kpis JSON, generado_en, leido)`. Si el LLM falla tras N reintentos → guarda el **respaldo** con `fuente="respaldo"`. | e33, e35, e36, correo de e39 | Nunca en el request del usuario. |
| **J4** | Notificaciones | Timer cada 5 min + mensajes de J1/J3 | Respeta el horario silencioso y los fines de semana. Avisos: límite cambió (lun 08:00 local), resumen listo, riesgo alto, recordatorio Modo Foco. Envía push por FCM (`token_dispositivo`) y correo (Azure Communication Services). | e39 | «Cuando me acerque al 80 %» se debe disparar **en el teléfono** (tiene el uso en tiempo real); el backend solo guarda la preferencia (C17). |
| **J5** | Exportaciones | Queue trigger (`POST /exportaciones`) | Genera CSV/JSON/PDF seudonimizado, sube a Blob (`exportaciones/{usuario}/{id}`), actualiza el estado y emite una SAS de 15 min por `GET`. | e29, e37, e42 | Los PDF con gráficas pesan: hacerlos en la Function, no en App Service. |
| **J6** | Retención y eliminación | Timer diario 03:00 | Purga según la retención de e29/e40 (30 / 90 días / fin del estudio; uso 12 meses; resúmenes 6 meses). Atiende las solicitudes de eliminación pendientes y anonimiza a los usuarios desactivados (e44). | e29, e40, e44 | Debe coincidir con `GET /privacidad/retencion`; registra en la auditoría. |
| **J7** | Reentrenamiento del modelo de riesgo | Timer mensual (o manual) | Entrena con datos reales de quienes consintieron, valida contra el modelo vigente y publica `modelo_riesgo_vX.json` + `metricas.json` en Blob. **No** cambia de versión automáticamente: requiere aprobación. | e13 «confiable / alertas acertadas» | Depende de que haya suficientes semanas reales. |
| **J8** | Clustering de comportamiento | Timer nocturno | k-means sobre `uso_hora` (aperturas, duración media, % nocturno) → `cluster_usuario`. | e6/e7 | Solo si se mantiene la tarjeta (C3). |
| **J9** | Envío de configuración al teléfono | Queue trigger (`PUT /configuracion`) | Manda un push FCM *data-only* «config v{n} disponible»; el teléfono hace `GET` y responde `POST /dispositivos/{id}/sync-ack`. | e20–e32 pie «última sincronización», e41 | — |
| **J10** | Limpieza de seguridad | Timer diario | Borra refresh tokens caducos, tokens de recuperación usados o vencidos, contadores de intentos de login y exportaciones vencidas en Blob. | — | — |

**Dónde se escriben los resultados:** todos los jobs escriben en la misma Azure SQL (identidad administrada, sin cadena con contraseña) y la API **solo lee** los agregados. Para encolar: Azure Storage Queues (ya hay una Storage Account para las fotos), sin infraestructura nueva.

---

## 4. Contratos faltantes y cabos sueltos

### 4.1 Datos inviables o ambiguos con una sola petición

| ID | Pantalla | Problema | Recomendación |
|---|---|---|---|
| **C1** | e1 | Login con Google / Apple / Facebook y «Ver demo sin cuenta». La cuenta se crea solo en el teléfono, así que un login social en la web crearía cuentas huérfanas. | Para el piloto: quitar los botones sociales o hacer que solo **vinculen** cuentas existentes. La demo usa un usuario semilla de solo lectura. |
| **C2** | e6–e8, e42, e44 | El «Panel General (original)» es un **portal de investigador** (telemetría, latencia, uptime, 15.2 M puntos, «Buscar métrica o usuario ⌘K»), pero el resto de la web es para el **participante**. No hay roles en la API. | Decidir: (a) rediseñar Inicio para el participante con los widgets de e9/e13/e17, o (b) crear el rol `investigador` con endpoints `/api/v1/admin/*` y RBAC. Las métricas de infraestructura (KB/s, uptime, latencia) salen de App Insights, no de la API de negocio. |
| **C3** | e6, e7 | Clústeres «Night Scrollers / Compulsive Openers / Focused Students» con porcentajes: no hay modelo, datos ni job. | Quitar la tarjeta o especificar J8 (algoritmo, features, k, umbral de 3 días). |
| **C4** | e6, e20 | «Mapa de riesgo · Mamdani · 87.4 % confianza» por hora y «Regla #07 IF unlock_count…»: mezcla el modelo **logístico** (semanal) con un controlador **difuso de fricción** (en tiempo real) que no existe. Un sistema Mamdani no da «confianza». | Separar: (1) heatmap de uso por hora (J2, ya planeado), (2) riesgo semanal (logístico), (3) si se quiere fricción adaptativa, especificar sus reglas y decidir si corren en el teléfono. |
| **C5** | e6, e22, e24 | «Frecuencia de sesiones», «Límite de aperturas por día» e «Intentos» requieren **contar aperturas**, pero `evento_uso` solo guarda tiempos (inicio/fin/duración). | Agregar un campo `tipo` (`uso`/`apertura`) o la tabla `apertura_app`; para sitios, la tabla `intento_dominio`. Cambia el contrato con la app Android. |
| **C6** | e17, e6 | Heatmap de 1 h, pero `franja` es un catálogo **global** de 2 h por fecha (no por usuario ni por tz). | Dejar `franja` para la app Android, si la usa, y hacer la analítica con `uso_hora` (J2). Si nadie más la usa, deprecar `/franjas`. |
| **C7** | e9, e16 | Explicar un ajuste pasado requiere sus entradas, pero `ajuste_plan` solo guarda `adherencia` y no `pct_ignoradas` ni `uso_real`. | Migración: `ajuste_plan.pct_ignoradas`, `uso_real_min`, `sensibilidad`, `limite_resultante_min`. |
| **C8** | e13 | «Qué tan confiable es 85 % · acierta en 85 de cada 100» usa el **AUC-ROC (0.848)**, que no significa eso; la exactitud real es 0.77. «Alertas acertadas 7 de 10» ≈ precisión (0.72–0.77). Además el modelo se entrenó con datos **sintéticos**. | Mostrar «acierta en 77 de cada 100» (exactitud) y «cuando avisa, acierta 7 de cada 10» (precisión), con la nota «modelo entrenado con datos simulados» hasta J7. |
| **C9** | e21, e22, e23 | Tres límites distintos para una app: **aperturas/día** (e22: 8), **minutos/día** (e21: 30 min) y **por categoría** (e23: Redes 60 min). La API solo tiene `limite_aperturas`. | Definir la jerarquía (¿cuál gana?) antes de modelar. Propuesta: `app.limite_diario_min` + `app.limite_aperturas` + `limite_categoria`; aplica el más restrictivo. |
| **C10** | e31 | Los avisos «Descargando 12 eventos nuevos del dispositivo» y «Solo guardado en este navegador · niveles de fricción no se pueden cambiar desde aquí» contradicen al botón «Guardar y enviar al teléfono». | Fijar qué secciones son editables desde la web (`/configuracion/capacidades`) y eliminar el estado «solo en este navegador» (nada debería quedar solo en localStorage). |
| **C11** | e20, e41 | Modo Foco programado 08:00–14:00 (e20) vs. «Modo Foco programado 23:30» (e41) vs. «Recordatorio de Modo Foco 23:30» (e39) vs. `sesion_foco` en la API. Hay 3 conceptos distintos. | Separar: `modo_foco` programado (bloques recurrentes), `recordatorio_foco` (notificación) y `sesion_foco` (sesión ad hoc iniciada en el teléfono). Corregir el texto de e41. |
| **C12** | e9, e23, e43 | El límite diario sale en 4 lugares con valores distintos: «Límite actual 2 h 21» (e9), «Límite diario global 3 h 00» (e23), meta final «2 h 00» (e9) vs. «2 h 30» (e23), y «Reducción gradual · baja 10 % cada semana» (e23), que contradice al difuso (−10…+5 %). Además «Semana 5 de 8» (e9) vs. «Semana 3 de 8» (e43). | **Una sola fuente de verdad:** el límite global lo controla el plan (`limite_actual_min`, solo lectura en e23) y e23 edita solo categorías, días y excepciones. Quitar el «10 % cada semana» o reemplazarlo por «Ajuste automático según tu semana». |
| **C13** | e30 | «Cambios sin guardar» lista un diff que cruza 3 recursos (límites, app Instagram, fricción). Con los endpoints CRUD actuales el guardado no es atómico (pueden fallar 1 de 3). | Documento agregado `PUT /api/v1/configuracion` con versión (ver 1.6). |
| **C14** | e35 | «Lo que pasó antes de la caída sigue guardado», pero la API no persiste conversaciones. | Decidir entre el historial en el cliente (`sessionStorage`) o la tabla `conversacion` con retención. |
| **C15** | e29, e40 | Dos pantallas de privacidad con controles que se solapan («Compartir métricas…», «Participar en el estudio», retención 30/90 días vs. tabla fija de 12/6 meses). | Unificar en una sola pantalla o, por lo menos, en un solo recurso `/privacidad/preferencias`. Aclarar si la retención es elegible o fija. |
| **C16** | e43 | Nombre y **Apellidos** separados vs. `usuario.nombre` único; foto ≤2 MB JPG/PNG vs. API ≤5 MB JPG/PNG/WEBP; «Participante · usuario 1» muestra el id interno. | Migración `apellidos` (nullable) o dejar un solo campo «Nombre completo»; alinear los límites de la foto; mostrar el seudónimo. |
| **C17** | e39 | «Cuando me acerque a mi límite (80 %)» requiere el uso en tiempo casi real, y la ingesta es por lotes. | Lo dispara el teléfono; el backend solo guarda la preferencia y la sincroniza (J9). |
| **C18** | e29 | El opt-out «Incluir horarios de uso nocturno» deja sin la variable `pct_nocturno`, la de **mayor peso** en el modelo de riesgo (e13 «Es lo que más sube tu riesgo»). | Definir el comportamiento: imputar la media (contribución 0) y marcar la variable como «no compartida» en la respuesta de `/riesgo`. |

### 4.2 Botones sin flujo de persistencia claro

| Botón / acción | Pantalla | Qué falta |
|---|---|---|
| «Mantener la sesión iniciada» | e1 | No hay tokens (T1) |
| «Reenviar en 0:45» | e5 | Endpoint de recuperación + rate limit |
| «Exportar datos CSV/JSON» (panel) | e6 | J5 + `/exportaciones` |
| «Abrir guía» / «Ir a Ajustes» (estados vacíos) | e7 | Solo navegación; OK |
| «Guardar» en Editar plan (sensibilidad, relajar) | e10 | Columnas en `plan` + vigencia desde la próxima semana |
| «Revisa tu meta final · Puedes cambiarla antes del primer ajuste» | e11 | `plan.meta_final_min` + regla de negocio (solo editable antes de la semana 1) |
| Clic en una semana del gráfico | e16 | `/riesgo/semanas/{s}` |
| «Guardar y enviar al teléfono» / «Restablecer» / «Deshacer» | e20–e31 | Documento `configuracion` versionado + J9 + ack del teléfono |
| «Personalizar tiempos de espera» | e20 | `configuracion.friccion.niveles[]` |
| Toggle de app activa/inactiva | e21 | `app.activa` (hoy solo DELETE) |
| «Añadir nueva app restringida» → toggle «fricción progresiva» | e22 | `app.friccion_progresiva` |
| «+ Agregar excepción» (días de examen) | e23 | Tabla `limite_excepcion` |
| Pausar sitio «hasta mañana» / sugerencias «+» | e24 | `dominio.pausado_hasta`, `dominio.horario` |
| «Deshacer» tras borrar sitio | e28 | Soft delete + restaurar |
| «Ver documento» / «Retirar consentimiento» | e29 | `consentimiento` + PDF en Blob (SAS) |
| «Solicitar eliminación de mis datos» | e29 | `solicitud_eliminacion` + J6 |
| «Descartar / Seguir editando / Guardar y salir» | e30 | Lo resuelve el cliente + `PUT /configuracion` |
| Chips de sugerencias / detener respuesta | e33, e34 | `sugerencias[]` + SSE con cancelación |
| «Reintentar» Foqui | e35 | Código `llm_no_disponible` distinto del respaldo |
| Badge «Nuevo» en resumen | e36 | `resumen_semanal.leido` + `POST …/leido` |
| «Cerrar» en sesiones abiertas | e38 | Tabla `refresh_token` / `sesion` |
| Cambiar contraseña | e38 | Endpoint dedicado que pida la contraseña actual |
| Todos los toggles de avisos y horario silencioso | e39 | `preferencias_notificacion` + J4 |
| «Quitar» foto | e43 | `DELETE /usuarios/me/foto` |
| «Ayuda y soporte» | e42 | Sin definir |
| «Desactivar y cerrar sesión» | e44 | Ya hace soft delete; falta revocar tokens, desactivar FCM y anonimizar |
| «Cerrar sesión» | e45 | `POST /auth/logout` |

---

## 5. Migraciones de esquema derivadas (resumen)

| Tabla | Cambio |
|---|---|
| `usuario` | `+ apellidos, zona_horaria, idioma, inicio_semana, formato_hora, rol, programa, password_cambiado_en` |
| `plan` | `+ semanas_totales, meta_final_min, sensibilidad, permitir_relajar, config_pendiente JSON` |
| `ajuste_plan` | `+ pct_ignoradas, uso_real_min, sensibilidad, limite_resultante_min` |
| `app` | `+ activa, nivel_friccion, limite_diario_min, friccion_progresiva`; unique `(usuario_id, paquete)`; `categoria` → enum/catálogo |
| `dominio_bloqueado` | `+ horario_tipo, horario_inicio, horario_fin, pausado_hasta, eliminado_en`; unique `(usuario_id, dominio)` |
| `evento_uso` | `+ tipo` (`uso`/`apertura`) o la tabla nueva `apertura_app` |
| **nuevas** | `refresh_token`, `intento_login`, `token_recuperacion`, `dispositivo`, `heartbeat_dispositivo`, `configuracion` + `configuracion_version`, `limite_categoria`, `limite_dia`, `limite_excepcion`, `intento_dominio`, `uso_hora`, `uso_dia`, `riesgo_semanal`, `resumen_semanal`, `exportacion`, `preferencias_privacidad`, `consentimiento`, `auditoria_privacidad`, `solicitud_eliminacion`, `preferencias_notificacion`, (opc.) `conversacion`/`mensaje`, `cluster_usuario` |

## 6. Orden sugerido

1. **P0 — seguridad y base:** T1 (JWT + refresh + logout + sesiones), T5 (zona horaria) y T3 (errores con código).
2. **P1 — datos que pintan casi todas las pantallas:** J2 (`uso_hora`/`uso_dia`) + `/analitica/*` (e17, e23, e33) y J1 (cierre semanal) + `riesgo_semanal` + `/riesgo/historial` + `/planes/.../explicacion`.
3. **P1 — Foqui:** J3 + `/resumenes/semanales` y luego SSE.
4. **P2 — configuración:** documento `configuracion` versionado + J9 + `dispositivo`.
5. **P2 — privacidad, exportaciones y notificaciones:** J4, J5 y J6.
6. **Antes de construir**, resolver con diseño C2, C4, C9, C11 y C12 (cambian el modelo de datos).
