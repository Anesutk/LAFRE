import Link from 'next/link';
import { Icon } from './icons';
import ui from './ui.module.css';
export default function PostCard({post, compact=false}){
 return <article className={ui.post}>
  <div className={ui.row} style={{justifyContent:'flex-start'}}><span className={ui.avatar}>{post.author[0]}</span><div><div style={{fontWeight:800,fontSize:12}}>{post.author} <span className={ui.role}>{post.role==='student'?'★ Law Student':'Civilian'}</span></div><div className={ui.muted} style={{fontSize:11}}>{post.time} · {post.category}</div></div></div>
  <Link href={`/forum/${post.id}`}><h3 className={ui.postTitle}>{post.title}</h3></Link>
  {!compact && <p className={ui.postExcerpt}>{post.excerpt}</p>}
  <div className={ui.row} style={{marginTop:12}}><div className={ui.metrics}><span>↑ {post.score}</span><span><Icon name="message" size={14}/> {post.replies}</span><span>◷ {post.views}</span></div><div className={ui.metrics}><span><Icon name="bookmark" size={14}/> Save</span><span><Icon name="share" size={14}/> Share</span></div></div>
 </article>
}
