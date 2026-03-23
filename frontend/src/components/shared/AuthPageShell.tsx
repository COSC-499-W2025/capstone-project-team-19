import type { ReactNode } from "react";
 
type Props = {
  children: ReactNode;
  /** @deprecated Move footer content inside the form instead. */
  footer?: ReactNode;
};
 
export default function AuthPageShell({ children, footer }: Props) {
  return (
    <div
      className="min-h-screen bg-[#F6F6F6] bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/auth-bg.jpg')" }}
    >
      <div className="flex min-h-screen items-center justify-center px-4 py-10">
        <div className="w-full max-w-[430px] overflow-hidden rounded-[5px] bg-white shadow-[0_4px_18px_rgba(0,0,0,0.08)]">
          {/* Header bar */}
          <div className="flex h-16 items-center bg-[#001166] px-6">
            <div className="font-['Open_Sans'] text-[30px] font-bold leading-none text-white">
              resuME
            </div>
          </div>
 
          {/* Body — natural height, centred content, no flex-1 spacer */}
          <div className="flex flex-col items-center px-[44px] py-[48px]">
            {children}
 
            {/* Legacy footer slot — only rendered if a parent still passes it */}
            {footer && (
              <div className="mt-[16px] text-center text-[12px] leading-[1.35] text-[#7f7f7f]">
                {footer}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}