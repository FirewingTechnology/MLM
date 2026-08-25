import React, { useState, useRef } from 'react';
import { BinaryTreeNode } from '../../types';
import { TreeNodeCard } from './TreeNodeCard';
import { NodeDetailModal } from './NodeDetailModal';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Search, 
  Maximize2, 
  ChevronRight, 
  Home, 
  Layers 
} from 'lucide-react';

interface BinaryTreeCanvasProps {
  rootNode: BinaryTreeNode | null;
  onSelectRootId?: (id: number | null) => void;
  depth?: number;
  onDepthChange?: (depth: number) => void;
  isLoading?: boolean;
}

export const BinaryTreeCanvas: React.FC<BinaryTreeCanvasProps> = ({
  rootNode,
  onSelectRootId,
  depth = 3,
  onDepthChange,
  isLoading,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<BinaryTreeNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.15, 1.8));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.15, 0.5));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    // Only drag on canvas background
    if ((e.target as HTMLElement).closest('button, input, .cursor-pointer')) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Recursive tree renderer
  const renderTree = (node: BinaryTreeNode | null, level: number, maxLevel: number, posLabel?: 'LEFT' | 'RIGHT' | 'ROOT') => {
    if (level > maxLevel) return null;

    return (
      <div className="flex flex-col items-center">
        {/* Node Box */}
        <TreeNodeCard
          node={node}
          positionLabel={posLabel}
          onSelectNode={(n) => setSelectedNode(n)}
          isSelected={selectedNode?.id === node?.id}
        />

        {/* Children connections */}
        {node && level < maxLevel && (
          <div className="flex flex-col items-center w-full">
            {/* Vertical connector down from parent */}
            <div className="w-0.5 h-6 bg-slate-700" />

            {/* Horizontal branch bar */}
            <div className="relative flex justify-center w-full">
              <div className="w-1/2 h-0.5 bg-slate-700" />
            </div>

            {/* Left & Right Child branches */}
            <div className="flex justify-between items-start w-full gap-8 sm:gap-14 pt-0">
              {/* Left Subtree */}
              <div className="flex flex-col items-center flex-1">
                <div className="w-0.5 h-6 bg-slate-700" />
                {renderTree(node.left || null, level + 1, maxLevel, 'LEFT')}
              </div>

              {/* Right Subtree */}
              <div className="flex flex-col items-center flex-1">
                <div className="w-0.5 h-6 bg-slate-700" />
                {renderTree(node.right || null, level + 1, maxLevel, 'RIGHT')}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="relative w-full h-[680px] rounded-2xl glass-panel overflow-hidden flex flex-col select-none border border-slate-800">
      {/* Top Controls Bar */}
      <div className="p-3.5 border-b border-slate-800/80 bg-navy-900/80 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 z-10">
        {/* Breadcrumb / Root info */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => onSelectRootId && onSelectRootId(null)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition-colors"
          >
            <Home className="w-3.5 h-3.5 text-brand-400" />
            <span>My Root Node</span>
          </button>

          {rootNode && (
            <div className="flex items-center gap-1 text-slate-400">
              <ChevronRight className="w-3.5 h-3.5" />
              <span className="font-bold text-white">{rootNode.full_name}</span>
              <span className="font-mono text-[10px] text-slate-400">({rootNode.user_code})</span>
            </div>
          )}
        </div>

        {/* Tree controls: Depth & Zoom */}
        <div className="flex items-center gap-2">
          {/* Depth selector */}
          <div className="flex items-center gap-1 bg-navy-950 p-1 rounded-lg border border-slate-800 text-xs">
            <span className="text-[10px] text-slate-400 px-1 font-semibold flex items-center gap-1">
              <Layers className="w-3 h-3" />
              Depth:
            </span>
            {[2, 3, 4].map((d) => (
              <button
                key={d}
                onClick={() => onDepthChange && onDepthChange(d)}
                className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all ${
                  depth === d
                    ? 'bg-brand-500 text-navy-950 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          {/* Zoom buttons */}
          <div className="flex items-center bg-navy-950 p-1 rounded-lg border border-slate-800 text-slate-400">
            <button
              onClick={handleZoomOut}
              className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-[10px] font-mono font-bold px-1.5 text-slate-300">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors ml-1 border-l border-slate-800 pl-2"
              title="Reset View"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Area */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`flex-1 overflow-hidden relative cursor-grab ${
          isDragging ? 'cursor-grabbing' : ''
        } bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px]`}
      >
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 rounded-full border-2 border-brand-400 border-t-transparent animate-spin" />
              <div className="text-xs text-slate-400 font-medium">Rendering Binary Tree...</div>
            </div>
          </div>
        ) : (
          <div
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'top center',
              transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            }}
            className="pt-8 pb-32 px-12 flex justify-center min-w-max"
          >
            {renderTree(rootNode, 1, depth, 'ROOT')}
          </div>
        )}
      </div>

      {/* Selected Node Inspector Modal */}
      <NodeDetailModal
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onFocusNode={(nodeId) => onSelectRootId && onSelectRootId(nodeId)}
      />
    </div>
  );
};
