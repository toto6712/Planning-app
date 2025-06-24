import React from 'react';

const AvsLogo = ({ className = "h-8 w-auto", variant = "full" }) => {
  if (variant === "icon") {
    return (
      <div className={`${className} flex items-center justify-center bg-avs-blue rounded-lg p-1`}>
        <svg viewBox="0 0 40 40" className="w-full h-full text-white">
          <text x="20" y="28" textAnchor="middle" className="text-lg font-bold fill-current">
            AVS
          </text>
        </svg>
      </div>
    );
  }

  return (
    <div className={`${className} flex items-center gap-3`}>
      {/* Logo Icon */}
      <div className="h-10 w-10 bg-avs-blue rounded-lg flex items-center justify-center">
        <svg viewBox="0 0 40 40" className="w-6 h-6 text-white">
          <text x="20" y="28" textAnchor="middle" className="text-sm font-bold fill-current">
            AVS
          </text>
        </svg>
      </div>
      
      {/* Logo Text */}
      <div className="flex flex-col">
        <span className="text-avs-blue font-bold text-lg leading-tight">
          AVS Autonomie
        </span>
        <span className="text-avs-green text-xs font-medium">
          Planning Tournées
        </span>
      </div>
    </div>
  );
};

export default AvsLogo;