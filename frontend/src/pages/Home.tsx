import { useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import { tokenStore } from "../auth/token";
import { getUsernameFromToken } from "../auth/jwt";
import { PageContainer, SectionCard, ShortcutCard } from "../components/shared";
import { FileText, FolderOpen, Search, Upload } from "../lib/ui-icons";

export default function HomePage() {
  const nav = useNavigate();
  const username = getUsernameFromToken(tokenStore.get()) ?? "user";

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="flex flex-col items-center px-0 pt-[150px]">
        <div className="flex w-full max-w-[1110px] flex-col items-center">
          <h1 className="text-center text-[56px] font-normal leading-[1.05] tracking-[-0.02em] text-[#3F3F3F]">
            Welcome, {username}!
          </h1>

          <p className="mt-[14px] text-center text-[16px] font-normal leading-5 text-[#7A7A7A]">
            Let&apos;s turn your work into cool insights.
          </p>
        </div>

        {/* max-w-[748px] = grid max-w-[664px] + px-[42px] on each side */}
        <SectionCard className="mt-[48px] w-full max-w-[748px] px-[42px] pb-[40px] pt-[21px]">
          <div className="text-[20px] font-light leading-7 text-[#2F2F2F]">
            Shortcuts
          </div>

          <div className="mt-[13px] flex justify-center">
            <div className="grid w-full grid-cols-1 gap-x-[24px] gap-y-[22px] sm:grid-cols-2 sm:max-w-[664px]">
              <ShortcutCard
                title="Analyze project"
                description="Upload a project folder or ZIP to generate summaries, skills, feedback, and other insights."
                icon={Upload}
                iconBoxClassName="bg-[#60A5FA40]"
                iconClassName="text-[#60A5FA]"
                onClick={() => nav("/upload/consent")}
              />

              <ShortcutCard
                title="Explore insights"
                description="See rankings, skill timelines, heatmaps, and other insights generated from your projects."
                icon={Search}
                iconBoxClassName="bg-[#FDBA7440]"
                iconClassName="text-[#854D0E]"
                onClick={() => nav("/insights")}
              />

              <ShortcutCard
                title="Review projects"
                description="Browse your analyzed projects, revisit details, and manage the projects already in your library."
                icon={FolderOpen}
                iconBoxClassName="bg-[#D1FAE5]"
                iconClassName="text-[#15803D]"
                onClick={() => nav("/projects")}
              />

              <ShortcutCard
                title="Create resume"
                description="Create and export resumes from your project data."
                icon={FileText}
                iconBoxClassName="bg-[#0011661A]"
                iconClassName="text-[#001166]"
                onClick={() => nav("/resume")}
              />
            </div>
          </div>
        </SectionCard>
      </PageContainer>
    </>
  );
}