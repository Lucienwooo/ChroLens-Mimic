'use client';

import styles from './ThemeToggle.module.css';

interface ThemeToggleProps {
    theme: 'dark' | 'light';
    onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
    const isDark = theme === 'dark';
    return (
        <div className={styles.themeToggle}>
            <button className={styles.toggleBtn} onClick={onToggle}>
                <span className={styles.icon}>{isDark ? '🌙' : '☀️'}</span>
                <span className={styles.label}>{isDark ? '深色模式' : '淺色模式'}</span>
            </button>
        </div>
    );
}
