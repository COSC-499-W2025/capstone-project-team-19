import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import {
  AppButton,
  AppField,
  AppInput,
  AuthPageShell,
} from "../components/shared";

export default function RegisterPage() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);

    if (password !== confirm) {
      setErr("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await register(username, password);
      nav("/login", { replace: true });
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Register failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthPageShell
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-[#7f7f7f] underline underline-offset-2">
            Login here
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
            autoComplete="new-password"
            aria-label="Password"
          />
        </AppField>

        <AppField label="Confirm Password">
          <AppInput
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password"
            aria-label="Confirm Password"
          />
        </AppField>

        {err ? (
          <div className="text-[13px] leading-[1.35] text-[#cc4b4b]" style={{ whiteSpace: "pre-line" }}>
            {err}
          </div>
        ) : null}

        <AppButton type="submit" disabled={loading} fullWidth className="mt-[4px]">
          {loading ? "Registering..." : "Register"}
        </AppButton>
      </form>
    </AuthPageShell>
  );
}