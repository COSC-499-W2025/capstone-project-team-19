import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RankedProjectsTab from "../tabs/RankedProjectsTab";
import { InsightsHeaderActionsProvider, useInsightsHeaderActions } from "../InsightsHeaderActionsContext";
import * as insights from "../../../api/insights";

vi.mock("../../../api/insights");

function HeaderActionsSlot() {
	const ctx = useInsightsHeaderActions();
	return <div data-testid="header-actions">{ctx?.actions}</div>;
}

function TabWrapper() {
	return (
		<InsightsHeaderActionsProvider>
			<HeaderActionsSlot />
			<RankedProjectsTab />
		</InsightsHeaderActionsProvider>
	);
}

const mockRankings = [
	{
		rank: 1,
		project_summary_id: 101,
		project_name: "Project A",
		score: 0.85,
		manual_rank: null,
	},
	{
		rank: 2,
		project_summary_id: 102,
		project_name: "Project B",
		score: 0.72,
		manual_rank: 2,
	},
];

describe("RankedProjectsTab", () => {
	beforeEach(() => {
		vi.mocked(insights.getRanking).mockResolvedValue({
			success: true,
			data: { rankings: mockRankings },
			error: null,
		});
	});

	it("shows loading state initially", () => {
		render(<TabWrapper />);
		expect(screen.getByText(/loading ranked projects/i)).toBeInTheDocument();
	});

	it("shows rankings after load", async () => {
		render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		expect(screen.getByText("Project B")).toBeInTheDocument();
		expect(screen.getByText("0.85")).toBeInTheDocument();
		expect(screen.getByText("0.72")).toBeInTheDocument();
	});

	it("shows error when fetch fails", async () => {
		vi.mocked(insights.getRanking).mockRejectedValue(new Error("Network error"));
		render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText("Network error")).toBeInTheDocument();
		});
	});

	it("shows empty state when no projects", async () => {
		vi.mocked(insights.getRanking).mockResolvedValue({
			success: true,
			data: { rankings: [] },
			error: null,
		});
		render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText(/no projects uploaded/i)).toBeInTheDocument();
		});
	});

	it("Save Order is disabled when order unchanged", async () => {
		render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		expect(screen.getByRole("button", { name: /save order/i })).toBeDisabled();
	});

	it("Save Order is enabled after reordering", async () => {
		const user = userEvent.setup();
		const { container } = render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		const rows = container.querySelectorAll(".ranked-row");
		const firstRow = rows[0];
		const downButton = within(firstRow as HTMLElement).getByRole("button", { name: /↓/ });
		await user.click(downButton);
		expect(screen.getByRole("button", { name: /save order/i })).toBeEnabled();
	});

	it("move up/down reorders the list", async () => {
		const user = userEvent.setup();
		const { container } = render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		const rows = container.querySelectorAll(".ranked-row");
		expect(rows[0]).toHaveTextContent("Project A");
		expect(rows[1]).toHaveTextContent("Project B");

		const downButton = within(rows[0] as HTMLElement).getByRole("button", { name: /↓/ });
		await user.click(downButton);

		const updatedRows = container.querySelectorAll(".ranked-row");
		expect(updatedRows[0]).toHaveTextContent("Project B");
		expect(updatedRows[1]).toHaveTextContent("Project A");
	});

	it("Reset to Auto calls resetRanking", async () => {
		vi.mocked(insights.resetRanking).mockResolvedValue({
			success: true,
			data: { rankings: mockRankings },
			error: null,
		});
		const user = userEvent.setup();
		render(<TabWrapper />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		await user.click(screen.getByRole("button", { name: /reset to auto/i }));
		await waitFor(() => {
			expect(insights.resetRanking).toHaveBeenCalled();
		});
	});
});
