"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { useAppStore } from "@/lib/store";
import { analyzeSeo, reviseDraft, optimizeDraft } from "@/lib/api";
import { BlogPreview } from "@/components/BlogPreview";
import { SeoChecklist } from "@/components/SeoChecklist";
import { StreamingText } from "@/components/StreamingText";
import {
  Loader2,
  FileText,
  FileDown,
  FileCode,
  PenTool,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import type { BlogDraft } from "@/lib/types";

const STRATEGIES = [
  { value: "balanced", label: "균형 (Balanced)" },
  { value: "keyword_focused", label: "키워드 집중" },
  { value: "authenticity", label: "진정성 강조" },
];

const SEO_PROFILES = [
  { value: "balanced", label: "균형 (Balanced)" },
  { value: "keyword_focused", label: "키워드 집중" },
  { value: "authenticity", label: "진정성 강조" },
];

export default function PreviewPage() {
  const {
    generated,
    setGenerated,
    targetKeyword,
    llmModel,
    seoProfile,
    setSettings,
    addRevision,
    revisionHistory,
  } = useAppStore();

  // SEO state
  const [seoLoading, setSeoLoading] = useState(false);
  const [seoResult, setSeoResult] = useState<{
    total_score: number;
    grade: string;
    items: Array<{
      key: string;
      label: string;
      score: number;
      max_score: number;
      passed: boolean;
      suggestions: string[];
    }>;
  } | null>(null);
  const [strategy, setStrategy] = useState("balanced");

  // Optimization
  const [optimizing, setOptimizing] = useState(false);

  // Revision
  const [revisionText, setRevisionText] = useState("");
  const [revising, setRevising] = useState(false);
  const [revisionStream, setRevisionStream] = useState("");
  const [isRevisionStreaming, setIsRevisionStreaming] = useState(false);

  // Guard
  if (!generated) {
    return (
      <div className="mx-auto max-w-3xl pt-20 text-center space-y-4">
        <h2 className="text-xl font-bold text-muted-foreground">
          생성된 글이 없습니다
        </h2>
        <p className="text-muted-foreground">
          먼저 글 작성 페이지에서 초안을 생성해주세요.
        </p>
        <Link href="/write">
          <Button className="bg-[#03C75A] hover:bg-[#02b350] text-white mt-4">
            <ArrowRight className="size-4 mr-2" />
            글 작성하러 가기
          </Button>
        </Link>
      </div>
    );
  }

  const handleSeoAnalyze = async () => {
    setSeoLoading(true);
    try {
      const result = await analyzeSeo({
        title: generated.title,
        content: generated.content,
        keyword: targetKeyword,
        hashtags: generated.hashtags,
        image_count: (generated.content.match(/<img/g) || []).length,
        profile: seoProfile,
      });
      setSeoResult(result);
    } catch (e) {
      alert(`SEO 분석 실패: ${e instanceof Error ? e.message : "오류"}`);
    } finally {
      setSeoLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!seoResult) return;
    setOptimizing(true);
    setRevisionStream("");
    setIsRevisionStreaming(true);

    const feedbackItems = seoResult.items
      .filter((item) => !item.passed)
      .map((item) => `${item.label}: ${item.suggestions.join(", ")}`)
      .join("\n");

    try {
      const fullText = await optimizeDraft(
        {
          original: generated as unknown as Record<string, unknown>,
          seo_feedback: feedbackItems,
          target_keyword: targetKeyword,
          strategy,
          model: llmModel,
        },
        (token) => setRevisionStream((prev) => prev + token),
        () => setIsRevisionStreaming(false)
      );

      try {
        const parsed = JSON.parse(fullText) as BlogDraft;
        setGenerated(parsed);
        addRevision(parsed);
      } catch {
        setGenerated({
          ...generated,
          content: fullText,
        });
      }
      setSeoResult(null);
    } catch (e) {
      alert(`최적화 실패: ${e instanceof Error ? e.message : "오류"}`);
      setIsRevisionStreaming(false);
    } finally {
      setOptimizing(false);
    }
  };

  const handleRevise = async () => {
    if (!revisionText.trim()) return;
    setRevising(true);
    setRevisionStream("");
    setIsRevisionStreaming(true);

    try {
      const fullText = await reviseDraft(
        {
          original: generated as unknown as Record<string, unknown>,
          instruction: revisionText,
          model: llmModel,
        },
        (token) => setRevisionStream((prev) => prev + token),
        () => setIsRevisionStreaming(false)
      );

      try {
        const parsed = JSON.parse(fullText) as BlogDraft;
        setGenerated(parsed);
        addRevision(parsed);
      } catch {
        setGenerated({
          ...generated,
          content: fullText,
        });
      }
      setRevisionText("");
      setSeoResult(null);
    } catch (e) {
      alert(`수정 실패: ${e instanceof Error ? e.message : "오류"}`);
      setIsRevisionStreaming(false);
    } finally {
      setRevising(false);
    }
  };

  // Export handlers
  const downloadFile = useCallback(
    (content: string, filename: string, mime: string) => {
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    },
    []
  );

  const exportHTML = () => {
    const html = `<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><title>${generated.title}</title></head>
<body>
<h1>${generated.title}</h1>
${generated.content}
<div>${generated.hashtags.map((t) => `#${t}`).join(" ")}</div>
</body>
</html>`;
    downloadFile(html, `${generated.title}.html`, "text/html");
  };

  const exportText = () => {
    const doc = new DOMParser().parseFromString(generated.content, "text/html");
    const text = `${generated.title}\n\n${doc.body.textContent || ""}\n\n${generated.hashtags.map((t) => `#${t}`).join(" ")}`;
    downloadFile(text, `${generated.title}.txt`, "text/plain");
  };

  const exportMarkdown = () => {
    const doc = new DOMParser().parseFromString(generated.content, "text/html");
    const md = `# ${generated.title}\n\n${doc.body.textContent || ""}\n\n${generated.hashtags.map((t) => `#${t}`).join(" ")}`;
    downloadFile(md, `${generated.title}.md`, "text/markdown");
  };

  const gradeColor = (grade: string) => {
    if (grade === "A" || grade === "A+") return "text-[#03C75A]";
    if (grade === "B" || grade === "B+") return "text-blue-500";
    if (grade === "C") return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-2xl font-bold">미리보기 & SEO</h1>

      {/* SEO Dashboard */}
      <Card>
        <CardHeader>
          <CardTitle>SEO 분석</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">SEO 프로파일</label>
              <Select
                value={seoProfile}
                onValueChange={(v) => v && setSettings({ seoProfile: v })}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEO_PROFILES.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={handleSeoAnalyze}
              disabled={seoLoading}
              className="bg-[#03C75A] hover:bg-[#02b350] text-white"
            >
              {seoLoading && <Loader2 className="size-4 animate-spin mr-2" />}
              SEO 분석
            </Button>
          </div>

          {seoResult && (
            <>
              <div className="flex items-center gap-6 py-4">
                <div className="text-center">
                  <p className="text-4xl font-bold">
                    {seoResult.total_score}
                  </p>
                  <p className="text-sm text-muted-foreground">점</p>
                </div>
                <div className="text-center">
                  <p
                    className={`text-4xl font-bold ${gradeColor(seoResult.grade)}`}
                  >
                    {seoResult.grade}
                  </p>
                  <p className="text-sm text-muted-foreground">등급</p>
                </div>
                <div className="flex-1" />
                <div className="flex items-center gap-2">
                  <Select value={strategy} onValueChange={(v) => v && setStrategy(v)}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STRATEGIES.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={handleOptimize}
                    disabled={optimizing}
                    variant="outline"
                  >
                    {optimizing ? (
                      <Loader2 className="size-4 animate-spin mr-2" />
                    ) : (
                      <Sparkles className="size-4 mr-2" />
                    )}
                    SEO 최적화
                  </Button>
                </div>
              </div>

              <SeoChecklist items={seoResult.items} />
            </>
          )}
        </CardContent>
      </Card>

      {/* Blog Preview */}
      <Card>
        <CardHeader>
          <CardTitle>블로그 미리보기</CardTitle>
        </CardHeader>
        <CardContent>
          <BlogPreview
            title={generated.title}
            content={generated.content}
            hashtags={generated.hashtags}
          />
        </CardContent>
      </Card>

      {/* Export */}
      <Card>
        <CardHeader>
          <CardTitle>내보내기</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Button onClick={exportHTML} variant="outline">
              <FileCode className="size-4 mr-2" />
              HTML
            </Button>
            <Button onClick={exportText} variant="outline">
              <FileText className="size-4 mr-2" />
              텍스트
            </Button>
            <Button onClick={exportMarkdown} variant="outline">
              <FileDown className="size-4 mr-2" />
              마크다운
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Revision */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PenTool className="size-5" />
            수정 반영
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={revisionText}
            onChange={(e) => setRevisionText(e.target.value)}
            placeholder="수정 지시사항을 입력하세요 (예: 도입부를 더 친근하게 바꿔주세요)"
            rows={3}
          />
          <Button
            onClick={handleRevise}
            disabled={revising || !revisionText.trim()}
            className="bg-[#03C75A] hover:bg-[#02b350] text-white"
          >
            {revising && <Loader2 className="size-4 animate-spin mr-2" />}
            수정 반영
          </Button>

          {isRevisionStreaming && (
            <StreamingText
              text={revisionStream}
              isStreaming={isRevisionStreaming}
            />
          )}
        </CardContent>
      </Card>

      <Separator />

      {/* Revision History */}
      {revisionHistory.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>수정 이력 ({revisionHistory.length}건)</CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion>
              {revisionHistory.map((draft, i) => (
                <AccordionItem key={i} value={`rev-${i}`}>
                  <AccordionTrigger className="text-sm">
                    버전 {i + 1}: {draft.title}
                    {draft.meta?.created_at &&
                      ` (${new Date(draft.meta.created_at).toLocaleString("ko-KR")})`}
                  </AccordionTrigger>
                  <AccordionContent>
                    <BlogPreview
                      title={draft.title}
                      content={draft.content}
                      hashtags={draft.hashtags}
                    />
                    <Button
                      onClick={() => setGenerated(draft)}
                      variant="outline"
                      size="sm"
                      className="mt-3"
                    >
                      이 버전으로 되돌리기
                    </Button>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
