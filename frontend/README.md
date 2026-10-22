# ONEAD Assistant IA — Frontend React + TypeScript

Interface Enterprise (standards Microsoft Copilot Enterprise / Azure AI Foundry) :
header fixe, sidebar 290px, accueil premium, conversation 1080px centrée, saisie simple,
thèmes sombre/clair persistés, responsive desktop / tablette / mobile. Zéro emoji, SVG monochromes.

État actuel : hero sans sous-titre, conversations sans préfixes `●`/`○`,
animation d'écriture limitée à la réponse en cours (`streamingId`),
sources en lignes texte simples collées à la réponse + visionneuse PDF intégrée.

## Prérequis

- Node.js 20+
- Backend FastAPI lancé sur `http://127.0.0.1:8000` (voir `../api.py`)
  (`GET /api/health|manifest|documents|drh`, `POST /api/chat`, `POST /api/chat/stream`, `GET /files/docs/{nom}`)

## Démarrage

```bash
# 1 — Backend (racine du projet)
uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# 2 — Frontend (dans frontend/)
npm install
npm run dev
```

Ouvrir `http://localhost:5173`.

> Depuis la racine du projet, les scripts font le même travail en une commande :
> `.\demarrer.bat` (dev), `.\demo.bat` (build + un seul serveur sur `:8000`),
> `.\arreter.bat` (arrêt). Voir le `README.md` racine.

En dev, Vite (`vite.config.ts` : `host 127.0.0.1:5173`) proxifie `/api` et `/files`
vers `http://127.0.0.1:8000` (`changeOrigin: true`).
Si le proxy est inactif (build `dist/` servi ailleurs), définir `VITE_API_URL`
(ex. `VITE_API_URL=http://127.0.0.1:8000`) — `src/lib/api.ts:5` l'utilise comme `API_BASE`.

## Build production

```bash
npm run build   # tsc --noEmit + vite build -> dist/
npm run preview # prévisualisation du build (port 4173)
```

## Architecture

```
frontend/
  index.html
  vite.config.ts        # host 127.0.0.1:5173, proxy /api + /files -> 127.0.0.1:8000 (changeOrigin)
  package.json          # react 18.3.1, pdfjs-dist ^6.4.299, vite ^5.4.0, typescript ^5.4.5
  public/logo.svg       # Logo ONEAD vectoriel (transparent, sans cadre)
  src/
    main.tsx            # entrée React
    App.tsx             # état global : conversations, thème localStorage, streamChat + repli postChat, notice DRH
    index.css           # design system : app 1480px, layout 290px + main 1080px, hero 960px, card-grid 4→2→1
    types.ts            # Source, ChatMessage, Conversation, Manifest, DocItem, DrhContact, ChatDone
    lib/api.ts          # client REST + SSE (API_BASE = VITE_API_URL ou '', events token/done/error)
    components/
      Header.tsx        # OneadMark 36 + titre + avatar AD (allégé : sans notifications/paramètres)
      Sidebar.tsx       # nouvelle conversation, recherche historique, 8 récentes (titres seuls), pied base + thème, aide
      HomeHero.tsx      # OneadLogoStacked 128 + question + 4 cartes (recherche / procédure / documentation / référentiels)
      ChatThread.tsx    # fil : bulles, typing/caret limités au streamingId, sources en lignes, carte DRH, blob-PDF
      Composer.tsx      # textarea seule (Enter = envoyer), bouton envoi
      DocViewer.tsx     # modale pdfjs-dist : blob + #page=N, canvas DPR, pages/zoom, Échap/flèches, extrait cité
      OneadLogo.tsx     # goutte bleue + feuille verte 100 % vectoriel (OneadMark + OneadLogoStacked)
      icons.tsx         # SVG monochromes (aucun emoji)
```

Le backend expose : `GET /api/health` (non-bloquant, `rag_loaded` via cache + warmup `lifespan`),
`GET /api/manifest|documents|drh`, `POST /api/chat` (JSON `{answer, sources, refusal, meta}`),
`POST /api/chat/stream` (SSE : events `token` puis `done`, headers anti-buffer),
`GET /files/docs/{nom}` (PDF `inline` depuis `data/raw/`, lien `#page=N` préservé, ouverture blob sans téléchargement).
