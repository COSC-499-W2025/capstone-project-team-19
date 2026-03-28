import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RepoSearchDropdown from "../RepoSearchDropdown";

const mockRepos = [
  { full_name: "owner/repo-a" },
  { full_name: "owner/repo-b" },
  { full_name: "other/mylib" },
];

describe("RepoSearchDropdown", () => {
  it("renders input with placeholder", () => {
    render(
      <RepoSearchDropdown repos={mockRepos} selectedRepo="" onSelect={vi.fn()} />,
    );
    expect(screen.getByPlaceholderText("Select a repository...")).toBeInTheDocument();
  });

  it("displays selected repo when one is selected", () => {
    render(
      <RepoSearchDropdown
        repos={mockRepos}
        selectedRepo="owner/repo-a"
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByDisplayValue("owner/repo-a")).toBeInTheDocument();
  });

  it("filters repos by search query", async () => {
    const user = userEvent.setup();
    render(
      <RepoSearchDropdown repos={mockRepos} selectedRepo="" onSelect={vi.fn()} />,
    );
    const input = screen.getByPlaceholderText("Select a repository...");
    await user.click(input);
    await user.type(input, "owner");
    expect(screen.getByRole("option", { name: "owner/repo-a" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "owner/repo-b" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "other/mylib" })).not.toBeInTheDocument();
  });

  it("calls onSelect when a repo option is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <RepoSearchDropdown repos={mockRepos} selectedRepo="" onSelect={onSelect} />,
    );
    await user.click(screen.getByPlaceholderText("Select a repository..."));
    await user.click(screen.getByRole("option", { name: "owner/repo-b" }));
    expect(onSelect).toHaveBeenCalledWith("owner/repo-b");
  });

  it("disables input when disabled prop is true", () => {
    render(
      <RepoSearchDropdown repos={mockRepos} selectedRepo="" onSelect={vi.fn()} disabled />,
    );
    expect(screen.getByPlaceholderText("Select a repository...")).toBeDisabled();
  });

  it("shows no matching message when filter has no results", async () => {
    const user = userEvent.setup();
    render(
      <RepoSearchDropdown repos={mockRepos} selectedRepo="" onSelect={vi.fn()} />,
    );
    const input = screen.getByPlaceholderText("Select a repository...");
    await user.click(input);
    await user.type(input, "nonexistent");
    expect(screen.getByText("No matching repositories")).toBeInTheDocument();
  });
});
