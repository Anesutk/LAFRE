'use client';
import {useState} from 'react';
import LafreShell from '../prototype/components/LafreShell';
import ui from '../prototype/components/ui.module.css';
export default function Profile(){
 const [saved,setSaved]=useState(false);
 return <LafreShell active="Home" role="civilian"><div className={ui.shell}><div className={ui.eyebrow}>Prototype profile</div><h1 className={ui.title}>Your profile.</h1><div className={ui.panel+' '+ui.pad} style={{maxWidth:760,marginTop:18}}><div className={ui.row} style={{justifyContent:'flex-start'}}><div className={ui.avatarLg}>T</div><div><h2 style={{margin:0,fontSize:21}}>Tendai M.</h2><div className={ui.muted} style={{fontSize:12}}>Civilian · public username</div></div></div><div className={ui.divider}/><div style={{display:'grid',gap:12}}><label style={{fontSize:12,fontWeight:850}}>Username<input defaultValue="@tendaim" style={{display:'block',width:'100%',height:42,marginTop:6,border:'1px solid #d9d5cc',borderRadius:7,padding:'0 11px'}}/></label><label style={{fontSize:12,fontWeight:850}}>Bio<textarea defaultValue="Legal community member." style={{display:'block',width:'100%',minHeight:95,marginTop:6,border:'1px solid #d9d5cc',borderRadius:7,padding:11}}/></label><button className={ui.goldBtn} onClick={()=>setSaved(true)}>{saved?'Saved in mock API':'Save profile'}</button></div></div></div></LafreShell>
}
