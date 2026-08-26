export default function StudentPending() {
  return (
    <main className="lafre-auth-single">
      <a className="lafre-wordmark" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
      <section className="centered auth2-success-card">
        <div className="auth2-success-mark">✓</div>
        <h2>Request sent to admin</h2>
        <p>Your LAFRE student account has been submitted. An administrator must approve your account before chat access.</p>
        <div className="auth2-next-box"><strong>What happens next?</strong><span>Admin reviews your student details.</span><span>After approval, you can sign in and start studying.</span></div>
        <a className="auth2-primary link-button" href="/login">Back to sign in</a>
      </section>
    </main>
  );
}
