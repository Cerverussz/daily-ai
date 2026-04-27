#!/usr/bin/env python3
"""Generate the daily AI news briefing via the Claude API.

Uses Claude Sonnet 4.6 with adaptive thinking and the server-side
web_search tool to research and write a curated HTML briefing for
the previous day. Output matches the format the user has approved
(Spanish, dark-theme HTML, 10-12 news items grouped by section).

Required env:
    ANTHROPIC_API_KEY   Anthropic API key

Optional env:
    BRIEFING_DATE       Target date as YYYY-MM-DD. Defaults to
                        yesterday (UTC).
"""

import os
import re
import signal
import sys
import time
from datetime import date, timedelta, timezone, datetime
from pathlib import Path

import anthropic
import httpx

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 10000
MAX_RETRIES = 3
RETRY_BASE_DELAY = 4
CALL_TIMEOUT_SECS = 240
RETRY_BASE_DELAY = 4

SYSTEM_PROMPT = """Eres un periodista tech senior que cura un briefing diario de IA en español.

Tu audiencia: founders técnicos y senior devs construyendo su propio producto — especialmente en Android, mobile, backend, marketplaces, y sports/health tech.

TU TRABAJO: buscar las noticias de IA más relevantes de una fecha específica, filtrar el ruido, y producir un briefing HTML curado.

EJES (peso aproximadamente igual):
1. Aplicaciones profesionales de IA que resuelven problemas reales — herramientas, frameworks, servicios que devs o empresas están usando en PRODUCCIÓN. Prioridad: desarrollo de software (Android, mobile, backend), automatización de workflows, marketplaces y plataformas.
2. Innovaciones técnicas con potencial práctico a corto plazo — nuevos modelos, técnicas (on-device AI, agentes, RAG, fine-tuning accesible), AI coding assistants (Claude Code, Cursor, Copilot, Gemini en Android Studio). Incluye AI + mobile/edge.
3. Creación de negocios y productos — historias reales de founders o equipos pequeños lanzando productos, startups o MVPs con IA. Herramientas o workflows que reducen drásticamente el tiempo o costo de lanzar tech. Modelos de negocio emergentes. Prioriza historias con lecciones aplicables.
4. Novedades de Claude y el ecosistema Anthropic — nuevas funcionalidades, modelos, API, herramientas, integraciones MCP, cambios en planes o pricing.
5. IA aplicada a sports tech, salud y bienestar — plataformas deportivas, coaching, nutrición, marketplaces de servicios profesionales.

FILTROS ESTRICTOS (excluye):
- Papers sin aplicación práctica
- Hype sin sustancia
- Noticias tipo "empresa X recaudó $Y" a menos que haya un producto concreto para discutir

RESTRICCIONES:
- Máximo 10-12 noticias
- Marca con 🔥 las noticias especialmente relevantes para Android, marketplaces, o founders técnicos
- Todo el contenido en español

PROCESO:
- Usa la herramienta web_search para encontrar noticias de la fecha indicada. Haz múltiples búsquedas cubriendo los 5 ejes.
- Verifica las fuentes — prioriza anuncios oficiales, blogs de las empresas, y medios tech reconocidos.
- No inventes URLs. Si no tienes una fuente, no incluyas la noticia.

POR CADA NOTICIA (en HTML):
- Titular (1 línea, puede incluir 🔥 al inicio)
- Qué es (2 oraciones)
- Por qué importa (1 oración, desde la perspectiva de un senior dev construyendo su propio producto)
- Link a la fuente

FORMATO DE SALIDA:

Devuelve EXACTAMENTE un documento HTML completo, siguiendo esta estructura (reproduce todo el CSS tal cual — es la plantilla visual aprobada):

```
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Noticias IA — [DD de MES YYYY]</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #e6edf3; line-height: 1.6; padding: 2rem 1rem; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { font-size: 1.5rem; color: #58a6ff; margin-bottom: 0.25rem; }
        .date { color: #8b949e; font-size: 0.9rem; margin-bottom: 2rem; }
        .news-item { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
        .news-item h2 { font-size: 1.05rem; color: #f0f6fc; margin-bottom: 0.5rem; }
        .news-item .tag { display: inline-block; font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; margin-right: 0.4rem; margin-bottom: 0.5rem; font-weight: 600; }
        .tag-tools { background: #1f3a5f; color: #58a6ff; }
        .tag-coding { background: #2a1f3f; color: #bc8cff; }
        .tag-mobile { background: #1f3f2a; color: #56d364; }
        .tag-startup { background: #3f2a1f; color: #f0883e; }
        .tag-anthropic { background: #3f1f2a; color: #f778ba; }
        .tag-health { background: #1f3f3f; color: #39d2c0; }
        .what { color: #c9d1d9; font-size: 0.9rem; margin-bottom: 0.4rem; }
        .why { color: #8b949e; font-size: 0.85rem; font-style: italic; margin-bottom: 0.4rem; }
        .source a { color: #58a6ff; font-size: 0.8rem; text-decoration: none; }
        .source a:hover { text-decoration: underline; }
        .section-title { color: #8b949e; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin: 1.5rem 0 0.75rem; }
        .fire { font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Noticias IA — Daily Briefing</h1>
        <p class="date">[DD de MES de YYYY] · Curado para senior devs construyendo producto</p>

        <p class="section-title">[Nombre de sección]</p>

        <div class="news-item">
            <h2><span class="fire">🔥</span> [Titular]</h2>
            <span class="tag tag-tools">[CATEGORÍA]</span>
            <p class="what">[Qué es — 2 oraciones]</p>
            <p class="why">[Por qué importa — 1 oración, perspectiva senior dev]</p>
            <p class="source"><a href="[URL real]">[Nombre de la fuente]</a></p>
        </div>

        <!-- más .news-item... -->

        <p style="color: #484f58; font-size: 0.75rem; margin-top: 2rem; text-align: center;">
            Generado automáticamente · Fuentes verificadas al [DD/MM/YYYY] · Filtrado para senior devs construyendo producto
        </p>
    </div>
</body>
</html>
```

Secciones sugeridas (usa las que apliquen según las noticias del día):
- "Herramientas y aplicaciones en producción"
- "Innovaciones técnicas con impacto práctico"
- "AI Coding y productividad para devs"
- "Novedades de Claude y Anthropic"
- "IA en sports tech, salud y bienestar"

Tags disponibles para las categorías: tag-tools, tag-coding, tag-mobile, tag-startup, tag-anthropic, tag-health.

REGLA CRÍTICA DEL OUTPUT:
Responde ÚNICAMENTE con el HTML completo, empezando con `<!DOCTYPE html>` y terminando con `</html>`. Sin preámbulo, sin explicaciones, sin backticks de markdown, sin texto después del HTML."""


