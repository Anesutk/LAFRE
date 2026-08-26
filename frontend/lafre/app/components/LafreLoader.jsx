export default function LafreLoader({ module = 'LAFRE', message = 'Preparing your workspace…' }) {
  return (
    <div className="loader-screen">
      <div className="loader-mark"><span>L</span></div>
      <h1>{module}</h1>
      <p>{message}</p>
      <div className="loader-dots"><i></i><i></i><i></i></div>
    </div>
  );
}
