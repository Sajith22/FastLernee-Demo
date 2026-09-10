import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function BrandMark() {
  return (
    <div className="brand-mark" aria-label="FastLearnee">
      <span>FastLearnee</span>
      <small>GRADE A+</small>
    </div>
  );
}

function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('student@oxford.ac.uk');
  const [password, setPassword] = useState('exam-ready-password');
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <section className="access-panel" aria-labelledby="access-title">
      <div className="access-content">
        <p className="eyebrow">FASTLEARN<span>EE</span> / STUDENT PORTAL</p>
        <h1 id="access-title">Access Your Syllabus</h1>
        <p className="intro">Enter your credentials to continue your custom test preparation and track historical mock metrics.</p>

        <div className="auth-tabs" role="tablist" aria-label="Account access">
          <button className="tab is-active" type="button" role="tab" aria-selected="true">Log In</button>
          <button className="tab" type="button" role="tab" aria-selected="false">Create Account</button>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Academic email address <span>e.g. student@university.edu</span></label>
          <div className="input-wrap">
            <span className="field-icon" aria-hidden="true">✉</span>
            <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>

          <div className="password-label">
            <label htmlFor="password">Password</label>
            <button type="button" className="text-button" onClick={() => setSubmitted(false)}>Forgot?</button>
          </div>
          <div className="input-wrap">
            <span className="field-icon" aria-hidden="true">▣</span>
            <input id="password" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} required />
            <button className="visibility-button" type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((visible) => !visible)}>
              {showPassword ? '◉' : '◌'}
            </button>
          </div>

          <div className="account-notice" role="status">
            <strong>!</strong>
            <p><b>University Account Detection</b><br />Using your .edu or academic address unlocks official course templates matched perfectly to your university's grading standards.</p>
          </div>

          <button className="submit-button" type="submit">Sign in to Platform</button>
          {submitted && <p className="form-message">Welcome back. Your syllabus is ready.</p>}
        </form>

        <p className="institution-link">Looking for institutional enterprise sign-in? <button type="button" className="text-button">SSO Access</button></p>
        <p className="security-note"><span aria-hidden="true">◉</span> Secured with AES-256 state-board compliant encryption.</p>
      </div>
    </section>
  );
}

function StudyPanel() {
  return (
    <section className="study-panel" aria-label="FastLearnee study promise">
      <div className="paper-sheet">
        <div className="paper-meta"><span>SUBJECT: &nbsp; Real Exam Patterns</span><span>DATE: &nbsp; 08/29/2026</span></div>
        <div className="score-stamp">100%<br /><small>READY</small></div>
        <BrandMark />
        <blockquote>“Practice with <em>real exam<br />patterns</em>, not random<br />questions.”</blockquote>
        <p className="paper-copy">We dissect official state boards, licensing bodies, and university syllabi to give you adaptive testing that mirrors your actual high-stakes day.</p>
        <ul className="proof-points">
          <li>No rote memorization required. Excellent.</li>
          <li>Proven 94.2% pass-rate for first attempts</li>
        </ul>
      </div>
    </section>
  );
}

function App() {
  return <main className="login-shell"><StudyPanel /><LoginForm /></main>;
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);