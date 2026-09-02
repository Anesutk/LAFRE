import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import ui from '../prototype/components/ui.module.css';
export default function DashboardPreview(){
 const roles=[
  ['Civilian','/dashboards/civilian','My questions, legal-help requests, connections and lawyer discovery.'],
  ['Law Student ★','/dashboards/student','Forum participation, lawyer-only questions, mentorship and the existing student workspace.'],
  ['Practising Lawyer ★★★','/dashboards/lawyer','Legal-help opportunities, professional profile, messaging, forum and mentorship.'],
  ['Admin Preview','/admin-preview','Trust, verification, moderation, users, reports and platform settings.']
 ];
 return <LafreShell active="Home"><div className={ui.shell}><div className={ui.eyebrow}>Prototype role switcher</div><h1 className={ui.title}>Signed-in views.</h1><p className={ui.subtitle}>These are separate prototype dashboards showing what each LAFRE role should see after login. They use mock API records and do not change the existing authentication.</p><div className={ui.threeCol} style={{marginTop:24}}>{roles.map(r=><Link key={r[1]} href={r[1]} className={ui.panel+' '+ui.pad} style={{textDecoration:'none',color:'#111'}}><div className={ui.eyebrow}>Role view</div><h2 style={{fontSize:19,margin:'8px 0'}}>{r[0]}</h2><p className={ui.muted} style={{fontSize:13,lineHeight:1.6}}>{r[2]}</p><span className={ui.goldText} style={{fontSize:12,fontWeight:900}}>Open view →</span></Link>)}</div></div></LafreShell>
}
