import AppButton from "./AppButton";
import AppDialogShell from "./AppDialogShell";
import AppField from "./AppField";
import AppInput from "./AppInput";
import { Trash2 } from "../../lib/ui-icons";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export default function ContactDialog({ open, onOpenChange }: Props) {
  return (
    <AppDialogShell
      open={open}
      onOpenChange={onOpenChange}
      title="Contact"
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
      <div className="space-y-[12px]">
        <div className="grid grid-cols-[1fr_18px] items-end gap-[8px]">
          <AppField label="Email">
            <AppInput placeholder="testuser@gmail.com" />
          </AppField>
          <button
            type="button"
            className="flex h-[20px] w-[18px] items-center justify-center text-[#cc4b4b]"
            aria-label="Remove email"
          >
            <Trash2 className="h-[12px] w-[12px]" strokeWidth={1.7} />
          </button>
        </div>

        <div className="grid grid-cols-[1fr_18px] items-end gap-[8px]">
          <AppField label="LinkedIn Profile">
            <AppInput placeholder="linkedin.com/in/test-user" />
          </AppField>
          <button
            type="button"
            className="flex h-[20px] w-[18px] items-center justify-center text-[#cc4b4b]"
            aria-label="Remove linkedin"
          >
            <Trash2 className="h-[12px] w-[12px]" strokeWidth={1.7} />
          </button>
        </div>

        <div className="grid grid-cols-[1fr_18px] items-end gap-[8px]">
          <AppField label="GitHub Profile">
            <AppInput placeholder="github.com/testuser" />
          </AppField>
          <button
            type="button"
            className="flex h-[20px] w-[18px] items-center justify-center text-[#cc4b4b]"
            aria-label="Remove github"
          >
            <Trash2 className="h-[12px] w-[12px]" strokeWidth={1.7} />
          </button>
        </div>
      </div>
    </AppDialogShell>
  );
}