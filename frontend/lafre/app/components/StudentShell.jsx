'use client';

import { useEffect } from 'react';

// Lightweight wrapper for standalone student pages (Library, Usage, Settings,
// Flashcards). These pages include their own "Back to chat" link and
// heading, so this shell intentionally stays minimal rather than duplicating
// the chat page's full sidebar. `title` keeps the browser tab title in sync;
// `active` is accepted for future nav highlighting.
export default function StudentShell({ children, title = 'LAFRE', active = '' }) {
  useEffect(() => {
    if (title) document.title = `${title} - LAFRE`;
  }, [title]);
  return <main className="study-main-page study-standalone-page" data-active={active || undefined}>{children}</main>;
}
