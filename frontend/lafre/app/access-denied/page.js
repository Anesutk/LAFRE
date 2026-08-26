export default function AccessDenied() {
  return (
    <main className="lafre-public-page">
      <nav className="lafre-public-nav">
        <a className="lafre-wordmark" href="/">
          <span className="brand-mark">⚖</span><strong>LAFRE</strong>
        </a>
      </nav>
      <section className="lafre-hero">
        <span className="lafre-pill">Access restricted</span>
        <h1>This account doesn't have student access.</h1>
        <p>If you believe this is a mistake, contact your administrator, or sign in with a student account instead.</p>
        <div className="lafre-hero-actions">
          <a className="lafre-brown-btn" href="/login">Sign in</a>
          <a className="lafre-light-btn" href="/">Back to home</a>
        </div>
      </section>
    </main>
  );
}
