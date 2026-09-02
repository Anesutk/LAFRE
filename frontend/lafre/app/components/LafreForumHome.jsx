'use client';

import { useMemo, useState } from 'react';
import styles from './LafreForumHome.module.css';

const categories = ['All Discussions','Employment Law','Family Law','Criminal Law','Property Law','Contracts','Business Law','Constitutional Law'];
const posts = [
  { user:'Tendai M.', role:'Public user', cat:'Employment Law', time:'2h ago', title:'Can my employer terminate me without notice?', text:'I have been working with my company for 3 years. Yesterday I was told my services are no longer needed effective immediately. Is this legal?', replies:18, views:286, likes:42 },
  { user:'Sarah N.', role:'Public user', cat:'Property Law', time:'4h ago', title:'What rights do I have as a tenant in Zimbabwe?', text:'My landlord wants me to leave the property within 7 days without giving me a reason. What are my rights as a tenant?', replies:11, views:194, likes:27 },
  { user:'John M.', role:'Public user', cat:'Criminal Law', time:'5h ago', title:'Can a police officer search my phone without a warrant?', text:'I was stopped and asked to unlock my phone. I would like to understand the general legal position.', replies:24, views:352, likes:39 },
  { user:'Rudo K.', role:'Law Student', cat:'Constitutional Law', time:'6h ago', title:'Question for practising lawyers: interpreting constitutional rights', text:'I am a law student looking for guidance on how practising lawyers approach conflicting constitutional rights in real cases.', replies:9, views:128, likes:21, studentOnly:true },
];
const lawyers = [
  ['Adv. Tapiwa Moyo','Employment Law','Harare','4.9','128'],
  ['Adv. Brian Chikore','Commercial Law','Harare','4.8','96'],
  ['Adv. Rudo Ncube','Family Law','Bulawayo','4.9','74'],
];
const tools = [
  ['Document Checker','▤','Check a legal document for important terms and possible issues.'],
  ['Clause Checker','⌑','Find important clauses and explain what they generally mean.'],
  ['Document Explainer','◫','Turn complex legal language into easier information.'],
  ['Affidavit Drafting','✎','Create a structured starting draft with AI assistance.'],
];

