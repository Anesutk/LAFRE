import Link from 'next/link';
import ui from './ui.module.css';
export default function LawyerCard({lawyer, compact=false}){
 return <div className={ui.panel+' '+ui.pad}>
   <div className={ui.row} style={{alignItems:'flex-start'}}><div className={ui.row} style={{justifyContent:'flex-start'}}><div className={ui.avatarLg}>{lawyer.name[0]}</div><div><div style={{fontSize:16,fontWeight:900}}>{lawyer.name}</div><div className={ui.stars}>★★★ <span style={{color:'#777',letterSpacing:0}}>Verified lawyer</span></div><div className={ui.muted} style={{fontSize:12,marginTop:3}}>{lawyer.area} · {lawyer.location}</div></div></div></div>
   {!compact && <><p style={{fontSize:13,lineHeight:1.55,color:'#5f5b54'}}>{lawyer.bio}</p><div className={ui.row}><span style={{fontWeight:800,fontSize:12}}>★ {lawyer.rating} <span className={ui.muted}>({lawyer.reviews})</span></span><span className={ui.tag}>{lawyer.available?'Available':'Currently busy'}</span></div></>}
   <div className={ui.btnRow} style={{marginTop:14}}><Link className={ui.outlineBtn} href={`/lawyers/${lawyer.slug}`}>View profile</Link>{!compact && <button className={ui.goldBtn} onClick={()=>alert('Mock API: connection request sent.')}>Connect</button>}</div>
 </div>
}
