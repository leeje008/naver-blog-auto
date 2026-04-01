"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Settings,
  Search,
  PenTool,
  Eye,
  History,
  FlaskConical,
  Menu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/", label: "홈", icon: Home },
  { href: "/settings", label: "설정", icon: Settings },
  { href: "/keyword", label: "키워드", icon: Search },
  { href: "/write", label: "글 작성", icon: PenTool },
  { href: "/preview", label: "미리보기", icon: Eye },
  { href: "/history", label: "이력", icon: History },
  { href: "/seo-lab", label: "SEO 랩", icon: FlaskConical },
];

function NavLinks({ onClick }: { onClick?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1 px-2">
      {NAV_ITEMS.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onClick}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              active
                ? "bg-[#03C75A]/10 text-[#03C75A]"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="size-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function DesktopSidebar() {
  return (
    <aside className="hidden md:flex md:w-56 md:flex-col md:border-r md:bg-card">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <div className="size-7 rounded-lg bg-[#03C75A] flex items-center justify-center text-white font-bold text-xs">
          N
        </div>
        <span className="font-semibold text-sm">블로그 자동생성</span>
      </div>
      <div className="flex-1 overflow-y-auto py-3">
        <NavLinks />
      </div>
    </aside>
  );
}

export function MobileHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="flex h-14 items-center gap-2 border-b px-4 md:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger
          render={<Button variant="ghost" size="icon" />}
        >
          <Menu className="size-5" />
        </SheetTrigger>
        <SheetContent side="left" className="w-56 p-0">
          <SheetTitle className="flex h-14 items-center gap-2 border-b px-4">
            <div className="size-7 rounded-lg bg-[#03C75A] flex items-center justify-center text-white font-bold text-xs">
              N
            </div>
            <span className="font-semibold text-sm">블로그 자동생성</span>
          </SheetTitle>
          <div className="py-3">
            <NavLinks onClick={() => setOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>
      <div className="size-7 rounded-lg bg-[#03C75A] flex items-center justify-center text-white font-bold text-xs">
        N
      </div>
      <span className="font-semibold text-sm">블로그 자동생성</span>
    </header>
  );
}
