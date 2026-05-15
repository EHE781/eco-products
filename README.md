# EcoScan

Aplicación web de productos ecológicos y alimentarios.  
Muestra puntuaciones de Nutriscore, Ecoscore y huella de carbono de cada producto, con filtros por categoría, ordenación y un asistente IA integrado.

---

## Estructura del proyecto

```
eco-products/
├── backend/                  # API Python (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # Punto de entrada FastAPI + montaje frontend
│   │   ├── config.py         # Ajustes (pydantic-settings, lee .env)
│   │   ├── database.py       # Motor SQLAlchemy, sesión, init_db(), haversine_km()
│   │   ├── models.py         # Modelos ORM (Product, ProductCert, ProductBenefit, Interaction)
│   │   ├── schemas.py        # Schemas Pydantic (ProductOut, InteractionIn)
│   │   ├── routers/
│   │   │   ├── products.py       # GET /api/products
│   │   │   ├── interactions.py   # POST /api/interactions
│   │   │   ├── recommendations.py# GET /api/recommendations
│   │   │   └── off.py            # GET /api/off/search  GET /api/off/product/{barcode}
│   │   └── services/
│   │       ├── openfoodfacts.py  # Cliente async Open Food Facts
│   │       └── recommender.py    # Recomendador basado en interacciones (scikit-learn)
│   ├── seed.py               # Carga inicial del catálogo en PostgreSQL
│   ├── requirements.txt
│   └── .env.example          # Variables de entorno requeridas
└── frontend/                 # SPA estática (Vanilla JS, sin build)
    ├── index.html
    ├── css/
    │   └── styles.css
    └── js/
        ├── i18n.js           # Traducciones ES/CA/EN + t(), changeLang()
        ├── data.js           # Catálogo P[], helpers pname(), pdesc(), pbens()
        ├── geo.js            # Geolocalización, haversine(), recomputeKm()
        ├── render.js         # render(), list(), updateHeroStats()
        ├── api.js            # logInteraction(), fetchProducts()
        ├── chat.js           # Chat Gemini AI, fallback por palabras clave
        └── app.js            # Estado global, eventos DOM, DOMContentLoaded
```

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+, FastAPI 0.115, Uvicorn |
| ORM / BD | SQLAlchemy 2.0, PostgreSQL 15+ |
| Validación | Pydantic 2, pydantic-settings |
| HTTP cliente | httpx (async) |
| ML | scikit-learn, pandas, numpy |
| BD externa | Open Food Facts API (REST, sin auth) |
| IA chat | Gemini 2.0 Flash (`generativelanguage.googleapis.com`) |
| Frontend | HTML/CSS/JS vanilla, Google Fonts (Inter) |
| Despliegue | FastAPI sirve el frontend como ficheros estáticos |

---

## Puesta en marcha

> **Estado actual de la BD**: la instancia PostgreSQL compartida aún no está disponible.  
> Mientras tanto tienes dos opciones:
> - **Opción A — sin backend**: abre `frontend/index.html` directamente en el navegador. El catálogo funciona con los datos hardcodeados en `data.js` y el chat IA llama a Gemini directamente.
> - **Opción B — con backend completo**: pide a Emanuel las credenciales de la BD (`DATABASE_URL`) antes de continuar, o espera a que se comparta la instancia.

---

### Opción A — Solo frontend (sin BD, sin servidor)

No requiere Python ni PostgreSQL.

