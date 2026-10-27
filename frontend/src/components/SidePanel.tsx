import type { Conversation, DocItem, Manifest, Theme } from '../types';
import type { PanelSection } from './Rail';
import { IconChat, IconClose, IconDocLines, IconHelp, IconPlus } from './icons';

interface Props {
  section: PanelSection;
  onClose: () => void;
  conversations: Conversation[];
  activeId: string;
  filter: string;
  onFilter: (v: string) => void;
  onSelect: (id: string) => void;
  onNew: () => void;
  documents: DocItem[];
  manifest: Manifest | null;
  theme: Theme;
  onTheme: (t: Theme) => void;
}

const TITLES: Record<PanelSection, string> = {
  conversations: 'Conversations',
  documents: 'Documents indexés',
  reglages: 'Réglages & aide',
};

function fileSize(bytes: number): string {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

/** Panneau coulissant ouvert depuis le rail : conversations, documents, réglages. */
export default function SidePanel(p: Props) {
  const q = p.filter.trim().toLowerCase();
  const items = [...p.conversations].reverse().filter((c) => {
    if (!q) return true;
    const hay = (c.title + ' ' + c.messages.map((m) => m.content).join(' ')).toLowerCase();
    return hay.includes(q);
  });

  return (
    <>
      <div className="panel-backdrop" onClick={p.onClose} aria-hidden="true" />
      <aside className="panel" role="dialog" aria-label={TITLES[p.section]}>
        <div className="panel-head">
          <span className="panel-title">{TITLES[p.section]}</span>
          <button type="button" className="panel-close" onClick={p.onClose} aria-label="Fermer le panneau">
            <IconClose />
          </button>
        </div>

        <div className="panel-body">
          {p.section === 'conversations' && (
            <>
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
                    <span className="side-item-text">{c.title}</span>
                  </button>
                ))}
                {items.length === 0 && <div className="side-meta">Aucune conversation trouvée.</div>}
              </nav>
            </>
          )}

          {p.section === 'documents' && (
            <>
              <div className="side-label">Corpus documentaire</div>
              <div className="doc-list">
                {p.documents.map((d) => (
                  <a key={d.url} className="doc-row" href={d.url} target="_blank" rel="noreferrer" title={d.name}>
                    <IconDocLines size={15} />
                    <span className="doc-row-name">{d.name}</span>
                    <span className="doc-row-size">{fileSize(d.size)}</span>
                  </a>
                ))}
                {p.documents.length === 0 && <div className="side-meta">Aucun document disponible.</div>}
              </div>

              {p.manifest && (
                <div className="manifest-card">
                  <div className="manifest-row">
                    Index {p.manifest.date_indexation ? `à jour · ${p.manifest.date_indexation}` : 'en cours'}
                  </div>
                  <div className="side-meta">
                    {p.manifest.nb_documents ?? p.documents.length} documents ·{' '}
                    {p.manifest.nb_chunks ?? '—'} passages
                  </div>
                  {p.manifest.embedding_model && (
                    <div className="side-meta">Modèle : {p.manifest.embedding_model}</div>
                  )}
                </div>
              )}
            </>
          )}

          {p.section === 'reglages' && (
            <>
              <div className="side-label">Thème</div>
              <div className="theme-switch" role="radiogroup" aria-label="Thème">
                {(['clair', 'sombre'] as Theme[]).map((t) => (
                  <button
                    key={t}
                    className={`theme-opt ${p.theme === t ? 'active' : ''}`}
                    onClick={() => p.onTheme(t)}
                    role="radio"
                    aria-checked={p.theme === t}
                  >
                    {t === 'clair' ? 'Clair' : 'Sombre'}
                  </button>
                ))}
              </div>

              <details className="help-box" open>
                <summary>
                  <IconHelp /> Aide
                </summary>
                <p>
                  Posez vos questions en langage naturel. Les réponses sont générées exclusivement à
                  partir des documents ONEAD indexés.
                </p>
              </details>

              <div className="side-foot">
                <span>
                  {p.manifest?.date_indexation
                    ? `Base à jour · ${p.documents.length} docs`
                    : `${p.documents.length} document(s)`}
                </span>
              </div>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
