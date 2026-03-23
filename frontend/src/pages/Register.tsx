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
import { Eye, EyeOff } from "../lib/ui-icons";

const PASSWORD_RULES = [
  { id: "length",  label: "At least 8 characters",              test: (p: string) => p.length >= 8 },
  { id: "upper",   label: "At least one uppercase letter (A–Z)", test: (p: string) => /[A-Z]/.test(p) },
  { id: "lower",   label: "At least one lowercase letter (a–z)", test: (p: string) => /[a-z]/.test(p) },
  { id: "number",  label: "At least one number (0–9)",           test: (p: string) => /[0-9]/.test(p) },
  { id: "special", label: "At least one special character",      test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

export default function RegisterPage() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const passwordTouched = password.length > 0;

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);

    const failures = PASSWORD_RULES.filter((r) => !r.test(password));
    if (failures.length > 0) {
      setErr("Please meet all password requirements.");
      return;
    }

    if (password !== confirm) {
      setErr("Passwords do not match.");
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
    <AuthPageShell>
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
          <div className="relative">
            <AppInput
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              aria-label="Password"
              className="pr-[36px]"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-[10px] top-1/2 -translate-y-1/2 text-[#7f7f7f] hover:text-[#3f3f3f]"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {passwordTouched && (
            <ul className="mt-[6px] flex flex-col gap-[3px]">
              {PASSWORD_RULES.map((rule) => {
                const passed = rule.test(password);
                return (
                  <li
                    key={rule.id}
                    className={`flex items-center gap-[5px] text-[12px] leading-[1.3] ${
                      passed ? "text-[#16a34a]" : "text-[#7f7f7f]"
                    }`}
                  >
                    <span className="text-[10px]">{passed ? "✓" : "○"}</span>
                    {rule.label}
                  </li>
                );
              })}
            </ul>
          )}
        </AppField>

        <AppField label="Confirm Password">
          <div className="relative">
            <AppInput
              type={showConfirm ? "text" : "password"}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              aria-label="Confirm Password"
              className="pr-[36px]"
            />
            <button
              type="button"
              onClick={() => setShowConfirm((v) => !v)}
              className="absolute right-[10px] top-1/2 -translate-y-1/2 text-[#7f7f7f] hover:text-[#3f3f3f]"
              aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
            >
              {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </AppField>

        {err && (
          <div className="text-[13px] leading-[1.35] text-[#cc4b4b]">
            {err}
          </div>
        )}

        <AppButton type="submit" disabled={loading} fullWidth className="mt-[4px]">
          {loading ? "Registering..." : "Register"}
        </AppButton>

        <p className="text-center text-[12px] text-[#7f7f7f]">
          Already have an account?{" "}
          <Link to="/login" className="underline underline-offset-2">
            Login here
          </Link>
        </p>
      </form>
    </AuthPageShell>
  );
}