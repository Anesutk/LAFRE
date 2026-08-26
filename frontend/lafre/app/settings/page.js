'use client';
import { useEffect, useState } from 'react';
import StudentShell from '../components/StudentShell';

export default function StudentSettings() {
  const [profile, setProfile] = useState(null);
  useEffect(() => { setProfile(getProfile()); document.title = 'Settings - LAFRE'; }, []);
  return <StudentShell active="settings" title="Settings">
    <section className="warm-page-copy"><a href="/chat" className="warm-back">← Back to chat</a><h1>Settings</h1><p>Manage your student profile and study workspace.</p></section>
    <section className="warm-account-card"><h2>Profile</h2><dl><dt>Name</dt><dd>{profile?.full_name || 'Demo Student'}</dd><dt>Email</dt><dd>{profile?.email || 'student@lafre.demo'}</dd><dt>Institution</dt><dd>{profile?.institution || 'LAFRE Law School'}</dd><dt>Status</dt><dd>{profile?.status || 'Approved'}</dd></dl></section>
    <section className="warm-empty-card"><h2>Study behaviour</h2><p>LAFRE searches the legal knowledge base and your uploaded documents, then explains the same legal meaning clearly in its own words. Sources are shown below responses as clean badges.</p></section>
  </StudentShell>;
}
