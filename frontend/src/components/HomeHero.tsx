import { IconBook, IconDb, IconDocLines, IconSearch } from './icons';

export interface Suggestion {
  key: string;
  title: string;
  desc: string;
  prompt: string;
}

const CARDS: (Suggestion & { icon: React.ReactNode })[] = [
  {
    key: 'search',
    title: 'Rechercher un document',
    desc: 'Retrouvez un document RH dans la base ONEAD.',
    prompt: 'Quels documents RH sont disponibles dans la base ONEAD ?',
    icon: <IconSearch size={20} />,
  },
  {
    key: 'procedure',
    title: 'Consulter une procédure',
    desc: 'Accédez aux procédures et modes opératoires.',
    prompt: 'Quelle est la procédure de demande de congé ?',
    icon: <IconDocLines size={20} />,
  },
  {
    key: 'explore',
    title: 'Explorer la documentation',
    desc: 'Parcourez la documentation d’entreprise.',
    prompt: 'Présente la documentation RH disponible dans la base.',
    icon: <IconBook size={20} />,
  },
  {
    key: 'referentiel',
    title: 'Accéder aux référentiels internes',
    desc: 'Consultez les référentiels et guides internes.',
    prompt: 'Quels référentiels internes puis-je consulter ?',
    icon: <IconDb size={20} />,
  },
];

export default function HomeHero({ onSuggest }: { onSuggest: (prompt: string) => void }) {
  return (
    <section className="hero">
      <img src="/logo.png" alt="ONEAD" className="hero-logo" />
      <h2>Comment puis-je vous aider aujourd&apos;hui ?</h2>
      <p className="hero-sub">
        Interrogez votre base documentaire ONEAD en langage naturel et obtenez des réponses fiables
        basées sur les connaissances de l&apos;entreprise.
      </p>
      <div className="card-grid">
        {CARDS.map((c) => (
          <article key={c.key} className="onead-card">
            <div className="card-icon">{c.icon}</div>
            <h3>{c.title}</h3>
            <p>{c.desc}</p>
            <button className="card-btn" onClick={() => onSuggest(c.prompt)}>
              Utiliser
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
