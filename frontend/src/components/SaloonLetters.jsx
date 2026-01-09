import React from 'react';

// Custom SVG letter components using saloon tool shapes
// Each letter incorporates scissors, combs, brushes to form recognizable letters

// Letter P - Scissors handle forms vertical, comb teeth form the curve
export const SaloonP = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 28 40"
    width={size * 0.7}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Scissors handle - vertical stem */}
    <path
      d="M6 38 L6 2"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
    {/* Scissor blade detail on stem */}
    <ellipse cx="6" cy="34" rx="3" ry="4" fill={color} opacity="0.3" />

    {/* Comb forming the P curve */}
    <path
      d="M6 2 Q26 2, 26 12 Q26 22, 6 22"
      stroke={color}
      strokeWidth="3"
      fill="none"
      strokeLinecap="round"
    />
    {/* Comb teeth on the curve */}
    <line x1="12" y1="4" x2="12" y2="9" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="17" y1="5" x2="17" y2="10" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="21" y1="8" x2="21" y2="13" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

// Letter R - Similar to P with a diagonal brush leg
export const SaloonR = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 30 40"
    width={size * 0.75}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Scissors handle - vertical stem */}
    <path
      d="M6 38 L6 2"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />

    {/* P curve with comb */}
    <path
      d="M6 2 Q24 2, 24 11 Q24 20, 6 20"
      stroke={color}
      strokeWidth="3"
      fill="none"
      strokeLinecap="round"
    />
    {/* Comb teeth */}
    <line x1="12" y1="4" x2="12" y2="8" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="17" y1="5" x2="17" y2="9" stroke={color} strokeWidth="2" strokeLinecap="round" />

    {/* Brush forming the leg */}
    <path
      d="M14 20 L26 38"
      stroke={color}
      strokeWidth="3.5"
      strokeLinecap="round"
      fill="none"
    />
    {/* Brush bristle details */}
    <line x1="23" y1="34" x2="28" y2="36" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="24" y1="36" x2="28" y2="39" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Letter I - Simple brush stroke
export const SaloonI = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 12 40"
    width={size * 0.3}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Brush handle */}
    <path
      d="M6 38 L6 6"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
    {/* Dot - brush head */}
    <circle cx="6" cy="2" r="2.5" fill={color} />
  </svg>
);

// Letter Y - Two brushes meeting
export const SaloonY = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 28 40"
    width={size * 0.7}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Left diagonal brush */}
    <path
      d="M2 2 L14 18"
      stroke={color}
      strokeWidth="3.5"
      strokeLinecap="round"
      fill="none"
    />
    {/* Right diagonal brush */}
    <path
      d="M26 2 L14 18"
      stroke={color}
      strokeWidth="3.5"
      strokeLinecap="round"
      fill="none"
    />
    {/* Vertical stem */}
    <path
      d="M14 18 L14 38"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
  </svg>
);

// Letter A - Scissors forming sides, comb crossbar
export const SaloonA = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 32 40"
    width={size * 0.8}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Left scissor blade */}
    <path
      d="M16 2 L4 38"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
    {/* Scissor pivot detail */}
    <circle cx="10" cy="20" r="2" fill={color} opacity="0.4" />

    {/* Right scissor blade */}
    <path
      d="M16 2 L28 38"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />

    {/* Comb crossbar */}
    <path
      d="M8 26 L24 26"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />
    {/* Comb teeth on crossbar */}
    <line x1="11" y1="26" x2="11" y2="30" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="16" y1="26" x2="16" y2="30" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="21" y1="26" x2="21" y2="30" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Letter N - Two brush verticals with diagonal comb
export const SaloonN = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 30 40"
    width={size * 0.75}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Left brush vertical */}
    <path
      d="M5 38 L5 2"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
    {/* Brush head detail */}
    <ellipse cx="5" cy="36" rx="2.5" ry="3" fill={color} opacity="0.3" />

    {/* Right brush vertical */}
    <path
      d="M25 2 L25 38"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />

    {/* Diagonal comb */}
    <path
      d="M5 2 L25 38"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />
    {/* Comb teeth on diagonal */}
    <line x1="11" y1="12" x2="14" y2="9" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="15" y1="20" x2="18" y2="17" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="19" y1="28" x2="22" y2="25" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Letter K - Vertical with angled scissors
export const SaloonK = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 28 40"
    width={size * 0.7}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Vertical stem */}
    <path
      d="M5 38 L5 2"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />

    {/* Upper scissor blade */}
    <path
      d="M5 22 L24 2"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />

    {/* Lower scissor blade */}
    <path
      d="M5 22 L24 38"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />

    {/* Scissor pivot */}
    <circle cx="5" cy="22" r="3" fill={color} opacity="0.4" />
  </svg>
);

