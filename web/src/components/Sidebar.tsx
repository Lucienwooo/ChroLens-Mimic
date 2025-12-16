'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from './ThemeToggle';
import styles from './Sidebar.module.css';

interface SidebarProps {
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
}

export default function Sidebar({ theme, onThemeToggle }: SidebarProps) {
    const pathname = usePathname();

    const navItems = [
        { href: '/', label: '📌 基本介紹', id: 'intro' },
        { href: '/script-editor', label: '✏️ 腳本編輯器', id: 'script-editor' },
        { href: '/changelog', label: '📋 更新日誌', id: 'changelog' },
    ];

    return (
        <div className={styles.sidebar}>
            <h1>
                <a href="https://github.com/Lucienwooo/ChroLens_Mimic" target="_blank" rel="noopener noreferrer">
                    📖 ChroLens Mimic
                </a>
            </h1>
            <nav>
                <ul>
                    {navItems.map((item) => (
                        <li key={item.id}>
                            <Link
                                href={item.href}
                                className={pathname === item.href ? styles.active : ''}
                            >
                                {item.label}
                            </Link>
                        </li>
                    ))}
                </ul>
            </nav>
            <ThemeToggle theme={theme} onToggle={onThemeToggle} />
        </div>
    );
}
