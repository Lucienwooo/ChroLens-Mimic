'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
    const [isExpanded, setIsExpanded] = useState(false);
    const [isVideoReady, setIsVideoReady] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // 如果沒有影片來源，不顯示任何內容
    if (!youtubeId && !videoSrc && !thumbnail) {
        return null;
    }

    // 自動生成 YouTube 縮圖
    const thumbnailUrl = thumbnail ||
        (youtubeId ? `https://img.youtube.com/vi/${youtubeId}/hqdefault.jpg` : undefined);

    const handleExpand = useCallback(() => {
        if (youtubeId || videoSrc) {
            setIsExpanded(true);
            // 延遲載入影片
            setTimeout(() => setIsVideoReady(true), 100);
        }
    }, [youtubeId, videoSrc]);

    const handleCollapse = useCallback(() => {
        setIsVideoReady(false);
        setIsExpanded(false);
    }, []);

    // 點擊外部區域時收起
    useEffect(() => {
        if (!isExpanded) return;

        const handleClickOutside = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                handleCollapse();
            }
        };

        // 延遲綁定，避免立即觸發
        const timer = setTimeout(() => {
            document.addEventListener('click', handleClickOutside);
        }, 100);

        return () => {
            clearTimeout(timer);
            document.removeEventListener('click', handleClickOutside);
        };
    }, [isExpanded, handleCollapse]);

    // ESC 鍵收起
    useEffect(() => {
        if (!isExpanded) return;
        
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                handleCollapse();
            }
        };
        
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isExpanded, handleCollapse]);

    const hasVideo = youtubeId || videoSrc;

    return (
        <div 
            ref={containerRef}
            className={`${styles.container} ${isExpanded ? styles.expanded : ''}`}
        >
            {/* 未展開時顯示縮圖 */}
            {!isExpanded && (
                <div
                    className={`${styles.preview} ${hasVideo ? styles.clickable : ''}`}
                    onClick={handleExpand}
                    role={hasVideo ? "button" : undefined}
                    tabIndex={hasVideo ? 0 : undefined}
                    onKeyDown={(e) => e.key === 'Enter' && handleExpand()}
                    aria-label={hasVideo ? `播放${title}` : title}
                >
                    {thumbnailUrl ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
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

                    {hasVideo && (
                        <div className={styles.playButton}>
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M8 5v14l11-7z" />
                            </svg>
                        </div>
                    )}
                </div>
            )}

            {/* 展開時顯示影片 */}
            {isExpanded && (
                <div className={styles.videoWrapper}>
                    {/* 收起按鈕 */}
                    <button
                        className={styles.collapseButton}
                        onClick={handleCollapse}
                        aria-label="收起"
                        type="button"
                    >
                        ✕ 收起
                    </button>

                    {/* 影片內容 */}
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

                    {/* 載入中 */}
                    {!isVideoReady && (
                        <div className={styles.loading}>
                            <span>載入中...</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
