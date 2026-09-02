'use client';

import { useEffect } from 'react';

// Shared visual shell for standalone student pages.
// The navigation below only links to routes that already exist in the app;
// it does not introduce any new backend actions or study functionality.
export default function StudentShell({ children, title = 'LAFRE', active = '' }) {
  useEffect(() => {
    if (title) document.title = `${title} - LAFRE`;
  }, [title]);

  return (
    <div className="student-shell">
      <aside className="student-shell-sidebar">
        <div className="student-shell-brand">
          <a href="/chat" className="study-brand" aria-label="LAFRE">
            <span>⚖</span>
            <strong>LAFRE</strong>
          </a>
        </div>

        <a className="student-shell-new-chat" href="/chat"><span className="sidebar-nav-icon" aria-hidden="true">＋</span><span>New chat</span></a>

        <nav className="student-shell-nav" aria-label="Student navigation">
          <a className={active === 'chat' ? 'active' : ''} href="/chat"><span className="sidebar-nav-icon" aria-hidden="true">⌂</span><span>Chat</span></a>
          <a className={active === 'library' ? 'active' : ''} href="/library"><span className="sidebar-nav-icon" aria-hidden="true">▤</span><span>Library</span></a>
          <a className={active === 'flashcards' ? 'active' : ''} href="/flashcards"><span className="sidebar-nav-icon" aria-hidden="true">◆</span><span>Flashcards</span></a>
          <a className={active === 'usage' ? 'active' : ''} href="/usage"><span className="sidebar-nav-icon" aria-hidden="true">◔</span><span>Usage & messages</span></a>
          <a className={active === 'settings' ? 'active' : ''} href="/settings"><span className="sidebar-nav-icon" aria-hidden="true">⚙</span><span>Settings</span></a>
        </nav>
      </aside>

      <main className="study-main-page study-standalone-page" data-active={active || undefined}>
        {children}
      </main>
    </div>
  );
}
