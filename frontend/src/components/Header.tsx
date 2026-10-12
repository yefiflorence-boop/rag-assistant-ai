import { OneadMark } from './OneadLogo';

export default function Header() {
  return (
    <header className="onead-header">
      <div className="onead-brand">
        <OneadMark size={36} className="onead-brand-logo" />
        <div className="onead-brand-name">
          ONE<span>AD</span>
        </div>
      </div>
      <div className="onead-title">
        <h1>ONEAD Assistant IA</h1>
        <p>Votre assistant documentaire intelligent</p>
      </div>
      <div className="onead-actions">
        <span className="avatar" title="Profil utilisateur">
          AD
        </span>
      </div>
    </header>
  );
}
