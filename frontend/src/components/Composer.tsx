import { useState } from 'react';
import { IconClip, IconMic, IconSearch, IconSend } from './icons';

interface Props {
  loading: boolean;
  onSend: (text: string) => void;
  onNotice: (msg: string) => void;
}

export default function Composer({ loading, onSend, onNotice }: Props) {
  const [value, setValue] = useState('');

  const submit = () => {
    const text = value.trim();
    if (!text || loading) return;
    onSend(text);
    setValue('');
  };

  return (
    <div className="composer-zone">
      <div className="input-toolbar">
        <button
          type="button"
          className="tool-btn"
          title="Pièce jointe"
          onClick={() => onNotice('Pièce jointe : fonction disponible prochainement.')}
        >
          <IconClip /> <span>Joindre</span>
        </button>
        <button
          type="button"
          className="tool-btn"
          title="Recherche documentaire"
          onClick={() => onNotice('Recherche documentaire activée sur la base ONEAD.')}
        >
          <IconSearch /> <span>Recherche</span>
        </button>
        <button
          type="button"
          className="tool-btn"
          title="Microphone"
          onClick={() => onNotice('Dictée vocale : fonction disponible prochainement.')}
        >
          <IconMic /> <span>Micro</span>
        </button>
        <span className="tool-hint">Réponses basées exclusivement sur vos documents ONEAD</span>
      </div>

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
        <button type="submit" className="send-btn" disabled={loading || value.trim() === ''} title="Envoyer">
          <IconSend />
        </button>
      </form>
    </div>
  );
}
