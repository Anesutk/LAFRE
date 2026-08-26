export default function Landing() {
  return (
    <main className="lafre-public-page">
      <nav className="lafre-public-nav">
        <a className="lafre-wordmark" href="/">
          <span className="brand-mark">⚖</span><strong>LAFRE</strong>
        </a>
        <div>
          <a href="/login">Sign in</a>
          <a className="lafre-brown-btn" href="/register">Register as student</a>
        </div>
      </nav>
      <section className="lafre-hero">
        <span className="lafre-pill">⚖ Student workspace</span>
        <h1>A quiet desk for the study of law.</h1>
        <p>LAFRE is a focused study assistant for law students. Ask about cases, compare doctrines, draft case briefs, generate flashcards, and search your own notes — all in one workspace.</p>
        <div className="lafre-hero-actions">
          <a className="lafre-brown-btn" href="/register">Create student account</a>
          <a className="lafre-light-btn" href="/login">I already have an account</a>
        </div>
      </section>
      <section className="lafre-feature-list">
        <article><span>▤</span><h2>Ask in plain language</h2><p>Concept explanations, case briefs, statute summaries, comparisons — the response shape adapts to the question.</p></article>
        <article><span>▭</span><h2>Your library, searchable</h2><p>Upload notes, cases and statutes to your private library. Cited sources appear under each answer.</p></article>
        <article><span>⚖</span><h2>Built for legal study</h2><p>Flashcards, exam-style questions, and structured explanations grounded in your materials.</p></article>
      </section>
      <footer className="lafre-public-footer">© 2026 LAFRE. For educational use; not legal advice.</footer>
    </main>
  );
}
