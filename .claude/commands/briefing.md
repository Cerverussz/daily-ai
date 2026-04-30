---
description: Genera el briefing diario de IA, lo sube a GitHub y dispara el envío por Telegram (sin usar la API de Anthropic)
---

# /briefing — Daily AI briefing

Tu trabajo en este comando: producir el briefing del día (o de la fecha que pase el usuario), commitearlo y empujarlo a GitHub. El workflow `telegram-notify.yml` se encargará de enviarlo por Telegram al detectar el push.

**Argumento opcional:** $ARGUMENTS — fecha objetivo en formato `YYYY-MM-DD`. Si está vacío, usa la fecha de ayer (UTC).

## Audiencia y criterios editoriales

Audiencia: founders técnicos y senior devs construyendo su propio producto — Android, mobile, backend, marketplaces, sports/health tech.

Cubre estos 5 ejes con peso similar:
1. **Aplicaciones profesionales de IA en producción** — herramientas/frameworks/servicios que devs o empresas están usando hoy. Prioriza desarrollo de software (Android, mobile, backend), automatización, marketplaces.
2. **Innovaciones técnicas con potencial práctico a corto plazo** — nuevos modelos, on-device AI, agentes, RAG, fine-tuning accesible, AI coding assistants (Claude Code, Cursor, Copilot, Gemini en Android Studio).
3. **Creación de negocios y productos** — founders / equipos pequeños lanzando productos con IA, herramientas que reducen tiempo o costo de lanzar tech, modelos de negocio emergentes con lecciones aplicables.
4. **Novedades de Claude y el ecosistema Anthropic** — funcionalidades, modelos, API, MCP, pricing.
5. **IA aplicada a sports tech, salud y bienestar** — plataformas deportivas, coaching, nutrición, marketplaces de servicios profesionales.

**Filtros estrictos (excluye):**
- Papers sin aplicación práctica.
- Hype sin sustancia.
- "Empresa X recaudó $Y" salvo que haya un producto concreto que comentar.

**Restricciones:**
- 10 a 12 noticias.
- Marca con 🔥 las especialmente relevantes para Android, marketplaces o founders técnicos (en HTML usa `class="news-item hot"`).
- Todo el contenido en español.
- No inventes URLs. Si no hay fuente verificable, no incluyas la noticia.

## Proceso

1. **Calcular fecha objetivo.** Si `$ARGUMENTS` está vacío, ejecuta `date -u -v-1d +%F` (macOS) para obtener ayer en UTC. Valida formato `YYYY-MM-DD`.
2. **Investigar.** Usa WebSearch (varias búsquedas, una por eje) para encontrar noticias publicadas en esa fecha o en las 24h previas. Verifica fuentes — anuncios oficiales, blogs de empresas, medios tech reconocidos. Para cada candidata, anota: titular, qué es (2 oraciones), por qué importa (1 oración desde la perspectiva senior dev), URL real, sección sugerida.
3. **Escribir el HTML.** Sigue exactamente la plantilla visual aprobada (mira el archivo `noticias-ia-*.html` más reciente del repo como referencia exacta de estilos y estructura). Estructura mínima:
   - `<header>` con `<h1>Daily AI Briefing</h1>` y un `<p>` con la fecha en español ("DD de mes de YYYY") y el subtítulo "Noticias filtradas para senior devs que construyen producto".
   - Secciones con `<div class="section-title">…</div>` agrupando los 5 ejes (usa solo las que apliquen).
   - Cada noticia en `<div class="news-item">` (o `news-item hot` para 🔥) con `<h3>`, `<p class="what">`, `<p class="why">`, `<p class="source">` con `<a href="…">…</a>` (puedes encadenar varias fuentes con ` &bull; `).
   - `<footer>` al final con un comentario tipo "Generado el DD/MM/YYYY · Filtrado para senior devs construyendo producto".
4. **Guardar el archivo** en la raíz del repo como `noticias-ia-YYYY-MM-DD.html`.
5. **Commitear y pushear** a una rama `claude/daily-YYYY-MM-DD`:
   ```bash
   DATE=<fecha>
   BRANCH="claude/daily-$DATE"
   FILE="noticias-ia-$DATE.html"
   git checkout -B "$BRANCH"
   git add "$FILE"
   git commit -m "Add daily AI briefing for $DATE"
   git push -u --force-with-lease origin "$BRANCH"
   ```
   Confirma con el usuario antes del primer push si la rama no existe en remoto.
6. **Reportar al usuario** la URL de la rama y avisar que `telegram-notify.yml` se disparará automáticamente. No ejecutes `send_to_telegram.py` localmente — el workflow lo hace.

## Notas

- No uses la API de Anthropic. Toda la generación la haces tú con WebSearch + escritura directa.
- No agregues comentarios al HTML más allá de los marcadores `<!-- EJE N: … -->` que ya usa la plantilla.
- Si el archivo del día ya existe, pregunta al usuario si quiere sobrescribirlo antes de regenerarlo.
