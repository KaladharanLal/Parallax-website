import React from 'react';

/**
 * PARALLAX official vector logo component.
 * Renders the authentic vector path from the official convention assets
 * with 100% transparency and responsive SVG scaling.
 */
export function ParallaxLogo({
  className = '',
  style = {},
  variant = 'default',
  id = 'parallax-logo',
  ...props
}) {
  const gradientId = `${id}-gradient`;
  const glowFilterId = `${id}-glow`;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 3161 969"
      fill="none"
      className={`parallax-vector-logo ${className}`}
      style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
      role="img"
      aria-label="PARALLAX"
      {...props}
    >
      <defs>
        {variant === 'hero' ? (
          <>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="45%" stopColor="#f3f5fc" />
              <stop offset="70%" stopColor="#b5caff" />
              <stop offset="100%" stopColor="#81e4e2" />
            </linearGradient>
            <filter id={glowFilterId} x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow
                dx="0"
                dy="8"
                stdDeviation="16"
                floodColor="#81e4e2"
                floodOpacity="0.22"
              />
            </filter>
          </>
        ) : (
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#edeef4" />
          </linearGradient>
        )}
      </defs>
      <path
        id="Parallax"
        fill={variant === 'hero' ? `url(#${gradientId})` : `url(#${gradientId})`}
        filter={variant === 'hero' ? `url(#${glowFilterId})` : undefined}
        fillRule="evenodd"
        d="M3625,990H3490L3330,819,3173,988H3046l220-238L3033,506h132l165,173,109-115h126L3396,747ZM2498,821c31.63-184.255,209-186,209-186h155c-8.87-55.755-63-62-63-62l-83-82h99c146.13,13.745,148,156,148,156l1,330H2627C2492.62,953.245,2498,821,2498,821ZM2350,272l131,79v784l-131-88V272Zm-200-24,131,79v784l-131-88V248ZM1655,821c31.62-184.255,209-186,209-186h155c-8.88-55.755-63-62-63-62l-83-82h99c146.12,13.745,148,156,148,156l1,330H1784C1649.63,953.245,1655,821,1655,821Zm-79-183-1,230L1429,990V444l68,38,48,45c51-53.753,144-46,144-46v98C1592.5,553.747,1576,638,1576,638ZM923,821c31.625-184.255,209-186,209-186h155c-8.87-55.755-63-62-63-62l-83-82h99c146.13,13.745,148,156,148,156l1,330H1052C917.625,953.245,923,821,923,821ZM779,712H630V904l-166,98,2-300,86-44c7.792-7.755,76-67,76-67H789c87.292-22.755,73-109,73-109,11.292-82.255-385-239-385-239V166L833,301c143.125,46.453,147,191,147,191C976.125,697.453,779,712,779,712Zm508,17V872H1105s-67.87-3.255-71-65c0,0,2.62-54.255,63-73Zm732,0V872H1837s-67.87-3.255-71-65c0,0,2.62-54.255,63-73Zm843,0V872H2680s-67.88-3.255-71-65c0,0,2.62-54.255,63-73Z"
        transform="translate(-464 -166)"
      />
    </svg>
  );
}

export default ParallaxLogo;
