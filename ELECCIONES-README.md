# Resultados Segunda Vuelta — Elecciones Colombia 2026

Página web de seguimiento de resultados de la **segunda vuelta presidencial de Colombia 2026**.
Se actualiza **automáticamente cada 5 segundos** leyendo el archivo `resultados.json`.

## ¿Cómo funciona?

- `index.html` — la página. Cada 5 s hace `fetch('resultados.json')` (sin caché) y vuelve a
  dibujar porcentajes, barras, mesas escrutadas y votos en blanco/nulos.
- `resultados.json` — la fuente de datos. **Edita este archivo** con las cifras oficiales y la
  página reflejará el cambio en la siguiente actualización (máx. 5 s).
- `.github/workflows/deploy-pages.yml` — publica el sitio en **GitHub Pages** en cada `push`.

## Publicar en GitHub Pages

1. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Haz `push` (o lanza el workflow `Deploy GitHub Pages` manualmente).
3. La URL aparecerá en la pestaña **Actions** y en **Settings → Pages**, normalmente:
   `https://<usuario>.github.io/daily-ai/`

## Actualizar los resultados

Edita `resultados.json`:

```json
{
  "actualizado": "2026-06-21T20:30:00-05:00",
  "mesas_informadas": 50000,
  "mesas_totales": 110000,
  "porcentaje_escrutado": 45.45,
  "candidatos": [
    { "nombre": "...", "partido": "...", "color": "#1d4ed8", "votos": 1234567 },
    { "nombre": "...", "partido": "...", "color": "#dc2626", "votos": 1198765 }
  ],
  "votos_blanco": 50000,
  "votos_nulos": 12000,
  "votos_no_marcados": 8000
}
```

> ⚠️ **Importante:** los datos incluidos son de demostración (en cero). Reemplázalos con las
> cifras oficiales de la [Registraduría Nacional del Estado Civil](https://www.registraduria.gov.co).
> Esta página es una herramienta de visualización, **no** una fuente oficial.

## Automatizar la actualización (opcional)

Para no editar a mano puedes crear un proceso que escriba `resultados.json` con datos del
boletín oficial (por ejemplo, un GitHub Action programado con `cron` que descargue y transforme
el boletín de la Registraduría) y haga `commit`/`push`. La página se actualizará sola.
