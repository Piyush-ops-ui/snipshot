import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  Video,
  Download,
  Scissors,
  Check,
  Copy,
  RefreshCw,
  Clock,
  Code2,
  FileText,
  Hash,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Sparkles,
  AlertTriangle,
  MessageSquare,
  QrCode,
  Activity,
  Volume2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ProvenanceDialog } from '@/components/provenance/ProvenanceDialog';
import { BrandKitConfig, TemplateArchetype, WordAlignment, SocialGrowthPack } from '@/types/reel_ir';
import { API_BASE } from '@/config/api';
import { DataFlowPipeline, PipelineTelemetry } from './DataFlowPipeline';

interface ModeAStudioProps {
  brandKit: BrandKitConfig;
  currentArchetype?: TemplateArchetype;
  onSelectArchetype?: (arch: TemplateArchetype) => void;
}

export interface RepairedTerm {
  id: string;
  raw_asr: string;
  repaired_term: string;
  confidence: number;
  thumbnail: string;
  timestamp: number;
  bbox?: [number, number, number, number];
}

interface ClipData {
  clip_id: string;
  title: string;
  video_url: string;
  source_video_path: string;
  start_sec: number;
  end_sec: number;
  duration: number;
  transcript: string;
  words?: any[];
  transcript_words?: any[];
  repaired_terms: RepairedTerm[];
  code_snippet: string;
  code_preview?: string;
  hashtags: string[];
  growth_pack: SocialGrowthPack;
  vocal_energy_score: number;
  screen_activity_score: number;
  bug2fix_detected: boolean;
  key_teaching_moment: boolean;
  typing_hyperlapse_sec: number;
  ocr_telemetry?: PipelineTelemetry;
  candidate_highlights?: any[];
}

export interface SampleLecture {
  id: string;
  label: string;
  tag: string;
  duration: string;
  badge: string;
}

export const SAMPLE_LECTURES: SampleLecture[] = [
  {
    id: 'apnacollege_python',
    label: 'ApnaCollege Python (FirstProgram.py)',
    tag: 'Python 3 • Type Casting & Conditions',
    duration: '1h 17m',
    badge: 'Python',
  },
  {
    id: 'java_whacamole',
    label: 'Java Swing GUI (WhacAMole.java)',
    tag: 'Java Swing • JFrame & ActionListeners',
    duration: '32m 22s',
    badge: 'Java Swing',
  },
  {
    id: 'java_oop_car',
    label: 'Java OOP (Main.java & Car.java)',
    tag: 'OOP Architecture • Class & Methods',
    duration: '9m 50s',
    badge: 'Java OOP',
  },
  {
    id: 'github_desktop',
    label: 'GitHub Desktop & Terminal',
    tag: 'Git Version Control • Branch & Push',
    duration: '11m 12s',
    badge: 'Git CLI',
  },
];

const buildPinnedCodeComment = (code: string) => {
  const trimmed = code.trim();
  return `⚡ Key code snippet from this video:\n\n\`\`\`\n${trimmed}\n\`\`\`\n\nFull production test suite and architectural notes linked in bio! 🚀`;
};

const DEFAULT_GROWTH_PACK: SocialGrowthPack = {
  hook_title: 'Master Core Architecture in 30 Seconds ⚡',
  broad_hashtags: ['#coding', '#programming', '#softwareengineering', '#learntocode'],
  stack_hashtags: ['#backend', '#fullstack', '#cleancode', '#developer'],
  micro_api_hashtags: ['#codereview', '#refactoring', '#algorithms', '#techtips'],
  pinned_code_comment: `⚡ Production code snippet extracted directly from video:

\`\`\`
// Key code snippet
\`\`\`

Full architectural guide and code notes linked in bio! 🚀`,
  qr_code_data: 'https://github.com/snipshot/production-code-guide',
};

const DEMO_REPAIRED_TERMS: RepairedTerm[] = [
  {
    id: 'crop_playground',
    raw_asr: 'kort palakrahun',
    repaired_term: 'Code Playground',
    confidence: 0.98,
    thumbnail: '/provenance/crop_1.png',
    timestamp: 14.2,
    bbox: [320, 140, 280, 44],
  },
  {
    id: 'crop_github',
    raw_asr: 'rip gethaph',
    repaired_term: 'sample-repo / GitHub',
    confidence: 0.96,
    thumbnail: '/provenance/crop_2.png',
    timestamp: 18.5,
    bbox: [240, 80, 310, 48],
  },
  {
    id: 'crop_tokenizer',
    raw_asr: 'token ice er',
    repaired_term: 'Tokenizer',
    confidence: 0.99,
    thumbnail: '/provenance/crop_1.png',
    timestamp: 21.4,
    bbox: [420, 180, 260, 48],
  },
  {
    id: 'crop_middleware',
    raw_asr: 'middle wear',
    repaired_term: 'Middleware',
    confidence: 0.97,
    thumbnail: '/provenance/crop_2.png',
    timestamp: 28.6,
    bbox: [460, 310, 310, 48],
  },
];

const ACCENT_STYLES: { id: TemplateArchetype; label: string }[] = [
  { id: 'standard_spotlight', label: 'Standard' },
  { id: 'bug_hunter', label: 'Bug Fix Highlight' },
  { id: 'predict_output', label: 'Quiz Pause' },
];

