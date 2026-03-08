import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import InsightsLayout from "../components/insights/InsightsLayout.tsx";

export default function InsightsPage() {
    const username = getUsername();

    return (
        <>
            <TopBar showNav username={username} />
            <InsightsLayout />
        </>
    );
}