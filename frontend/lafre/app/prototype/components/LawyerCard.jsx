import Link from 'next/link';
import ui from './ui.module.css';
export default function LawyerCard({lawyer, compact=false}){
 return <div className={ui.panel+' '+ui.pad}>
   <div className={ui.row} style={{alignItems:'flex-start'}}><div className={ui.row} style={{justifyContent:'flex-start'}}><div className={ui.avatarLg}>{lawyer.name[0]}</div><div><div style={{fontFamily:"'Source Serif 4',serif",fontSize:16,fontWeight:700}}>{lawyer.name}</div><div>{lawyer.verified ? <span className={ui.starsLawyer}>★★★ Verified lawyer</span> : <span className={ui.roleLabel}>Unverified — pending admin review</span>}</div><div className={ui.muted} style={{fontSize:12,marginTop:3}}>{lawyer.area} · {lawyer.location}</div></div></div></div>
   {!compact && <><p style={{fontSize:13,lineHeight:1.6,color:'#6f6d66'}}>{lawyer.bio}</p><div className={ui.row}><span style={{fontWeight:700,fontSize:12}}>★ {lawyer.rating} <span className={ui.muted}>({lawyer.reviews})</span></span><span className={ui.tag}>{lawyer.available?'Available':'Currently busy'}</span></div></>}
   <div className={ui.btnRow} style={{marginTop:14}}><Link className={ui.outlineBtn} href={`/lawyers/${lawyer.slug}`}>View profile</Link>{!compact && <button className={ui.goldBtn} onClick={()=>alert('Mock API: connection request sent.')}>Connect</button>}</div>
 </div>
}
