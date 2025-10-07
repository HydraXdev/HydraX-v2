"use client"

import React from 'react';

export interface MilitaryHeaderProps {
  title?: string;
  subtitle?: string;
}

export const MilitaryHeader: React.FC<MilitaryHeaderProps> = ({
  title = "BITTEN",
  subtitle
}) => {
  return (
    <div className="relative border-4 border-gray-700 bg-gradient-to-b from-gray-800 to-gray-900 p-4 mb-3 shadow-2xl" style={{
      boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5), 0 4px 8px rgba(0,0,0,0.5)'
    }}>
      {/* Corner rivets */}
      <div className="absolute top-1 left-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>
      <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>
      <div className="absolute bottom-1 left-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>
      <div className="absolute bottom-1 right-1 w-2 h-2 rounded-full bg-gray-600 border border-gray-800"></div>

      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          {/* Globe/Logo placeholder */}
          <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gray-700 border-2 border-gray-600 flex items-center justify-center">
            <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full border-2 border-gray-500 opacity-50"></div>
          </div>
          {/* BITTEN text - military stencil style */}
          <div>
            <div className="text-3xl sm:text-4xl font-bold tracking-wider" style={{
              color: '#8b7355',
              textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
              fontFamily: 'Impact, Arial Black, sans-serif',
              letterSpacing: '0.15em'
            }}>
              {title}
            </div>
            {subtitle && (
              <div className="text-xs sm:text-sm text-green-500 mt-1">
                {subtitle}
              </div>
            )}
          </div>
        </div>

        {/* Gear icon */}
        <div className="text-gray-600">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v6m0 6v6m11-11h-6m-6 0H1m16.24 6.76l-4.24-4.24m-6 6l-4.24-4.24M19.07 19.07l-4.24-4.24m-6 6l-4.24-4.24"/>
          </svg>
        </div>
      </div>
    </div>
  );
};

export default MilitaryHeader;
