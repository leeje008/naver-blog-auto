"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/store";
import { analyzeKeywords, analyzeTopPosts } from "@/lib/api";
import { Loader2, Search, CheckCircle2 } from "lucide-react";

interface KeywordRow {
  keyword: string;
  score: number;
  source: string;
  blog_count: number;
  competition: string;
}

export default function KeywordPage() {
  const router = useRouter();
  const {
    naverClientId,
    naverClientSecret,
    keywordModel,
    setTargetKeyword,
  } = useAppStore();

  const [seed, setSeed] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<KeywordRow[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState("");

  // Top posts
  const [topLoading, setTopLoading] = useState(false);
  const [topMetrics, setTopMetrics] = useState<Record<string, unknown> | null>(
    null
  );

  const handleAnalyze = async () => {
    if (!seed.trim()) return;
    setAnalyzing(true);
    setProgress(10);
    setResults([]);
    setSelectedKeyword("");
    setTopMetrics(null);

    // Simulate progress
    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 8, 90));
    }, 2000);

    try {
      const data = await analyzeKeywords({
        seed: seed.trim(),
        naver_client_id: naverClientId,
        naver_client_secret: naverClientSecret,
        model: keywordModel,
      });
      setResults(data.results || []);
      setProgress(100);
    } catch (e) {
      alert(
        `키워드 분석 실패: ${e instanceof Error ? e.message : "알 수 없는 오류"}`
      );
    } finally {
      clearInterval(interval);
      setAnalyzing(false);
    }
  };

  const handleTopPosts = async () => {
    if (!selectedKeyword) return;
    setTopLoading(true);
    setTopMetrics(null);
    try {
      const data = await analyzeTopPosts({
        keyword: selectedKeyword,
        naver_client_id: naverClientId,
        naver_client_secret: naverClientSecret,
      });
      setTopMetrics(data);
    } catch (e) {
      alert(
        `경쟁 분석 실패: ${e instanceof Error ? e.message : "알 수 없는 오류"}`
      );
    } finally {
      setTopLoading(false);
    }
  };

  const handleConfirm = () => {
    if (!selectedKeyword) return;
    setTargetKeyword(selectedKeyword);
    router.push("/write");
  };

  const competitionColor = (comp: string) => {
    switch (comp) {
      case "낮음":
        return "bg-green-100 text-green-800";
      case "보통":
        return "bg-yellow-100 text-yellow-800";
      case "높음":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-2xl font-bold">키워드 분석</h1>

      {/* Seed keyword input */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Input
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="시드 키워드를 입력하세요 (예: 제주도 맛집)"
              className="flex-1"
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
            <Button
              onClick={handleAnalyze}
              disabled={analyzing || !seed.trim()}
              className="bg-[#03C75A] hover:bg-[#02b350] text-white shrink-0"
            >
              {analyzing ? (
                <Loader2 className="size-4 animate-spin mr-2" />
              ) : (
                <Search className="size-4 mr-2" />
              )}
              키워드 분석
            </Button>
          </div>
          {analyzing && (
            <div className="mt-4 space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-xs text-muted-foreground text-center">
                키워드 분석 중... (30~60초 소요)
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results table */}
      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>분석 결과 ({results.length}개)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">점수</TableHead>
                    <TableHead>키워드</TableHead>
                    <TableHead>소스</TableHead>
                    <TableHead className="text-right">블로그 수</TableHead>
                    <TableHead>경쟁도</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results
                    .sort((a, b) => b.score - a.score)
                    .map((row, i) => (
                      <TableRow
                        key={i}
                        className={
                          selectedKeyword === row.keyword
                            ? "bg-[#03C75A]/5"
                            : ""
                        }
                      >
                        <TableCell className="font-mono font-medium">
                          {row.score}
                        </TableCell>
                        <TableCell className="font-medium">
                          {row.keyword}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {row.source}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {row.blog_count?.toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={competitionColor(row.competition)}
                          >
                            {row.competition}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Keyword selection + actions */}
      {results.length > 0 && (
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">키워드 선택</label>
              <Select
                value={selectedKeyword}
                onValueChange={(v) => setSelectedKeyword(v ?? "")}
              >
                <SelectTrigger>
                  <SelectValue placeholder="분석할 키워드를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {results
                    .sort((a, b) => b.score - a.score)
                    .map((r, i) => (
                      <SelectItem key={i} value={r.keyword}>
                        {r.keyword} (점수: {r.score})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-3">
              <Button
                onClick={handleTopPosts}
                disabled={!selectedKeyword || topLoading}
                variant="outline"
              >
                {topLoading && (
                  <Loader2 className="size-4 animate-spin mr-2" />
                )}
                상위 포스트 경쟁 분석
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={!selectedKeyword}
                className="bg-[#03C75A] hover:bg-[#02b350] text-white"
              >
                <CheckCircle2 className="size-4 mr-2" />
                이 키워드로 글 작성하기
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top posts metrics */}
      {topMetrics && (
        <Card>
          <CardHeader>
            <CardTitle>상위 포스트 분석 결과</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(topMetrics).map(([key, value]) => {
                if (key === "common_patterns" || typeof value === "object")
                  return null;
                const labels: Record<string, string> = {
                  avg_length: "평균 글자수",
                  avg_images: "평균 이미지",
                  avg_headings: "평균 소제목",
                  keyword_density: "키워드 밀도",
                };
                return (
                  <div
                    key={key}
                    className="rounded-lg border bg-card p-4 text-center"
                  >
                    <p className="text-xs text-muted-foreground">
                      {labels[key] || key}
                    </p>
                    <p className="mt-1 text-xl font-bold">
                      {typeof value === "number" ? value.toFixed(1) : String(value)}
                    </p>
                  </div>
                );
              })}
            </div>
            {Array.isArray(topMetrics.common_patterns) && (
                <div className="mt-4">
                  <p className="text-sm font-medium mb-2">공통 패턴</p>
                  <div className="flex flex-wrap gap-2">
                    {(topMetrics.common_patterns as string[]).map((p, i) => (
                      <Badge key={i} variant="secondary">
                        {p}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
