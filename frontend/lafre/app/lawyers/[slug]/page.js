'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch } from '../../lib/api';
import ui from '../../prototype/components/ui.module.css';

export default function LawyerDetailPage() {
  const { slug } = useParams();
  const [lawyer, setLawyer] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { if (slug) apiFetch(`/forum/lawyers/${slug}/`).then((result) => setLawyer(result.lawyer)).catch((err) => setError(err.message || 'Could not load this profile.')); }, [slug]);
  return <LafreShell active="Find Lawyers"><div className={ui.shell}>{error && <div className={ui.panel + ' ' + ui.pad}><p>{error}</p></div>}{lawyer && <><Link href="/lawyers" className={ui.goldText}>← All lawyers</Link><div className={ui.eyebrow} style={{ marginTop: 24 }}>{lawyer.location || 'Location not listed'}</div><h1 className={ui.title}>{lawyer.full_name}</h1><p className={ui.subtitle}>{lawyer.firm_name || 'Independent practice'} · {lawyer.practice_area || 'Legal services'}</p><section className={ui.panel + ' ' + ui.pad}><p>{lawyer.bio || 'No biography has been provided.'}</p><p className={ui.muted}>{lawyer.years_experience || 0} years of experience · {lawyer.public_email || 'Contact details available on request'}</p></section></>}{!lawyer && !error && <p>Loading profile…</p>}</div></LafreShell>;
}
