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

        <a className="student-shell-new-chat" href="/chat">▣ New chat</a>

        <nav className="student-shell-nav" aria-label="Student navigation">
          <a className={active === 'chat' ? 'active' : ''} href="/chat">Chat</a>
          <a className={active === 'library' ? 'active' : ''} href="/library">▭ Library</a>
          <a className={active === 'flashcards' ? 'active' : ''} href="/flashcards">◆ Flashcards</a>
          <a className={active === 'usage' ? 'active' : ''} href="/usage">◔ Usage & messages</a>
          <a className={active === 'settings' ? 'active' : ''} href="/settings">⚙ Settings</a>
        </nav>
      </aside>

      <main className="study-main-page study-standalone-page" data-active={active || undefined}>
        {children}
      </main>
    </div>
  );
}
