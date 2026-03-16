import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// ResizeObserver is used by Recharts ResponsiveContainer but is not available in JSDOM
vi.stubGlobal(
	"ResizeObserver",
	class ResizeObserverMock {
		observe() {}
		unobserve() {}
		disconnect() {}
	},
);
