import { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import type { Source } from '../types';

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

interface Props {
  source: Source;
  onClose: () => void;
}

function citedPage(s: Source): number {
  const n = parseInt(s.page, 10);
  return Number.isFinite(n) && n > 0 ? n : 1;
}

export default function DocViewer({ source, onClose }: Props) {
  const cited = citedPage(source);
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [page, setPage] = useState(cited);
  const [scale, setScale] = useState(1.25);
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Chargement du document (une seule fois par source)
  useEffect(() => {
    let cancelled = false;
    setPdf(null);
    setError(null);
    setPage(citedPage(source));
    fetch(source.url.split('#')[0])
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.arrayBuffer();
      })
      .then((buf) => pdfjsLib.getDocument({ data: buf }).promise)
      .then((doc) => {
        if (!cancelled) setPdf(doc);
      })
      .catch(() => {
        if (!cancelled) setError('Impossible de charger ce document.');
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source.url]);

  // Rendu de la page courante
  useEffect(() => {
    if (!pdf || !canvasRef.current) return;
    let cancelled = false;
    const target = Math.min(Math.max(page, 1), pdf.numPages);
    pdf
      .getPage(target)
      .then((pg) => {
        if (cancelled) return;
        const dpr = window.devicePixelRatio || 1;
        const viewport = pg.getViewport({ scale: scale * dpr });
        const canvas = canvasRef.current!;
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = '100%';
        canvas.style.height = 'auto';
        return pg.render({ canvas, viewport }).promise;
      })
      .catch(() => {
        if (!cancelled) setError('Impossible d’afficher cette page.');
      });
    return () => {
      cancelled = true;
    };
  }, [pdf, page, scale]);

  // Échap ferme, flèches naviguent
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') setPage((p) => p + 1);
      if (e.key === 'ArrowLeft') setPage((p) => Math.max(1, p - 1));
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  const total = pdf?.numPages ?? 0;
  const clamped = total ? Math.min(Math.max(page, 1), total) : page;

  return (
    <div className="doc-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="doc-modal"
        role="dialog"
        aria-modal="true"
        aria-label={source.name}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="doc-modal-bar">
          <div className="doc-modal-title" title={source.name}>
            {source.name}
          </div>
          <span className="page-badge" title="Page d’où est tirée la réponse">
            Page {source.page}
          </span>
          <div className="doc-modal-tools">
            <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={!total || clamped <= 1} title="Page précédente">
              ‹
            </button>
            <span className="doc-modal-count">
              {total ? `${clamped} / ${total}` : '…'}
            </span>
            <button type="button" onClick={() => setPage((p) => (total ? Math.min(total, p + 1) : p + 1))} disabled={!total || clamped >= total} title="Page suivante">
              ›
            </button>
            <button type="button" onClick={() => setScale((s) => Math.max(0.6, +(s - 0.15).toFixed(2)))} title="Zoom arrière">
              −
            </button>
            <button type="button" onClick={() => setScale((s) => Math.min(2.5, +(s + 0.15).toFixed(2)))} title="Zoom avant">
              +
            </button>
            {clamped !== cited && total > 0 && (
              <button type="button" className="goto-cited" onClick={() => setPage(cited)} title="Revenir à la page citée">
                Page citée : {source.page}
              </button>
            )}
            <button type="button" className="doc-modal-close" onClick={onClose} title="Fermer (Échap)">
              ✕
            </button>
          </div>
        </div>
        {source.excerpt && (
          <div className="doc-modal-excerpt">
            <strong>Extrait cité (page {source.page}) — </strong>
            {source.excerpt}…
          </div>
        )}
        <div className="doc-modal-body">
          {error ? (
            <div className="doc-modal-error">{error}</div>
          ) : (
            <canvas ref={canvasRef} className="doc-modal-canvas" />
          )}
          {!pdf && !error && (
            <div className="doc-modal-loading">
              <span className="typing"><span /><span /><span /></span> Chargement du document…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
