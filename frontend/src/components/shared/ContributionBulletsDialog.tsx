import AppButton from "./AppButton";
import AppDialogShell from "./AppDialogShell";
import AppInput from "./AppInput";
import { Trash2 } from "../../lib/ui-icons";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectName?: string;
};

export default function ContributionBulletsDialog({
  open,
  onOpenChange,
  projectName = "SampleCodeProject",
}: Props) {
  return (
    <AppDialogShell
      open={open}
      onOpenChange={onOpenChange}
      title="Contribution Bullets"
      width="lg"
      footer={
        <>
          <AppButton variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </AppButton>
          <AppButton onClick={() => onOpenChange(false)}>Save</AppButton>
        </>
      }
    >
      <div className="text-[14px] text-[#3f3f3f]">{projectName}</div>

      <div className="space-y-[8px]">
        {[1, 2, 3].map((index) => (
          <div
            key={index}
            className="grid grid-cols-[16px_1fr_18px] items-center gap-[8px]"
          >
            <span className="text-[13px] leading-none text-[#3f3f3f]">
              {index}.
            </span>

            <AppInput placeholder="" className="h-[30px]" />

            <button
              type="button"
              className="flex h-[20px] w-[18px] items-center justify-center text-[#cc4b4b]"
              aria-label={`Remove bullet ${index}`}
            >
              <Trash2 className="h-[12px] w-[12px]" strokeWidth={1.7} />
            </button>
          </div>
        ))}
      </div>

      <div>
        <AppButton
          variant="outline"
          size="sm"
          className="h-[28px] px-[10px] text-[14px]"
        >
          + Add bullet
        </AppButton>
      </div>
    </AppDialogShell>
  );
}