import { useCallback, useEffect, useMemo, useState } from 'react';
import Rail, { type PanelSection } from './components/Rail';
import SidePanel from './components/SidePanel';
import TopBar from './components/TopBar';
import HomeHero from './components/HomeHero';
import ChatThread from './components/ChatThread';
import Composer from './components/Composer';
import { fetchDocuments, fetchDrh, fetchManifest, postChat, streamChat } from './lib/api';
import type {
  ChatDone,
  ChatMessage,
  Conversation,
  DocItem,
  DrhContact,
  Manifest,
  Theme,
} from './types';

const WELCOME =
  'Bonjour, je suis l’assistant documentaire ONEAD. Interrogez la base documentaire en langage naturel, je réponds à partir des documents de l’entreprise.';

function now(): string {
  return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

function today(): string {
  const d = new Date();
  return `${d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })} ${now()}`;
}

function makeConversation(): Conversation {
  return {
    id: uid(),
    title: 'Nouvelle conversation',
    createdAt: today(),
    messages: [{ id: uid(), role: 'assistant', content: WELCOME, time: now(), sources: [] }],
  };
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    // Le design « pastel glass » est pensé d'abord en clair : seul un choix
    // explicite de l'utilisateur (ou son historique) bascule en sombre.
    const saved = localStorage.getItem('onead-theme');
    return saved === 'sombre' ? 'sombre' : 'clair';
  });
  const [conversations, setConversations] = useState<Conversation[]>(() => [makeConversation()]);
  const [activeId, setActiveId] = useState<string>(() => conversations[0].id);
  const [filter, setFilter] = useState('');
  const [panel, setPanel] = useState<PanelSection | null>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [drh, setDrh] = useState<DrhContact | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('onead-theme', theme);
  }, [theme]);

  useEffect(() => {
    fetchManifest().then(setManifest).catch(() => {});
    fetchDocuments().then((r) => setDocuments(r.documents)).catch(() => {});
    fetchDrh().then(setDrh).catch(() => {});
  }, []);

  useEffect(() => {
    if (!notice) return;
    const t = setTimeout(() => setNotice(null), 3200);
    return () => clearTimeout(t);
  }, [notice]);

  const active = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? conversations[0],
    [conversations, activeId],
  );

  const isHome = active.messages.length <= 1 && active.messages[0]?.role === 'assistant';

  const patchActive = useCallback(
    (fn: (c: Conversation) => Conversation) => {
      setConversations((prev) => prev.map((c) => (c.id === activeId ? fn(c) : c)));
    },
    [activeId],
  );

  const sendQuestion = useCallback(
    async (question: string) => {
      const text = question.trim();
      if (!text || loading) return;
      setLoading(true);

      const userMsg: ChatMessage = { id: uid(), role: 'user', content: text, time: now(), sources: [] };
      const assistId = uid();
      const placeholder: ChatMessage = {
        id: assistId,
        role: 'assistant',
        content: '',
        time: now(),
        sources: [],
      };

      patchActive((c) => ({
        ...c,
        title: c.title === 'Nouvelle conversation' ? text.slice(0, 45) : c.title,
        messages: [...c.messages, userMsg, placeholder],
      }));

      const applyDelta = (delta: string) => {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistId ? { ...m, content: m.content + delta } : m,
                  ),
                }
              : c,
          ),
        );
      };

      try {
        let done: ChatDone;
        try {
          done = await streamChat(text, applyDelta);
        } catch {
          done = await postChat(text);
          setConversations((prev) =>
            prev.map((c) =>
              c.id === activeId
                ? {
                    ...c,
                    messages: c.messages.map((m) =>
                      m.id === assistId ? { ...m, content: done.answer } : m,
                    ),
                  }
                : c,
            ),
          );
        }
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistId
                      ? {
                          ...m,
                          content: done.answer,
                          sources: done.sources,
                          refusal: done.refusal,
                          time: now(),
                        }
                      : m,
                  ),
                }
              : c,
          ),
        );
        if (done.refusal) setNotice('Question transmise pour revue DRH.');
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Erreur inconnue';
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistId
                      ? {
                          ...m,
                          content: `La génération a échoué (${msg}). Vérifiez que l’API backend est démarrée sur le port 8000.`,
                          time: now(),
                        }
                      : m,
                  ),
                }
              : c,
          ),
        );
        setNotice('Échec de la génération — backend injoignable.');
      } finally {
        setLoading(false);
      }
    },
    [activeId, loading, patchActive],
  );

  const newConversation = useCallback(() => {
    const c = makeConversation();
    setConversations((prev) => [...prev, c]);
    setActiveId(c.id);
    setFilter('');
    setPanel(null);
  }, []);

  return (
    <div className="app">
      <div className="frame">
        <Rail
          section={panel}
          onSection={setPanel}
          onNew={newConversation}
          theme={theme}
          onTheme={setTheme}
        />
        <div className="stage">
          <TopBar onNew={newConversation} />
          <main className="stage-scroll">
            {isHome ? (
              <HomeHero onSuggest={sendQuestion} />
            ) : (
              <ChatThread messages={active.messages} loading={loading} drh={drh} />
            )}
          </main>
          <Composer
            loading={loading}
            onSend={sendQuestion}
            docCount={documents.length}
            onHelp={() => setPanel(panel === 'reglages' ? null : 'reglages')}
          />
        </div>
        {panel && (
          <SidePanel
            section={panel}
            onClose={() => setPanel(null)}
            conversations={conversations}
            activeId={activeId}
            filter={filter}
            onFilter={setFilter}
            onSelect={(id) => {
              setActiveId(id);
              setPanel(null);
            }}
            onNew={newConversation}
            documents={documents}
            manifest={manifest}
            theme={theme}
            onTheme={setTheme}
          />
        )}
      </div>
      {notice && (
        <div className="toast" role="status">
          {notice}
        </div>
      )}
    </div>
  );
}
