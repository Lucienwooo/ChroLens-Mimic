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
