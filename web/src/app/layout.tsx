import { ReactNode } from 'react';
import ClientShell from '@/components/ClientShell';
import './globals.css';

export const metadata = {
    title: 'ChroLens Mimic 完整使用手冊',
    description: '輕量級 Windows 巨集錄製與回放工具，支援腳本編輯器、圖片辨識、OCR等進階功能。',
};

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="zh-TW">
            <head>
                <meta charSet="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Geist:wght@400;500&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet" />
                <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" rel="stylesheet" />
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
                <ClientShell>{children}</ClientShell>
            </body>
        </html>
    );
}
