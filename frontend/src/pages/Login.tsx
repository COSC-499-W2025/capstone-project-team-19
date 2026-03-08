import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import { login } from "../api/auth";
import { tokenStore } from "../auth/token";
import { Button } from "../components/ui/button";

export default function LoginPage() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      const tok = await login(username, password);
      tokenStore.set(tok.access_token);
      nav("/", { replace: true });
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <TopBar />
      <div className="page">
        <form className="card" onSubmit={onSubmit}>
          <label>Username</label>
          <input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />

          <label>Password</label>
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />

          {err && (
            <div className="error" style={{ whiteSpace: "pre-line" }}>
              {err}
            </div>
          )}

          <Button type="submit" disabled={loading} className="w-full mt-1.5">
            {loading ? "Logging in..." : "Login"}
          </Button>


          <div className="helper">
            Don&apos;t have an account? <Link to="/register">Register here</Link>
          </div>
        </form>
      </div>
    </>
  );
}
