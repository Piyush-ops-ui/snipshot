import React, { useState, useRef } from 'react';
import {
  Sparkles,
  Download,
  Copy,
  Check,
  RefreshCw,
  Code2,
  FileText,
  AlertCircle,
  Hash,
  UploadCloud,
  FileCode,
  Trash2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { BrandKitConfig } from '@/types/reel_ir';

interface ModeBStudioProps {
  brandKit: BrandKitConfig;
}

interface SceneItem {
  title: string;
  narration_text: string;
  code_snippet: string;
  language: string;
}

interface ExplainerData {
  video_url: string;
  duration: number;
  scenes: SceneItem[];
  hashtags: string[];
  reel_id?: string;
  elapsed_seconds?: number;
}

const DEFAULT_SUGGESTIONS = [
  'JSON vs XML',
  'Docker vs Virtual Machine',
  'React useState vs useEffect',
  'SQL vs NoSQL',
  'Git merge vs rebase',
];

export const ModeBStudio: React.FC<ModeBStudioProps> = ({ brandKit }) => {
  const [subMode, setSubMode] = useState<'prompt' | 'document'>('prompt');
  const [prompt, setPrompt] = useState<string>('JSON vs XML');

  // Document state
  const [docFile, setDocFile] = useState<File | null>(null);
  const [topicFocus, setTopicFocus] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [progressStage, setProgressStage] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [explainer, setExplainer] = useState<ExplainerData | null>(null);
  const [cacheBuster, setCacheBuster] = useState<number>(Date.now());
  const [copiedTags, setCopiedTags] = useState<boolean>(false);

  const handleGenerateFromPrompt = async () => {
    if (!prompt.trim()) return;

    setIsGenerating(true);
    setProgress(20);
    setProgressStage('Synthesizing 4-scene pedagogical script...');
    setErrorMsg(null);

    try {
      const timer = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 85) return prev;
          if (prev === 40) setProgressStage('Synthesizing neural voiceover...');
          if (prev === 70) setProgressStage('Assembling 1080x1920 code slides with FFmpeg...');
          return prev + 20;
        });
      }, 500);

      const response = await fetch('http://localhost:8000/api/v1/mode-b/generate-explainer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt.trim(),
          brand_kit: {
            name: brandKit.name || 'SNIPSHOT ACADEMY',
            primary_color: brandKit.primary_color || '#4F46E5',
            logo_base64: brandKit.logo_base64 || brandKit.logo_path,
          },
        }),
      });

      clearInterval(timer);

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Explainer generation failed.');
      }

      const data: ExplainerData = await response.json();
      setProgress(100);
      setProgressStage('Finished!');
      setExplainer(data);
      setCacheBuster(Date.now());
    } catch (err: any) {
      setErrorMsg(err.message || 'Error generating explainer video.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateFromDoc = async () => {
    if (!docFile) return;

    setIsGenerating(true);
    setProgress(15);
    setProgressStage('Extracting AST & text structures from document...');
    setErrorMsg(null);

    try {
      const timer = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 85) return prev;
          if (prev === 35) setProgressStage('Compiling pedagogical scenes from content...');
          if (prev === 60) setProgressStage('Synthesizing neural audio narration...');
          if (prev === 80) setProgressStage('Assembling 1080x1920 code reel with FFmpeg...');
          return prev + 15;
        });
      }, 500);

      const formData = new FormData();
      formData.append('file', docFile);
      if (topicFocus.trim()) {
        formData.append('topic_focus', topicFocus.trim());
      }
      formData.append(
        'brand_kit',
        JSON.stringify({
          name: brandKit.name || 'SNIPSHOT ACADEMY',
          primary_color: brandKit.primary_color || '#4F46E5',
          logo_base64: brandKit.logo_base64 || brandKit.logo_path,
        })
      );

      const response = await fetch('http://localhost:8000/api/v1/mode-b/generate-from-doc', {
        method: 'POST',
        body: formData,
      });

      clearInterval(timer);

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Document explainer generation failed.');
      }

      const data: ExplainerData = await response.json();
      setProgress(100);
      setProgressStage('Finished!');
      setExplainer(data);
      setCacheBuster(Date.now());
    } catch (err: any) {
      setErrorMsg(err.message || 'Error generating explainer from document.');
    } finally {
      setIsGenerating(false);
    }
  };

  const onDropFile = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setDocFile(e.dataTransfer.files[0]);
    }
  };

  const copyHashtags = () => {
    if (!explainer) return;
    navigator.clipboard.writeText(explainer.hashtags.join(' '));
    setCopiedTags(true);
    setTimeout(() => setCopiedTags(false), 2000);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Input Card */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Sparkles className="size-4.5 text-indigo-600" />
              Explainer Reel Studio (Mode B)
            </CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Generate 1080x1920 pedagogical explainer reels from a topic prompt or any uploaded document.
            </p>
          </div>

          {/* Mode Switcher Pills */}
          <div className="flex items-center p-1 rounded-lg bg-slate-100 border border-slate-200 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setSubMode('prompt')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                subMode === 'prompt'
                  ? 'bg-white text-indigo-600 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles className="size-3.5" />
              Topic Prompt
            </button>
            <button
              type="button"
              onClick={() => setSubMode('document')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                subMode === 'document'
                  ? 'bg-white text-indigo-600 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText className="size-3.5" />
              Upload Document
              <span className="text-[10px] px-1 py-0.2 rounded bg-indigo-50 text-indigo-600 border border-indigo-200/60 font-mono">
                PDF/Doc/Code
              </span>
            </button>
          </div>
        </CardHeader>

        <CardContent className="pt-4 flex flex-col gap-4">
          {subMode === 'prompt' ? (
            /* Sub-mode 1: Topic Prompt */
            <>
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1">
                  <Input
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g., JSON vs XML, Docker vs VM, Python GIL..."
                    className="h-10 text-sm bg-slate-50 border-slate-200 text-slate-900 focus:bg-white"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleGenerateFromPrompt();
                    }}
                  />
                </div>
                <Button
                  onClick={handleGenerateFromPrompt}
                  disabled={isGenerating || !prompt.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs h-10 px-5 gap-2 shrink-0 shadow-xs"
                >
                  <RefreshCw className={`size-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                  {isGenerating ? 'Generating Reel...' : 'Generate Explainer'}
                </Button>
              </div>

              {/* Quick Suggestions Chips */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-500">Quick suggestions:</span>
                {DEFAULT_SUGGESTIONS.map((sug) => (
                  <button
                    key={sug}
                    type="button"
                    onClick={() => setPrompt(sug)}
                    className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 transition-colors"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </>
          ) : (
            /* Sub-mode 2: Document Upload (PDF, DOCX, Markdown, Code) */
            <div className="flex flex-col gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.md,.py,.js,.ts,.tsx,.jsx,.txt,.json,.yaml,.yml,.cpp,.java,.go,.rs,.html,.css"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setDocFile(e.target.files[0]);
                  }
                }}
              />

              {!docFile ? (
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={onDropFile}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors ${
                    isDragging
                      ? 'border-indigo-500 bg-indigo-50/50'
                      : 'border-slate-200 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300'
                  }`}
                >
                  <div className="size-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
                    <UploadCloud className="size-5" />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-semibold text-slate-800">
                      Click to browse or drop any document here
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Supports PDF, DOCX, Markdown (.md), Python, TypeScript, Java, and all source code
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 gap-3">
                  <div className="flex items-center gap-3">
                    <div className="size-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                      <FileCode className="size-5" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-900 truncate max-w-[280px] sm:max-w-[400px]">
                        {docFile.name}
                      </p>
                      <p className="text-[11px] text-slate-500 font-mono">
                        {formatFileSize(docFile.size)} • {docFile.name.split('.').pop()?.toUpperCase()} Document
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDocFile(null)}
                    className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 h-8 px-2.5 text-xs gap-1.5"
                  >
                    <Trash2 className="size-3.5" />
                    Remove
                  </Button>
                </div>
              )}

              {/* Optional Topic Focus */}
              <div className="flex flex-col sm:flex-row gap-3 pt-1">
                <div className="flex-1">
                  <Input
                    value={topicFocus}
                    onChange={(e) => setTopicFocus(e.target.value)}
                    placeholder="Optional focus topic (e.g. 'Authentication & JWT', 'Database Schema', 'Architecture Overview')"
                    className="h-10 text-sm bg-slate-50 border-slate-200 text-slate-900 focus:bg-white"
                  />
                </div>
                <Button
                  onClick={handleGenerateFromDoc}
                  disabled={isGenerating || !docFile}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs h-10 px-5 gap-2 shrink-0 shadow-xs"
                >
                  <RefreshCw className={`size-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                  {isGenerating ? 'Compiling Reel...' : 'Generate Reel from Doc'}
                </Button>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="size-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {isGenerating && (
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
        </CardContent>
      </Card>

      {/* Output Section (Left: Video Player | Right: 4-Scene Script Cards) */}
      {explainer && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Real HTML5 Video Player + Download */}
          <div className="lg:col-span-5 flex flex-col items-center gap-3">
            <div className="w-[300px] aspect-[9/16] rounded-xl overflow-hidden bg-black border border-slate-200 shadow-sm relative group">
              <video
                key={`${explainer.video_url}?${cacheBuster}`}
                controls
                src={`http://localhost:8000${explainer.video_url}${explainer.video_url.includes('?') ? '&' : '?'}t=${cacheBuster}`}
                className="w-full h-full object-cover"
              />
            </div>
            <a
              href={`http://localhost:8000${explainer.video_url}`}
              download="snipshot_explainer.mp4"
              target="_blank"
              rel="noreferrer"
              className="w-[300px] inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs transition-colors shadow-xs"
            >
              <Download className="size-4" />
              Download .mp4 Video
            </a>
          </div>

          {/* Right Column: 4-Scene Script Inspection Cards */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            <Card className="bg-white border-slate-200 shadow-xs">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <FileText className="size-4 text-indigo-600" />
                    4-Scene Pedagogical Script
                  </CardTitle>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Total Duration: {explainer.duration.toFixed(1)}s • Rendered in {explainer.elapsed_seconds || 1.5}s
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyHashtags}
                  className="h-7 text-xs border-slate-200 text-slate-700 hover:bg-slate-50 gap-1.5"
                >
                  {copiedTags ? <Check className="size-3 text-emerald-600" /> : <Copy className="size-3" />}
                  {copiedTags ? 'Copied Tags' : 'Copy Hashtags'}
                </Button>
              </CardHeader>
              <CardContent className="pt-4 flex flex-col gap-3">
                {explainer.scenes.map((scene, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-900 font-mono">
                        {scene.title}
                      </span>
                      <Badge variant="outline" className="bg-white text-[10px] text-slate-500 font-mono">
                        {scene.language}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed italic">
                      "{scene.narration_text}"
                    </p>
                    <pre className="text-xs font-mono bg-slate-900 text-slate-100 p-2.5 rounded-md overflow-x-auto leading-relaxed border border-slate-800">
                      <code>{scene.code_snippet}</code>
                    </pre>
                  </div>
                ))}

                {/* Hashtags */}
                <div className="flex flex-wrap items-center gap-1.5 pt-2">
                  <Hash className="size-3.5 text-slate-400" />
                  {explainer.hashtags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModeBStudio;
