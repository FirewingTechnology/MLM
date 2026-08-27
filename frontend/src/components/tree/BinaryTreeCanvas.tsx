import React, { useState, useRef, useEffect } from 'react';
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
  ChevronLeft,
  ArrowLeft,
  ArrowRight,
  Home, 
  Layers,
  Sparkles 
} from 'lucide-react';

interface BinaryTreeCanvasProps {
  rootNode: BinaryTreeNode | null;
  onSelectRootId?: (id: number | null) => void;
  depth?: number;
  onDepthChange?: (depth: number) => void;
  isLoading?: boolean;
  onPrevUser?: () => void;
  onNextUser?: () => void;
  prevUser?: any;
  nextUser?: any;
  currentIndex?: number;
  totalMembers?: number;
  viewMode?: 'network' | 'active_slot' | 'history';
}

export const BinaryTreeCanvas: React.FC<BinaryTreeCanvasProps> = ({
  rootNode,
  onSelectRootId,
  depth = 3,
  onDepthChange,
  isLoading,
  onPrevUser,
  onNextUser,
  prevUser,
  nextUser,
  currentIndex,
  totalMembers,
  viewMode = 'network',
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<BinaryTreeNode | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation for previous/next user
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;
      if (selectedNode) return;

      if (e.key === 'ArrowLeft' && onPrevUser && prevUser) {
        e.preventDefault();
        onPrevUser();
      } else if (e.key === 'ArrowRight' && onNextUser && nextUser) {
        e.preventDefault();
        onNextUser();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onPrevUser, onNextUser, prevUser, nextUser, selectedNode]);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.15, 1.8));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.15, 0.5));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
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

  // Recursive tree renderer with curved SVG branch connectors
  const renderTree = (node: BinaryTreeNode | null, level: number, maxLevel: number, posLabel?: 'LEFT' | 'RIGHT' | 'ROOT') => {
    if (level > maxLevel) return null;

    const hasLeft = node && node.left;
    const hasRight = node && node.right;

    return (
      <div className="flex flex-col items-center">
        {/* Node Card */}
        <TreeNodeCard
          node={node}
          positionLabel={posLabel}
          onSelectNode={(n) => setSelectedNode(n)}
          isSelected={selectedNode?.id === node?.id}
          viewMode={viewMode}
        />

        {/* Children connections with curved SVG aesthetics */}
        {node && level < maxLevel && (
          <div className="flex flex-col items-center w-full">
            {/* Smooth curved connector down to children */}
            <div className="w-full flex justify-center py-1">
              <svg className="w-full h-10 overflow-visible" style={{ minWidth: '240px' }} preserveAspectRatio="none">
                <defs>
                  <linearGradient id={`gradLeft-${node.id}`} x1="50%" y1="0%" x2="25%" y2="100%">
                    <stop offset="0%" stopColor="#C9A227" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#063B32" stopOpacity="0.9" />
                  </linearGradient>
                  <linearGradient id={`gradRight-${node.id}`} x1="50%" y1="0%" x2="75%" y2="100%">
                    <stop offset="0%" stopColor="#C9A227" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#063B32" stopOpacity="0.9" />
                  </linearGradient>
                </defs>

                {/* Left Branch Curve */}
                <path
                  d="M 50% 0 C 50% 20, 25% 15, 25% 40"
                  fill="none"
                  stroke={hasLeft ? `url(#gradLeft-${node.id})` : '#D3CCA9'}
                  strokeWidth="2"
                  strokeDasharray={hasLeft ? 'none' : '4 3'}
                />

                {/* Right Branch Curve */}
                <path
                  d="M 50% 0 C 50% 20, 75% 15, 75% 40"
                  fill="none"
                  stroke={hasRight ? `url(#gradRight-${node.id})` : '#D3CCA9'}
                  strokeWidth="2"
                  strokeDasharray={hasRight ? 'none' : '4 3'}
                />

                {/* Center junction dot */}
                <circle cx="50%" cy="0" r="3" fill="#C9A227" />
              </svg>
            </div>

            {/* Left & Right Child branches container */}
            <div className="flex justify-between items-start w-full gap-8 sm:gap-14 pt-0">
              {/* Left Subtree */}
              <div className="flex flex-col items-center flex-1">
                {renderTree(node.left || null, level + 1, maxLevel, 'LEFT')}
              </div>

              {/* Right Subtree */}
              <div className="flex flex-col items-center flex-1">
                {renderTree(node.right || null, level + 1, maxLevel, 'RIGHT')}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="relative w-full h-[700px] rounded-3xl bg-[#FFFEF9] overflow-hidden flex flex-col select-none border border-[#E5E0D3] shadow-wealth-card">
      {/* Top Controls Bar */}
      <div className="p-3.5 border-b border-[#E5E0D3] bg-[#FFFEF9]/95 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 z-10">
        {/* Breadcrumb / Root info */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => onSelectRootId && onSelectRootId(null)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F7F4EC] hover:bg-[#EFECE2] text-[#18211F] font-semibold transition-colors cursor-pointer border border-[#E5E0D3]"
          >
            <Home className="w-3.5 h-3.5 text-[#063B32]" />
            <span>My Root Node</span>
          </button>

          {rootNode && (
            <div className="flex items-center gap-1 text-[#69736F]">
              <ChevronRight className="w-3.5 h-3.5 text-[#C9A227]" />
              <span className="font-heading font-bold text-[#18211F]">{rootNode.full_name}</span>
              <span className="font-mono text-[10px] text-[#063B32] font-bold">({rootNode.user_code})</span>
            </div>
          )}
        </div>

        {/* Center/Right Controls: User Navigation, Depth & Zoom */}
        <div className="flex flex-wrap items-center gap-2">
          {/* User Navigation: Prev / Next */}
          {(onPrevUser || onNextUser) && (
            <div className="flex items-center bg-[#F7F4EC] p-1 rounded-xl border border-[#E5E0D3] text-xs">
              <button
                onClick={onPrevUser}
                disabled={!prevUser}
                title={prevUser ? `Previous User: ${prevUser.full_name} (${prevUser.user_code})` : 'No previous user'}
                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${
                  prevUser
                    ? 'hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] cursor-pointer font-bold'
                    : 'text-[#C9C4B7] cursor-not-allowed opacity-40'
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
                <span className="text-[11px] hidden md:inline">Prev</span>
              </button>

              {currentIndex !== undefined && totalMembers !== undefined && (
                <span className="text-[10px] font-mono text-[#063B32] px-2 font-bold">
                  {currentIndex >= 0 ? `${currentIndex + 1}/${totalMembers}` : 'Root'}
                </span>
              )}

              <button
                onClick={onNextUser}
                disabled={!nextUser}
                title={nextUser ? `Next User: ${nextUser.full_name} (${nextUser.user_code})` : 'No next user'}
                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${
                  nextUser
                    ? 'hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] cursor-pointer font-bold'
                    : 'text-[#C9C4B7] cursor-not-allowed opacity-40'
                }`}
              >
                <span className="text-[11px] hidden md:inline">Next</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Depth selector */}
          <div className="flex items-center gap-1 bg-[#F7F4EC] p-1 rounded-xl border border-[#E5E0D3] text-xs">
            <span className="text-[10px] text-[#69736F] px-1 font-semibold flex items-center gap-1">
              <Layers className="w-3 h-3 text-[#063B32]" />
              Depth:
            </span>
            {[2, 3, 4].map((d) => (
              <button
                key={d}
                onClick={() => onDepthChange && onDepthChange(d)}
                className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                  depth === d
                    ? 'bg-[#063B32] text-[#FFFEF9] shadow-xs'
                    : 'text-[#69736F] hover:text-[#18211F]'
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          {/* Zoom buttons */}
          <div className="flex items-center bg-[#F7F4EC] p-1 rounded-xl border border-[#E5E0D3] text-[#69736F]">
            <button
              onClick={handleZoomOut}
              className="p-1.5 hover:text-[#18211F] hover:bg-[#EFECE2] rounded-lg transition-colors cursor-pointer"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-[10px] font-mono font-bold px-1.5 text-[#18211F]">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 hover:text-[#18211F] hover:bg-[#EFECE2] rounded-lg transition-colors cursor-pointer"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              className="p-1.5 hover:text-[#18211F] hover:bg-[#EFECE2] rounded-lg transition-colors ml-1 border-l border-[#E5E0D3] pl-2 cursor-pointer"
              title="Reset View"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Area with Warm Paper Radial Dot Pattern */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`flex-1 overflow-hidden relative cursor-grab bg-[#F7F4EC] ${
          isDragging ? 'cursor-grabbing' : ''
        } bg-[radial-gradient(#D3CCA9_1.2px,transparent_1.2px)] [background-size:24px_24px]`}
      >
        {/* Floating Left Arrow Overlay (Previous User) */}
        {onPrevUser && prevUser && (
          <button
            onClick={onPrevUser}
            title={`Previous User: ${prevUser.full_name} (${prevUser.user_code})`}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-20 px-3.5 py-2.5 rounded-2xl bg-[#FFFEF9]/95 hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] border border-[#E5E0D3] shadow-wealth-elevated flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95 group backdrop-blur-md cursor-pointer"
          >
            <ChevronLeft className="w-5 h-5 text-[#C9A227] group-hover:text-[#E2C766] transition-colors" />
            <span className="text-[11px] font-bold hidden lg:inline font-sans">{prevUser.full_name}</span>
          </button>
        )}

        {/* Floating Right Arrow Overlay (Next User) */}
        {onNextUser && nextUser && (
          <button
            onClick={onNextUser}
            title={`Next User: ${nextUser.full_name} (${nextUser.user_code})`}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-20 px-3.5 py-2.5 rounded-2xl bg-[#FFFEF9]/95 hover:bg-[#063B32] hover:text-[#FFFEF9] text-[#18211F] border border-[#E5E0D3] shadow-wealth-elevated flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95 group backdrop-blur-md cursor-pointer"
          >
            <span className="text-[11px] font-bold hidden lg:inline font-sans">{nextUser.full_name}</span>
            <ChevronRight className="w-5 h-5 text-[#C9A227] group-hover:text-[#E2C766] transition-colors" />
          </button>
        )}

        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 rounded-full border-2 border-[#063B32] border-t-[#C9A227] animate-spin" />
              <div className="text-xs text-[#69736F] font-medium">Rendering Wealth Network...</div>
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

