'use client';

import { ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';
import { useTheme } from '@/hooks/useTheme';
import styles from '../app/layout.module.css';

export default function ClientShell({ children }: { children: ReactNode }) {
    const { theme, toggleTheme } = useTheme();

    return (
        <div className={styles.container}>
            <Sidebar theme={theme} onThemeToggle={toggleTheme} />
            <main className={styles.mainContent}>
                {children}
            </main>
        </div>
    );
}
