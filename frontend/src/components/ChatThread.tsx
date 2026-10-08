import { useEffect, useRef } from 'react';
import type { ChatMessage, DrhContact } from '../types';
import { IconExternal } from './icons';

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  drh: DrhContact | null;
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
                    <a href={s.url} target="_blank" rel="noreferrer">
                      {s.label} <IconExternal />
                    </a>
                    <div className="src-sub">
                      Document consulté — cliquez pour ouvrir à la page citée.
                    </div>
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
    </section>
  );
}
