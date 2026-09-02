export default function Status({children='Mock API'} ){
  return <span style={{display:'inline-flex',alignItems:'center',gap:6,border:'1px solid #ded7c8',background:'#fbf8ef',color:'#806323',borderRadius:999,padding:'5px 9px',fontSize:10,fontWeight:900,letterSpacing:.5}}><span style={{width:6,height:6,borderRadius:'50%',background:'#c99222'}}></span>{children}</span>
}
