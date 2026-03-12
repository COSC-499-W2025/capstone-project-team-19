import { createContext, useContext, useState, type ReactNode } from "react";

type HeaderActionsContextValue = {
    actions: ReactNode;
    setActions: (node: ReactNode) => void;
};

const InsightsHeaderActionsContext = createContext<HeaderActionsContextValue | null>(null);

export function InsightsHeaderActionsProvider({ children }: { children: ReactNode }) {
    const [actions, setActions] = useState<ReactNode>(null);
    return (
        <InsightsHeaderActionsContext.Provider value={{ actions, setActions }}>
            {children}
        </InsightsHeaderActionsContext.Provider>
    );
}

export function useInsightsHeaderActions() {
    return useContext(InsightsHeaderActionsContext);
}
