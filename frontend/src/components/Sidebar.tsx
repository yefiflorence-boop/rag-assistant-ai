import type { Conversation, Manifest, Theme } from '../types';
import { IconChat, IconHelp, IconPlus } from './icons';

interface Props {
  conversations: Conversation[];
  activeId: string;
  filter: string;
  onFilter: (v: string) => void;
  onSelect: (id: string) => void;
  onNew: () => void;
  docCount: number;
  manifest: Manifest | null;
  theme: Theme;
  onTheme: (t: Theme) => void;
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
              {c.title}
            </span>
          </button>
        ))}
        {items.length === 0 && <div className="side-meta">Aucune conversation trouvée.</div>}
      </nav>

      <div className="side-foot">
        <span>
          {p.manifest?.date_indexation
            ? `Base à jour · ${p.docCount} docs`
            : `${p.docCount} document(s)`}
        </span>
        <span className="theme-mini" role="radiogroup" aria-label="Thème">
          {(['sombre', 'clair'] as Theme[]).map((t) => (
            <button
              key={t}
              className={`theme-mini-opt ${p.theme === t ? 'active' : ''}`}
              onClick={() => p.onTheme(t)}
              role="radio"
              aria-checked={p.theme === t}
              title={t === 'sombre' ? 'Thème sombre' : 'Thème clair'}
            >
              {t === 'sombre' ? 'Sombre' : 'Clair'}
            </button>
          ))}
        </span>
      </div>

      <details className="help-box">
        <summary>
          <IconHelp /> Aide
        </summary>
        <p>
          Posez vos questions en langage naturel. Les réponses sont générées exclusivement à partir
          des documents ONEAD indexés.
        </p>
      </details>
    </aside>
  );
}
