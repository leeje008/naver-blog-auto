"use client";

import { Badge } from "@/components/ui/badge";

interface BlogPreviewProps {
  title: string;
  content: string;
  hashtags: string[];
}

export function BlogPreview({ title, content, hashtags }: BlogPreviewProps) {
  return (
    <div className="rounded-lg border bg-white p-6">
      <h2 className="mb-4 text-xl font-bold">{title}</h2>
      <div
        className="prose prose-sm max-w-none [&_h2]:text-lg [&_h2]:font-bold [&_h2]:mt-6 [&_h2]:mb-3 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:mt-4 [&_h3]:mb-2 [&_p]:mb-3 [&_p]:leading-relaxed [&_img]:rounded-lg [&_img]:my-4"
        dangerouslySetInnerHTML={{ __html: content }}
      />
      {hashtags.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2 border-t pt-4">
          {hashtags.map((tag, i) => (
            <Badge key={i} variant="secondary" className="text-[#03C75A]">
              #{tag}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
