"use client";

interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
}

export function StreamingText({ text, isStreaming }: StreamingTextProps) {
  return (
    <div className="relative rounded-lg border bg-muted/30 p-4 font-mono text-sm whitespace-pre-wrap min-h-[120px]">
      {text}
      {isStreaming && (
        <span className="inline-block w-2 h-4 bg-[#03C75A] animate-pulse ml-0.5 align-text-bottom" />
      )}
      {!text && !isStreaming && (
        <span className="text-muted-foreground">
          생성 버튼을 눌러 글 작성을 시작하세요...
        </span>
      )}
    </div>
  );
}