1. Clona el repositorio
2. Abre `frontend/index.html` en el navegador (doble clic o con Live Server en VS Code)
3. Para que el chat IA funcione, edita `frontend/js/chat.js` y sustituye `GEMINI_KEY` por tu clave de [Google AI Studio](https://aistudio.google.com)

---

### Opción B — Stack completo (FastAPI + PostgreSQL)

**Requisitos previos**
- Python 3.11+
- PostgreSQL 15+ accesible
- Credenciales de BD (pídelas a Emanuel si usáis la instancia compartida)
- Clave de API de Gemini ([Google AI Studio](https://aistudio.google.com))

**1. Configurar variables de entorno**

```bash
cd backend
cp .env.example .env
# Rellena .env con los valores que te facilite Emanuel:
#   DATABASE_URL=postgresql://usuario:contraseña@host:5432/ecoscan
#   GEMINI_KEY=tu_clave_gemini
```

**2. Crear la base de datos** *(solo si usas tu propio PostgreSQL local)*

```sql
-- En psql:
CREATE DATABASE ecoscan;
```

**3. Instalar dependencias e inicializar**

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Crear tablas y cargar catálogo inicial:
python seed.py
```

**4. Arrancar el servidor**

```powershell
# Windows — desde backend/
$env:PYTHONPATH = "$PWD"
uvicorn app.main:app --reload
```

```bash
# Linux/macOS — desde backend/
PYTHONPATH=. uvicorn app.main:app --reload
```

> Si no se establece `PYTHONPATH`, uvicorn no encontrará el paquete `app` y fallará con `ModuleNotFoundError`.

La app queda disponible en `http://localhost:8000`.  
La API se documenta automáticamente en `http://localhost:8000/docs`.  
**Sin BD configurada**: el servidor arranca igualmente y sirve el frontend; los endpoints `/api/*` devuelven error hasta tener `DATABASE_URL` válida.

---

## Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/products` | Lista productos alimentarios ordenados por distancia |
| `GET` | `/api/recommendations` | Productos recomendados para la sesión actual |
| `POST` | `/api/interactions` | Registra una interacción de usuario (vista, chat…) |
| `GET` | `/api/off/search?q=...` | Búsqueda en Open Food Facts |
| `GET` | `/api/off/product/{barcode}` | Ficha de producto de Open Food Facts |
| `GET` | `/health` | Comprobación de salud del servicio |

### Parámetros comunes en `/api/products`

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `lang` | `es\|ca\|en` | `es` | Idioma de nombre, descripción y certificaciones |
| `user_lat` | float | `41.3851` | Latitud del usuario (Barcelona por defecto) |
| `user_lon` | float | `2.1734` | Longitud del usuario |

---

## Categorías de productos

Solo se incluyen categorías alimentarias:

- **Alimentación** — frutas, verduras, aceites, miel, chocolate, pasta
- **Lácteos** — yogures, leche, quesos
- **Panadería** — panes, granola, bollería
- **Bebidas** — bebidas vegetales, tés, infusiones

> Cosmética y limpieza se excluyen: la variedad de datos (ingredientes INCI, categorías COSMOS) requeriría un modelo de datos diferente.

---

## Base de datos externa: Open Food Facts

Se utiliza [Open Food Facts](https://world.openfoodfacts.org) como fuente de datos externa para:

- Búsqueda de productos por nombre o código de barras
- Obtención de puntuaciones Nutriscore y Ecoscore oficiales
- Enriquecer el catálogo con datos reales actualizados

La integración está en `backend/app/services/openfoodfacts.py` y se expone a través de `/api/off/*`. No requiere autenticación.

---

## Internacionalización (i18n)

El frontend soporta tres idiomas: **español (ES)**, **catalán (CA)** e **inglés (EN)**.  
Las traducciones están en `frontend/js/i18n.js`. El idioma activo se guarda en `localStorage`.

El backend acepta el parámetro `lang` en los endpoints que devuelven texto (nombres, descripciones, certificaciones, beneficios).

---

## Sistema de puntuaciones

Cada producto muestra tres indicadores:

- **Nutriscore A–E**: calidad nutricional (A = mejor)
- **Ecoscore A–E**: impacto ambiental (A = mejor)
- **Distancia**: calculada con la fórmula de Haversine desde la posición del usuario; representada con una barra logarítmica verde→rojo

El **banner de valoración** (Excelente / Buena opción / Aceptable / Considera alternativas) se calcula combinando Nutriscore, Ecoscore y penalización por distancia.

---

## Recomendador

`backend/app/services/recommender.py` implementa un recomendador sencillo basado en interacciones:

1. Vectoriza cada producto: `[km, nutriscore, ecoscore, precio, co2]`
2. Entrena un modelo de vecinos más cercanos (KNN) con las interacciones de la sesión
3. Devuelve los `n` productos más relevantes, con fallback a ordenación por distancia+puntuación si no hay datos suficientes

---

## Despliegue en producción

```powershell
# Windows — desde backend/
$env:PYTHONPATH = "$PWD"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
# Linux/macOS — desde backend/
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI sirve el frontend desde `frontend/` como ficheros estáticos (`/`).  
Para Netlify (solo frontend estático, sin backend):

```bash
npx netlify-cli deploy --dir=frontend --prod
```

> En ese caso, el chat IA usa Gemini directamente desde el navegador. Sustituye `GEMINI_KEY` en `frontend/js/chat.js` o mejor: añade un endpoint `/api/chat` en el backend para no exponer la clave.

---

## Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Cadena de conexión PostgreSQL | `postgresql://user:pass@localhost:5432/ecoscan` |
| `GEMINI_KEY` | Clave API de Google Gemini | `AIzaSy...` |
| `OPENFOODFACTS_BASE_URL` | Base URL de Open Food Facts | `https://world.openfoodfacts.org` |

---

## Desarrollo

### Añadir un producto nuevo

1. Añade la entrada al array `PRODUCTS` en `backend/seed.py` (solo categorías alimentarias)
2. Ejecuta `python seed.py` para repoblar la BD
3. Añade la misma entrada al array `P` en `frontend/js/data.js` para el modo estático

### Añadir un idioma

1. Añade el bloque de traducciones en `frontend/js/i18n.js`
2. Añade el botón `.lang-btn` en `frontend/index.html`
3. Añade las columnas `name_XX` / `desc_XX` en el modelo ORM y en los datos de seed

### Ejecutar con recarga automática (desarrollo)

```powershell
# Windows
cd backend; $env:PYTHONPATH = "$PWD"; uvicorn app.main:app --reload
```

```bash
# Linux/macOS
cd backend && PYTHONPATH=. uvicorn app.main:app --reload
```
