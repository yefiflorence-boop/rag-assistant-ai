import { useState } from 'react';
import { IconSend } from './icons';

interface Props {
  loading: boolean;
  onSend: (text: string) => void;
}

/** Carte de saisie en bas de la scène : zone de texte + bouton d'envoi. */
export default function Composer({ loading, onSend }: Props) {
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
          <div className="composer-actions">
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
