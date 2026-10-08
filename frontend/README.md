# ONEAD Assistant IA — Frontend React + TypeScript

Interface Enterprise (standards Microsoft Copilot Enterprise / Azure AI Foundry) :
Header fixe, sidebar 280px, accueil premium, conversation 900px, saisie style Copilot,
thèmes sombre/clair, responsive desktop / tablette / mobile. Zéro emoji, SVG monochromes.

## Prérequis

- Node.js 20+
- Backend FastAPI lancé sur `http://127.0.0.1:8000` (voir `../api.py`)

## Démarrage

```bash
# 1 — Backend (racine du projet)
uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# 2 — Frontend (dans frontend/)
npm install
npm run dev
```

Ouvrir `http://localhost:5173`.

En dev, Vite proxifie `/api` et `/files` vers le backend (voir `vite.config.ts`).

## Build production

```bash
npm run build   # tsc --noEmit + vite build -> dist/
npm run preview # prévisualisation du build
```

## Architecture

```
frontend/
  index.html
  vite.config.ts        # proxy /api + /files -> 127.0.0.1:8000
  src/
    main.tsx            # entrée React
    App.tsx             # état global : conversations, thème, streaming
    index.css           # design system (variables sombre/clair, responsive)
    types.ts            # Message, Source, Conversation, Manifest, DRH
    lib/api.ts          # client REST + SSE (/api/chat/stream)
    components/
      Header.tsx        # logo, titre, notifications, paramètres, avatar
      Sidebar.tsx       # 280px : nouvelle conversation, recherche, docs, base, aide
      HomeHero.tsx      # hero + 4 cartes professionnelles
      ChatThread.tsx    # fil 900px : bulles, sources, carte DRH, typing
      Composer.tsx      # saisie 60px / 16px : joindre, recherche, micro, envoyer
      icons.tsx         # SVG monochromes (aucun emoji)
```

Le backend expose : `GET /api/health|manifest|documents|drh`,
`POST /api/chat`, `POST /api/chat/stream` (SSE : events `token` puis `done`),
`GET /files/docs/{nom}` (PDF, lien `#page=N` préservé).
