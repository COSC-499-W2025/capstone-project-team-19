import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  footer: ReactNode;
};

export default function AuthPageShell({ children, footer }: Props) {
  return (
    <div
      className="min-h-screen bg-[#F6F6F6] bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/auth-bg.jpg')" }}
    >
      <div className="flex min-h-screen items-center justify-center px-4 py-10">
        <div className="w-full max-w-[460px] overflow-hidden rounded-[5px] bg-white shadow-[0_4px_18px_rgba(0,0,0,0.08)]">
          <div className="flex h-16 items-center bg-[#001166] px-6">
            <div className="font-['Open_Sans'] text-[36px] font-bold leading-none text-white">
              resuMe
            </div>
          </div>

          <div className="px-[44px] py-[38px]">
            {children}

            <div className="mt-[14px] text-center text-[12px] leading-[1.35] text-[#7f7f7f]">
              {footer}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}