export default function LafreForumHome(){
  const [category,setCategory]=useState('All Discussions');
  const [search,setSearch]=useState('');
  const [menu,setMenu]=useState(false);
  const [liked,setLiked]=useState([]);
  const [saved,setSaved]=useState([]);
  const visible=useMemo(()=>posts.filter(p=>{
    const cat=category==='All Discussions'||p.cat===category;
    const q=search.trim().toLowerCase();
    return cat && (!q || `${p.title} ${p.text} ${p.cat}`.toLowerCase().includes(q));
  }),[category,search]);
  const toggle=(setter,i)=>setter(v=>v.includes(i)?v.filter(x=>x!==i):[...v,i]);
  return <div className={styles.app}>
    <header className={styles.topbar}>
      <div className={styles.topInner}>
        <a href="/" className={styles.brand}><span className={styles.mark}>⚖</span><span><b>LAFRE</b><small>LAW · COMMUNITY · SOLUTIONS</small></span></a>
        <button className={styles.menu} onClick={()=>setMenu(!menu)}>☰</button>
        <nav className={`${styles.nav} ${menu?styles.navOpen:''}`}>
          <a className={styles.active} href="#home">Home</a><a href="#forum">Forum</a><a href="#lawyers">Find Lawyers</a><a href="#mentorship">Mentorship</a><a href="#tools">AI Tools</a><a href="#about">About</a>
        </nav>
        <div className={styles.topActions}>
          <label className={styles.search}><span>⌕</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search discussions, lawyers, topics..."/></label>
          <a href="/login" className={styles.login}>Log in</a><a href="/register" className={styles.signup}>Sign up</a>
        </div>
      </div>
    </header>

    <div className={styles.layout}>
      <aside className={`${styles.sidebar} ${menu?styles.sidebarOpen:''}`}>
        <div className={styles.sideLinks}>
          <a className={styles.sideLinkActive} href="#home">⌂ <span>Home</span></a><a href="#forum">◉ <span>Popular</span></a><a href="#forum">▤ <span>Latest discussions</span></a><a href="#lawyers">♧ <span>Find lawyers</span></a><a href="#mentorship">♙ <span>Mentorship</span></a>
        </div>
        <div className={styles.sideTitle}>LEGAL CATEGORIES</div>
        {categories.slice(1).map(c=><button key={c} onClick={()=>{setCategory(c);setMenu(false)}} className={styles.categoryLink}>⚖ <span>{c}</span></button>)}
        <div className={styles.helpBox}><b>Need legal help?</b><p>Ask a question or request to connect with a verified lawyer.</p><a href="/login" className={styles.goldBtn}>Get started</a></div>
        <p className={styles.disclaimer}>General information and community discussion. Not legal advice.</p>
      </aside>

      <main className={styles.main} id="home">
        <section className={styles.hero}>
          <div><span className={styles.eyebrow}>THE LEGAL COMMUNITY</span><h1>Ask. Discuss. <em>Connect.</em></h1><p>A professional legal community where people can ask questions, share knowledge, discover verified lawyers, and find the right next step.</p><div className={styles.heroBtns}><a href="/login" className={styles.goldBtn}>Ask a Question ↗</a><a href="#lawyers" className={styles.outlineBtn}>Find a Lawyer</a></div></div>
          <div className={styles.heroScale}>⚖<i></i></div>
        </section>

        <section id="tools" className={styles.section}>
          <div className={styles.sectionHead}><div><span className={styles.eyebrow}>ASSISTIVE AI</span><h2>Quick Legal Tools</h2></div><a href="#tools">View all tools →</a></div>
          <div className={styles.tools}>{tools.map(([n,icon,d])=><button key={n} onClick={()=>alert(`${n} is a frontend demo for now.`)}><span>{icon}</span><b>{n}</b><p>{d}</p></button>)}</div>
          <div className={styles.chatBanner}><span>✦</span><div><b>Need a quick answer?</b><p>Use the LAFRE legal chatbot for general legal information and guidance.</p></div><a href="/chat">Open LAFRE Chatbot →</a></div>
        </section>

        <section id="forum" className={styles.section}>
          <div className={styles.sectionHead}><div><span className={styles.eyebrow}>COMMUNITY</span><h2>Latest Discussions</h2></div><select><option>Latest</option><option>Most discussed</option><option>Most viewed</option></select></div>
          <div className={styles.pills}>{categories.map(c=><button key={c} className={category===c?styles.pillActive:''} onClick={()=>setCategory(c)}>{c}</button>)}</div>
          <div className={styles.feed}>{visible.map((p,i)=><article key={p.title} className={styles.post}>
            <div className={styles.vote}><button onClick={()=>toggle(setLiked,i)} className={liked.includes(i)?styles.voted:''}>↑</button><b>{p.likes+(liked.includes(i)?1:0)}</b><button>↓</button></div>
            <div className={styles.postBody}><div className={styles.meta}><span className={styles.avatar}>{p.user[0]}</span><span><b>{p.user}</b><small> · {p.role==='Law Student'?<strong className={styles.student}>★ Law Student</strong>:'Public user'} · {p.time}</small></span><button>•••</button></div><a href="#question" className={styles.postTitle}>{p.title}</a><div><span className={styles.tag}>{p.cat}</span>{p.studentOnly&&<span className={styles.lawyerOnly}>Lawyer responses only</span>}</div><p className={styles.excerpt}>{p.text}</p><div className={styles.actions}><button>◌ {p.replies} Replies</button><button>◉ {p.views}</button><button onClick={()=>toggle(setSaved,i)} className={saved.includes(i)?styles.saved:''}>♡ {saved.includes(i)?'Saved':'Save'}</button><button>↗ Share</button><a href="/login">Request Legal Help</a></div></div>
          </article>)}{!visible.length&&<div className={styles.empty}>No discussions match your current search or category.</div>}</div>
          <a href="#forum" className={styles.more}>View more discussions</a>
        </section>
      </main>

      <aside className={styles.right}>
        <section className={styles.card}><div className={styles.cardHead}><span>✦</span><b>AI Assistant</b><small>BETA</small></div><p>Get general legal information, identify a likely area of law, and discover useful next steps.</p><a href="/chat" className={styles.darkBtn}>Try LAFRE Chatbot →</a></section>
        <section className={styles.card} id="lawyers"><div className={styles.cardHead}><b>Find a Lawyer</b></div><label>Area of Law<select><option>All Areas</option><option>Employment Law</option><option>Family Law</option><option>Criminal Law</option><option>Property Law</option></select></label><label>Location<select><option>All Locations</option><option>Harare</option><option>Bulawayo</option><option>Mutare</option></select></label><a href="#lawyers-list" className={styles.goldBtn}>Search Lawyers</a></section>
        <section className={styles.card} id="lawyers-list"><div className={styles.cardHead}><b>Verified Lawyers</b><a href="#lawyers">View all →</a></div>{lawyers.map(l=><a href="#lawyers" className={styles.lawyer} key={l[0]}><span>⚖</span><div><b>{l[0]} <i>★★★</i></b><small>{l[1]} · {l[2]}</small><small>★ {l[3]} ({l[4]} reviews)</small></div></a>)}</section>
        <section className={styles.card} id="mentorship"><div className={styles.cardHead}><b>Lawyer Mentorship</b></div><p>Private professional-development programmes led by verified lawyers for law students.</p><a href="/login" className={styles.outlineBtn}>Explore Mentorship</a></section>
        <section className={styles.about} id="about"><b>What is LAFRE?</b><p>LAFRE connects the public, law students and verified practising lawyers through legal discussion, professional networking and assistive AI.</p><a href="#about">Learn more →</a></section>
      </aside>
    </div>
    <footer className={styles.footer}><span>© 2026 LAFRE</span><span>Legal community · Professional networking · AI-assisted tools</span><span>General information only · Not legal advice</span></footer>
  </div>;
}
