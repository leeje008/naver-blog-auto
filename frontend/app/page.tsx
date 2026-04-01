"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Settings, Search, PenTool, Eye, History } from "lucide-react";

const STEPS = [
  {
    num: 1,
    label: "설정",
    desc: "LLM 모델 선택, 네이버 API 인증, 참고 글 크롤링",
    href: "/settings",
    icon: Settings,
  },
  {
    num: 2,
    label: "키워드 분석",
    desc: "시드 키워드 입력 후 블로그 최적 키워드 발굴",
    href: "/keyword",
    icon: Search,
  },
  {
    num: 3,
    label: "글 작성",
    desc: "키워드 + 이미지 기반 SEO 최적화 블로그 초안 생성",
    href: "/write",
    icon: PenTool,
  },
  {
    num: 4,
    label: "미리보기 & SEO",
    desc: "SEO 점수 확인, 최적화, 수정 반영, 내보내기",
    href: "/preview",
    icon: Eye,
  },
  {
    num: 5,
    label: "이력 관리",
    desc: "작성 이력 조회, 통계 확인, 검색 및 삭제",
    href: "/history",
    icon: History,
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="text-center space-y-2 pt-8">
        <h1 className="text-3xl font-bold">네이버 블로그 자동 생성기</h1>
        <p className="text-muted-foreground">
          AI 기반 네이버 블로그 글 자동 생성 &amp; SEO 최적화 도구
        </p>
      </div>

      <div className="space-y-3">
        {STEPS.map((step) => {
          const Icon = step.icon;
          return (
            <Link key={step.num} href={step.href}>
              <Card className="transition-shadow hover:shadow-md cursor-pointer mb-3">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-3">
                    <span className="flex size-8 items-center justify-center rounded-full bg-[#03C75A] text-white text-sm font-bold">
                      {step.num}
                    </span>
                    <Icon className="size-5 text-[#03C75A]" />
                    <span>{step.label}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground ml-11">
                    {step.desc}
                  </p>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      <Card className="bg-[#03C75A]/5 border-[#03C75A]/20">
        <CardContent className="pt-4">
          <p className="text-sm text-muted-foreground">
            <strong>Tip:</strong> 왼쪽 사이드바에서 각 단계로 바로 이동할 수
            있습니다. 순서대로 진행하면 최상의 결과를 얻을 수 있습니다.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
