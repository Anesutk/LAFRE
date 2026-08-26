export default function StatusPill({ children, tone = 'green' }) {
  const map = { green: 'pill-green', yellow: 'pill-yellow', red: 'pill-red', grey: 'pill-grey', gray: 'pill-grey' };
  return <span className={`pill ${map[tone] || 'pill-grey'}`}>{children}</span>;
}
