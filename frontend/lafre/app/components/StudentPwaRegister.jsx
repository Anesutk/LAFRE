'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

export default function StudentPwaRegister() {
  const pathname = usePathname();

  useEffect(() => {
    if (!pathname?.startsWith('/student')) return;
    if (typeof window === 'undefined') return;
    if (!('serviceWorker' in navigator)) return;

    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .catch(() => {
        // Keep the working student app unaffected if service worker registration fails.
      });
  }, [pathname]);

  return null;
}
