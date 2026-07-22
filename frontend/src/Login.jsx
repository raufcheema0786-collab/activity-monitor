import { useState } from "react";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");

  const handleLogin = () => {
    if (username.trim() === "") return;
    onLogin(username);
  };

  return (
    <div style={{ padding: "60px", textAlign: "center" }}>
      <h1>Activity Monitor</h1>
      <p>Sign in to continue</p>
      <input
        type="text"
        placeholder="Enter your name"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={{ padding: "8px", marginRight: "10px" }}
      />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}

export default Login;
