"use client"

import React from 'react';
import { PatternOverlay, SignalSnapshot, domainToPixels, PATTERN_REGISTRY, PatternId } from '@/lib/patterns/registry';

interface PatternOverlayRendererProps {
  patternId: PatternId;
  snapshot: SignalSnapshot;
  dimensions: { width: number; height: number };
}

export const PatternOverlayRenderer: React.FC<PatternOverlayRendererProps> = ({
  patternId,
  snapshot,
  dimensions,
}) => {
  const overlay = snapshot.overlayBase;
  const bounds = {
    xStartTs: snapshot.xStartTs,
    xEndTs: snapshot.xEndTs,
    yMin: snapshot.yMin,
    yMax: snapshot.yMax,
  };

  const pattern = PATTERN_REGISTRY[patternId];

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}>
      {/* Render Zones */}
      {overlay.zones?.map((zone, i) => {
        const topLeft = domainToPixels(zone.tStart, zone.priceTop, bounds, dimensions);
        const bottomRight = domainToPixels(zone.tEnd, zone.priceBottom, bounds, dimensions);
        const width = bottomRight.x - topLeft.x;
        const height = bottomRight.y - topLeft.y;

        return (
          <g key={`zone-${i}`}>
            <rect
              x={topLeft.x}
              y={topLeft.y}
              width={width}
              height={height}
              fill={zone.color}
              opacity={zone.opacity || 0.3}
              stroke={zone.color}
              strokeWidth="1"
            />
            <text
              x={topLeft.x + width / 2}
              y={topLeft.y + 12}
              fill={zone.color}
              fontSize="10"
              fontWeight="bold"
              textAnchor="middle"
            >
              {zone.label}
            </text>
          </g>
        );
      })}

      {/* Render Levels */}
      {overlay.levels?.map((level, i) => {
        const left = domainToPixels(bounds.xStartTs, level.price, bounds, dimensions);
        const right = domainToPixels(bounds.xEndTs, level.price, bounds, dimensions);

        return (
          <g key={`level-${i}`}>
            <line
              x1={left.x}
              y1={left.y}
              x2={right.x}
              y2={right.y}
              stroke={level.color}
              strokeWidth="2"
              strokeDasharray={level.style === 'dashed' ? '4,2' : undefined}
            />
            <text
              x={right.x - 5}
              y={right.y - 5}
              fill={level.color}
              fontSize="11"
              fontWeight="bold"
              textAnchor="end"
            >
              {level.label}
            </text>
          </g>
        );
      })}

      {/* Render Paths */}
      {overlay.paths?.map((path, i) => {
        const pathData = path.points
          .map((point, idx) => {
            const { x, y } = domainToPixels(point.t, point.price, bounds, dimensions);
            return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
          })
          .join(' ');

        const color = path.color || (path.style === 'expected' ? '#06b6d4' : '#fbbf24');

        return (
          <path
            key={`path-${i}`}
            d={pathData}
            stroke={color}
            strokeWidth="2"
            fill="none"
            strokeDasharray={path.style === 'expected' ? '4,2' : undefined}
            markerEnd="url(#arrowhead)"
          />
        );
      })}

      {/* Render Markers */}
      {overlay.markers?.map((marker, i) => {
        const pos = domainToPixels(marker.t, marker.price, bounds, dimensions);
        const color = getMarkerColor(marker.kind);

        return (
          <g key={`marker-${i}`}>
            <circle
              cx={pos.x}
              cy={pos.y}
              r="4"
              fill={color}
              stroke="#000"
              strokeWidth="1"
            />
            {marker.label && (
              <text
                x={pos.x}
                y={pos.y - 8}
                fill={color}
                fontSize="9"
                fontWeight="bold"
                textAnchor="middle"
              >
                {marker.label}
              </text>
            )}
          </g>
        );
      })}

      {/* Render Notes */}
      {overlay.notes?.map((note, i) => {
        const pos = domainToPixels(note.t, note.price, bounds, dimensions);

        return (
          <text
            key={`note-${i}`}
            x={pos.x}
            y={pos.y}
            fill="#fbbf24"
            fontSize="10"
            fontWeight="bold"
          >
            {note.text}
          </text>
        );
      })}

      {/* Arrow marker definition */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 10 3, 0 6" fill="#06b6d4" />
        </marker>
      </defs>
    </svg>
  );
};

function getMarkerColor(kind: string): string {
  switch (kind) {
    case 'sweep': return '#ef4444';
    case 'kalmanSignal': return '#10b981';
    case 'wickReject': return '#3b82f6';
    case 'vcb': return '#8b5cf6';
    case 'touch': return '#fbbf24';
    case 'midpoint': return '#06b6d4';
    case 'momentum': return '#f59e0b';
    default: return '#fbbf24';
  }
}