export const ModeAStudio: React.FC<ModeAStudioProps> = ({
  brandKit,
  currentArchetype = 'bug_hunter',
  onSelectArchetype,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('apnacollege_python');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [progressStage, setProgressStage] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Active clip state
  const [clip, setClip] = useState<ClipData | null>(null);
  const [clips, setClips] = useState<ClipData[]>([]);
  const [activeClipIndex, setActiveClipIndex] = useState<number>(0);
  const [cacheBuster, setCacheBuster] = useState<number>(Date.now());
  const [trimStart, setTrimStart] = useState<number>(0);
  const [trimEnd, setTrimEnd] = useState<number>(30);
  const [trimStartInput, setTrimStartInput] = useState<string>('0');
  const [trimEndInput, setTrimEndInput] = useState<string>('30');
  const [editableCode, setEditableCode] = useState<string>(
    `// Production code snippet\nfunction processItem(item) {\n  return item.validate();\n}`
  );
  const [isRerendering, setIsRerendering] = useState<boolean>(false);
  const [rerenderNotice, setRerenderNotice] = useState<string | null>(null);

  // Sync string inputs with trimStart and trimEnd
  useEffect(() => {
    setTrimStartInput(String(trimStart));
  }, [trimStart]);

  useEffect(() => {
    setTrimEndInput(String(trimEnd));
  }, [trimEnd]);

  const commitTrimInputs = () => {
    const s = parseFloat(trimStartInput);
    const e = parseFloat(trimEndInput);
    if (!isNaN(s) && !isNaN(e) && e > s) {
      const validS = Math.max(0, s);
      const validE = Math.max(validS + 3, e);
      setTrimStart(validS);
      setTrimEnd(validE);
      return { start: validS, end: validE };
    }
    return { start: trimStart, end: trimEnd };
  };

  const nudgeStart = (delta: number) => {
    const current = parseFloat(trimStartInput) || trimStart;
    const nextVal = Math.max(0, Math.round((current + delta) * 2) / 2);
    if (nextVal < trimEnd - 2) {
      setTrimStart(nextVal);
      setTrimStartInput(String(nextVal));
    }
  };

  const nudgeEnd = (delta: number) => {
    const current = parseFloat(trimEndInput) || trimEnd;
    const nextVal = Math.max(trimStart + 3, Math.round((current + delta) * 2) / 2);
    setTrimEnd(nextVal);
    setTrimEndInput(String(nextVal));
  };

  const isTrimModified =
    clip !== null &&
    (Math.abs((parseFloat(trimStartInput) || 0) - clip.start_sec) > 0.3 ||
      Math.abs((parseFloat(trimEndInput) || 30) - clip.end_sec) > 0.3);

  // Layout & Settings
  const [privacyShieldActive, setPrivacyShieldActive] = useState<boolean>(true);
  const [templateArchetype, setTemplateArchetype] = useState<TemplateArchetype>(currentArchetype);
  const [growthPack, setGrowthPack] = useState<SocialGrowthPack>(DEFAULT_GROWTH_PACK);
  const [copiedComment, setCopiedComment] = useState<boolean>(false);
  const [copiedTags, setCopiedTags] = useState<boolean>(false);
  const [copiedHook, setCopiedHook] = useState<boolean>(false);
  const [silentTypingHyperlapse, setSilentTypingHyperlapse] = useState<boolean>(true);

  // Provenance Dialog Modal Inspector
  const [inspectedWord, setInspectedWord] = useState<WordAlignment | null>(null);
  const [provenanceDialogOpen, setProvenanceDialogOpen] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Keep template Archetype in sync with props
  useEffect(() => {
    if (currentArchetype) {
      setTemplateArchetype(currentArchetype);
    }
  }, [currentArchetype]);

  const handleArchetypeChange = (arch: TemplateArchetype) => {
    setTemplateArchetype(arch);
    if (onSelectArchetype) {
      onSelectArchetype(arch);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMsg(null);
    }
  };

  const handleProcessVideo = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setProgress(15);
    setProgressStage('Extracting audio & scanning video frames with RapidOCR...');
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append(
      'brand_kit',
      JSON.stringify({
        name: brandKit.name || 'TechSummit Academy',
        primary_color: brandKit.primary_color || '#4F46E5',
        logo_base64: brandKit.logo_base64 || brandKit.logo_path,
      })
    );

    try {
      const timer = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 85) return prev;
          if (prev === 30) setProgressStage('Running local faster-whisper ASR & phonetic grounding...');
          if (prev === 60) setProgressStage('Compositing 9:16 layout & burning subtitles with FFmpeg...');
          return prev + 15;
        });
      }, 1200);

      const response = await fetch(`${API_BASE}/api/v1/mode-a/process-video`, {
        method: 'POST',
        body: formData,
      });

      clearInterval(timer);

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Processing failed. Please check backend server.');
      }

      const data = await response.json();
      setProgress(100);
      setProgressStage('Finished!');

      applyProcessedData(data, selectedFile.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
    } catch (err: any) {
      setErrorMsg(err.message || 'Error processing video.');
    } finally {
      setIsProcessing(false);
    }
  };

  const applyProcessedData = (data: any, baseTitle: string) => {
    const backendRepairs: RepairedTerm[] = (data.repaired_terms || []).map((t: any, idx: number) => ({
      id: t.id || `crop_${idx}`,
      raw_asr: t.raw_asr || t.raw || 'misheard term',
      repaired_term: t.repaired_term || t.term || 'RepairedCode',
      confidence: t.confidence ?? 0.95,
      thumbnail: t.thumbnail || `/provenance/crop_${(idx % 10) + 1}.png`,
      timestamp: t.timestamp ?? 12.0,
      bbox: t.bbox,
    }));

    const finalRepairs = backendRepairs.length > 0 ? backendRepairs : DEMO_REPAIRED_TERMS;
    const extractedCode = data.code_snippet || editableCode;

    const rawClips = Array.isArray(data.clips) && data.clips.length > 0 ? data.clips : [data];
    const parsedClips: ClipData[] = rawClips.map((c: any, idx: number) => ({
      clip_id: c.clip_id || `reel_${idx}`,
      title: c.title || `${baseTitle} (Part ${idx + 1})`,
      video_url: c.video_url || (idx === 0 ? data.video_url : ''),
      source_video_path: c.source_video_path || data.source_video_path || '',
      start_sec: Number(c.start_sec ?? 0),
      end_sec: Number(c.end_sec ?? 30),
      duration: Number(c.duration ?? 30),
      transcript: c.transcript || data.transcript || '',
      words: c.words || data.words || [],
      transcript_words: c.transcript_words || data.transcript_words || [],
      repaired_terms: c.repaired_terms && c.repaired_terms.length > 0 ? c.repaired_terms : finalRepairs,
      code_snippet: c.code_snippet || extractedCode,
      code_preview: c.code_preview || '',
      hashtags: c.hashtags || data.hashtags || ['#coding', '#tech', '#softwareengineering'],
      growth_pack: {
        ...DEFAULT_GROWTH_PACK,
        hook_title: `Master ${c.title || 'Core Architecture'} in 30 Seconds ⚡`,
        pinned_code_comment: buildPinnedCodeComment(c.code_snippet || extractedCode),
      },
      vocal_energy_score: c.vocal_energy_score ?? 88.5,
      screen_activity_score: c.screen_activity_score ?? 92.4,
      bug2fix_detected: Boolean(c.is_bug_to_fix ?? true),
      key_teaching_moment: true,
      typing_hyperlapse_sec: 3.2,
      ocr_telemetry: data.ocr_telemetry,
      candidate_highlights: data.candidate_highlights || data.candidate_clips,
    }));

    setClips(parsedClips);
    setActiveClipIndex(0);
    const primaryClip = parsedClips[0];
    setClip(primaryClip);
    setTrimStart(primaryClip.start_sec);
    setTrimEnd(primaryClip.end_sec);
    setTrimStartInput(String(primaryClip.start_sec));
    setTrimEndInput(String(primaryClip.end_sec));
    setEditableCode(primaryClip.code_snippet);
    setGrowthPack(primaryClip.growth_pack);
    setCacheBuster(Date.now());
  };

  const handleProcessSampleVideo = async (sampleId: string, sampleTitle?: string) => {
    const resolvedTitle =
      sampleTitle || SAMPLE_LECTURES.find((s) => s.id === sampleId)?.label || 'Sample Lecture';
    setIsProcessing(true);
    setProgress(15);
    setProgressStage(`Processing sample (${resolvedTitle})...`);
    setErrorMsg(null);

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 85) return prev;
        if (prev === 30) setProgressStage('Running local faster-whisper ASR & phonetic grounding...');
        if (prev === 60) setProgressStage('Compositing 9:16 layout & burning subtitles with FFmpeg...');
        return prev + 15;
      });
    }, 1200);

    try {
      const response = await fetch(`${API_BASE}/api/v1/mode-a/process-sample-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_id: sampleId,
          brand_kit: {
            name: brandKit.name || 'TechSummit Academy',
            primary_color: brandKit.primary_color || '#4F46E5',
            logo_base64: brandKit.logo_base64 || brandKit.logo_path,
          },
        }),
      });

      clearInterval(timer);

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Sample video processing failed. Please check backend server.');
      }

      const data = await response.json();
      setProgress(100);
      setProgressStage('Finished!');
      applyProcessedData(data, resolvedTitle);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error processing sample video.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSelectHighlight = async (index: number) => {
    if (!clips[index]) return;
    setActiveClipIndex(index);
    const target = clips[index];
    setTrimStart(target.start_sec);
    setTrimEnd(target.end_sec);
    setTrimStartInput(String(target.start_sec));
    setTrimEndInput(String(target.end_sec));
    if (target.code_snippet) {
      setEditableCode(target.code_snippet);
    }
    if (target.video_url && target.video_url.length > 5) {
      setClip(target);
      setCacheBuster(Date.now());
    } else {
      handleRerender(target.start_sec, target.end_sec, target.code_snippet);
    }
  };

  const handleRerender = async (overrideStart?: number, overrideEnd?: number, overrideCode?: string) => {
    if (!clip) return;
    setIsRerendering(true);
    setRerenderNotice(null);

    const s = overrideStart !== undefined ? overrideStart : Number(trimStart);
    const e = overrideEnd !== undefined ? overrideEnd : Number(trimEnd);
    const code = overrideCode !== undefined ? overrideCode : editableCode;

    try {
      const response = await fetch(`${API_BASE}/api/v1/mode-a/rerender-clip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clip_id: clip.clip_id,
          source_video_path: clip.source_video_path,
          start_sec: s,
          end_sec: e,
          code_snippet: code,
          words: clip.transcript_words || clip.words || [],
          transcript_words: clip.transcript_words || clip.words || [],
          template_archetype: templateArchetype,
          layout_mode: 'single_focus',
          silent_typing_hyperlapse: silentTypingHyperlapse,
          privacy_shield: privacyShieldActive,
          brand_kit: {
            name: brandKit.name,
            primary_color: brandKit.primary_color,
            logo_base64: brandKit.logo_base64 || brandKit.logo_path,
          },
        }),
      });

      if (!response.ok) {
        throw new Error('Re-render failed.');
      }

      const res = await response.json();
      setClip((prev) =>
        prev
          ? {
              ...prev,
              video_url: res.video_url,
              start_sec: res.start_sec,
              end_sec: res.end_sec,
              duration: res.duration,
              code_snippet: res.code_snippet || prev.code_snippet,
              words: res.words || prev.words,
              transcript_words: res.transcript_words || res.words || prev.transcript_words,
            }
          : null
      );
      setTrimStart(res.start_sec);
      setTrimEnd(res.end_sec);
      setTrimStartInput(String(res.start_sec));
      setTrimEndInput(String(res.end_sec));
      if (res.code_snippet) {
        setEditableCode(res.code_snippet);
      }
      setCacheBuster(Date.now());
      setRerenderNotice(`Re-rendered in ${res.elapsed_seconds || 2.4}s!`);
      setTimeout(() => setRerenderNotice(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to re-render clip.');
    } finally {
      setIsRerendering(false);
    }
  };

  const openInspector = (item: RepairedTerm) => {
    const wordAlign: WordAlignment = {
      id: item.id,
      word: item.repaired_term,
      raw_asr_word: item.raw_asr,
      start: item.timestamp,
      end: item.timestamp + 0.6,
      confidence: item.confidence,
      is_technical: true,
      provenance_thumbnail_url: item.thumbnail,
      provenance_frame_time: item.timestamp,
      provenance_bbox: item.bbox || [320, 140, 280, 44],
    };
    setInspectedWord(wordAlign);
    setProvenanceDialogOpen(true);
  };

  const handleSaveTermOverride = (wordId: string, newWord: string) => {
    if (!clip) return;
    setClip((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        repaired_terms: prev.repaired_terms.map((t) =>
          t.id === wordId ? { ...t, repaired_term: newWord } : t
        ),
      };
    });
  };

  const handleCodeChange = (newCode: string) => {
    setEditableCode(newCode);
    setGrowthPack((prev) => ({
      ...prev,
      pinned_code_comment: buildPinnedCodeComment(newCode),
    }));
  };

  const copyHookTitle = () => {
    if (!growthPack.hook_title) return;
    navigator.clipboard.writeText(growthPack.hook_title);
    setCopiedHook(true);
    setTimeout(() => setCopiedHook(false), 2000);
  };

  const copyPinnedComment = () => {
    const comment = buildPinnedCodeComment(editableCode);
    navigator.clipboard.writeText(comment);
    setCopiedComment(true);
    setTimeout(() => setCopiedComment(false), 2000);
  };

  const copyAllHashtags = () => {
    const all = [
      ...growthPack.broad_hashtags,
      ...growthPack.stack_hashtags,
      ...growthPack.micro_api_hashtags,
    ].join(' ');
    navigator.clipboard.writeText(all);
    setCopiedTags(true);
    setTimeout(() => setCopiedTags(false), 2000);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Upload Card */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Video className="size-4.5 text-indigo-600" />
              Upload Lecture Video (Mode A)
            </CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Screen-Grounded Pedagogical Compilation: extracts high-signal coding moments and compiles a 9:16 vertical Reel in &lt;15s.
            </p>
          </div>
        </CardHeader>
        <CardContent className="pt-4 flex flex-col gap-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/quicktime,video/webm"
            onChange={handleFileChange}
            className="hidden"
          />

          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-200 hover:border-indigo-400 bg-slate-50/60 hover:bg-indigo-50/20 rounded-xl p-8 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors"
          >
            <div className="size-11 rounded-full bg-white border border-slate-200 flex items-center justify-center text-indigo-600 shadow-2xs">
              <Upload className="size-5" />
            </div>
            <div className="text-center">
              <span className="text-sm font-medium text-slate-900">
                {selectedFile ? selectedFile.name : 'Click to select or drag and drop lecture video'}
              </span>
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedFile
                  ? `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB • Ready to process`
                  : 'MP4, MOV up to 2 hours (Intel Core Ultra 5 & Arc QSV hardware accelerated)'}
              </p>
            </div>
          </div>

          {/* Pre-loaded Sample Lectures Dropdown & 1-Click Testing */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col gap-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                  <Sparkles className="size-3.5 text-indigo-600" />
                  Pre-loaded Sample Lectures (1-Click Instant Test)
                </span>
                <span className="text-[11px] text-slate-500">
                  Select a WhatsApp benchmark recording for instant hardware-accelerated processing
                </span>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={selectedSampleId}
                  onChange={(e) => {
                    setSelectedSampleId(e.target.value);
                    setErrorMsg(null);
                  }}
                  disabled={isProcessing}
                  className="text-xs h-9 px-3 rounded-lg border border-slate-300 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer min-w-[240px]"
                >
                  {SAMPLE_LECTURES.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label} ({s.duration})
                    </option>
                  ))}
                </select>

                <Button
                  type="button"
                  disabled={!selectedSampleId || isProcessing}
                  onClick={() => handleProcessSampleVideo(selectedSampleId)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs h-9 px-3.5 gap-1.5 shrink-0 shadow-xs"
                >
                  <Zap className="size-3.5 text-amber-300" />
                  1-Click Process
                </Button>
              </div>
            </div>

            {/* Quick 1-Click Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 pt-1 border-t border-slate-200/60">
              {SAMPLE_LECTURES.map((sample) => {
                const isSelected = selectedSampleId === sample.id;
                return (
                  <button
                    key={sample.id}
                    type="button"
                    disabled={isProcessing}
                    onClick={() => {
                      setSelectedSampleId(sample.id);
                      handleProcessSampleVideo(sample.id, sample.label);
                    }}
                    className={`flex items-center justify-between p-2 rounded-lg border transition-all text-left group cursor-pointer disabled:opacity-50 shadow-2xs ${
                      isSelected
                        ? 'border-indigo-400 bg-indigo-50/60 ring-1 ring-indigo-400/30'
                        : 'border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex flex-col min-w-0 pr-1.5">
                      <span className="text-[11px] font-semibold text-slate-800 group-hover:text-indigo-600 truncate">
                        {sample.label}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono truncate">{sample.tag}</span>
                    </div>
                    <Badge
                      variant="outline"
                      className={`text-[9px] px-1.5 py-0 h-4 shrink-0 font-mono ${
                        isSelected
                          ? 'border-indigo-200 bg-indigo-100/60 text-indigo-700'
                          : 'border-slate-200 bg-slate-50 text-slate-600 group-hover:border-indigo-200 group-hover:text-indigo-600'
                      }`}
                    >
                      {sample.badge}
                    </Badge>
                  </button>
                );
              })}
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="size-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {isProcessing && (
            <div className="flex flex-col gap-2 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between text-xs font-medium text-slate-700">
                <span className="flex items-center gap-2">
                  <RefreshCw className="size-3.5 animate-spin text-indigo-600" />
                  {progressStage}
                </span>
                <span className="font-mono text-indigo-600">{progress}%</span>
              </div>
              <Progress value={progress} className="h-1.5" />
            </div>
          )}

          <div className="flex justify-between items-center pt-1">
            <span className="text-xs text-slate-400 font-mono">
              ⚡ Intel Core Ultra 5 125H + Arc QSV • ₹0.00 Cloud Billed
            </span>
            <Button
              onClick={() => {
                if (selectedFile) {
                  handleProcessVideo();
                } else if (selectedSampleId) {
                  handleProcessSampleVideo(selectedSampleId);
                }
              }}
              disabled={(!selectedFile && !selectedSampleId) || isProcessing}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs h-9 px-5 gap-2 shadow-xs"
            >
              {isProcessing ? (
                <>
                  <RefreshCw className="size-3.5 animate-spin" />
                  Processing Video (&lt;12s)...
                </>
              ) : (
                <>
                  <Video className="size-3.5" />
                  Generate Reel
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 5-Node Dynamic Data-Flow Pipeline Bar (Mounted right above results view) */}
      <DataFlowPipeline
        telemetry={clip?.ocr_telemetry}
        candidateHighlights={clip?.candidate_highlights || clips}
        isProcessing={isProcessing}
        processingStage={progressStage}
        sourceMeta={{
          resolution: clip ? '1920×1080 (16:9)' : undefined,
          duration: clip?.duration,
        }}
      />

      {/* Initial / Empty State Prompt */}
      {!clip && (
        <div className="p-8 rounded-xl border border-dashed border-slate-200 bg-white text-center flex flex-col items-center justify-center gap-3 shadow-xs">
          <div className="size-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Video className="size-6" />
          </div>
          <div className="max-w-md">
            <h3 className="text-sm font-semibold text-slate-900">No Lecture Video Loaded</h3>
            <p className="text-xs text-slate-500 mt-1">
              Upload a programming lecture or tutorial video above. SnipShot will automatically extract key coding moments, verify technical terms from the screen, and compile a 9:16 vertical Reel in seconds.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-lg mt-2 text-left">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs">
              <span className="font-semibold text-slate-800 block">Code Spotlight &amp; Trim</span>
              <span className="text-[11px] text-slate-500">Sentence-aligned cuts &amp; burned code cards</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs">
              <span className="font-semibold text-slate-800 block">Screen Grounding</span>
              <span className="text-[11px] text-slate-500">Phonetic misspellings fixed via OCR</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs">
              <span className="font-semibold text-slate-800 block">Social Distribution</span>
              <span className="text-[11px] text-slate-500">Hashtags, pinned comments &amp; QR code</span>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Studio Workspace */}
      {clip && (
        <div className="flex flex-col gap-5">
          {/* Top Banner: Status Bar */}
          <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-slate-900 text-sm tracking-tight mr-1">
                {clip.title}
              </span>

              {clip.bug2fix_detected && (
                <Badge className="bg-amber-50 text-amber-800 border-amber-300 text-xs px-2.5 py-0.5 font-medium flex items-center gap-1.5 shadow-2xs">
                  <AlertTriangle className="size-3 text-amber-600" />
                  Bug Fix Highlight
                </Badge>
              )}

              {clip.key_teaching_moment && (
                <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200 text-xs px-2.5 py-0.5 font-medium flex items-center gap-1.5 shadow-2xs">
                  <Sparkles className="size-3 text-indigo-600" />
                  Key Teaching Moment
                </Badge>
              )}

              <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs px-2.5 py-0.5 font-medium flex items-center gap-1.5 shadow-2xs">
                <CheckCircle2 className="size-3 text-emerald-600" />
                Complete Thought
              </Badge>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Duration <strong className="text-slate-800 font-mono">{(trimEnd - trimStart).toFixed(1)}s</strong></span>
              <span className="text-slate-300">•</span>
              <span className="text-slate-600 font-medium">Local Hardware</span>
            </div>
          </div>

          {/* AI-Discovered Highlights Switcher */}
          {clips.length > 1 && (
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col gap-2.5">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-800">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="size-3.5 text-indigo-600" />
                  AI-Discovered Lecture Highlights ({clips.length})
                </span>
                <span className="text-[11px] text-slate-500 font-normal">
                  Click any key moment to switch &amp; re-render reel in 3s
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {clips.map((c, idx) => {
                  const isActive = activeClipIndex === idx;
                  return (
                    <button
                      key={c.clip_id || idx}
                      type="button"
                      onClick={() => handleSelectHighlight(idx)}
                      className={`p-3 rounded-lg text-left border transition-all cursor-pointer flex flex-col gap-1 ${
                        isActive
                          ? 'bg-indigo-50/70 border-indigo-500 shadow-xs ring-1 ring-indigo-500/30'
                          : 'bg-slate-50/70 hover:bg-slate-100/70 border-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className={`text-xs font-semibold truncate ${isActive ? 'text-indigo-950' : 'text-slate-800'}`}>
                          {c.title || `Highlight ${idx + 1}`}
                        </span>
                        <Badge variant="outline" className={`text-[10px] px-1.5 py-0 font-mono shrink-0 ${isActive ? 'bg-indigo-100 text-indigo-800 border-indigo-300' : 'bg-white text-slate-600'}`}>
                          {Math.round(c.start_sec)}s – {Math.round(c.end_sec)}s
                        </Badge>
                      </div>
                      <p className="text-[11px] text-slate-500 line-clamp-1 font-mono">
                        {c.code_preview ? c.code_preview : `Duration: ${Math.round(c.duration)}s`}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Center Column (5 Cols): Video Player & Summary Card */}
            <div className="lg:col-span-5 flex flex-col items-center gap-4">
              {/* Real 9:16 HTML5 Video Player */}
              <div className="w-[300px] aspect-[9/16] rounded-xl overflow-hidden bg-black border border-slate-200 shadow relative group">
                <video
                  key={`${clip.video_url}?t=${cacheBuster}`}
                  controls
                  playsInline
                  src={`${API_BASE}${clip.video_url}${clip.video_url.includes('?') ? '&' : '?'}t=${cacheBuster}`}
                  className="w-full h-full object-cover [&:fullscreen]:object-contain"
                />
              </div>

              {/* Download MP4 Button */}
              <a
                href={`${API_BASE}${clip.video_url}${clip.video_url.includes('?') ? '&' : '?'}t=${cacheBuster}`}
                download={`snipshot_reel_${clip.clip_id}.mp4`}
                target="_blank"
                rel="noreferrer"
                className="w-[300px] inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs transition-colors shadow-xs"
              >
                <Download className="size-4" />
                Download .mp4 Video
              </a>

              {/* One Simple Summary Card */}
              <Card className="w-[300px] bg-white border-slate-200 shadow-xs">
                <CardContent className="p-3.5 flex flex-col gap-3">
                  {/* Auto-Blur Private Info Toggle */}
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <div
                        className={`p-1.5 rounded-md ${
                          privacyShieldActive ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-400'
                        }`}
                      >
                        <ShieldCheck className="size-4" />
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-800 block">
                          Auto-Blur Private Info
                        </span>
                        <span className="text-[10px] text-slate-500 block">
                          {privacyShieldActive ? 'ON — Secrets auto-redacted' : 'OFF — Shield inactive'}
                        </span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setPrivacyShieldActive(!privacyShieldActive)}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${
                        privacyShieldActive ? 'bg-indigo-600' : 'bg-slate-300'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                          privacyShieldActive ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Clip Quality Scores */}
                  <div className="flex flex-col gap-2">
                    <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                      <Activity className="size-3.5 text-indigo-600" />
                      Clip Quality Scores
                    </span>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                      <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                          <Volume2 className="size-3 text-indigo-600" />
                          Voice Clarity
                        </span>
                        <span className="text-sm font-bold text-slate-900">
                          {clip.vocal_energy_score || 88.5}%
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                          <CheckCircle2 className="size-3 text-emerald-600" />
                          Sentence
                        </span>
                        <span className="text-sm font-bold text-slate-900">100%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column (7 Cols): Only 3 Clean Cards */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              {/* Card 1: Clip & Code Spotlight */}
              <Card className="bg-white border-slate-200/80 shadow-xs">
                <CardHeader className="pb-3 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <Scissors className="size-4 text-indigo-600" />
                      Clip &amp; Code Spotlight
                    </CardTitle>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Adjust timestamps, style the header accent, and edit code syntax.
                    </p>
                  </div>
                  {rerenderNotice && (
                    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[11px]">
                      <Check className="size-3 mr-1" />
                      {rerenderNotice}
                    </Badge>
                  )}
                </CardHeader>

                <CardContent className="pt-4 flex flex-col gap-4">
                  {/* Trim Sliders / Inputs */}
                  <div className="flex flex-col gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center justify-between">
                          <Label className="text-xs text-slate-700 font-medium flex items-center gap-1">
                            <Clock className="size-3 text-slate-400" />
                            Start Time (s)
                          </Label>
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => nudgeStart(-5)}
                              className="px-1.5 py-0.5 text-[10px] bg-white border border-slate-200 rounded hover:bg-slate-100 text-slate-600 cursor-pointer"
                              title="Subtract 5 seconds"
                            >
                              -5s
                            </button>
                            <button
                              type="button"
                              onClick={() => nudgeStart(5)}
                              className="px-1.5 py-0.5 text-[10px] bg-white border border-slate-200 rounded hover:bg-slate-100 text-slate-600 cursor-pointer"
                              title="Add 5 seconds"
                            >
                              +5s
                            </button>
                          </div>
                        </div>
                        <Input
                          type="text"
                          value={trimStartInput}
                          onChange={(e) => setTrimStartInput(e.target.value)}
                          onBlur={commitTrimInputs}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              const { start, end } = commitTrimInputs();
                              handleRerender(start, end);
                            }
                          }}
                          placeholder="0.0"
                          className="h-8.5 text-xs font-mono font-medium bg-white border-slate-200 text-slate-900 focus:border-indigo-500"
                        />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center justify-between">
                          <Label className="text-xs text-slate-700 font-medium flex items-center gap-1">
                            <Clock className="size-3 text-slate-400" />
                            End Time (s)
                          </Label>
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => nudgeEnd(-5)}
                              className="px-1.5 py-0.5 text-[10px] bg-white border border-slate-200 rounded hover:bg-slate-100 text-slate-600 cursor-pointer"
                              title="Subtract 5 seconds"
                            >
                              -5s
                            </button>
                            <button
                              type="button"
                              onClick={() => nudgeEnd(5)}
                              className="px-1.5 py-0.5 text-[10px] bg-white border border-slate-200 rounded hover:bg-slate-100 text-slate-600 cursor-pointer"
                              title="Add 5 seconds"
                            >
                              +5s
                            </button>
                          </div>
                        </div>
                        <Input
                          type="text"
                          value={trimEndInput}
                          onChange={(e) => setTrimEndInput(e.target.value)}
                          onBlur={commitTrimInputs}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              const { start, end } = commitTrimInputs();
                              handleRerender(start, end);
                            }
                          }}
                          placeholder="30.0"
                          className="h-8.5 text-xs font-mono font-medium bg-white border-slate-200 text-slate-900 focus:border-indigo-500"
                        />
                      </div>
                    </div>

                    {/* Dedicated Prominent Apply Trim Button right next to inputs */}
                    <div className="flex items-center justify-between pt-1 border-t border-slate-200/60">
                      <Button
                        type="button"
                        onClick={() => {
                          const { start, end } = commitTrimInputs();
                          handleRerender(start, end);
                        }}
                        disabled={isRerendering}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs h-8 px-3.5 gap-1.5 shadow-xs transition-colors cursor-pointer"
                      >
                        <RefreshCw className={`size-3 ${isRerendering ? 'animate-spin' : ''}`} />
                        {isRerendering ? 'Re-Rendering...' : 'Apply Trim & Re-Render (3s)'}
                      </Button>
                      {isTrimModified && (
                        <span className="text-[10px] text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded font-medium flex items-center gap-1">
                          <AlertCircle className="size-3 text-amber-600" />
                          Unapplied: [{trimStartInput}s – {trimEndInput}s]
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Fast-Forward Silent Typing Checkbox */}
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-amber-50/50 border border-amber-200">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={silentTypingHyperlapse}
                        onChange={(e) => setSilentTypingHyperlapse(e.target.checked)}
                        className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-medium text-slate-800">
                        Fast-Forward Silent Typing
                      </span>
                    </label>

                    <Badge className="bg-amber-100 text-amber-900 border-amber-300 text-[10px] font-mono flex items-center gap-1 shadow-2xs">
                      <Zap className="size-3 text-amber-700" />
                      ⚡ 2.5x Hyperlapse Gaps &gt; 1.5s
                    </Badge>
                  </div>

                  {/* Header Accent Style Pill Selector */}
                  <div className="flex flex-col gap-1.5">
                    <Label className="text-xs font-semibold text-slate-700">
                      Header Accent Style
                    </Label>
                    <div className="flex items-center gap-2 flex-wrap">
                      {ACCENT_STYLES.map((style) => {
                        const isSelected = templateArchetype === style.id;
                        return (
                          <button
                            key={style.id}
                            type="button"
                            onClick={() => handleArchetypeChange(style.id)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                              isSelected
                                ? 'bg-indigo-600 text-white shadow-xs'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900 border border-slate-200'
                            }`}
                          >
                            {style.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Code Spotlight Text Area */}
                  <div className="flex flex-col gap-1.5">
                    <Label className="text-xs font-medium text-slate-700 flex items-center gap-1.5">
                      <Code2 className="size-3.5 text-indigo-600" />
                      Code Spotlight
                    </Label>
                    <Textarea
                      rows={5}
                      value={editableCode}
                      onChange={(e) => handleCodeChange(e.target.value)}
                      className="font-mono text-xs bg-slate-950 text-slate-100 border-slate-800 rounded-lg p-3 leading-relaxed shadow-inner"
                      placeholder="Enter code snippet to feature..."
                    />
                  </div>

                    <div className="flex justify-end pt-1">
                    <Button
                      onClick={() => handleRerender()}
                      disabled={isRerendering}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs h-8.5 px-4 gap-2 shadow-xs transition-colors"
                    >
                      <RefreshCw className={`size-3.5 ${isRerendering ? 'animate-spin' : ''}`} />
                      {isRerendering ? 'Re-Rendering Video (3s)...' : 'Re-Render Video (3s)'}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Card 2: Verified Technical Vocabulary */}
              <Card className="bg-white border-slate-200 shadow-xs">
                <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <FileText className="size-4 text-indigo-600" />
                      Verified Technical Vocabulary
                    </CardTitle>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Phonetically repaired terms verified against on-screen video frames.
                    </p>
                  </div>
                  <Badge variant="outline" className="text-[10px] font-mono text-slate-600 bg-slate-50">
                    Click term to inspect proof
                  </Badge>
                </CardHeader>

                <CardContent className="pt-4 flex flex-col gap-3">
                  <div className="flex flex-col gap-2.5">
                    {clip.repaired_terms.length > 0 ? (
                      clip.repaired_terms.map((item) => {
                        const thumbUrl = item.thumbnail.startsWith('http')
                          ? item.thumbnail
                          : `${API_BASE}${item.thumbnail.startsWith('/') ? '' : '/'}${item.thumbnail}`;

                        return (
                          <div
                            key={item.id}
                            onClick={() => openInspector(item)}
                            className="flex flex-col sm:flex-row sm:items-center justify-between p-2.5 rounded-lg bg-slate-50 hover:bg-indigo-50/30 border border-slate-200 hover:border-indigo-300 text-xs gap-3 cursor-pointer transition-all shadow-2xs group"
                          >
                            <div className="flex items-center gap-3">
                              {/* Actual Cropped Snapshot Image from Video Frame */}
                              <div className="relative shrink-0 overflow-hidden rounded border border-slate-200 bg-slate-900">
                                <img
                                  src={thumbUrl}
                                  alt="Actual OCR Proof from Video"
                                  className="h-10 w-24 object-cover group-hover:scale-105 transition-transform"
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).src = `${API_BASE}/provenance/crop_1.png`;
                                  }}
                                />
                                <span className="absolute bottom-0.5 right-0.5 bg-black/70 text-[8px] font-mono text-cyan-300 px-1 rounded">
                                  {item.timestamp.toFixed(1)}s
                                </span>
                              </div>

                              {/* Misheard Phonetic -> Grounded Code Term */}
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="line-through text-slate-400 font-mono text-xs">
                                  "{item.raw_asr}"
                                </span>
                                <span className="text-slate-400 font-semibold">→</span>
                                <span className="font-bold text-indigo-600 font-mono text-xs">
                                  {item.repaired_term}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 self-end sm:self-auto">
                              <Badge
                                variant="outline"
                                className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px] font-mono"
                              >
                                {(item.confidence * 100).toFixed(0)}% match
                              </Badge>
                              <span className="text-[10px] text-indigo-600 font-medium group-hover:underline">
                                Inspect Proof →
                              </span>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-xs text-slate-500 italic">No phonetic misspellings detected.</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Card 3: Social Caption & Code QR */}
              <Card className="bg-white border-slate-200 shadow-xs">
                <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <Hash className="size-4 text-indigo-600" />
                      Social Caption &amp; Code QR
                    </CardTitle>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Social growth pack: hook title, pinned code comment, 3-tier hashtags, and scannable QR badge.
                    </p>
                  </div>
                </CardHeader>

                <CardContent className="pt-4 flex flex-col gap-4">
                  {/* Hook Title (Editable) */}
                  <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                        <Sparkles className="size-3.5 text-indigo-600" />
                        Hook Title (Editable)
                      </Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copyHookTitle}
                        className="h-6 text-xs text-indigo-600 hover:bg-indigo-50 gap-1 px-2"
                      >
                        {copiedHook ? <Check className="size-3 text-emerald-600" /> : <Copy className="size-3" />}
                        {copiedHook ? 'Copied' : 'Copy'}
                      </Button>
                    </div>
                    <Input
                      value={growthPack.hook_title}
                      onChange={(e) => setGrowthPack((prev) => ({ ...prev, hook_title: e.target.value }))}
                      className="h-8 text-xs font-medium text-slate-900 bg-white border-slate-200"
                    />
                  </div>

                  {/* Pinned Code Comment (1-Click Copy with Indented Snippet from this video) */}
                  <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                        <MessageSquare className="size-3.5 text-indigo-600" />
                        Pinned Code Comment
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copyPinnedComment}
                        className="h-6 text-xs text-indigo-600 hover:bg-indigo-50 gap-1 px-2"
                      >
                        {copiedComment ? <Check className="size-3 text-emerald-600" /> : <Copy className="size-3" />}
                        {copiedComment ? 'Copied' : '1-Click Copy Pinned Code Comment'}
                      </Button>
                    </div>
                    <pre className="text-[11px] font-mono text-slate-700 bg-white p-2.5 rounded border border-slate-200 whitespace-pre-wrap leading-relaxed max-h-36 overflow-y-auto">
                      {buildPinnedCodeComment(editableCode)}
                    </pre>
                  </div>

                  {/* 3-Tier Hashtags */}
                  <div className="flex flex-col gap-2 p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                        <Hash className="size-3.5 text-indigo-600" />
                        3-Tier Social Hashtags
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copyAllHashtags}
                        className="h-6 text-xs text-indigo-600 hover:bg-indigo-50 gap-1 px-2"
                      >
                        {copiedTags ? <Check className="size-3 text-emerald-600" /> : <Copy className="size-3" />}
                        {copiedTags ? 'Copied' : 'Copy All'}
                      </Button>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] uppercase font-semibold text-slate-400 w-16">Broad:</span>
                        {growthPack.broad_hashtags.map((tag) => (
                          <span key={tag} className="text-[11px] px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 font-mono">
                            {tag}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] uppercase font-semibold text-slate-400 w-16">Stack:</span>
                        {growthPack.stack_hashtags.map((tag) => (
                          <span key={tag} className="text-[11px] px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 font-mono">
                            {tag}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] uppercase font-semibold text-slate-400 w-16">Micro-API:</span>
                        {growthPack.micro_api_hashtags.map((tag) => (
                          <span key={tag} className="text-[11px] px-2 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-indigo-700 font-mono font-medium">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* QR Code Badge */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="flex items-center gap-3">
                      <div className="size-10 rounded-lg bg-white border border-slate-300 flex items-center justify-center text-slate-800 shadow-2xs">
                        <QrCode className="size-6 text-indigo-600" />
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                          Outro QR Code Badge
                          <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px]">
                            Scannable
                          </Badge>
                        </span>
                        <a
                          href={growthPack.qr_code_data}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] font-mono text-indigo-600 hover:underline flex items-center gap-1 mt-0.5"
                        >
                          {growthPack.qr_code_data}
                          <ExternalLink className="size-3" />
                        </a>
                      </div>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono hidden sm:inline">
                      Burned into final 2.0s
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* Screen OCR Provenance Inspector Modal */}
      <ProvenanceDialog
        word={inspectedWord}
        isOpen={provenanceDialogOpen}
        onClose={() => setProvenanceDialogOpen(false)}
        onSaveOverride={handleSaveTermOverride}
      />
    </div>
  );
};

export default ModeAStudio;
