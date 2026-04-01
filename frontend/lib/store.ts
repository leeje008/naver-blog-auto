import { create } from "zustand";
import type { BlogDraft } from "./types";

interface AppStore {
  // Settings
  naverClientId: string;
  naverClientSecret: string;
  llmModel: string;
  keywordModel: string;
  seoProfile: string;
  setSettings: (partial: Partial<AppStore>) => void;

  // Cross-page
  targetKeyword: string;
  setTargetKeyword: (kw: string) => void;
  generated: BlogDraft | null;
  setGenerated: (draft: BlogDraft | null) => void;
  imageFiles: File[];
  setImageFiles: (files: File[]) => void;
  imageHtmlTags: string[];
  setImageHtmlTags: (tags: string[]) => void;
  revisionHistory: BlogDraft[];
  addRevision: (draft: BlogDraft) => void;
  clearAll: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  // Settings
  naverClientId: "",
  naverClientSecret: "",
  llmModel: "gemma3:12b",
  keywordModel: "gemma3:12b",
  seoProfile: "balanced",
  setSettings: (partial) => set(partial),

  // Cross-page
  targetKeyword: "",
  setTargetKeyword: (kw) => set({ targetKeyword: kw }),
  generated: null,
  setGenerated: (draft) => set({ generated: draft }),
  imageFiles: [],
  setImageFiles: (files) => set({ imageFiles: files }),
  imageHtmlTags: [],
  setImageHtmlTags: (tags) => set({ imageHtmlTags: tags }),
  revisionHistory: [],
  addRevision: (draft) =>
    set((state) => ({ revisionHistory: [...state.revisionHistory, draft] })),
  clearAll: () =>
    set({
      targetKeyword: "",
      generated: null,
      imageFiles: [],
      imageHtmlTags: [],
      revisionHistory: [],
    }),
}));
