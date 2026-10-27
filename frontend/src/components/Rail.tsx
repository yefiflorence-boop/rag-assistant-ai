import type { Theme } from '../types';
import { OneadMark } from './OneadLogo';
import { IconChat, IconDoc, IconGear, IconMoon, IconSparkles, IconSun } from './icons';

export type PanelSection = 'conversations' | 'documents' | 'reglages';

interface Props {
  section: PanelSection | null;
  onSection: (s: PanelSection | null) => void;
  onNew: () => void;
  theme: Theme;
  onTheme: (t: Theme) => void;
}

/** Barre latérale réduite (style « rail » d'icônes) — ouvre le panneau coulissant. */
export default function Rail({ section, onSection, onNew, theme, onTheme }: Props) {
  const toggle = (s: PanelSection) => onSection(section === s ? null : s);

  return (
    <nav className="rail" aria-label="Navigation principale">
      <div className="rail-logo">
        <OneadMark size={30} />
      </div>

      <div className="rail-group">
        <button
          type="button"
          className={`rail-btn ${section === null ? 'active' : ''}`}
          onClick={onNew}
          title="Nouvelle conversation"
          aria-label="Nouvelle conversation"
        >
          <IconSparkles size={19} />
        </button>
        <button
          type="button"
          className={`rail-btn ${section === 'conversations' ? 'active' : ''}`}
          onClick={() => toggle('conversations')}
          title="Conversations récentes"
          aria-label="Conversations récentes"
          aria-expanded={section === 'conversations'}
        >
          <IconChat size={18} />
        </button>
        <button
          type="button"
          className={`rail-btn ${section === 'documents' ? 'active' : ''}`}
          onClick={() => toggle('documents')}
          title="Documents indexés"
          aria-label="Documents indexés"
          aria-expanded={section === 'documents'}
        >
          <IconDoc size={18} />
        </button>
        <button
          type="button"
          className={`rail-btn ${section === 'reglages' ? 'active' : ''}`}
          onClick={() => toggle('reglages')}
          title="Réglages et aide"
          aria-label="Réglages et aide"
          aria-expanded={section === 'reglages'}
        >
          <IconGear size={18} />
        </button>
      </div>

      <div className="rail-foot">
        <button
          type="button"
          className="rail-btn"
          onClick={() => onTheme(theme === 'clair' ? 'sombre' : 'clair')}
          title={theme === 'clair' ? 'Passer en thème sombre' : 'Passer en thème clair'}
          aria-label={theme === 'clair' ? 'Passer en thème sombre' : 'Passer en thème clair'}
        >
          {theme === 'clair' ? <IconMoon size={18} /> : <IconSun size={18} />}
        </button>
      </div>
    </nav>
  );
}
