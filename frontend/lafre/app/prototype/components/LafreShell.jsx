'use client';
import Link from 'next/link';
import { useState } from 'react';
import { Icon } from './icons';
import styles from './LafreShell.module.css';

export default function LafreShell({children, role='visitor', active=''}){
  const [open, setOpen]=useState(false);
  const roleNames={visitor:'Visitor',civilian:'Civilian',student:'Law Student',lawyer:'Practising Lawyer',admin:'Admin Preview'};
  const links=[
    {href:'/',label:'Home',icon:'home'},
    {href:'/forum',label:'Forum',icon:'forum'},
    {href:'/lawyers',label:'Find Lawyers',icon:'lawyer'},
    {href:'/mentorship',label:'Mentorship',icon:'users',hide:role==='visitor'||role==='civilian'},
    {href:'/ai-tools',label:'AI Tools',icon:'tool'},
  ].filter(x=>!x.hide);
  if(role!=='visitor'){
    links.push({href:'/connections',label:'Connections',icon:'users'});
    links.push({href:'/messages',label:'Messages',icon:'message'});
  }
  if(role==='civilian') links.push({href:'/legal-help',label:'Legal Help Requests',icon:'brief'});
  if(role==='lawyer') links.push({href:'/legal-help',label:'Legal Help Requests',icon:'brief'});
  return <div className={styles.page}>
    <header className={styles.topbar}>
      <button className={styles.iconBtnMobile} onClick={()=>setOpen(!open)} aria-label="Open navigation"><Icon name="menu"/></button>
      <Link className={styles.brand} href="/"><span className={styles.brandMark}>⚖</span><span><strong>LAFRE</strong><small>LEGAL COMMUNITY</small></span></Link>
      <div className={styles.search}><Icon name="search" size={17}/><input placeholder="Search discussions, lawyers, topics..."/><kbd>/</kbd></div>
      <div className={styles.topActions}>
        {role!=='visitor' && <><Link href="/messages" className={styles.topIcon}><Icon name="message"/></Link><button className={styles.topIcon}><Icon name="bell"/></button><span className={styles.userBadge}>{roleNames[role][0]}</span></>}
        {role==='visitor' && <><Link href="/login" className={styles.ghostBtn}>Log in</Link><Link href="/register" className={styles.goldBtn}>Sign up</Link></>}
      </div>
    </header>
    <div className={styles.layout}>
      <aside className={`${styles.sidebar} ${open?styles.sidebarOpen:''}`}>
        <div className={styles.sidebarSection}>
          <p className={styles.sectionLabel}>EXPLORE</p>
          {links.map(l=><Link key={l.href} href={l.href} className={`${styles.navLink} ${active===l.label?styles.active:''}`} onClick={()=>setOpen(false)}><Icon name={l.icon}/><span>{l.label}</span></Link>)}
        </div>
        <div className={styles.sidebarSection}>
          <p className={styles.sectionLabel}>LEGAL TOPICS</p>
          {['Employment Law','Family Law','Criminal Law','Property Law','Contracts','Business Law','Constitutional Law'].map(x=><Link key={x} href={`/forum?category=${encodeURIComponent(x)}`} className={styles.topic}>{x}</Link>)}
        </div>
        {role!=='visitor' && <div className={styles.sidebarSection}>
          <p className={styles.sectionLabel}>MY LAFRE</p>
          <Link className={styles.topic} href={role==='lawyer'?'/dashboards/lawyer':role==='student'?'/dashboards/student':'/dashboards/civilian'}>My dashboard</Link>
          <Link className={styles.topic} href="/profile">Profile</Link>
        </div>}
        {role==='visitor' && <div className={styles.helpPanel}><span className={styles.goldDot}></span><strong>Need legal help?</strong><p>Ask a question, explore the forum, or find a verified lawyer.</p><Link href="/login" className={styles.fullGold}>Get started</Link></div>}
      </aside>
      <main className={styles.content}>{children}</main>
    </div>
  </div>
}

export function RoleSwitcher({current}){
  return <div className={styles.roleSwitcher}><span>Prototype view</span><Link href="/dashboards/civilian">Civilian</Link><Link href="/dashboards/student">Student</Link><Link href="/dashboards/lawyer">Lawyer</Link></div>
}

export {styles};
