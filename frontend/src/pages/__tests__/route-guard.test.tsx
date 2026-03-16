import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../../App";
import { tokenStore } from "../../auth/token";

vi.mock("../../pages/Login", () => ({
  default: () => <div data-testid="login-page">login page</div>,
}));

vi.mock("../../pages/Register", () => ({
  default: () => <div data-testid="register-page">register page</div>,
}));

vi.mock("../../pages/Home", () => ({
  default: () => <div data-testid="home-page">home page</div>,
}));

vi.mock("../../pages/upload/upload/UploadPage", () => ({
  default: () => <div data-testid="upload-page">upload page</div>,
}));

vi.mock("../../pages/upload/setup/SetupPage", () => ({
  default: () => <div data-testid="setup-page">setup page</div>,
}));

vi.mock("../../pages/upload/analyze/AnalyzePage", () => ({
  default: () => <div data-testid="analyze-page">analyze page</div>,
}));

vi.mock("../../pages/upload/consent/ConsentPage", () => ({
  default: () => <div data-testid="consent-page">consent page</div>,
}));

vi.mock("../../pages/Projects", () => ({
  default: () => <div data-testid="projects-page">projects page</div>,
}));

vi.mock("../../pages/ProjectDetail", () => ({
  default: () => <div data-testid="project-detail-page">project detail page</div>,
}));

vi.mock("../../pages/InsightsPage", () => ({
  default: () => <div data-testid="insights-page">insights page</div>,
}));

vi.mock("../../pages/Outputs", () => ({
  default: () => <div data-testid="outputs-page">outputs page</div>,
}));

vi.mock("../../pages/Profile", () => ({
  default: () => <div data-testid="profile-page">profile page</div>,
}));

vi.mock("../../pages/UIPlayground", () => ({
  default: () => <div data-testid="ui-preview-page">ui preview page</div>,
}));

vi.mock("../../pages/public/PublicProjects", () => ({
  default: () => <div data-testid="public-projects-page">public projects page</div>,
}));

vi.mock("../../pages/public/PublicProjectDetail", () => ({
  default: () => <div data-testid="public-project-detail-page">public project detail page</div>,
}));

function setRoute(path: string) {
  window.history.pushState({}, "", path);
}

function makeJwt(payload: Record<string, unknown>) {
  const header = { alg: "HS256", typ: "JWT" };

  const b64url = (obj: unknown) =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/g, "");

  return `${b64url(header)}.${b64url(payload)}.sig`;
}

describe("route guard", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("redirects unauthenticated users from protected routes to /login", async () => {
    setRoute("/projects");
    render(<App />);

    expect(await screen.findByTestId("login-page")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/login");
  });

  it("redirects users with expired tokens from protected routes to /login", async () => {
    tokenStore.set(
      makeJwt({
        sub: "1",
        username: "testuser",
        exp: Math.floor(Date.now() / 1000) - 60,
      })
    );

    setRoute("/projects");
    render(<App />);

    expect(await screen.findByTestId("login-page")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/login");
  });

  it("allows authenticated users to access protected routes", async () => {
    tokenStore.set(
      makeJwt({
        sub: "1",
        username: "testuser",
        exp: Math.floor(Date.now() / 1000) + 60 * 60,
      })
    );

    setRoute("/projects");
    render(<App />);

    expect(await screen.findByTestId("projects-page")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/projects");
  });

  it("allows public routes without authentication", async () => {
    setRoute("/public/alice/projects");
    render(<App />);

    expect(await screen.findByTestId("public-projects-page")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/public/alice/projects");
  });
});