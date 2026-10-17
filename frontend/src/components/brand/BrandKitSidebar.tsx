import React, { useRef } from 'react';
import {
  Building2,
  Palette,
  Upload,
  Check,
  ShieldCheck,
  Zap,
  Trash2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { TemplateArchetype, BrandKitConfig } from '@/types/reel_ir';

interface BrandKitSidebarProps {
  brandKit: BrandKitConfig;
  onUpdateBrandKit: (updated: Partial<BrandKitConfig>) => void;
  currentArchetype: TemplateArchetype;
  onSelectArchetype: (archetype: TemplateArchetype) => void;
  safeCohortActive?: boolean;
  onToggleSafeCohort?: (active: boolean) => void;
}

const TEMPLATE_ARCHETYPES: {
  id: TemplateArchetype;
  name: string;
  badge: string;
}[] = [
  { id: 'standard_spotlight', name: 'Standard Spotlight', badge: 'Split-Screen' },
  { id: 'bug_hunter', name: 'Bug Hunter', badge: 'Red → Green' },
  { id: 'vs_battle', name: 'VS Battle', badge: 'Comparison' },
  { id: 'predict_output', name: 'Predict Output', badge: 'Countdown' },
];

const PRESET_COLORS = [
  '#4F46E5', // Calm Indigo (Default)
  '#0284C7', // Sky Blue
  '#059669', // Emerald Green
  '#D97706', // Warm Amber
  '#DC2626', // Crimson Red
  '#7C3AED', // Vivid Violet
];

export const BrandKitSidebar: React.FC<BrandKitSidebarProps> = ({
  brandKit,
  onUpdateBrandKit,
  currentArchetype,
  onSelectArchetype,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const previewUrl = URL.createObjectURL(file);
      onUpdateBrandKit({ logo_path: previewUrl });
    }
  };

  const handleRemoveLogo = () => {
    onUpdateBrandKit({ logo_path: undefined });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <aside className="w-full lg:w-[280px] shrink-0 flex flex-col gap-4">
      {/* Brand Kit Settings Card */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Building2 className="size-4 text-indigo-600" />
            Brand Kit
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 flex flex-col gap-4 text-sm">
          {/* Institute Name */}
          <div className="flex flex-col gap-1.5">
            <Label className="text-xs font-medium text-slate-700">Institute Name</Label>
            <Input
              value={brandKit.name || ''}
              onChange={(e) => onUpdateBrandKit({ name: e.target.value })}
              placeholder="e.g., TechSummit Academy"
              className="h-8 text-xs bg-slate-50 border-slate-200 text-slate-900 focus:bg-white"
            />
          </div>

          {/* Brand Accent Color */}
          <div className="flex flex-col gap-2">
            <Label className="text-xs font-medium text-slate-700 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Palette className="size-3.5 text-slate-500" />
                Brand Color
              </span>
              <span className="font-mono text-[11px] text-slate-500">{brandKit.primary_color}</span>
            </Label>
            <div className="flex items-center gap-2">
              {PRESET_COLORS.map((c) => {
                const isSelected = brandKit.primary_color?.toUpperCase() === c.toUpperCase();
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() => onUpdateBrandKit({ primary_color: c })}
                    style={{ backgroundColor: c }}
                    className={`size-6 rounded-full transition-transform flex items-center justify-center ${
                      isSelected ? 'ring-2 ring-offset-2 ring-indigo-600 scale-110' : 'hover:scale-105'
                    }`}
                  >
                    {isSelected && <Check className="size-3 text-white stroke-[3]" />}
                  </button>
                );
              })}
            </div>
            <Input
              type="text"
              value={brandKit.primary_color || '#4F46E5'}
              onChange={(e) => onUpdateBrandKit({ primary_color: e.target.value })}
              className="h-7 text-xs font-mono bg-slate-50 border-slate-200"
              maxLength={7}
            />
          </div>

          {/* Logo Upload */}
          <div className="flex flex-col gap-1.5">
            <Label className="text-xs font-medium text-slate-700">Logo</Label>
            {brandKit.logo_path ? (
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
                <img
                  src={brandKit.logo_path}
                  alt="Logo"
                  className="h-7 w-auto max-w-[120px] object-contain rounded"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveLogo}
                  className="h-7 px-2 text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </div>
            ) : (
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleLogoUpload}
                  className="hidden"
                  id="sidebar-logo-input"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full h-8 text-xs border-slate-200 text-slate-700 hover:bg-slate-50 gap-1.5"
                >
                  <Upload className="size-3.5 text-slate-500" />
                  Upload PNG / SVG
                </Button>
              </div>
            )}
          </div>

          {/* Template Style Dropdown */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-100">
            <Label className="text-xs font-medium text-slate-700">Video Template</Label>
            <div className="flex flex-col gap-1.5">
              {TEMPLATE_ARCHETYPES.map((arch) => {
                const isActive = currentArchetype === arch.id;
                return (
                  <button
                    key={arch.id}
                    type="button"
                    onClick={() => onSelectArchetype(arch.id)}
                    className={`flex items-center justify-between px-2.5 py-2 rounded-md text-xs transition-colors text-left ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-900 font-medium border border-indigo-200'
                        : 'text-slate-600 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    <span>{arch.name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{arch.badge}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Simple Status Card */}
      <Card className="bg-white border-slate-200 shadow-xs p-3.5 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-xs font-medium text-slate-800">
          <Zap className="size-3.5 text-indigo-600" />
          <span>Fast Native Pipeline</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          Native FFmpeg filtergraph rendering with zero frame-by-frame Python loops. Renders under 4 seconds.
        </p>
        <div className="flex items-center gap-1.5 text-[11px] text-emerald-600 font-medium pt-1 border-t border-slate-100">
          <ShieldCheck className="size-3 text-emerald-600" />
          <span>100% On-Device • Zero Cloud Egress</span>
        </div>
      </Card>
    </aside>
  );
};

export default BrandKitSidebar;
