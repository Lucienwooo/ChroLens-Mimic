'use client';

import React, { useState } from 'react';
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

    // 如果沒有影片來源，不顯示任何內容
    if (!youtubeId && !videoSrc && !thumbnail) {
        return null;
    }

    // 自動生成 YouTube 縮圖
    const thumbnailUrl = thumbnail ||
        (youtubeId ? `https://img.youtube.com/vi/${youtubeId}/hqdefault.jpg` : undefined);

    const handleOpen = () => {
        if (youtubeId || videoSrc) {
            setIsOpen(true);
        }
    };

    const handleClose = () => {
        setIsOpen(false);
    };

    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            handleClose();
        }
    };

    const hasVideo = youtubeId || videoSrc;

    return (
        <>
            {/* 縮圖預覽 */}
            <div
                className={`${styles.preview} ${hasVideo ? styles.clickable : ''}`}
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

                {hasVideo && (
                    <div className={styles.playButton}>
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M8 5v14l11-7z" />
                        </svg>
                    </div>
                )}
            </div>

            {/* 模態框 */}
            {isOpen && (
                <div className={styles.modal} onClick={handleBackdropClick}>
                    <div className={styles.modalContent}>
                        <button
                            className={styles.closeButton}
                            onClick={handleClose}
                            aria-label="關閉"
                        >
                            ✕
                        </button>

                        {youtubeId ? (
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
                        ) : null}
                    </div>
                </div>
            )}
        </>
    );
}
