import { useEffect, useRef, useState } from 'react';
import type { ChatMessage, DrhContact, Source } from '../types';
import { IconExternal } from './icons';
import DocViewer from './DocViewer';

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  drh: DrhContact | null;
}

/** Ouvre le PDF dans un onglet de lecture, sans jamais déclencher de téléchargement :
 *  le fichier est récupéré en blob (aucun Content-Disposition sur une URL blob),
 *  puis ouvert avec le fragment #page=N conservé pour arriver à la page citée. */
async function openDoc(s: Source, setOpening: (v: string | null) => void) {
  setOpening(s.label);
  try {
    const res = await fetch(s.url.split('#')[0]);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const objUrl = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
    const frag = s.url.includes('#') ? s.url.slice(s.url.indexOf('#')) : '';
    window.open(objUrl + frag, '_blank', 'noopener');
  } catch {
    window.open(s.url, '_blank', 'noopener'); // repli : navigation directe
  } finally {
    setOpening(null);
  }
}

function renderText(content: string) {
  // Rendu minimaliste : paragraphes + puces "•"/"-", sans dépendance markdown.
  const blocks = content.split(/\n{2,}/);
  return blocks.map((b, i) => {
    const lines = b.split('\n').map((l) => l.trim()).filter(Boolean);
    const isList = lines.length > 0 && lines.every((l) => /^[•\-*]/.test(l));
    if (isList) {
      return (
        <ul key={i} className="md-list">
          {lines.map((l, j) => (
            <li key={j}>{l.replace(/^[•\-*]\s*/, '')}</li>
          ))}
        </ul>
      );
    }
    return (
      <p key={i} className="md-p">
        {b}
      </p>
    );
  });
}

export default function ChatThread({ messages, loading, drh }: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const [viewing, setViewing] = useState<Source | null>(null);

  useEffect(() => {
    const onScroll = () => {
      const dist =
        document.documentElement.scrollHeight - (window.scrollY + window.innerHeight);
      nearBottom.current = dist < 140;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    // Ne force le scroll que si l'utilisateur est déjà en bas : sinon le
    // défilement fluide à chaque token se bat avec la lecture manuelle.
    if (nearBottom.current) {
      endRef.current?.scrollIntoView({ behavior: loading ? 'auto' : 'smooth', block: 'end' });
    }
  }, [messages, loading]);

  return (
    <section className="chat-wrap" aria-live="polite">
      {messages.map((m) => (
        <div key={m.id}>
          <div className={`msg-row ${m.role}`}>
            <div className="msg-col">
              <div className={`bubble ${m.role === 'user' ? 'user-b' : 'assist-b'}`}>
                {m.content === '' && m.role === 'assistant' ? (
                  <span className="typing" aria-label="Réponse en cours">
                    <span />
                    <span />
                    <span />
                  </span>
                ) : (
                  renderText(m.content)
                )}
                {loading && m.role === 'assistant' && m.content !== '' && (
                  <span className="stream-caret" />
                )}
              </div>
              <div className="msg-meta">
                {m.role === 'user' ? 'Vous' : 'ONEAD Assistant'} · {m.time}
              </div>
            </div>
          </div>

          {m.role === 'assistant' && m.sources.length > 0 && (
            <div className="msg-row assistant">
              <div className="msg-col">
                <div className="src-title">RÉFÉRENCES DOCUMENTAIRES</div>
                {m.sources.map((s) => (
                  <div key={s.label} className="src-card">
                    <div className="src-head">
                      <button
                        type="button"
                        className="src-link"
                        onClick={() => setViewing(s)}
                        title="Lire le document à la page citée"
                      >
                        {s.name} <IconExternal />
                      </button>
                      <span className="page-badge" title="Page d’où est tirée la réponse">
                        Page {s.page}
                      </span>
                    </div>
                    {s.excerpt && <blockquote className="src-excerpt">{s.excerpt}…</blockquote>}
                    <div className="src-sub">Cliquez pour lire le document à la page citée.</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {m.role === 'assistant' && m.refusal && drh && (
            <div className="msg-row assistant">
              <div className="msg-col">
                <div className="drh-card">
                  <strong>Recours DRH — {drh.nom}</strong>
                  <br />
                  {drh.email} · {drh.tel}
                  <br />
                  <span className="muted">{drh.horaires}</span>
                  <br />
                  Votre question a été journalisée pour une revue par la DRH.
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
      <div ref={endRef} />
      {viewing && <DocViewer source={viewing} onClose={() => setViewing(null)} />}
    </section>
  );
}
