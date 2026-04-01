"use client";

import { useEffect, useState, useMemo } from "react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { getHistory, deleteHistory } from "@/lib/api";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Loader2,
  Trash2,
  FileText,
  Calendar,
  TrendingUp,
  Hash,
} from "lucide-react";

interface HistoryEntry {
  id: string;
  title: string;
  keyword: string;
  created_at: string;
  word_count: number;
  seo_score: number;
  tags: string[];
  content?: string;
}

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tagFilter, setTagFilter] = useState("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await getHistory();
      setEntries(data.entries || []);
    } catch {
      // Silently fail — show empty state
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("정말 삭제하시겠습니까?")) return;
    setDeletingId(id);
    try {
      await deleteHistory(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch {
      alert("삭제에 실패했습니다.");
    } finally {
      setDeletingId(null);
    }
  };

  // All tags
  const allTags = useMemo(() => {
    const tagSet = new Set<string>();
    entries.forEach((e) => e.tags?.forEach((t) => tagSet.add(t)));
    return Array.from(tagSet).sort();
  }, [entries]);

  // Filtered entries
  const filtered = useMemo(() => {
    return entries.filter((e) => {
      const matchSearch =
        !search ||
        e.title.toLowerCase().includes(search.toLowerCase()) ||
        e.keyword.toLowerCase().includes(search.toLowerCase());
      const matchTag =
        tagFilter === "all" || e.tags?.includes(tagFilter);
      return matchSearch && matchTag;
    });
  }, [entries, search, tagFilter]);

  // Stats
  const totalCount = entries.length;
  const thisMonth = entries.filter((e) => {
    const d = new Date(e.created_at);
    const now = new Date();
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  }).length;
  const avgWords =
    entries.length > 0
      ? Math.round(entries.reduce((s, e) => s + e.word_count, 0) / entries.length)
      : 0;
  const avgSeo =
    entries.length > 0
      ? Math.round(entries.reduce((s, e) => s + e.seo_score, 0) / entries.length)
      : 0;

  // Chart data
  const monthlyData = useMemo(() => {
    const map = new Map<string, number>();
    entries.forEach((e) => {
      const d = new Date(e.created_at);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      map.set(key, (map.get(key) || 0) + 1);
    });
    return Array.from(map.entries())
      .sort()
      .map(([month, count]) => ({ month, count }));
  }, [entries]);

  const wordData = useMemo(() => {
    return entries
      .sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      )
      .map((e) => ({
        date: new Date(e.created_at).toLocaleDateString("ko-KR"),
        words: e.word_count,
      }));
  }, [entries]);

  const tagFreqData = useMemo(() => {
    const map = new Map<string, number>();
    entries.forEach((e) =>
      e.tags?.forEach((t) => map.set(t, (map.get(t) || 0) + 1))
    );
    return Array.from(map.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15)
      .map(([tag, count]) => ({ tag, count }));
  }, [entries]);

  if (loading) {
    return (
      <div className="flex items-center justify-center pt-20">
        <Loader2 className="size-8 animate-spin text-[#03C75A]" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold">이력 관리</h1>

      {/* Metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <FileText className="size-5 mx-auto text-[#03C75A] mb-1" />
            <p className="text-2xl font-bold">{totalCount}</p>
            <p className="text-xs text-muted-foreground">전체 글</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <Calendar className="size-5 mx-auto text-[#03C75A] mb-1" />
            <p className="text-2xl font-bold">{thisMonth}</p>
            <p className="text-xs text-muted-foreground">이번 달</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <TrendingUp className="size-5 mx-auto text-[#03C75A] mb-1" />
            <p className="text-2xl font-bold">{avgWords}</p>
            <p className="text-xs text-muted-foreground">평균 단어수</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <Hash className="size-5 mx-auto text-[#03C75A] mb-1" />
            <p className="text-2xl font-bold">{avgSeo}</p>
            <p className="text-xs text-muted-foreground">평균 SEO</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      {entries.length > 0 && (
        <Tabs defaultValue="monthly">
          <TabsList>
            <TabsTrigger value="monthly">월별 작성</TabsTrigger>
            <TabsTrigger value="words">단어수 추이</TabsTrigger>
            <TabsTrigger value="tags">태그 빈도</TabsTrigger>
          </TabsList>

          <TabsContent value="monthly">
            <Card>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#03C75A" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="words">
            <Card>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={wordData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="words"
                      stroke="#03C75A"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tags">
            <Card>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={tagFreqData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="tag" width={100} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#03C75A" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Search + filter */}
      <div className="flex gap-3">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="제목 또는 키워드로 검색..."
          className="flex-1"
        />
        <Select value={tagFilter} onValueChange={(v) => setTagFilter(v ?? "all")}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="태그 필터" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 태그</SelectItem>
            {allTags.map((t) => (
              <SelectItem key={t} value={t}>
                {t}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* History list */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {entries.length === 0
              ? "작성된 글이 없습니다. 글 작성 페이지에서 시작하세요."
              : "검색 결과가 없습니다."}
          </CardContent>
        </Card>
      ) : (
        <Accordion>
          {filtered.map((entry) => (
            <AccordionItem key={entry.id} value={entry.id}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-3 text-left flex-1 mr-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">
                      {entry.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">
                        {new Date(entry.created_at).toLocaleDateString("ko-KR")}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {entry.keyword}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {entry.word_count}자
                      </span>
                      <span className="text-xs font-mono text-[#03C75A]">
                        SEO {entry.seo_score}
                      </span>
                    </div>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {entry.tags && entry.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {entry.tags.map((t, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          #{t}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {entry.content && (
                    <div
                      className="rounded-lg border bg-white p-4 text-sm max-h-60 overflow-y-auto"
                      dangerouslySetInnerHTML={{ __html: entry.content }}
                    />
                  )}
                  <Button
                    onClick={() => handleDelete(entry.id)}
                    disabled={deletingId === entry.id}
                    variant="destructive"
                    size="sm"
                  >
                    {deletingId === entry.id ? (
                      <Loader2 className="size-4 animate-spin mr-2" />
                    ) : (
                      <Trash2 className="size-4 mr-2" />
                    )}
                    삭제
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}
    </div>
  );
}
