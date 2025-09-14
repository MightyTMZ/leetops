import React from 'react';

interface LeetOpsLogoProps {
  size?: number;
  className?: string;
}

export const LeetOpsLogo: React.FC<LeetOpsLogoProps> = ({ size = 32, className = '' }) => {
  return (
    <div className={`flex items-center ${className}`}>
      {/* Logo Icon */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox="0 0 32 32"
          className="drop-shadow-sm"
        >
          {/* Gradient definitions */}
          <defs>
            <linearGradient id="squircleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ff6b35" />
              <stop offset="50%" stopColor="#f7931e" />
              <stop offset="100%" stopColor="#ffd700" />
            </linearGradient>
            <linearGradient id="textGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b4513" />
              <stop offset="70%" stopColor="#8b4513" />
              <stop offset="100%" stopColor="#ff6b35" />
            </linearGradient>
          </defs>
          
          {/* Squircle background */}
          <path
            d="M16 2C8.268 2 2 8.268 2 16s6.268 14 14 14 14-6.268 14-14S23.732 2 16 2z"
            fill="url(#squircleGradient)"
            className="drop-shadow-sm"
          />
          
          {/* Black hexagon */}
          <path
            d="M16 6l8.66 5v10l-8.66 5-8.66-5V11L16 6z"
            fill="#000000"
          />
          
          {/* Orange exclamation mark */}
          <path
            d="M16 10h2v8h-2z"
            fill="#ff6b35"
          />
          <circle
            cx="17"
            cy="20"
            r="1.5"
            fill="#ff6b35"
          />
          
          {/* Green dot */}
          <circle
            cx="24"
            cy="8"
            r="2"
            fill="#22c55e"
          />
          
          {/* Orange dot */}
          <circle
            cx="24"
            cy="24"
            r="1.5"
            fill="#ff6b35"
          />
        </svg>
      </div>
      
      {/* Text */}
      <div className="ml-3">
        <span 
          className="text-xl font-bold"
          style={{ 
            background: 'linear-gradient(90deg, #8b4513 0%, #8b4513 70%, #ff6b35 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}
        >
          LeetOps
        </span>
      </div>
    </div>
  );
};

export default LeetOpsLogo;
