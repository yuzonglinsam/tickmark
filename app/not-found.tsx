import Link from "next/link";
import { LogoMark } from "@/components/brand/logo";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <LogoMark className="size-10" />
      <div className="label-caps">404 · not agreed to source</div>
      <h1 className="text-2xl font-semibold text-ink-1">This page doesn&apos;t tick and tie.</h1>
      <Link href="/terminal" className="text-[14px] text-amber hover:underline">Back to the terminal →</Link>
    </div>
  );
}
