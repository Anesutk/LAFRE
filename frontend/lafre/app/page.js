'use client';

import { useEffect } from 'react';
import { getProfile, getToken, redirectTo } from './lib/api';

function destination(profile) {
  if (!profile) return '/login';
  if (profile.is_superuser || profile.is_staff || profile.can_access_admin || profile.role === 'admin') return '/admin';
  if (profile.role === 'lawyer' || profile.can_access_lawyer_portal) return '/dashboards/lawyer';
  if (profile.role === 'student' || profile.can_use_student) return '/chat';
  if (profile.role === 'citizen' || profile.can_use_civilian) return '/dashboards/civilian';
  return '/access-denied';
}

export default function Landing() {
  useEffect(() => {
    redirectTo(getToken() ? destination(getProfile()) : '/login');
  }, []);
  return <main style={{ padding: 40 }}>Opening your LAFRE workspace…</main>;
}
