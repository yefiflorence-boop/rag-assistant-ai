import { OneadMark } from './OneadLogo';
import { IconBook, IconDb, IconDocLines, IconSearch } from './icons';

export interface Suggestion {
  key: string;
  label: string;
  prompt: string;
  icon: React.ReactNode;
}

/** Suggestions rapides — pastilles au-dessus du champ de saisie. */
const CHIPS: Suggestion[] = [
  {
    key: 'search',
    label: 'Documents RH',
    prompt: 'Quels documents RH sont disponibles dans la base ONEAD ?',
    icon: <IconSearch size={16} />,
  },
  {
    key: 'procedure',
    label: 'Procédure congé',
    prompt: 'Quelle est la procédure de demande de congé ?',
    icon: <IconDocLines size={16} />,
  },
  {
    key: 'explore',
    label: 'Documentation',
    prompt: 'Présente la documentation RH disponible dans la base.',
    icon: <IconBook size={16} />,
  },
  {
    key: 'referentiel',
    label: 'Référentiels',
    prompt: 'Quels référentiels internes puis-je consulter ?',
    icon: <IconDb size={16} />,
  },
];

export default function HomeHero({ onSuggest }: { onSuggest: (prompt: string) => void }) {
  return (
    <section className="hero">
      <h1 className="hero-title">
        <span className="t-brand">ONEAD</span> <span className="t-ink">Assistant</span>{' '}
        <span className="t-soft">Documentaire</span>
        <br />
        <span className="t-ink">Intelligent</span>
      </h1>
      <p className="hero-sub">Interrogez la base documentaire ONEAD en langage naturel.</p>

      <div className="orb-wrap">
        <div className="orb-mark">
          <OneadMark size={240} shine />
        </div>
        <div className="orb-shadow" aria-hidden="true" />
        <div className="orb-reflect" aria-hidden="true">
          <OneadMark size={240} />
        </div>
      </div>

      <div className="chips">
        {CHIPS.map((c) => (
          <button key={c.key} type="button" className="chip" onClick={() => onSuggest(c.prompt)}>
            <span className="chip-ico">{c.icon}</span>
            {c.label}
          </button>
        ))}
      </div>
    </section>
  );
}
