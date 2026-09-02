export const posts = [
  { id:'p1', title:'Can my employer terminate me without notice?', excerpt:'I have worked for the company for three years. Yesterday HR told me my services are no longer needed. What rights do I have?', category:'Employment Law', author:'Tendai M.', role:'civilian', time:'2h ago', replies:18, views:312, score:142 },
  { id:'p2', title:'What rights do I have as a tenant in Zimbabwe?', excerpt:'My landlord wants me to leave the property within seven days without giving a clear reason. What should I know?', category:'Property Law', author:'Sarah N.', role:'civilian', time:'4h ago', replies:11, views:191, score:96 },
  { id:'p3', title:'Can a police officer search my phone without a warrant?', excerpt:'I was stopped yesterday and asked to unlock my phone. I would like to understand the general legal position.', category:'Criminal Law', author:'John M.', role:'civilian', time:'5h ago', replies:15, views:264, score:121 },
  { id:'p4', title:'How should I approach a research problem for my dissertation?', excerpt:'I am struggling to narrow my research question and would appreciate guidance from practising lawyers.', category:'Student Question', author:'Rudo K.', role:'student', time:'7h ago', replies:6, views:87, score:44 },
  { id:'p5', title:'What should I check before signing a consultancy agreement?', excerpt:'I have been sent an independent contractor agreement and want to understand the areas that usually deserve attention.', category:'Contracts', author:'Munashe P.', role:'civilian', time:'9h ago', replies:9, views:144, score:77 },
];

export const lawyers = [
  { slug:'tapiwa-moyo', name:'Tapiwa Moyo', firm:'Moyo Legal Practice', area:'Employment Law', location:'Harare', experience:'8+ years', rating:'4.9', reviews:128, available:true, mentorship:true, verified:true, bio:'Employment lawyer focused on workplace disputes, contracts, dismissal matters and practical dispute resolution.' },
  { slug:'brian-chikore', name:'Brian Chikore', firm:'Chikore Chambers', area:'Commercial Law', location:'Harare', experience:'11 years', rating:'4.8', reviews:96, available:true, mentorship:true, verified:true, bio:'Commercial and contract lawyer advising businesses on transactions, agreements and disputes.' },
  { slug:'rudo-ncube', name:'Rudo Ncube', firm:'Ncube Attorneys', area:'Family Law', location:'Bulawayo', experience:'6 years', rating:'4.9', reviews:74, available:false, mentorship:true, verified:true, bio:'Family lawyer working across family disputes, maintenance, estates and related proceedings.' },
  { slug:'adrian-chikore', name:'Adv. Brian Chikore', firm:'Chikore Chambers', area:'Constitutional Law', location:'Harare', experience:'12 years', rating:'5.0', reviews:51, available:true, mentorship:false, verified:true, bio:'Advocate with a practice focused on constitutional, public-law and complex litigation matters.' },
];

export const requests = [
  { id:'lh1', title:'Employment dispute after role change', area:'Employment Law', location:'Harare', summary:'User says their signed offer and actual pay do not match after starting a new role.', posted:'32 min ago', matches:4, status:'Open' },
  { id:'lh2', title:'Tenant notice and threatened eviction', area:'Property Law', location:'Chitungwiza', summary:'Tenant is seeking a lawyer to review a notice and advise on next steps.', posted:'2h ago', matches:3, status:'Open' },
  { id:'lh3', title:'Contract review before signing', area:'Contracts', location:'Harare', summary:'User wants professional review of a consultancy agreement before signing.', posted:'5h ago', matches:6, status:'Open' },
];

export const messages = [
  { id:'m1', name:'Tapiwa Moyo', role:'lawyer', preview:'I saw your legal-help request. I may be able to assist with the employment matter.', time:'9:42' },
  { id:'m2', name:'Rudo K.', role:'student', preview:'Thanks for connecting. Are you still offering the mentorship programme?', time:'Yesterday' },
  { id:'m3', name:'Brian Chikore', role:'lawyer', preview:'Happy to connect. I can share more about commercial practice.', time:'Tue' },
];

export const mentorship = [
  { id:'ment1', title:'Career Guidance in Law', mentor:'Adv. Brian Chikore', area:'Career Development', students:12, weeks:6, description:'A private programme covering practice areas, CVs, interviews, professional conduct and early legal careers.' },
  { id:'ment2', title:'Starting Your Legal Career', mentor:'Tapiwa Moyo', area:'Professional Development', students:8, weeks:4, description:'Practical discussions about law-firm life, client work, workplace skills and building a sustainable legal career.' },
];

const wait = (value, ms = 180) => new Promise(resolve => setTimeout(() => resolve(value), ms));
export const mockApi = {
  getPosts: () => wait(posts),
  getPost: (id) => wait(posts.find(p => p.id === id) || posts[0]),
  getLawyers: () => wait(lawyers),
  getLawyer: (slug) => wait(lawyers.find(l => l.slug === slug) || lawyers[0]),
  getRequests: () => wait(requests),
  getMessages: () => wait(messages),
  getMentorship: () => wait(mentorship),
};
