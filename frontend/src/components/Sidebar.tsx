import type { Conversation, DocItem, DrhContact, Manifest, Theme } from '../types';
import {
  IconBook,
  IconChat,
  IconDb,
  IconDoc,
  IconGear,
  IconHelp,
  IconHistory,
  IconPlus,
} from './icons';

interface Props {
  conversations: Conversation[];
  activeId: string;
  filter: string;
  onFilter: (v: string) => void;
  onSelect: (id: string) => void;
  onNew: () => void;
  documents: DocItem[];
  manifest: Manifest | null;
  totalMessages: number;
  theme: Theme;
  onTheme: (t: Theme) => void;
  drh: DrhContact | null;
}

export default function Sidebar(p: Props) {
  const q = p.filter.trim().toLowerCase();
  const items = [...p.conversations].reverse().filter((c) => {
    if (!q) return true;
    const hay = (c.title + ' ' + c.messages.map((m) => m.content).join(' ')).toLowerCase();
    return hay.includes(q);
  });

  return (
    <aside className="sidebar">
      <button className="btn-new" onClick={p.onNew}>
        <IconPlus /> Nouvelle conversation
      </button>

      <div className="side-label">Recherche</div>
      <input
        className="side-search"
        value={p.filter}
        onChange={(e) => p.onFilter(e.target.value)}
        placeholder="Rechercher dans l'historique..."
        aria-label="Rechercher dans l'historique"
      />

      <div className="side-label">Conversations récentes</div>
      <nav className="side-nav">
        {items.slice(0, 8).map((c) => (
          <button
            key={c.id}
            className={`side-item ${c.id === p.activeId ? 'active' : ''}`}
            onClick={() => p.onSelect(c.id)}
            title={c.title}
          >
            <IconChat />
            <span className="side-item-text">
              {(c.id === p.activeId ? '● ' : '○ ') + c.title}
            </span>
          </button>
        ))}
        {items.length === 0 && <div className="side-meta">Aucune conversation trouvée.</div>}
      </nav>

      <div className="side-label">Documents importés</div>
      {p.documents.length > 0 ? (
        <>
          <div className="side-meta">{p.documents.length} document(s) disponible(s)</div>
          <div className="doc-list">
            {p.documents.slice(0, 6).map((d) => (
              <a key={d.name} className="doc-row" href={d.url} target="_blank" rel="noreferrer">
                <IconDoc />
                <span>{d.name}</span>
              </a>
            ))}
          </div>
        </>
      ) : (
        <div className="side-meta">Aucun document importé.</div>
      )}

      <div className="side-label">Base documentaire</div>
      {p.manifest && p.manifest.nb_documents !== undefined ? (
        <div className="manifest-card">
          <div className="manifest-row">
            <IconDb /> <strong>Base à jour</strong>
          </div>
          <div className="side-meta">
            Mise à jour : {p.manifest.date_indexation ?? '?'}
            <br />
            Documents : {p.manifest.nb_documents ?? '?'} — Chunks : {p.manifest.nb_chunks ?? '?'}
            <br />
            Modèle : {p.manifest.embedding_model ?? '?'}
          </div>
        </div>
      ) : (
        <div className="side-meta">Base non versionnée.</div>
      )}

      <div className="side-label">Historique</div>
      <div className="side-meta">
        <IconHistory /> {p.conversations.length} conversation(s) — {p.totalMessages} message(s)
      </div>

      <div className="side-label">Paramètres</div>
      <div className="theme-switch" role="radiogroup" aria-label="Thème">
        {(['sombre', 'clair'] as Theme[]).map((t) => (
          <button
            key={t}
            className={`theme-opt ${p.theme === t ? 'active' : ''}`}
            onClick={() => p.onTheme(t)}
            role="radio"
            aria-checked={p.theme === t}
          >
            {t === 'sombre' ? 'Sombre' : 'Clair'}
          </button>
        ))}
      </div>

      <div className="side-label">Aide</div>
      <details className="help-box">
        <summary>
          <IconHelp /> Aide et confidentialité
        </summary>
        <p>
          Posez vos questions en langage naturel. Les réponses sont générées exclusivement à partir
          des documents ONEAD indexés.
        </p>
        {p.drh && (
          <p className="side-meta">
            Recours : {p.drh.nom} — {p.drh.email} / {p.drh.tel}
          </p>
        )}
      </details>

      <div className="side-foot">
        <span>
          <IconGear /> ONEAD Enterprise
        </span>
        <span>
          <IconBook /> v1.0
        </span>
      </div>
    </aside>
  );
}
