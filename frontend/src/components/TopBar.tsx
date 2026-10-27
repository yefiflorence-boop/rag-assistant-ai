import { IconPlus } from './icons';

/** Actions flottantes en haut à droite de la scène (style pilule de l'image). */
export default function TopBar({ onNew }: { onNew: () => void }) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="btn-pill"
        onClick={onNew}
        aria-label="Nouvelle conversation"
      >
        <span className="pill-plus">
          <IconPlus size={14} />
        </span>
        <span className="btn-pill-label">Nouvelle conversation</span>
      </button>
      <span className="avatar" title="Profil utilisateur">
        AD
      </span>
    </header>
  );
}
