"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { SeoChecklist } from "@/components/SeoChecklist";
import { useAppStore } from "@/lib/store";
import {
  analyzeSeo,
  analyzeSeoCustomWeights,
  getHistory,
} from "@/lib/api";
import { Loader2 } from "lucide-react";

const WEIGHT_KEYS = [
  { key: "title", label: "제목" },
  { key: "body_length", label: "본문 길이" },
  { key: "keyword_density", label: "키워드 밀도" },
  { key: "heading_structure", label: "소제목 구조" },
  { key: "images", label: "이미지" },
  { key: "hashtags", label: "해시태그" },
  { key: "readability", label: "가독성" },
  { key: "experience_signals", label: "경험 시그널" },
  { key: "information_depth", label: "정보 깊이" },
  { key: "ai_safety", label: "AI 안전" },
];

const PROFILE_PRESETS: Record<string, Record<string, number>> = {
  balanced: {
    title: 0.15,
    body_length: 0.1,
    keyword_density: 0.18,
    heading_structure: 0.12,
    images: 0.08,
    hashtags: 0.07,
    readability: 0.12,
    experience_signals: 0.08,
    information_depth: 0.05,
    ai_safety: 0.05,
  },
  keyword_focused: {
    title: 0.2,
    body_length: 0.1,
    keyword_density: 0.3,
    heading_structure: 0.15,
    images: 0.05,
    hashtags: 0.05,
    readability: 0.05,
    experience_signals: 0.05,
    information_depth: 0.03,
    ai_safety: 0.02,
  },
  authenticity: {
    title: 0.1,
    body_length: 0.05,
    keyword_density: 0.1,
    heading_structure: 0.05,
    images: 0.03,
    hashtags: 0.02,
    readability: 0.2,
    experience_signals: 0.2,
    information_depth: 0.15,
    ai_safety: 0.1,
  },
};

const PRESET_OPTIONS = [
  { value: "balanced", label: "균형 (Balanced)" },
  { value: "keyword_focused", label: "키워드 집중" },
  { value: "authenticity", label: "진정성 강조" },
];

interface SeoItem {
  key: string;
  label: string;
  score: number;
  max_score: number;
  passed: boolean;
  suggestions: string[];
}

interface CompareResult {
  profile: string;
  total_score: number;
  grade: string;
  items: SeoItem[];
}

