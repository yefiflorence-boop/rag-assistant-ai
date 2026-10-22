import type { ChatDone, DocItem, DrhContact, Manifest } from '../types';

// En dev Vite, '/api' est proxifié vers le backend (vite.config.ts).
// VITE_API_URL permet de forcer l'URL absolue du backend si le proxy est inactif.
const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '';

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status} : ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function fetchManifest(): Promise<Manifest> {
  return fetch(`${API_BASE}/api/manifest`).then(json<Manifest>);
}

export function fetchDocuments(): Promise<{ documents: DocItem[]; total: number }> {
  return fetch(`${API_BASE}/api/documents`).then(json<{ documents: DocItem[]; total: number }>);
}

export function fetchDrh(): Promise<DrhContact> {
  return fetch(`${API_BASE}/api/drh`).then(json<DrhContact>);
}

export function fetchHealth(): Promise<{ status: string; rag_loaded: boolean }> {
  return fetch(`${API_BASE}/api/health`).then(json<{ status: string; rag_loaded: boolean }>);
}

/** POST /api/chat non-streamé (secours si SSE indisponible). */
export function postChat(question: string): Promise<ChatDone> {
  return fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  }).then(json<ChatDone>);
}

/**
 * POST /api/chat/stream — lit les events SSE `token` puis `done`.
 * Appelle onToken à chaque delta, résout avec le payload final.
 */
export function streamChat(question: string, onToken: (delta: string) => void): Promise<ChatDone> {
  return fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  }).then(async (res) => {
    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => '');
      throw new Error(`Stream ${res.status} : ${text || res.statusText}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let final: ChatDone = { answer: '', sources: [], refusal: false };

    const handleEvent = (event: string, data: string) => {
      try {
        const payload = JSON.parse(data);
        if (event === 'token' && typeof payload.delta === 'string') {
          onToken(payload.delta);
          final.answer += payload.delta;
        } else if (event === 'done') {
          final = payload as ChatDone;
        } else if (event === 'error') {
          throw new Error(payload.detail || 'Erreur de génération');
        }
      } catch (e) {
        if (e instanceof Error && e.message !== 'Erreur de génération') throw e;
        if (event === 'error') throw e;
      }
    };

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const raw = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const lines = raw.split('\n');
        let event = 'message';
        const dataLines: string[] = [];
        for (const line of lines) {
          if (line.startsWith('event:')) event = line.slice(6).trim();
          else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
        }
        if (dataLines.length > 0) handleEvent(event, dataLines.join('\n'));
      }
    }
    return final;
  });
}
