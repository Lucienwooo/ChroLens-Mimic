'use client';

import styles from './ThemeToggle.module.css';

interface ThemeToggleProps {
    theme: 'dark' | 'light';
    onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
    return (
        <div className={styles.themeToggle}>
            <div
                className={`${styles.toggleButton} ${theme === 'light' ? styles.lightMode : ''}`}
                onClick={onToggle}
            >
                <span className={styles.icon}>
                    {theme === 'dark' ? '🌙' : '☀️'}
                </span>
                <div className={styles.slider}></div>
            </div>
        </div>
    );
}
