import { IconBell, IconGear } from './icons';

export default function Header() {
  return (
    <header className="onead-header">
      <div className="onead-brand">
        <img src="/logo.png" alt="ONEAD" />
        <div className="onead-brand-name">
          ONE<span>AD</span>
        </div>
      </div>
      <div className="onead-title">
        <h1>ONEAD Assistant IA</h1>
        <p>Votre assistant documentaire intelligent</p>
      </div>
      <div className="onead-actions">
        <span className="icon-btn" title="Notifications" role="button" tabIndex={0}>
          <IconBell />
          <span className="dot" />
        </span>
        <span className="icon-btn" title="Paramètres" role="button" tabIndex={0}>
          <IconGear size={18} />
        </span>
        <span className="avatar" title="Profil utilisateur">
          AD
        </span>
      </div>
    </header>
  );
}