USER_PROMPT_TEMPLATE = """Genera el briefing de IA para las noticias del {pretty_date} ({iso_date}).

Busca exhaustivamente noticias publicadas en esa fecha específica (o en las últimas 24 horas antes de esa fecha). Cubre los 5 ejes. Produce entre 10 y 12 noticias. Devuelve solo el HTML."""


def _pretty_date_es(iso_date: str) -> str:
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return f"{d.day} de {meses[d.month - 1]} de {d.year}"


def yesterday_iso() -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()


def extract_html(text: str) -> str:
    match = re.search(
        r"<!DOCTYPE html>.*?</html>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        preview = text[:800] if text else "(empty response)"
        raise ValueError(
            "No <!DOCTYPE html>…</html> document found in the response.\n"
            f"Response preview:\n{preview}"
        )
    return match.group(0)


class _CallTimeout(Exception):
    pass


def _alarm_handler(_signum, _frame):
    raise _CallTimeout("API call exceeded wall-clock timeout")


def generate_briefing(target_date: str) -> str:
    client = anthropic.Anthropic(
        timeout=httpx.Timeout(CALL_TIMEOUT_SECS, connect=15.0),
    )
    user_prompt = USER_PROMPT_TEMPLATE.format(
        pretty_date=_pretty_date_es(target_date),
        iso_date=target_date,
    )

    api_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": user_prompt}],
    )

    prev_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    try:
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"Calling {MODEL} for briefing {target_date} (attempt {attempt}/{MAX_RETRIES})…", flush=True)
            signal.alarm(CALL_TIMEOUT_SECS)
            try:
                final = client.messages.create(**api_kwargs)
                signal.alarm(0)
                break
            except (
                _CallTimeout,
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ReadTimeout,
                httpx.ConnectError,
                anthropic.APIConnectionError,
                anthropic.APITimeoutError,
            ) as exc:
                signal.alarm(0)
                if attempt == MAX_RETRIES:
                    raise
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"Attempt {attempt} failed ({type(exc).__name__}), retrying in {delay}s…", flush=True)
                time.sleep(delay)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prev_handler)

    print(
        "Usage: "
        f"input={final.usage.input_tokens} "
        f"output={final.usage.output_tokens} "
        f"cache_read={getattr(final.usage, 'cache_read_input_tokens', 0)}",
        flush=True,
    )

    full_text = "".join(
        block.text for block in final.content if block.type == "text"
    )
    return extract_html(full_text)


def main() -> int:
    target = os.environ.get("BRIEFING_DATE") or yesterday_iso()
    try:
        datetime.strptime(target, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid BRIEFING_DATE: {target!r} (expected YYYY-MM-DD)", file=sys.stderr)
        return 2

    html = generate_briefing(target)
    out = Path(__file__).resolve().parent.parent / f"noticias-ia-{target}.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(html)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
