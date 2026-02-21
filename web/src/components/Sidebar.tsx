'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from './ThemeToggle';
import styles from './Sidebar.module.css';

interface SidebarProps {
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
}

const navGroups = [
    {
        title: '文件',
        items: [
            { href: '/', icon: '📌', label: '基本介紹' },
            { href: '/tutorial', icon: '📚', label: '使用教學' },
            { href: '/script-editor', icon: '✏️', label: '腳本編輯器' },
            { href: '/changelog', icon: '📋', label: '更新日誌' },
        ],
    },
];

const externalLinks = [
    { href: 'https://github.com/Lucienwooo/ChroLens_Mimic', label: 'GitHub', icon: '⭐' },
    { href: 'https://discord.gg/72Kbs4WPPn', label: 'Discord', icon: '💬' },
    { href: 'https://ko-fi.com/B0B51FBVA8', label: 'Ko-fi', icon: '☕' },
];

export default function Sidebar({ theme, onThemeToggle }: SidebarProps) {
    const pathname = usePathname();

    return (
        <div className={styles.sidebar}>
            {/* ── Brand ── */}
            <div className={styles.brand}>
                <a
                    className={styles.brandLink}
                    href="https://github.com/Lucienwooo/ChroLens_Mimic"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    <span style={{ fontSize: '1.5rem' }}>🎮</span>
                    <span>
                        <span className={styles.brandName}>ChroLens Mimic</span>
                        <span className={styles.brandVersion}>使用手冊</span>
                    </span>
                </a>
            </div>

            {/* ── Navigation ── */}
            <nav className={styles.nav}>
                {navGroups.map((group) => (
                    <div key={group.title} className={styles.navSection}>
                        <div className={styles.navSectionTitle}>{group.title}</div>
                        <ul className={styles.navList}>
                            {group.items.map((item) => (
                                <li key={item.href}>
                                    <Link
                                        href={item.href}
                                        className={`${styles.navLink} ${pathname === item.href ? styles.active : ''}`}
                                    >
                                        <span className={styles.navIcon}>{item.icon}</span>
                                        {item.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </nav>

            {/* ── Footer ── */}
            <div className={styles.sidebarFooter}>
                {externalLinks.map((link) => (
                    <a
                        key={link.href}
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.externalLink}
                    >
                        <span>{link.icon}</span>
                        <span>{link.label}</span>
                        <svg viewBox="0 0 16 16" fill="currentColor" style={{ marginLeft: 'auto' }}>
                            <path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z" />
                        </svg>
                    </a>
                ))}
                <ThemeToggle theme={theme} onToggle={onThemeToggle} />
            </div>
        </div>
    );
}
