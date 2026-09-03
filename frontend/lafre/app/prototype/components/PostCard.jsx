import Link from 'next/link';
import { Icon } from './icons';
import ui from './ui.module.css';

// The star badge is not decorative - it's the platform's trust signal, so it must be
// derived strictly from the verified role, never guessed or left to default to something
// reasonable-looking. Civilians/public get no stars at all, by design.
function RoleBadge({ role }) {
  if (role === 'lawyer') return <span className={ui.starsLawyer}>★★★ Verified Lawyer</span>;
  if (role === 'student') return <span className={ui.starsStudent}>★ Law Student</span>;
  return <span className={ui.roleLabel}>Civilian</span>;
}

export default function PostCard({post, compact=false}){
 return <article className={ui.post}>
  <div className={ui.row} style={{justifyContent:'flex-start'}}><span className={ui.avatar}>{post.author[0]}</span><div><div style={{fontWeight:700,fontSize:12.5}}>{post.author} <RoleBadge role={post.role} /></div><div className={ui.muted} style={{fontSize:11}}>{post.time} · {post.category}</div></div></div>
  <Link href={`/forum/${post.id}`}><h3 className={ui.postTitle}>{post.title}</h3></Link>
  {!compact && <p className={ui.postExcerpt}>{post.excerpt}</p>}
  <div className={ui.row} style={{marginTop:12}}><div className={ui.metrics}><span>↑ {post.score}</span><span><Icon name="message" size={14}/> {post.replies}</span><span>◷ {post.views}</span></div><div className={ui.metrics}><span><Icon name="bookmark" size={14}/> Save</span><span><Icon name="share" size={14}/> Share</span></div></div>
 </article>
}
export { RoleBadge };
