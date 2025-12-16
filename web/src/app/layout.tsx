'use client';

import { ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';
import { useTheme } from '@/hooks/useTheme';
import './globals.css';
import styles from './layout.module.css';

export default function RootLayout({ children }: { children: ReactNode }) {
    const { theme, toggleTheme } = useTheme();

    return (
        <html lang="zh-TW">
            <head>
                <meta charSet="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>ChroLens Mimic 完整使用手冊</title>
                <script
                    type="text/javascript"
                    dangerouslySetInnerHTML={{
                        __html: `
              (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
              })(window, document, "clarity", "script", "u4so97z7de");
            `,
                    }}
                />
            </head>
            <body>
                <div className={styles.container}>
                    <Sidebar theme={theme} onThemeToggle={toggleTheme} />
                    <main className={styles.mainContent}>
                        {children}
                    </main>
                </div>
            </body>
        </html>
    );
}
