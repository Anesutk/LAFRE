'use client';
import {useState} from 'react';
import ui from './ui.module.css';
export default function QuestionComposer(){
 const [posted,setPosted]=useState(false);
 return <div className={ui.panel+' '+ui.pad}>
  <div className={ui.eyebrow}>Start a discussion</div><h2 style={{fontSize:21,margin:'7px 0'}}>Ask a legal question</h2>
  <textarea placeholder="Explain your situation in your own words..." style={{width:'100%',minHeight:135,resize:'vertical',border:'1px solid #d9d5cc',borderRadius:8,padding:13,fontSize:14,fontFamily:'inherit',outline:0,background:'#fff'}}/>
  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,marginTop:10}}><select defaultValue="" style={{height:42,border:'1px solid #d9d5cc',borderRadius:7,padding:'0 10px',background:'#fff'}}><option value="">Area of law</option><option>Employment Law</option><option>Family Law</option><option>Criminal Law</option><option>Property Law</option><option>Contracts</option></select><select defaultValue="" style={{height:42,border:'1px solid #d9d5cc',borderRadius:7,padding:'0 10px',background:'#fff'}}><option value="">Location (optional)</option><option>Harare</option><option>Bulawayo</option><option>Mutare</option></select></div>
  <label style={{display:'flex',gap:8,alignItems:'center',fontSize:12,fontWeight:800,margin:'14px 0'}}><input type="checkbox" defaultChecked/> Make this public</label>
  <button className={ui.goldBtn} style={{width:'100%'}} onClick={()=>setPosted(true)}>{posted?'Question saved as demo':'Post question'}</button>
  <p className={ui.muted} style={{fontSize:11,marginTop:9}}>Mock frontend only. No data is sent to a backend.</p>
 </div>
}
