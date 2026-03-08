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
  it("Home shows username from token and Start analyzing navigates to /upload", async () => {
    const user = userEvent.setup();
    tokenStore.set(makeJwt({ sub: "1", username: "testuser" }));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<div data-testid="upload">upload</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText("Hello, testuser!")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Start analyzing" }));
    expect(await screen.findByTestId("upload")).toBeInTheDocument();
  });

  it("Clicking resuME logo navigates back to home", async () => {
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

    await user.click(screen.getByText("resuME"));
    expect(await screen.findByTestId("home")).toBeInTheDocument();
  });
});