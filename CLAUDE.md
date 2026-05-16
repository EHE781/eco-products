# EcoScan — Ecological Products Web App

## Branches
- `master` — versión original: SPA estática, datos hardcodeados, Gemini en frontend
- `off-integration` — versión actual activa: FastAPI backend + Open Food Facts + Gemini en backend

---

## Stack (off-integration)

**Backend**
- FastAPI + Uvicorn
- SQLAlchemy con SQLite por defecto (PostgreSQL opcional via `DATABASE_URL`)
- httpx AsyncClient para llamadas externas no bloqueantes
- Gemini `gemini-3.1-flash-lite` via `generativelanguage.googleapis.com`
- Open Food Facts API v2 (`world.openfoodfacts.org/api/v2/search`)

**Frontend**
- Vanilla HTML/CSS/JS, sin frameworks ni paso de build
- Google Fonts (Inter)
- Servido como ficheros estáticos por FastAPI (`/` montado tras las rutas de API)

---

## Arrancar en local

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

Crear `backend/.env` (ver `.env.example`):
```
GEMINI_KEY=tu_clave_aqui
# DATABASE_URL=postgresql://user:pass@localhost:5432/ecoscan  # opcional
```

---

## Estructura

```
backend/
  app/
    main.py              # FastAPI app, lifespan, monta frontend como static
    config.py            # Settings (pydantic-settings, lee .env)
    database.py          # SQLAlchemy engine + init_db()
    models.py            # ORM models (Interaction, etc.)
    schemas.py           # Pydantic schemas (ProductOut, ChatPayload…)
    routers/
      off.py             # GET /api/off/search  → proxy a Open Food Facts
      chat.py            # POST /api/chat       → Gemini AI
      products.py        # GET /api/products    → catálogo (usa OFF)
      recommendations.py # GET /api/recommendations
      interactions.py    # POST /api/interactions (log clicks/chat)
    services/
      openfoodfacts.py   # search_food(): llama OFF, mapea producto, retry 503
      llm.py             # generate_chat_reply(): llama Gemini async
      recommender.py     # _feature_vector(), score colaborativo simple
frontend/
  index.html
  css/styles.css
  js/
    i18n.js    # traducciones ES/CA/EN, t(), changeLang(), applyLang()
    data.js    # P_ALL, loadProducts(), prefetchNext(), _fetchBatch()
    geo.js     # haversine, recomputeKm(), initGeolocation()
    render.js  # render(), list(), renderPagination(), updateHeroStats()
    api.js     # logInteraction()
    chat.js    # toggleChat(), send(), callBackendChat(), _md()
    app.js     # setCat(), goToPage(), cardClick(), DOMContentLoaded
```

---

## Flujo de datos

1. `DOMContentLoaded` → `loadProducts("bio ecologico")` → `GET /api/off/search?q=...&page=1&page_size=50`
2. Backend llama OFF con `countries_tags=en:spain`, retry hasta 3 veces en 503
3. Frontend acumula en `P_ALL`, muestra 15 por página (`PAGE_SIZE=15`)
4. Al llegar a la última página cargada → `prefetchNext()` llama al siguiente batch silenciosamente
5. Geolocalización opcional (modal): recomputa `_km` en todos los productos de `P_ALL`

---

## Paginación / prefetch

| Constante | Valor | Descripción |
|-----------|-------|-------------|
| `FETCH_SIZE` | 50 | productos por llamada a la API |
| `PAGE_SIZE` | 15 | productos visibles por página |
| `MAX_BATCHES` | 8 | tope de 400 productos por sesión |

- `P_ALL` acumula todos los batches; `apiBatch` lleva la cuenta del último batch cargado
- `goToPage(page)` no llama a la API; solo actualiza `currentPage` + dispara `prefetchNext()` si está en la última página
- Al cambiar búsqueda/categoría, `P_ALL` se mantiene visible (grid atenuado) hasta que llegan los nuevos resultados
- La última página rellena los huecos con skeletons si hay más productos pendientes

---

## AI / Chat

- Ruta: `POST /api/chat` con `{ message, lang, context, user_lat, user_lon }`
- El backend usa el mensaje del usuario como query a OFF para dar contexto al modelo
- System prompt incluye los productos relevantes encontrados + ubicación del usuario
- Fallback local en `chat.js` si el backend falla
- El chat renderiza markdown (negrita, cursiva, listas) via `_md()` en `chat.js`

---

## Open Food Facts — notas

- Usar `world.openfoodfacts.org` (no `es.openfoodfacts.org` — rate limit agresivo)
- Filtrar por `countries_tags=en:spain` en los params
- No usar `sort_by=ecoscore_score` — limita mucho los resultados (solo productos con ecoscore)
- Retry automático (3 intentos, backoff 1s/2s/3s) ante respuestas 503

---

## Categorías

| Cat | Query OFF |
|-----|-----------|
| all | `bio ecologico` |
| Alimentación | `alimentos bio ecologicos` |
| Lácteos | `lacteos bio ecologicos` |
| Panadería | `pan espelta bio ecologico` |
| Bebidas | `bebidas bio ecologicas` |

---

## Internacionalización

Tres idiomas: ES (default), CA, EN. Cambiar con los botones del header.  
Las claves se definen en `i18n.js`; los elementos HTML usan `data-i18n="clave"`.
