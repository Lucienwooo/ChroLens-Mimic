'use client';

import React, { useState, useEffect, useCallback } from 'react';
import styles from './VideoPreview.module.css';

interface VideoPreviewProps {
    /** 縮圖圖片路徑 */
    thumbnail?: string;
    /** YouTube 影片 ID */
    youtubeId?: string;
    /** 本地影片路徑 */
    videoSrc?: string;
    /** 標題（用於無障礙） */
    title?: string;
}

export default function VideoPreview({
    thumbnail,
    youtubeId,
    videoSrc,
    title = '影片預覽'
}: VideoPreviewProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isVideoReady, setIsVideoReady] = useState(false);

    // 如果沒有影片來源，不顯示任何內容
    if (!youtubeId && !videoSrc && !thumbnail) {
        return null;
    }

    // 自動生成 YouTube 縮圖
    const thumbnailUrl = thumbnail ||
        (youtubeId ? `https://img.youtube.com/vi/${youtubeId}/hqdefault.jpg` : undefined);

    const handleOpen = useCallback(() => {
        if (youtubeId || videoSrc) {
            setIsOpen(true);
            // 延遲載入影片，避免模態框開啟瞬間的閃爍
            setTimeout(() => setIsVideoReady(true), 100);
        }
    }, [youtubeId, videoSrc]);

    const handleClose = useCallback(() => {
        setIsVideoReady(false);
        setIsOpen(false);
    }, []);

    const handleBackdropClick = useCallback((e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            handleClose();
        }
    }, [handleClose]);

    // ESC 鍵關閉
    useEffect(() => {
        if (!isOpen) return;
        
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                handleClose();
            }
        };
        
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, handleClose]);

    const hasVideo = youtubeId || videoSrc;

    return (
        <>
            {/* 縮圖預覽 - 模態框開啟時停止 hover 效果 */}
            <div
                className={`${styles.preview} ${hasVideo && !isOpen ? styles.clickable : ''}`}
                onClick={handleOpen}
                role={hasVideo ? "button" : undefined}
                tabIndex={hasVideo ? 0 : undefined}
                onKeyDown={(e) => e.key === 'Enter' && handleOpen()}
                aria-label={hasVideo ? `播放${title}` : title}
            >
                {thumbnailUrl ? (
                    <img
                        src={thumbnailUrl}
                        alt={title}
                        className={styles.thumbnail}
                    />
                ) : (
                    <div className={styles.placeholder}>
                        <span>🎬</span>
                    </div>
                )}

                {hasVideo && !isOpen && (
                    <div className={styles.playButton}>
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M8 5v14l11-7z" />
                        </svg>
                    </div>
                )}
            </div>

            {/* 模態框 - 使用 contain 優化重繪 */}
            {isOpen && (
                <div 
                    className={styles.modal} 
                    onClick={handleBackdropClick}
                    role="dialog"
                    aria-modal="true"
                    aria-label={title}
                >
                    <div className={styles.modalContent}>
                        <button
                            className={styles.closeButton}
                            onClick={handleClose}
                            aria-label="關閉"
                            type="button"
                        >
                            ✕
                        </button>

                        {/* 延遲載入影片內容，避免閃爍 */}
                        {isVideoReady && (
                            youtubeId ? (
                                <iframe
                                    src={`https://www.youtube.com/embed/${youtubeId}?autoplay=1`}
                                    title={title}
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                    className={styles.video}
                                />
                            ) : videoSrc ? (
                                <video
                                    src={videoSrc}
                                    controls
                                    autoPlay
                                    className={styles.video}
                                >
                                    您的瀏覽器不支援影片播放
                                </video>
                            ) : null
                        )}
                        
                        {/* 載入中提示 */}
                        {!isVideoReady && (
                            <div className={styles.loading}>
                                <span>載入中...</span>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
