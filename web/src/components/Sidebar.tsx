'use client';

import React from 'react';
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
      { href: '/', icon: 'home', label: '基本介紹' },
      { href: '/tutorial', icon: 'menu_book', label: '使用教學' },
      { href: '/script-editor', icon: 'edit_note', label: '腳本編輯器' },
      { href: '/changelog', icon: 'history', label: '更新日誌' },
    ],
  },
];

const externalLinks = [
  { href: 'https://github.com/Lucienwooo/ChroLens-Mimic', label: 'GitHub', icon: 'code' },
  { href: 'https://discord.gg/72Kbs4WPPn', label: 'Discord', icon: 'chat' },
];

export default function Sidebar({ theme, onThemeToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className={styles.sidebar}>
      {/* Brand */}
      <div className={styles.sidebarHeader}>
        <Link href="/" className={styles.logo}>
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>terminal</span>
          Mimic
        </Link>
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        {navGroups.map((group) => (
          <div key={group.title} className={styles.navSection}>
            <ul className={styles.navList}>
              {group.items.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`${styles.navLink} ${pathname === item.href ? styles.active : ''}`}
                  >
                    <span className="material-symbols-outlined">{item.icon}</span>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
        
        <div className={styles.navSection}>
           <div className={styles.navSectionTitle}>外部連結</div>
           <ul className={styles.navList}>
              {externalLinks.map((link) => (
                <li key={link.href}>
                   <a
                     href={link.href}
                     target="_blank"
                     rel="noopener noreferrer"
                     className={styles.navLink}
                   >
                     <span className="material-symbols-outlined">{link.icon}</span>
                     {link.label}
                   </a>
                </li>
              ))}
           </ul>
        </div>
      </nav>

      {/* Footer */}
      <div className={styles.sidebarFooter}>
        <div className={styles.statusBadge}>
          <div className={styles.pulse}></div>
          v2.7.8 OK
        </div>
        <div className={styles.themeRow}>
           <ThemeToggle theme={theme} onToggle={onThemeToggle} />
        </div>
      </div>
    </aside>
  );
}
