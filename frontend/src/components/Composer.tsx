import { useState } from 'react';
import { IconDb, IconHelp, IconSend } from './icons';

interface Props {
  loading: boolean;
  onSend: (text: string) => void;
  docCount: number;
  onHelp: () => void;
}

/** Carte de saisie en bas de la scène : zone de texte + barre d'outils. */
export default function Composer({ loading, onSend, docCount, onHelp }: Props) {
  const [value, setValue] = useState('');

  const submit = () => {
    const text = value.trim();
    if (!text || loading) return;
    onSend(text);
    setValue('');
  };

  return (
    <div className="composer-zone">
      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Posez votre question sur les documents ONEAD..."
          aria-label="Posez votre question sur les documents ONEAD"
          rows={1}
          disabled={loading}
        />

        <div className="composer-bar">
          <div className="composer-tools">
            <span className="pill-info" title="Corpus indexé disponible pour les réponses">
              <IconDb size={14} />
              Base : {docCount} document{docCount > 1 ? 's' : ''}
            </span>
            <button type="button" className="pill-ghost" onClick={onHelp}>
              <IconHelp size={14} />
              Aide
            </button>
          </div>

          <div className="composer-actions">
            <span className="kbd-hint">Entrée pour envoyer</span>
            <button
              type="submit"
              className="send-pill"
              disabled={loading || value.trim() === ''}
              title="Envoyer la question"
            >
              <IconSend size={15} />
              {loading ? 'En cours…' : 'Envoyer'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
