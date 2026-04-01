const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// ---------------------------------------------------------------------------
// Generic helpers
// ---------------------------------------------------------------------------

async function fetchJSON<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// SSE streaming helper
// ---------------------------------------------------------------------------

export async function streamSSE(
  path: string,
  body: unknown,
  onToken: (token: string) => void,
  onDone?: () => void
): Promise<string> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No readable stream");
  const decoder = new TextDecoder();
  let full = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value, { stream: true });
    for (const line of text.split("\n")) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") {
          onDone?.();
          return full;
        }
        if (data.startsWith("[ERROR]")) {
          throw new Error(data);
        }
        full += data;
        onToken(data);
      }
    }
  }
  onDone?.();
  return full;
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export async function getModels(): Promise<string[]> {
  const data = await fetchJSON<{ models: string[] }>("/api/settings/models");
  return data.models;
}

export async function getConfig(): Promise<Record<string, unknown>> {
  return fetchJSON("/api/settings/config");
}

export async function putConfig(
  config: Record<string, unknown>
): Promise<void> {
  await fetchJSON("/api/settings/config", {
    method: "PUT",
    body: JSON.stringify(config),
  });
}

export async function testNaver(
  clientId: string,
  clientSecret: string
): Promise<{ success: boolean; message: string }> {
  return fetchJSON("/api/settings/test-naver", {
    method: "POST",
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
  });
}

// ---------------------------------------------------------------------------
// Reference
// ---------------------------------------------------------------------------

export async function crawlReference(
  url: string
): Promise<Record<string, unknown>> {
  return fetchJSON("/api/reference/crawl", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function getReferences(): Promise<Record<string, unknown>[]> {
  const data = await fetchJSON<{ references: Record<string, unknown>[] }>(
    "/api/reference/"
  );
  return data.references;
}

export async function saveReferences(
  refs: Record<string, unknown>[]
): Promise<void> {
  await fetchJSON("/api/reference/", {
    method: "POST",
    body: JSON.stringify(refs),
  });
}

// ---------------------------------------------------------------------------
// Keyword
// ---------------------------------------------------------------------------

export async function analyzeKeywords(payload: {
  seed: string;
  naver_client_id?: string;
  naver_client_secret?: string;
  model?: string;
}) {
  return fetchJSON<{
    seed: string;
    results: Array<{
      keyword: string;
      score: number;
      source: string;
      blog_count: number;
      competition: string;
    }>;
  }>("/api/keyword/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function analyzeTopPosts(payload: {
  keyword: string;
  naver_client_id?: string;
  naver_client_secret?: string;
}) {
  return fetchJSON<Record<string, unknown>>("/api/keyword/top-posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Generate (SSE)
// ---------------------------------------------------------------------------

export function generateDraft(
  payload: {
    target_keyword: string;
    image_descriptions?: string[];
    model?: string;
    template?: string;
  },
  onToken: (t: string) => void,
  onDone?: () => void
) {
  return streamSSE("/api/generate/draft", payload, onToken, onDone);
}

export function reviseDraft(
  payload: {
    original: Record<string, unknown>;
    instruction: string;
    model?: string;
  },
  onToken: (t: string) => void,
  onDone?: () => void
) {
  return streamSSE("/api/generate/revise", payload, onToken, onDone);
}

export function optimizeDraft(
  payload: {
    original: Record<string, unknown>;
    seo_feedback: string;
    target_keyword: string;
    strategy?: string;
    model?: string;
  },
  onToken: (t: string) => void,
  onDone?: () => void
) {
  return streamSSE("/api/generate/optimize", payload, onToken, onDone);
}

// ---------------------------------------------------------------------------
// Image
// ---------------------------------------------------------------------------

export async function analyzeImages(
  formData: FormData
): Promise<{ descriptions: string[] }> {
  const res = await fetch(`${API_URL}/api/image/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// SEO
// ---------------------------------------------------------------------------

export async function analyzeSeo(payload: {
  title: string;
  content: string;
  keyword: string;
  hashtags?: string[];
  image_count?: number;
  profile?: string;
}) {
  return fetchJSON<{
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
  }>("/api/seo/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getSeoProfiles() {
  return fetchJSON<{
    profiles: Record<string, Record<string, number>>;
  }>("/api/seo/profiles");
}

export async function analyzeSeoCustomWeights(payload: {
  title: string;
  content: string;
  keyword: string;
  hashtags?: string[];
  image_count?: number;
  weights: Record<string, number>;
}) {
  return fetchJSON<{
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
  }>("/api/seo/analyze-custom", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

export async function getHistory() {
  return fetchJSON<{
    entries: Array<{
      id: string;
      title: string;
      keyword: string;
      created_at: string;
      word_count: number;
      seo_score: number;
      tags: string[];
      content?: string;
    }>;
  }>("/api/history/");
}

export async function deleteHistory(id: string) {
  return fetchJSON(`/api/history/${id}`, { method: "DELETE" });
}

export async function saveHistory(entry: Record<string, unknown>) {
  return fetchJSON("/api/history/", {
    method: "POST",
    body: JSON.stringify(entry),
  });
}
