import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";

import LoginPage from "../../pages/Login";
import RegisterPage from "../../pages/Register";
import { tokenStore } from "../../auth/token";

// Mock the auth API module used by the pages
vi.mock("../../api/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
}));

import { login, register } from "../../api/auth";

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

describe("Auth pages", () => {
  it("Login success stores token and navigates to /", async () => {
    const user = userEvent.setup();

    (login as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      access_token: "fake.jwt.token",
      token_type: "bearer",
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<div data-testid="home">home</div>} />
        </Routes>
      </MemoryRouter>
    );

    await user.type(screen.getByPlaceholderText("Username"), "adara");
    await user.type(screen.getByPlaceholderText("Password"), "Password123");
    await user.click(screen.getByRole("button", { name: "Login" }));

    expect(await screen.findByTestId("home")).toBeInTheDocument();
    expect(login).toHaveBeenCalledWith("adara", "Password123");
    expect(tokenStore.get()).toBe("fake.jwt.token");
  });

  it("Login failure shows error message", async () => {
    const user = userEvent.setup();

    (login as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Invalid credentials")
    );

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>
    );

    await user.type(screen.getByPlaceholderText("Username"), "adara");
    await user.type(screen.getByPlaceholderText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Login" }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
  });

  it("Register password mismatch shows error and does not call API", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </MemoryRouter>
    );

    await user.type(screen.getByPlaceholderText("Username"), "adara");
    await user.type(screen.getByPlaceholderText("Password"), "Password123");
    await user.type(screen.getByPlaceholderText("Confirm Password"), "Password124");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(await screen.findByText("Passwords do not match")).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });

  it("Register success navigates to /login", async () => {
    const user = userEvent.setup();

    (register as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      user_id: 1,
      username: "adara",
    });

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<div data-testid="login">login</div>} />
        </Routes>
      </MemoryRouter>
    );

    await user.type(screen.getByPlaceholderText("Username"), "adara");
    await user.type(screen.getByPlaceholderText("Password"), "Password123");
    await user.type(screen.getByPlaceholderText("Confirm Password"), "Password123");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(await screen.findByTestId("login")).toBeInTheDocument();
    expect(register).toHaveBeenCalledWith("adara", "Password123");
  });
});