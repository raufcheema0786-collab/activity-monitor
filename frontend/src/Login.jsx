import { useEffect, useState } from "react";

const MIN_PASSWORD_LENGTH = 4;

function Login({ onLogin }) {
  const [phase, setPhase] = useState("loading"); // loading | not_activated | create_password | login | switch | error
  const [employeeName, setEmployeeName] = useState("");
  const [switchName, setSwitchName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState("");

  const loadState = () => {
    setPhase("loading");
    setLoadError("");
    setPassword("");
    setError("");
    window.pywebview.api
      .get_login_state()
      .then((result) => {
        if (result.state === "error") {
          setLoadError(result.error || "Something went wrong.");
          setPhase("error");
          return;
        }
        setEmployeeName(result.employee_name || "");
        setPhase(result.state);
      })
      .catch((err) => {
        setLoadError(String(err));
        setPhase("error");
      });
  };

  useEffect(() => {
    // pywebview injects window.pywebview asynchronously after the page
    // loads -- calling into api before that fires throws, and with no
    // error boundary that blanks the whole page instead of showing this
    // screen's own error state.
    if (window.pywebview) {
      loadState();
      return;
    }
    window.addEventListener("pywebviewready", loadState);
    return () => window.removeEventListener("pywebviewready", loadState);
  }, []);

  const handleCreatePassword = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setSubmitting(true);
    const setResult = await window.pywebview.api.set_password(password);
    if (!setResult.success) {
      setSubmitting(false);
      setError(setResult.error || "Couldn't set your password.");
      return;
    }

    const loginResult = await window.pywebview.api.login(password);
    setSubmitting(false);
    if (!loginResult.success) {
      setError(loginResult.error || "Password was set, but signing you in failed. Try logging in.");
      setPhase("login");
      return;
    }
    onLogin(loginResult.employee_name);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const result = await window.pywebview.api.login(password);
    setSubmitting(false);
    if (!result.success) {
      setError(result.error || "Couldn't sign you in.");
      return;
    }
    onLogin(result.employee_name);
  };

  const handleSwitchLogin = async (e) => {
    e.preventDefault();
    setError("");
    if (!switchName.trim()) {
      setError("Enter your name.");
      return;
    }
    setSubmitting(true);
    const result = await window.pywebview.api.login_as(switchName.trim(), password);
    setSubmitting(false);
    if (!result.success) {
      setError(result.error || "Couldn't sign you in.");
      return;
    }
    onLogin(result.employee_name);
  };

  const startSwitch = () => {
    setSwitchName("");
    setPassword("");
    setError("");
    setPhase("switch");
  };

  return (
    <div className="app-shell" style={{ justifyContent: "center" }}>
      <div className="card" style={{ maxWidth: 380, margin: "0 auto", width: "100%" }}>
        <div style={{ textAlign: "center", marginBottom: 22 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "var(--accent-bg)",
              color: "var(--accent)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 14px",
              fontSize: 20,
              fontWeight: 700,
            }}
          >
            AM
          </div>
          <h1>Activity Monitor</h1>
        </div>

        {phase === "loading" && <p className="empty-state">Checking your account…</p>}

        {phase === "not_activated" && (
          <div className="notice notice-warn">
            This machine hasn't been activated yet. Use the activation link your admin sent you to set it up.
          </div>
        )}

        {phase === "error" && (
          <>
            <div className="notice notice-danger">{loadError}</div>
            <button className="btn btn-block" style={{ marginTop: 14 }} onClick={loadState}>
              Try again
            </button>
          </>
        )}

        {phase === "create_password" && (
          <form onSubmit={handleCreatePassword} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <p style={{ color: "var(--text-muted)", fontSize: 13.5, textAlign: "center" }}>
              Welcome, <strong style={{ color: "var(--text)" }}>{employeeName}</strong>. Set a password so only you
              can open this app and see your monitoring status.
            </p>
            <div className="field">
              <label htmlFor="new-password">New password</label>
              <input
                id="new-password"
                type="password"
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="confirm-password">Confirm password</label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            {error && <div className="field-error">{error}</div>}
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? "Setting up…" : "Set password & continue"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={startSwitch}>
              Not you? Sign in as someone else
            </button>
          </form>
        )}

        {phase === "login" && (
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <p style={{ color: "var(--text-muted)", fontSize: 13.5, textAlign: "center" }}>
              Welcome back, <strong style={{ color: "var(--text)" }}>{employeeName}</strong>.
            </p>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && <div className="field-error">{error}</div>}
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={startSwitch}>
              Not you? Sign in as someone else
            </button>
          </form>
        )}

        {phase === "switch" && (
          <form onSubmit={handleSwitchLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <p style={{ color: "var(--text-muted)", fontSize: 13.5, textAlign: "center" }}>
              Sign in as a different employee on this computer. This will end{" "}
              {employeeName ? <strong style={{ color: "var(--text)" }}>{employeeName}</strong> : "the current employee"}
              's session if one is running.
            </p>
            <div className="field">
              <label htmlFor="switch-name">Your name</label>
              <input
                id="switch-name"
                type="text"
                autoFocus
                value={switchName}
                onChange={(e) => setSwitchName(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="switch-password">Password</label>
              <input
                id="switch-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && <div className="field-error">{error}</div>}
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={loadState}>
              ← Back
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default Login;