export default function SeoLabPage() {
  const { generated, targetKeyword } = useAppStore();

  // Tab 1: Profile comparison
  const [compareSource, setCompareSource] = useState<"current" | "manual">(
    "current"
  );
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResults, setCompareResults] = useState<CompareResult[]>([]);

  // Tab 2: Weight tuning
  const [weightPreset, setWeightPreset] = useState("balanced");
  const [weights, setWeights] = useState<Record<string, number>>(
    PROFILE_PRESETS.balanced
  );
  const [customResult, setCustomResult] = useState<{
    total_score: number;
    grade: string;
    items: SeoItem[];
  } | null>(null);
  const [customLoading, setCustomLoading] = useState(false);

  // Tab 3: Content test
  const [testKeyword, setTestKeyword] = useState("");
  const [testTitle, setTestTitle] = useState("");
  const [testContent, setTestContent] = useState("");
  const [testTags, setTestTags] = useState("");
  const [testImageCount, setTestImageCount] = useState(3);
  const [testResult, setTestResult] = useState<{
    total_score: number;
    grade: string;
    items: SeoItem[];
  } | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  // Tab 4: Batch analysis
  const [batchProfile, setBatchProfile] = useState("balanced");
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResults, setBatchResults] = useState<
    Array<{
      title: string;
      score: number;
      grade: string;
    }>
  >([]);

  // Profile comparison
  const handleCompare = async () => {
    if (!generated && compareSource === "current") return;
    setCompareLoading(true);
    setCompareResults([]);

    const title = generated?.title || testTitle;
    const content = generated?.content || testContent;
    const keyword = targetKeyword || testKeyword;
    const hashtags = generated?.hashtags || testTags.split(",").map((t) => t.trim()).filter(Boolean);

    try {
      const results: CompareResult[] = [];
      for (const profileName of ["balanced", "keyword_focused", "authenticity"]) {
        const data = await analyzeSeo({
          title,
          content,
          keyword,
          hashtags,
          profile: profileName,
        });
        results.push({
          profile: profileName,
          total_score: data.total_score,
          grade: data.grade,
          items: data.items,
        });
      }
      setCompareResults(results);
    } catch (e) {
      alert(`비교 분석 실패: ${e instanceof Error ? e.message : "오류"}`);
    } finally {
      setCompareLoading(false);
    }
  };

  // Custom weight analysis
  const handleCustomAnalyze = async () => {
    if (!generated) return;
    setCustomLoading(true);
    try {
      const data = await analyzeSeoCustomWeights({
        title: generated.title,
        content: generated.content,
        keyword: targetKeyword,
        hashtags: generated.hashtags,
        weights,
      });
      setCustomResult(data);
    } catch (e) {
      alert(`분석 실패: ${e instanceof Error ? e.message : "오류"}`);
    } finally {
      setCustomLoading(false);
    }
  };

  // Content test
  const handleContentTest = async () => {
    if (!testKeyword || !testTitle || !testContent) return;
    setTestLoading(true);
    try {
      const data = await analyzeSeo({
        title: testTitle,
        content: testContent,
        keyword: testKeyword,
        hashtags: testTags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        image_count: testImageCount,
      });
      setTestResult(data);
    } catch (e) {
      alert(`분석 실패: ${e instanceof Error ? e.message : "오류"}`);
    } finally {
      setTestLoading(false);
    }
  };

  // Batch analysis
  const handleBatchAnalyze = async () => {
    setBatchLoading(true);
    setBatchResults([]);
    try {
      const data = await getHistory();
      const entries = data.entries || [];
      const results: Array<{ title: string; score: number; grade: string }> =
        [];
      for (const entry of entries.slice(0, 20)) {
        try {
          const seo = await analyzeSeo({
            title: entry.title,
            content: entry.content || "",
            keyword: entry.keyword,
            hashtags: entry.tags,
            profile: batchProfile,
          });
          results.push({
            title: entry.title,
            score: seo.total_score,
            grade: seo.grade,
          });
        } catch {
          results.push({ title: entry.title, score: 0, grade: "-" });
        }
      }
      setBatchResults(results);
    } catch (e) {
      alert(`일괄 분석 실패: ${e instanceof Error ? e.message : "오류"}`);
    } finally {
      setBatchLoading(false);
    }
  };

  const profileLabel = (name: string) => {
    const map: Record<string, string> = {
      balanced: "균형",
      keyword_focused: "키워드 집중",
      authenticity: "진정성",
    };
    return map[name] || name;
  };

  const gradeColor = (grade: string) => {
    if (grade === "A" || grade === "A+") return "text-[#03C75A]";
    if (grade === "B" || grade === "B+") return "text-blue-500";
    if (grade === "C") return "text-yellow-500";
    return "text-red-500";
  };

  const weightSum = Object.values(weights).reduce((a, b) => a + b, 0);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold">SEO 랩</h1>

      <Tabs defaultValue="compare">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="compare">프로파일 비교</TabsTrigger>
          <TabsTrigger value="tuning">가중치 튜닝</TabsTrigger>
          <TabsTrigger value="test">콘텐츠 테스트</TabsTrigger>
          <TabsTrigger value="batch">일괄 분석</TabsTrigger>
        </TabsList>

        {/* Tab 1: Profile comparison */}
        <TabsContent value="compare" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>3개 프로파일 비교 분석</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="compareSource"
                    checked={compareSource === "current"}
                    onChange={() => setCompareSource("current")}
                  />
                  현재 생성된 글
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="compareSource"
                    checked={compareSource === "manual"}
                    onChange={() => setCompareSource("manual")}
                  />
                  직접 입력
                </label>
              </div>

              {compareSource === "current" && !generated && (
                <p className="text-sm text-muted-foreground">
                  생성된 글이 없습니다. 먼저 글을 작성해주세요.
                </p>
              )}

              <Button
                onClick={handleCompare}
                disabled={
                  compareLoading ||
                  (compareSource === "current" && !generated)
                }
                className="bg-[#03C75A] hover:bg-[#02b350] text-white"
              >
                {compareLoading && (
                  <Loader2 className="size-4 animate-spin mr-2" />
                )}
                비교 분석
              </Button>
            </CardContent>
          </Card>

          {compareResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {compareResults.map((r) => (
                <Card key={r.profile}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">
                      {profileLabel(r.profile)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 mb-4">
                      <span className="text-3xl font-bold">
                        {r.total_score}
                      </span>
                      <span
                        className={`text-2xl font-bold ${gradeColor(r.grade)}`}
                      >
                        {r.grade}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {r.items.map((item) => (
                        <div
                          key={item.key}
                          className="flex justify-between text-xs"
                        >
                          <span className={item.passed ? "text-[#03C75A]" : "text-red-500"}>
                            {item.passed ? "O" : "X"} {item.label}
                          </span>
                          <span className="font-mono">
                            {item.score}/{item.max_score}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Tab 2: Weight tuning */}
        <TabsContent value="tuning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>가중치 커스텀 튜닝</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium">프리셋:</label>
                <Select
                  value={weightPreset}
                  onValueChange={(v) => {
                    if (!v) return;
                    setWeightPreset(v);
                    setWeights({ ...PROFILE_PRESETS[v] });
                  }}
                >
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRESET_OPTIONS.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Badge
                  variant={
                    Math.abs(weightSum - 1) < 0.01 ? "secondary" : "destructive"
                  }
                >
                  합계: {(weightSum * 100).toFixed(0)}%
                </Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                {WEIGHT_KEYS.map((wk) => (
                  <div key={wk.key} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span>{wk.label}</span>
                      <span className="font-mono text-xs text-muted-foreground">
                        {((weights[wk.key] || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[(weights[wk.key] || 0) * 100]}
                      onValueChange={(val) => {
                        const v = Array.isArray(val) ? val[0] : val;
                        setWeights((prev) => ({
                          ...prev,
                          [wk.key]: v / 100,
                        }));
                      }}
                      max={50}
                      step={1}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>

              <Button
                onClick={handleCustomAnalyze}
                disabled={customLoading || !generated}
                className="bg-[#03C75A] hover:bg-[#02b350] text-white"
              >
                {customLoading && (
                  <Loader2 className="size-4 animate-spin mr-2" />
                )}
                커스텀 가중치로 분석
              </Button>

              {!generated && (
                <p className="text-sm text-muted-foreground">
                  생성된 글이 있어야 분석할 수 있습니다.
                </p>
              )}
            </CardContent>
          </Card>

          {customResult && (
            <Card>
              <CardHeader>
                <CardTitle>
                  커스텀 분석 결과: {customResult.total_score}점 (
                  <span className={gradeColor(customResult.grade)}>
                    {customResult.grade}
                  </span>
                  )
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SeoChecklist items={customResult.items} />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab 3: Content test */}
        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>콘텐츠 수동 테스트</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">타겟 키워드</label>
                  <Input
                    value={testKeyword}
                    onChange={(e) => setTestKeyword(e.target.value)}
                    placeholder="키워드"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">제목</label>
                  <Input
                    value={testTitle}
                    onChange={(e) => setTestTitle(e.target.value)}
                    placeholder="블로그 제목"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">본문 내용</label>
                <Textarea
                  value={testContent}
                  onChange={(e) => setTestContent(e.target.value)}
                  placeholder="블로그 본문 (HTML 또는 텍스트)"
                  rows={8}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    해시태그 (쉼표 구분)
                  </label>
                  <Input
                    value={testTags}
                    onChange={(e) => setTestTags(e.target.value)}
                    placeholder="태그1, 태그2, 태그3"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">이미지 수</label>
                  <Input
                    type="number"
                    value={testImageCount}
                    onChange={(e) =>
                      setTestImageCount(parseInt(e.target.value) || 0)
                    }
                    min={0}
                    max={20}
                  />
                </div>
              </div>
              <Button
                onClick={handleContentTest}
                disabled={
                  testLoading || !testKeyword || !testTitle || !testContent
                }
                className="bg-[#03C75A] hover:bg-[#02b350] text-white"
              >
                {testLoading && (
                  <Loader2 className="size-4 animate-spin mr-2" />
                )}
                SEO 분석
              </Button>
            </CardContent>
          </Card>

          {testResult && (
            <Card>
              <CardHeader>
                <CardTitle>
                  분석 결과: {testResult.total_score}점 (
                  <span className={gradeColor(testResult.grade)}>
                    {testResult.grade}
                  </span>
                  )
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SeoChecklist items={testResult.items} />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab 4: Batch analysis */}
        <TabsContent value="batch" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>이력 일괄 SEO 분석</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium">프로파일:</label>
                <Select value={batchProfile} onValueChange={(v) => v && setBatchProfile(v)}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRESET_OPTIONS.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleBatchAnalyze}
                  disabled={batchLoading}
                  className="bg-[#03C75A] hover:bg-[#02b350] text-white"
                >
                  {batchLoading && (
                    <Loader2 className="size-4 animate-spin mr-2" />
                  )}
                  일괄 분석
                </Button>
              </div>
            </CardContent>
          </Card>

          {batchResults.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">#</TableHead>
                      <TableHead>제목</TableHead>
                      <TableHead className="w-20 text-right">점수</TableHead>
                      <TableHead className="w-16 text-center">등급</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {batchResults.map((r, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono text-muted-foreground">
                          {i + 1}
                        </TableCell>
                        <TableCell className="font-medium truncate max-w-xs">
                          {r.title}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {r.score}
                        </TableCell>
                        <TableCell className="text-center">
                          <span
                            className={`font-bold ${gradeColor(r.grade)}`}
                          >
                            {r.grade}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 text-sm text-muted-foreground text-center">
                  평균 점수:{" "}
                  <span className="font-bold">
                    {(
                      batchResults.reduce((s, r) => s + r.score, 0) /
                      batchResults.length
                    ).toFixed(1)}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
