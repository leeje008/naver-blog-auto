"use client";

import { useEffect, useState, useCallback } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useAppStore } from "@/lib/store";
import {
  getModels,
  getConfig,
  putConfig,
  testNaver,
  crawlReference,
} from "@/lib/api";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

export default function SettingsPage() {
  const {
    naverClientId,
    naverClientSecret,
    llmModel,
    keywordModel,
    setSettings,
  } = useAppStore();

  const [models, setModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState(false);

  // Manual model inputs (fallback)
  const [manualLlm, setManualLlm] = useState("");
  const [manualKeyword, setManualKeyword] = useState("");

  // Naver test
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [testing, setTesting] = useState(false);

  // Reference URLs
  const [refUrls, setRefUrls] = useState(["", "", ""]);
  const [crawling, setCrawling] = useState(false);
  const [crawlResults, setCrawlResults] = useState<string[]>([]);
  const [manualRef, setManualRef] = useState("");

  // Save
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const fetchModels = useCallback(async () => {
    try {
      setModelsLoading(true);
      const m = await getModels();
      setModels(m);
      setModelsError(false);
    } catch {
      setModelsError(true);
    } finally {
      setModelsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
    // Load existing config
    getConfig()
      .then((cfg) => {
        if (cfg.naver_client_id)
          setSettings({ naverClientId: cfg.naver_client_id as string });
        if (cfg.naver_client_secret)
          setSettings({ naverClientSecret: cfg.naver_client_secret as string });
        if (cfg.llm_model)
          setSettings({ llmModel: cfg.llm_model as string });
        if (cfg.keyword_model)
          setSettings({ keywordModel: cfg.keyword_model as string });
      })
      .catch(() => {});
  }, [fetchModels, setSettings]);

  const handleTestNaver = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testNaver(naverClientId, naverClientSecret);
      setTestResult(result);
    } catch (e) {
      setTestResult({
        success: false,
        message: e instanceof Error ? e.message : "연결 실패",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleCrawl = async () => {
    setCrawling(true);
    setCrawlResults([]);
    const results: string[] = [];
    for (const url of refUrls) {
      if (!url.trim()) {
        results.push("");
        continue;
      }
      try {
        await crawlReference(url.trim());
        results.push("성공");
      } catch {
        results.push("실패");
      }
    }
    setCrawlResults(results);
    setCrawling(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await putConfig({
        naver_client_id: naverClientId,
        naver_client_secret: naverClientSecret,
        llm_model: llmModel,
        keyword_model: keywordModel,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      alert("설정 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold">설정</h1>

      {/* Model Selection */}
      <Card>
        <CardHeader>
          <CardTitle>LLM 모델 설정</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Writing model */}
            <div className="space-y-2">
              <label className="text-sm font-medium">글 작성 모델</label>
              {modelsLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  모델 목록 로딩 중...
                </div>
              ) : modelsError ? (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">
                    서버 연결 실패 - 모델명을 직접 입력하세요
                  </p>
                  <Input
                    value={manualLlm || llmModel}
                    onChange={(e) => {
                      setManualLlm(e.target.value);
                      setSettings({ llmModel: e.target.value });
                    }}
                    placeholder="예: gemma3:12b"
                  />
                </div>
              ) : (
                <Select
                  value={llmModel}
                  onValueChange={(v) => v && setSettings({ llmModel: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="모델 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    {models.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Keyword model */}
            <div className="space-y-2">
              <label className="text-sm font-medium">키워드 분석 모델</label>
              {modelsLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  모델 목록 로딩 중...
                </div>
              ) : modelsError ? (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">
                    서버 연결 실패 - 모델명을 직접 입력하세요
                  </p>
                  <Input
                    value={manualKeyword || keywordModel}
                    onChange={(e) => {
                      setManualKeyword(e.target.value);
                      setSettings({ keywordModel: e.target.value });
                    }}
                    placeholder="예: gemma3:12b"
                  />
                </div>
              ) : (
                <Select
                  value={keywordModel}
                  onValueChange={(v) => v && setSettings({ keywordModel: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="모델 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    {models.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Naver API Credentials */}
      <Card>
        <CardHeader>
          <CardTitle>네이버 API 인증</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Client ID</label>
              <Input
                value={naverClientId}
                onChange={(e) =>
                  setSettings({ naverClientId: e.target.value })
                }
                placeholder="네이버 Client ID"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Client Secret</label>
              <Input
                type="password"
                value={naverClientSecret}
                onChange={(e) =>
                  setSettings({ naverClientSecret: e.target.value })
                }
                placeholder="네이버 Client Secret"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={handleTestNaver}
              disabled={testing || !naverClientId || !naverClientSecret}
              variant="outline"
            >
              {testing && <Loader2 className="size-4 animate-spin mr-2" />}
              연결 테스트
            </Button>
            {testResult && (
              <span
                className={`flex items-center gap-1 text-sm ${testResult.success ? "text-[#03C75A]" : "text-red-500"}`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="size-4" />
                ) : (
                  <XCircle className="size-4" />
                )}
                {testResult.message}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Reference URLs */}
      <Card>
        <CardHeader>
          <CardTitle>참고 글 크롤링</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {refUrls.map((url, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground w-16 shrink-0">
                URL {i + 1}
              </span>
              <Input
                value={url}
                onChange={(e) => {
                  const next = [...refUrls];
                  next[i] = e.target.value;
                  setRefUrls(next);
                }}
                placeholder="https://blog.naver.com/..."
              />
              {crawlResults[i] && (
                <span
                  className={`text-xs shrink-0 ${crawlResults[i] === "성공" ? "text-[#03C75A]" : "text-red-500"}`}
                >
                  {crawlResults[i]}
                </span>
              )}
            </div>
          ))}
          <Button
            onClick={handleCrawl}
            disabled={crawling || refUrls.every((u) => !u.trim())}
            className="bg-[#03C75A] hover:bg-[#02b350] text-white"
          >
            {crawling && <Loader2 className="size-4 animate-spin mr-2" />}
            크롤링 시작
          </Button>

          <Accordion>
            <AccordionItem value="manual">
              <AccordionTrigger className="text-sm">
                직접 입력 (크롤링 실패 시)
              </AccordionTrigger>
              <AccordionContent>
                <Textarea
                  value={manualRef}
                  onChange={(e) => setManualRef(e.target.value)}
                  placeholder="참고할 블로그 글 내용을 직접 붙여넣으세요..."
                  rows={6}
                />
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-[#03C75A] hover:bg-[#02b350] text-white px-8"
        >
          {saving && <Loader2 className="size-4 animate-spin mr-2" />}
          {saved ? "저장 완료!" : "설정 저장"}
        </Button>
      </div>
    </div>
  );
}
