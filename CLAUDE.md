# EcoScan — Ecological Products Web App

## What this is
Single-page static HTML app (`index.html`) — no build step, no dependencies, no database. Everything is in one file: CSS, JS, product data.

Hosted on Netlify (anonymous drop, needs reclaiming every session or sign in to persist).

## Stack
- Vanilla HTML/CSS/JS, no frameworks
- Google Fonts (Inter)
- **Gemini 2.0 Flash** via `generativelanguage.googleapis.com` for the AI chat advisor
- No backend — all data is hardcoded in the JS `const P = [...]` array

## AI integration
- Key: hardcoded as `const GEMINI_KEY` in the `<script>` block
- Model: `gemini-2.0-flash`
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=KEY`
- Full product catalog is injected as `systemInstruction` on every call
- Fallback: keyword-based smart responses if API fails

## Product data
14 invented products in `const P`, each with:
`id, name, cat, origin, km (distance from Barcelona), price, unit, ns (Nutriscore A-E), es (Ecoscore A-E), certs, emoji, season, co2 (kg saved, negative = added), desc, bens`

Categories: Alimentación, Lácteos, Panadería, Bebidas, Cosmética, Limpieza

## Key UI features
- Nutriscore A–E scale (colored bar, active letter highlighted)
- Ecoscore A–E scale (same visual)
- Distance bar (log-scale, green→red, label: Muy cercano / Cercano / etc.)
- CO₂ badge (green if positive saving, red if negative)
- Overall rating banner per card (Excelente / Buena / Aceptable / Considera alternativas) — computed from nutriscore + ecoscore + distance
- Filter chips by category + sort dropdown (proximity / nutriscore / ecoscore / price)
- Search bar (filters name, category, origin, description)
- Floating "Asistente IA" FAB → opens chat panel
- Clicking a product card opens the chat with that product's details

## Deployment
```
cd C:\Users\emanu\Claude\workspace\eco-products
npx netlify-cli deploy --dir=. --prod --allow-anonymous
```
Claim the URL at `https://app.netlify.com/drop/<site-id>` within 60 min, or log in to Netlify first for a permanent URL.

## Last known live URL
`http://sparkly-moonbeam-9caf09.netlify.app` (may have expired — redeploy if needed)
