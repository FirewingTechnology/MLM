import React from 'react';

interface MyStatusLogoProps {
  variant?: 'full' | 'horizontal' | 'icon-only';
  theme?: 'light' | 'dark';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showTagline?: boolean;
}

export const MyStatusIcon: React.FC<{ size?: number | string; className?: string }> = ({ 
  size = 40, 
  className = '' 
}) => {
  return (
    <svg 
      viewBox="0 0 320 250" 
      width={size} 
      height={typeof size === 'number' ? size * 0.78 : size} 
      className={`shrink-0 ${className}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="logoSkyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#29B6F6" />
          <stop offset="100%" stopColor="#0288D1" />
        </linearGradient>
        <linearGradient id="logoNavyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1E3A8A" />
          <stop offset="100%" stopColor="#0F172A" />
        </linearGradient>
      </defs>

      {/* Top Upward Arrow */}
      <path d="M 160 5 L 195 55 L 175 55 L 175 80 L 145 80 L 145 55 L 125 55 Z" fill="#0288D1" />

      {/* Right Speech Bubble (Navy) */}
      <path 
        d="M 165 65 
           H 265 A 25 25 0 0 1 290 90 
           V 170 A 25 25 0 0 1 265 195 
           H 215 
           L 245 225 
           L 195 195 
           H 165 
           A 25 25 0 0 1 140 170 
           V 90 
           A 25 25 0 0 1 165 65 Z" 
        fill="url(#logoNavyGrad)" 
      />

      {/* Play Triangle in Navy Bubble */}
      <polygon points="208,112 208,158 246,135" fill="#FFFFFF" />

      {/* Left Speech Bubble (Sky Blue) */}
      <path 
        d="M 50 65 
           H 160 A 25 25 0 0 1 185 90 
           V 170 A 25 25 0 0 1 160 195 
           H 85 
           L 45 225 
           L 60 195 
           H 50 
           A 25 25 0 0 1 25 170 
           V 90 
           A 25 25 0 0 1 50 65 Z" 
        fill="url(#logoSkyGrad)" 
      />

      {/* Bar Chart */}
      <rect x="58" y="135" width="13" height="30" rx="3" fill="#FFFFFF" />
      <rect x="77" y="120" width="13" height="45" rx="3" fill="#FFFFFF" />
      <rect x="96" y="110" width="13" height="55" rx="3" fill="#FFFFFF" />
      <rect x="115" y="95" width="13" height="70" rx="3" fill="#FFFFFF" />

      {/* Trendline & Arrow */}
      <polyline 
        points="55,140 76,122 97,128 132,90" 
        fill="none" 
        stroke="#FFFFFF" 
        strokeWidth="5.5" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
      />
      <polygon points="120,85 138,85 138,103" fill="#FFFFFF" />
    </svg>
  );
};

export const MyStatusLogo: React.FC<MyStatusLogoProps> = ({
  variant = 'horizontal',
  theme = 'light',
  size = 'md',
  className = '',
  showTagline = true,
}) => {
  const isDark = theme === 'dark';

  const iconSizes = {
    xs: 24,
    sm: 32,
    md: 40,
    lg: 54,
    xl: 72,
  };

  const currentIconSize = iconSizes[size];

  if (variant === 'icon-only') {
    return <MyStatusIcon size={currentIconSize} className={className} />;
  }

  if (variant === 'full') {
    return (
      <div className={`flex flex-col items-center text-center ${className}`}>
        <MyStatusIcon size={currentIconSize * 1.5} className="mb-2" />
        <div className="font-heading font-black tracking-tight leading-none text-2xl sm:text-3xl">
          <span className="text-[#0288D1]">My </span>
          <span className={isDark ? 'text-[#FFFEF9]' : 'text-[#0F172A]'}>Status</span>
        </div>
        {showTagline && (
          <div className="text-[10px] sm:text-xs font-bold tracking-[0.22em] text-[#64748B] uppercase mt-1">
            Elevate Your Reach
          </div>
        )}
      </div>
    );
  }

  // Horizontal variant (Ideal for Navbars, Sidebars, Modals)
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <MyStatusIcon size={currentIconSize} />
      <div className="flex flex-col leading-tight">
        <div className={`font-heading font-black tracking-tight ${size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-xl' : 'text-base'}`}>
          <span className="text-[#0288D1]">My </span>
          <span className={isDark ? 'text-[#FFFEF9]' : 'text-[#0F172A]'}>Status</span>
        </div>
        {showTagline && (
          <span className={`text-[8px] sm:text-[9px] font-bold tracking-[0.16em] uppercase ${isDark ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>
            Elevate Your Reach
          </span>
        )}
      </div>
    </div>
  );
};
