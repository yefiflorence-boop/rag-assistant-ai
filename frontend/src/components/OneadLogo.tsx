import { useId } from 'react';

interface MarkProps {
  size?: number;
  className?: string;
}

/**
 * ONEAD — goutte bleue + feuille verte imbriquée, 100% vectoriel,
 * fond transparent, sans encadrement. Lisible en thème sombre ET clair.
 */
export function OneadMark({ size = 38, className = '' }: MarkProps) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '');
  const dropId = `onead-drop-${uid}`;
  const leafId = `onead-leaf-${uid}`;

  return (
    <svg
      width={size}
      height={Math.round((size * 60) / 48)}
      viewBox="0 0 48 60"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`onead-mark ${className}`.trim()}
      role="img"
      aria-label="ONEAD"
    >
      <defs>
        <linearGradient id={dropId} x1="10" y1="4" x2="38" y2="52" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#38BDF8" />
          <stop offset="0.45" stopColor="#00AEEF" />
          <stop offset="1" stopColor="#006EA8" />
        </linearGradient>
        <linearGradient id={leafId} x1="25" y1="24" x2="40" y2="46" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#34D399" />
          <stop offset="1" stopColor="#009E77" />
        </linearGradient>
      </defs>

      {/* Goutte principale */}
      <path
        d="M24 2.5C22.6 11.5 9.5 26.2 9.5 37.6a14.5 14.5 0 0 0 29 0C38.5 26.2 25.4 11.5 24 2.5Z"
        fill={`url(#${dropId})`}
      />
      {/* Reflet vertical — éclat d'eau */}
      <path
        d="M17.2 30.5c-1.9 2.6-3 5.7-3 8.6 0 4.4 2.5 8.1 6.1 9.9-4.6-2.9-6-11.3-3.1-18.5Z"
        fill="#FFFFFF"
        opacity="0.28"
      />
      <ellipse cx="18.6" cy="36.4" rx="2.1" ry="4.4" fill="#FFFFFF" opacity="0.55" transform="rotate(-12 18.6 36.4)" />

      {/* Feuille / goutte verte imbriquée */}
      <path
        d="M31.5 23.5c-1.2 4.6-6.3 8.6-6.3 14.1a7.6 7.6 0 0 0 15.2 0c0-5.5-6.5-9.9-8.9-14.1Z"
        fill={`url(#${leafId})`}
      />
      <path
        d="M32.9 29.5c-.7 2.6-3 4.7-3 7.4 0 1.9 1 3.5 2.6 4.3-2-1.8-2.4-6.7.4-11.7Z"
        fill="#FFFFFF"
        opacity="0.35"
      />
    </svg>
  );
}

interface StackedProps {
  width?: number;
  className?: string;
}

/**
 * Version complète centrée (hero) : goutte + wordmark ONEAD en dégradé,
 * toujours sans fond ni cadre.
 */
export function OneadLogoStacked({ width = 132, className = '' }: StackedProps) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '');
  const dropId = `onead-s-drop-${uid}`;
  const leafId = `onead-s-leaf-${uid}`;
  const textId = `onead-s-text-${uid}`;
  const height = Math.round((width * 104) / 132);

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 132 104"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`onead-stacked ${className}`.trim()}
      role="img"
      aria-label="ONEAD"
    >
      <defs>
        <linearGradient id={dropId} x1="42" y1="2" x2="90" y2="62" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#38BDF8" />
          <stop offset="0.45" stopColor="#00AEEF" />
          <stop offset="1" stopColor="#006EA8" />
        </linearGradient>
        <linearGradient id={leafId} x1="66" y1="26" x2="88" y2="58" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#34D399" />
          <stop offset="1" stopColor="#009E77" />
        </linearGradient>
        <linearGradient id={textId} x1="14" y1="72" x2="118" y2="72" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#00AEEF" />
          <stop offset="1" stopColor="#00C896" />
        </linearGradient>
      </defs>

      {/* Goutte centrée */}
      <g transform="translate(42 2)">
        <path
          d="M24 2.5C22.6 11.5 9.5 26.2 9.5 37.6a14.5 14.5 0 0 0 29 0C38.5 26.2 25.4 11.5 24 2.5Z"
          fill={`url(#${dropId})`}
        />
        <ellipse cx="18.6" cy="36.4" rx="2.1" ry="4.4" fill="#FFFFFF" opacity="0.55" transform="rotate(-12 18.6 36.4)" />
        <path
          d="M31.5 23.5c-1.2 4.6-6.3 8.6-6.3 14.1a7.6 7.6 0 0 0 15.2 0c0-5.5-6.5-9.9-8.9-14.1Z"
          fill={`url(#${leafId})`}
        />
      </g>

      {/* Wordmark */}
      <text
        x="66"
        y="92"
        textAnchor="middle"
        fontFamily="Inter, 'Segoe UI', system-ui, sans-serif"
        fontWeight={800}
        fontSize="27"
        letterSpacing="1.5"
        fill={`url(#${textId})`}
      >
        ONEAD
      </text>
    </svg>
  );
}
