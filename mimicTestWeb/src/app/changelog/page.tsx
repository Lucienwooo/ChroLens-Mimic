'use client';

import { useState } from 'react';
import { versionData } from '@/data/versions';
import Pagination from '@/components/Pagination';
import styles from '../page.module.css';
import changelogStyles from './changelog.module.css';

const ITEMS_PER_PAGE = 10;

export default function Changelog() {
    const [currentPage, setCurrentPage] = useState(1);

    const totalPages = Math.ceil(versionData.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const currentVersions = versionData.slice(startIndex, endIndex);

    const handlePageChange = (newPage: number) => {
        setCurrentPage(newPage);
        // 滾動到頁面頂部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const renderChangeLine = (change: string) => {
        // 空行
        if (change.trim() === '') {
            return <li key={Math.random()} style={{ height: '8px' }}></li>;
        }

        // 指令語法（以 > 開頭）
        if (change.trim().startsWith('>')) {
            return (
                <li key={Math.random()} style={{ marginLeft: '20px' }}>
                    <pre className={changelogStyles.codeBlock}>
                        <code>{change}</code>
                    </pre>
                </li>
            );
        }

        // 單行格式：標題__說明
        if (change.includes('__')) {
            const parts = change.split('__');
            const title = parts[0];
            const description = parts.slice(1).join('__');
            return (
                <li key={Math.random()} style={{ listStyle: 'disc', marginLeft: '20px' }}>
                    {title}__{description}
                </li>
            );
        }

        // 檢查是否為標題（沒有全形空格開頭）
        const isTitle = !change.startsWith('　');

        if (isTitle) {
            return (
                <li key={Math.random()} style={{ listStyle: 'disc', marginLeft: '20px' }}>
                    {change}
                </li>
            );
        } else {
            return <li key={Math.random()}>{change}</li>;
        }
    };

    return (
        <div className={styles.page}>
            <h2>📋 更新日誌</h2>

            {/* 留言板區塊 */}
            <div className={changelogStyles.messageBoard}>
                <h3>💬 開發者的話</h3>
                <p>感謝各位使用 ChroLens Mimic！這裡會記錄每個版本的更新內容。</p>
                <p>如果您有任何建議、問題或發現 Bug，歡迎透過 <strong><a href="https://discord.gg/your-discord-link" target="_blank" rel="noopener noreferrer" style={{ color: '#5865F2' }}>🎮 Discord 社群</a></strong> 反饋給我們。您的每一個意見都是我們進步的動力！</p>
                <p>如果這個工具對您有幫助，歡迎 <strong><a href="https://ko-fi.com/lucienwooo" target="_blank" rel="noopener noreferrer" style={{ color: '#ff6b6b' }}>☕ 贊助支持開發</a></strong>，讓我們能持續為您帶來更好的功能！</p>
            </div>

            {/* 版本列表 */}
            <div>
                {currentVersions.map((version) => {
                    const githubUrl = `https://github.com/Lucienwooo/ChroLens_Mimic/releases/tag/${version.version}`;

                    return (
                        <div key={version.version} className={changelogStyles.versionItem}>
                            <h3>
                                <a href={githubUrl} target="_blank" rel="noopener noreferrer">
                                    📦 {version.version}
                                </a>
                            </h3>
                            <div className={changelogStyles.versionDate}>
                                發布日期：{version.date}
                            </div>
                            <ul style={{ listStyle: 'none', paddingLeft: 0 }}>
                                {version.changes.map((change, index) => (
                                    <span key={index}>{renderChangeLine(change)}</span>
                                ))}
                            </ul>
                        </div>
                    );
                })}
            </div>

            {/* 分頁 */}
            <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
            />
        </div>
    );
}
