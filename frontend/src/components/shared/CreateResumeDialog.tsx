import AppButton from "./AppButton";
import AppDialogShell from "./AppDialogShell";
import AppField from "./AppField";
import AppInput from "./AppInput";
import AppRadio from "./AppRadio";

type ProjectOption = {
  id: string;
  label: string;
  score: string;
};

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects?: ProjectOption[];
};

const defaultProjects: ProjectOption[] = [
  { id: "projA", label: "projA", score: "0.37" },
  { id: "projB", label: "projB", score: "0.45" },
  { id: "projC", label: "projC", score: "0.46" },
];

export default function CreateResumeDialog({
  open,
  onOpenChange,
  projects = defaultProjects,
}: Props) {
  return (
    <AppDialogShell
      open={open}
      onOpenChange={onOpenChange}
      title="Create Resume"
      width="md"
      footer={
        <>
          <AppButton variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </AppButton>
          <AppButton onClick={() => onOpenChange(false)}>Save</AppButton>
        </>
      }
    >
      <AppField label="Resume Name *">
        <AppInput placeholder="resume1" className="max-w-[260px]" />
      </AppField>

      <div className="space-y-[6px]">
        <div className="text-[14px] font-medium text-foreground">
          Available Projects
        </div>
        <div className="text-[13px] text-[#8a8a8a]">
          Select projects to include in the resume.
        </div>
      </div>

      <div className="grid grid-cols-[1fr_56px] gap-y-[8px] text-[13px] text-[#3f3f3f]">
        <div className="font-medium">Project</div>
        <div className="font-medium">Score</div>

        {projects.map((project) => (
          <label key={project.id} className="contents">
            <div className="flex items-center gap-[8px]">
              <AppRadio name="resume-project-preview" />
              <span className="text-[13px] leading-none text-[#3f3f3f]">
                {project.label}
              </span>
            </div>
            <div className="text-[13px] leading-none text-[#3f3f3f]">
              {project.score}
            </div>
          </label>
        ))}
      </div>
    </AppDialogShell>
  );
}