'use client';

import React, { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import styles from './builder.module.css';

// --- Types ---
type BlockType = 'heading' | 'text' | 'container';
interface Block {
  id: string;
  type: BlockType;
  content: string;
  style: {
    color?: string;
    fontSize?: string;
    textAlign?: 'left' | 'center' | 'right';
    padding?: string;
    backgroundColor?: string;
  };
}

// --- Sortable Item Component ---
function SortableBlock({ block, selectedId, onSelect, onDelete }: { block: Block, selectedId: string | null, onSelect: (id: string) => void, onDelete: (id: string) => void }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: block.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${styles.blockWrapper} ${selectedId === block.id ? styles.selected : ''} ${isDragging ? styles.dragging : ''}`}
      onClick={(e) => { e.stopPropagation(); onSelect(block.id); }}
    >
      <div className={styles.dragHandle} {...attributes} {...listeners}>
        ☰
      </div>
      <button className={styles.deleteBtn} onClick={(e) => { e.stopPropagation(); onDelete(block.id); }}>X</button>
      
      {block.type === 'heading' && (
        <h2 style={block.style}>{block.content}</h2>
      )}
      {block.type === 'text' && (
        <p style={block.style}>{block.content}</p>
      )}
      {block.type === 'container' && (
        <div style={{ ...block.style, border: '1px solid #403c52', minHeight: '50px' }}>
          {block.content}
        </div>
      )}
    </div>
  );
}

// --- Main Page ---
export default function BuilderPage() {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    const saved = localStorage.getItem('mimic_page_builder');
    if (saved) {
      try {
        setBlocks(JSON.parse(saved));
      } catch (e) {}
    } else {
      setBlocks([
        { id: '1', type: 'heading', content: '歡迎使用視覺化編輯器', style: { color: '#eceaf2', fontSize: '32px', textAlign: 'center' } },
        { id: '2', type: 'text', content: '點擊此處即可在右側面板修改內容、顏色與大小。您可以拖曳左上角的把手來移動順序。', style: { color: '#938e9c', fontSize: '16px', textAlign: 'center' } },
      ]);
    }
  }, []);

  const saveToLocal = (newBlocks: Block[]) => {
    setBlocks(newBlocks);
    localStorage.setItem('mimic_page_builder', JSON.stringify(newBlocks));
  };

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: any) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      const oldIndex = blocks.findIndex((b) => b.id === active.id);
      const newIndex = blocks.findIndex((b) => b.id === over.id);
      saveToLocal(arrayMove(blocks, oldIndex, newIndex));
    }
  };

  const addBlock = (type: BlockType) => {
    const newBlock: Block = {
      id: Date.now().toString(),
      type,
      content: type === 'heading' ? '新標題' : type === 'text' ? '新段落文字' : '容器區塊',
      style: { color: '#eceaf2', fontSize: type === 'heading' ? '24px' : '16px' }
    };
    saveToLocal([...blocks, newBlock]);
    setSelectedId(newBlock.id);
  };

  const deleteBlock = (id: string) => {
    saveToLocal(blocks.filter(b => b.id !== id));
    if (selectedId === id) setSelectedId(null);
  };

  const updateSelectedBlock = (updates: Partial<Block> | { style: Partial<Block['style']> }) => {
    if (!selectedId) return;
    const newBlocks = blocks.map(b => {
      if (b.id === selectedId) {
        if ('style' in updates) {
          return { ...b, style: { ...b.style, ...updates.style } };
        }
        return { ...b, ...updates };
      }
      return b;
    });
    saveToLocal(newBlocks);
  };

  const selectedBlock = blocks.find(b => b.id === selectedId);

  if (!isClient) return null;

  return (
    <div className={styles.container} onClick={() => setSelectedId(null)}>
      {/* Canvas */}
      <div className={styles.canvas}>
        <div className={styles.canvasInner}>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={blocks} strategy={verticalListSortingStrategy}>
              {blocks.length === 0 ? (
                <div className={styles.emptyState}>暫無區塊，請從右側新增</div>
              ) : (
                blocks.map((block) => (
                  <SortableBlock
                    key={block.id}
                    block={block}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                    onDelete={deleteBlock}
                  />
                ))
              )}
            </SortableContext>
          </DndContext>
        </div>
      </div>

      {/* Sidebar */}
      <div className={styles.sidebar} onClick={(e) => e.stopPropagation()}>
        <div className={styles.sidebarTitle}>視覺化編輯器 (Builder)</div>
        
        <div className={styles.formGroup}>
          <label>新增區塊</label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className={`${styles.btn} ${styles.btnSecondary}`} onClick={() => addBlock('heading')}>標題</button>
            <button className={`${styles.btn} ${styles.btnSecondary}`} onClick={() => addBlock('text')}>段落</button>
            <button className={`${styles.btn} ${styles.btnSecondary}`} onClick={() => addBlock('container')}>容器</button>
          </div>
        </div>

        {selectedBlock ? (
          <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className={styles.sidebarTitle} style={{ fontSize: '1rem' }}>屬性設定 ({selectedBlock.type})</div>
            
            <div className={styles.formGroup}>
              <label>內容文字</label>
              <textarea 
                value={selectedBlock.content} 
                onChange={(e) => updateSelectedBlock({ content: e.target.value })}
                rows={4}
              />
            </div>

            <div className={styles.formGroup}>
              <label>字體大小 (px/rem)</label>
              <input 
                type="text" 
                value={selectedBlock.style.fontSize || ''} 
                onChange={(e) => updateSelectedBlock({ style: { fontSize: e.target.value } })}
              />
            </div>

            <div className={styles.formGroup}>
              <label>字體顏色</label>
              <input 
                type="color" 
                value={selectedBlock.style.color?.startsWith('#') ? selectedBlock.style.color.substring(0, 7) : '#ffffff'} 
                onChange={(e) => updateSelectedBlock({ style: { color: e.target.value } })}
                style={{ width: '100%', height: '40px', padding: '0' }}
              />
            </div>
            
            <div className={styles.formGroup}>
              <label>對齊方式</label>
              <select 
                value={selectedBlock.style.textAlign || 'left'}
                onChange={(e) => updateSelectedBlock({ style: { textAlign: e.target.value as any } })}
              >
                <option value="left">靠左 (Left)</option>
                <option value="center">置中 (Center)</option>
                <option value="right">靠右 (Right)</option>
              </select>
            </div>
          </div>
        ) : (
          <div style={{ marginTop: '20px', color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>
            請點擊左側畫布中的區塊來編輯屬性
          </div>
        )}
        
        <div style={{ marginTop: 'auto' }}>
          <button className={styles.btn} style={{ width: '100%', backgroundColor: '#2c2839', border: '1px solid #403c52' }} onClick={() => {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(blocks, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href",     dataStr);
            downloadAnchorNode.setAttribute("download", "page_layout.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
          }}>匯出 JSON 設定檔</button>
        </div>
      </div>
    </div>
  );
}
