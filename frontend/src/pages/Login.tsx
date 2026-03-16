import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { tokenStore } from "../auth/token";
import {
  AppButton,
  AppField,
  AppInput,
  AuthPageShell,
} from "../components/shared";

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
    <AuthPageShell
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link to="/register" className="text-[#7f7f7f] underline underline-offset-2">
            Register here
          </Link>
        </>
      }
    >
      <form
        className="mx-auto flex w-full max-w-[300px] flex-col gap-[14px]"
        onSubmit={onSubmit}
      >
        <AppField label="Username">
          <AppInput
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            aria-label="Username"
          />
        </AppField>

        <AppField label="Password">
          <AppInput
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            aria-label="Password"
          />
        </AppField>

        {err ? (
          <div className="text-[13px] leading-[1.35] text-[#cc4b4b]" style={{ whiteSpace: "pre-line" }}>
            {err}
          </div>
        ) : null}

        <AppButton type="submit" disabled={loading} fullWidth className="mt-[4px]">
          {loading ? "Logging in..." : "Login"}
        </AppButton>
      </form>
    </AuthPageShell>
  );
}