// Letter T - Comb forming the top, brush forming vertical
export const SaloonT = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 28 40"
    width={size * 0.7}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Horizontal comb top */}
    <path
      d="M2 4 L26 4"
      stroke={color}
      strokeWidth="3.5"
      strokeLinecap="round"
      fill="none"
    />
    {/* Comb teeth */}
    <line x1="6" y1="4" x2="6" y2="10" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="14" y1="4" x2="14" y2="10" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="22" y1="4" x2="22" y2="10" stroke={color} strokeWidth="2" strokeLinecap="round" />

    {/* Brush vertical */}
    <path
      d="M14 4 L14 38"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
  </svg>
);

// Letter U - Two curved brushes
export const SaloonU = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 30 40"
    width={size * 0.75}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* U shape with curved bottom */}
    <path
      d="M5 2 L5 28 Q5 38, 15 38 Q25 38, 25 28 L25 2"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
    {/* Brush head details at top */}
    <ellipse cx="5" cy="4" rx="2" ry="3" fill={color} opacity="0.3" />
    <ellipse cx="25" cy="4" rx="2" ry="3" fill={color} opacity="0.3" />
  </svg>
);

// Letter E - Comb forming horizontals
export const SaloonE = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 24 40"
    width={size * 0.6}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* Vertical brush */}
    <path
      d="M5 38 L5 2"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />

    {/* Top horizontal comb */}
    <path
      d="M5 4 L22 4"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />
    {/* Top comb teeth */}
    <line x1="10" y1="4" x2="10" y2="9" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="16" y1="4" x2="16" y2="9" stroke={color} strokeWidth="1.5" strokeLinecap="round" />

    {/* Middle horizontal comb */}
    <path
      d="M5 20 L18 20"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />

    {/* Bottom horizontal comb */}
    <path
      d="M5 36 L22 36"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      fill="none"
    />
    {/* Bottom comb teeth */}
    <line x1="10" y1="31" x2="10" y2="36" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="16" y1="31" x2="16" y2="36" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Letter C - Curved comb/brush
export const SaloonC = ({ size = 32, color = '#0F766E', className = '' }) => (
  <svg
    viewBox="0 0 28 40"
    width={size * 0.7}
    height={size}
    className={`saloon-letter ${className}`}
    aria-hidden="true"
  >
    {/* C curve - brush handle shape */}
    <path
      d="M24 8 Q24 2, 14 2 Q4 2, 4 20 Q4 38, 14 38 Q24 38, 24 32"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      fill="none"
    />
    {/* Brush bristle details */}
    <line x1="22" y1="5" x2="26" y2="3" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="22" y1="35" x2="26" y2="37" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

// Map of available custom letters
const letterComponents = {
  P: SaloonP,
  R: SaloonR,
  I: SaloonI,
  Y: SaloonY,
  A: SaloonA,
  N: SaloonN,
  K: SaloonK,
  T: SaloonT,
  U: SaloonU,
  E: SaloonE,
  C: SaloonC,
};

// SaloonText component - renders text with custom letters where available
export const SaloonText = ({
  text,
  size = 32,
  color = '#0F766E',
  className = '',
  fallbackClassName = ''
}) => {
  const characters = text.split('');

  return (
    <span className={`saloon-text ${className}`} aria-label={text}>
      {characters.map((char, index) => {
        const upperChar = char.toUpperCase();
        const LetterComponent = letterComponents[upperChar];

        if (LetterComponent) {
          return (
            <LetterComponent
              key={index}
              size={size}
              color={color}
              className="saloon-custom-letter"
            />
          );
        }

        // Fallback to regular character
        return (
          <span
            key={index}
            className={`saloon-fallback-letter ${fallbackClassName}`}
            style={{ color }}
          >
            {char}
          </span>
        );
      })}
    </span>
  );
};

// SaloonWord component - renders a word with custom styling
export const SaloonWord = ({
  word,
  size = 32,
  color = '#0F766E',
  className = ''
}) => {
  return (
    <span className={`saloon-word ${className}`} aria-label={word}>
      <SaloonText text={word} size={size} color={color} />
    </span>
  );
};

export default {
  SaloonP,
  SaloonR,
  SaloonI,
  SaloonY,
  SaloonA,
  SaloonN,
  SaloonK,
  SaloonT,
  SaloonU,
  SaloonE,
  SaloonC,
  SaloonText,
  SaloonWord,
};
