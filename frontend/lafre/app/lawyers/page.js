'use client';
import {useMemo,useState} from 'react';
import LafreShell from '../prototype/components/LafreShell';
import LawyerCard from '../prototype/components/LawyerCard';
import {lawyers} from '../prototype/mock-api';
import ui from '../prototype/components/ui.module.css';
import Status from '../prototype/components/Status';
export default function Lawyers(){
 const [q,setQ]=useState(''); const [area,setArea]=useState('All areas');
 const filtered=useMemo(()=>lawyers.filter(l=>(l.name+l.area+l.location).toLowerCase().includes(q.toLowerCase())&&(area==='All areas'||l.area===area)),[q,area]);
 return <LafreShell active="Find Lawyers"><div className={ui.shell}><div className={ui.row}><div><div className={ui.eyebrow}>Verified professionals</div><h1 className={ui.title}>Find a lawyer.</h1><p className={ui.subtitle}>Search verified practising lawyers by area, location and availability.</p></div><Status/></div>
 <div className={ui.panel+' '+ui.pad} style={{margin:'20px 0'}}><div style={{display:'grid',gridTemplateColumns:'1.5fr 1fr 160px',gap:10}}><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search lawyer, firm or location" style={{height:42,border:'1px solid #d9d5cc',borderRadius:7,padding:'0 12px'}}/><select value={area} onChange={e=>setArea(e.target.value)} style={{height:42,border:'1px solid #d9d5cc',borderRadius:7,padding:'0 10px'}}><option>All areas</option>{[...new Set(lawyers.map(l=>l.area))].map(a=><option key={a}>{a}</option>)}</select><button className={ui.goldBtn}>Search</button></div></div>
 <div className={ui.row} style={{marginBottom:12}}><b>{filtered.length} verified lawyers</b><span className={ui.muted} style={{fontSize:12}}>Organic best matches · sponsored placements can be shown separately later</span></div><div className={ui.threeCol}>{filtered.map(l=><LawyerCard key={l.slug} lawyer={l}/>)}</div>
 </div></LafreShell>
}
