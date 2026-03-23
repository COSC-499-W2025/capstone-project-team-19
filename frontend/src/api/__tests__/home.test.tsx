import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";

import HomePage from "../../pages/Home";
import TopBar from "../../components/TopBar";
import { tokenStore } from "../../auth/token";

// helper to build a fake JWT
function makeJwt(payload: Record<string, unknown>) {
  const header = { alg: "HS256", typ: "JWT" };

  const b64url = (obj: unknown) =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/g, "");

  return `${b64url(header)}.${b64url(payload)}.sig`;
}

beforeEach(() => {
  localStorage.clear();
});

describe("Home and navigation", () => {
  it("Home shows username from token and renders the shortcuts section", async () => {
    tokenStore.set(makeJwt({ sub: "1", username: "testuser" }));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText("Welcome, testuser!")).toBeInTheDocument();
    expect(
      screen.getByText("Let's turn your work into cool insights.")
    ).toBeInTheDocument();
    expect(screen.getByText("Shortcuts")).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /Analyze project/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Explore insights/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Review projects/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Create outputs/i })
    ).toBeInTheDocument();
  });

  it("Analyze project shortcut navigates to /upload/consent", async () => {
    const user = userEvent.setup();
    tokenStore.set(makeJwt({ sub: "1", username: "testuser" }));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/upload/consent"
            element={<div data-testid="consent">consent</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: /Analyze project/i }));
    expect(await screen.findByTestId("consent")).toBeInTheDocument();
  });

  it("Explore insights shortcut navigates to /insights", async () => {
    const user = userEvent.setup();
    tokenStore.set(makeJwt({ sub: "1", username: "testuser" }));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/insights"
            element={<div data-testid="insights">insights</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: /Explore insights/i }));
    expect(await screen.findByTestId("insights")).toBeInTheDocument();
  });

  it("Review projects shortcut navigates to /projects", async () => {
    const user = userEvent.setup();
    tokenStore.set(makeJwt({ sub: "1", username: "testuser" }));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/projects"
            element={<div data-testid="projects">projects</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: /Review projects/i }));
    expect(await screen.findByTestId("projects")).toBeInTheDocument();
  });

  it("Create outputs shortcut navigates to /outputs", async () => {
    const user = userEvent.setup();
    tokenStore.set(makeJwt({ sub: "1", username: "testuser" }));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/outputs"
            element={<div data-testid="outputs">outputs</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: /Create outputs/i }));
    expect(await screen.findByTestId("outputs")).toBeInTheDocument();
  });

  it("Clicking resuMe logo navigates back to home", async () => {
    const user = userEvent.setup();

    const UploadFake = () => (
      <>
        <TopBar showNav username="testuser" />
        <div>Upload</div>
      </>
    );

    render(
      <MemoryRouter initialEntries={["/upload"]}>
        <Routes>
          <Route path="/" element={<div data-testid="home">home</div>} />
          <Route path="/upload" element={<UploadFake />} />
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole("link", { name: "Go to home" }));
    expect(await screen.findByTestId("home")).toBeInTheDocument();
  });
});