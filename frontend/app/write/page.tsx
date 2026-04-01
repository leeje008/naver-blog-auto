"use client";

import { useState, useRef, useCallback } from "react";
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
import { Switch } from "@/components/ui/switch";
import { useAppStore } from "@/lib/store";
import { generateDraft, analyzeImages } from "@/lib/api";
import { StreamingText } from "@/components/StreamingText";
import { BlogPreview } from "@/components/BlogPreview";
import {
  Loader2,
  Upload,
  ImageIcon,
  Rocket,
  RefreshCw,
  Save,
  X,
} from "lucide-react";
import type { BlogDraft } from "@/lib/types";

const TEMPLATES = [
  { value: "default", label: "기본 템플릿" },
  { value: "review", label: "리뷰/체험기" },
  { value: "howto", label: "방법/가이드" },
  { value: "listicle", label: "리스트형" },
  { value: "comparison", label: "비교 분석" },
];

export default function WritePage() {
  const {
    targetKeyword,
    setTargetKeyword,
    llmModel,
    generated,
    setGenerated,
    imageFiles,
    setImageFiles,
    addRevision,
  } = useAppStore();

  const [template, setTemplate] = useState("default");
  const [useVision, setUseVision] = useState(false);
  const [visionAnalyzing, setVisionAnalyzing] = useState(false);
  const [imageDescs, setImageDescs] = useState<string[]>([]);

  const [streamText, setStreamText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Image handling
  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      const arr = Array.from(files);
      setImageFiles([...imageFiles, ...arr]);
      setImageDescs((prev) => [...prev, ...arr.map(() => "")]);
    },
    [imageFiles, setImageFiles]
  );

  const removeImage = (idx: number) => {
    setImageFiles(imageFiles.filter((_, i) => i !== idx));
    setImageDescs((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  // Vision analysis
  const handleVisionAnalyze = async () => {
    if (imageFiles.length === 0) return;
    setVisionAnalyzing(true);
    try {
      const formData = new FormData();
      imageFiles.forEach((f) => formData.append("files", f));
      const data = await analyzeImages(formData);
      setImageDescs(data.descriptions || imageFiles.map(() => ""));
    } catch (e) {
      alert(
        `이미지 분석 실패: ${e instanceof Error ? e.message : "알 수 없는 오류"}`
      );
    } finally {
      setVisionAnalyzing(false);
    }
  };

  // Generate draft
  const handleGenerate = async () => {
    if (!targetKeyword.trim()) return;
    setIsStreaming(true);
    setStreamText("");
    setGenerated(null);

    try {
      const fullText = await generateDraft(
        {
          target_keyword: targetKeyword,
          image_descriptions: imageDescs.filter(Boolean),
          model: llmModel,
          template,
        },
        (token) => setStreamText((prev) => prev + token),
        () => setIsStreaming(false)
      );

      // Try to parse the generated text as JSON
      try {
        const parsed = JSON.parse(fullText) as BlogDraft;
        setGenerated(parsed);
        addRevision(parsed);
      } catch {
        // If not JSON, treat full text as content
        const draft: BlogDraft = {
          title: targetKeyword,
          content: fullText,
          hashtags: [],
          meta: {
            keyword: targetKeyword,
            model: llmModel,
            template,
            created_at: new Date().toISOString(),
          },
        };
        setGenerated(draft);
        addRevision(draft);
      }
    } catch (e) {
      alert(
        `생성 실패: ${e instanceof Error ? e.message : "알 수 없는 오류"}`
      );
      setIsStreaming(false);
    }
  };

  const handleRegenerate = () => {
    setGenerated(null);
    setStreamText("");
    handleGenerate();
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-2xl font-bold">글 작성</h1>

      {/* Target keyword + template */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-2">
              <label className="text-sm font-medium">타겟 키워드</label>
              <Input
                value={targetKeyword}
                onChange={(e) => setTargetKeyword(e.target.value)}
                placeholder="타겟 키워드를 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">템플릿</label>
              <Select value={template} onValueChange={(v) => v && setTemplate(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Image upload */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ImageIcon className="size-5" />
            이미지 업로드
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 p-8 transition-colors hover:border-[#03C75A]/50 cursor-pointer"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="size-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              이미지를 드래그하거나 클릭하여 업로드
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              JPG, PNG, WEBP (여러 장 가능)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>

          {imageFiles.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Switch
                    checked={useVision}
                    onCheckedChange={setUseVision}
                  />
                  <span className="text-sm">Vision 분석 사용</span>
                </div>
                {useVision && (
                  <Button
                    onClick={handleVisionAnalyze}
                    disabled={visionAnalyzing}
                    variant="outline"
                    size="sm"
                  >
                    {visionAnalyzing && (
                      <Loader2 className="size-4 animate-spin mr-2" />
                    )}
                    이미지 분석
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {imageFiles.map((file, i) => (
                  <div key={i} className="relative group">
                    <div className="aspect-square rounded-lg border overflow-hidden bg-muted">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={URL.createObjectURL(file)}
                        alt={`이미지 ${i + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeImage(i)}
                      className="absolute -top-2 -right-2 size-6 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="size-3" />
                    </button>
                    <Input
                      value={imageDescs[i] || ""}
                      onChange={(e) => {
                        const next = [...imageDescs];
                        next[i] = e.target.value;
                        setImageDescs(next);
                      }}
                      placeholder="이미지 설명"
                      className="mt-2 text-xs"
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Generate button */}
      <div className="flex gap-3">
        <Button
          onClick={handleGenerate}
          disabled={isStreaming || !targetKeyword.trim()}
          className="bg-[#03C75A] hover:bg-[#02b350] text-white px-8"
          size="lg"
        >
          {isStreaming ? (
            <Loader2 className="size-4 animate-spin mr-2" />
          ) : (
            <Rocket className="size-4 mr-2" />
          )}
          초안 생성
        </Button>
        {generated && (
          <>
            <Button onClick={handleRegenerate} variant="outline" size="lg">
              <RefreshCw className="size-4 mr-2" />
              재생성
            </Button>
            <Button variant="outline" size="lg">
              <Save className="size-4 mr-2" />
              템플릿으로 저장
            </Button>
          </>
        )}
      </div>

      {/* Streaming output */}
      {(isStreaming || streamText) && !generated && (
        <Card>
          <CardHeader>
            <CardTitle>생성 중...</CardTitle>
          </CardHeader>
          <CardContent>
            <StreamingText text={streamText} isStreaming={isStreaming} />
          </CardContent>
        </Card>
      )}

      {/* Blog preview */}
      {generated && (
        <Card>
          <CardHeader>
            <CardTitle>생성 결과</CardTitle>
          </CardHeader>
          <CardContent>
            <BlogPreview
              title={generated.title}
              content={generated.content}
              hashtags={generated.hashtags}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
