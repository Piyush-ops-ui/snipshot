import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { BrandKitSidebar } from '@/components/brand/BrandKitSidebar';
import { ModeAStudio } from '@/components/studio/ModeAStudio';
import { ModeBStudio } from '@/components/studio/ModeBStudio';
import { AnalyticsStudio } from '@/components/studio/AnalyticsStudio';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Video, Sparkles, BarChart3 } from 'lucide-react';
import { BrandKitConfig, TemplateArchetype } from '@/types/reel_ir';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('mode_a');
  const [currentArchetype, setCurrentArchetype] = useState<TemplateArchetype>('standard_spotlight');

  const [brandKit, setBrandKit] = useState<BrandKitConfig>({
    id: 'brand_tech_summit',
    name: 'TechSummit Academy',
    primary_color: '#4F46E5', // Calm Indigo
    secondary_color: '#6366F1',
    background_color: '#F8FAFC',
    text_color: '#0F172A',
    font_family: 'Inter',
    font_size_pt: 32,
    logo_position: 'top_right',
    show_provenance_badge: true,
    enable_intro_bumper: false,
    intro_bumper_duration: 1.5,
    enable_outro_bumper: true,
    outro_bumper_duration: 2.0,
    watermark_text: 'TechSummit Academy',
  });

  const handleUpdateBrandKit = (updated: Partial<BrandKitConfig>) => {
    setBrandKit((prev) => ({
      ...prev,
      ...updated,
    }));
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Minimal Top Header */}
      <Header />

      {/* Main Studio Body: 280px Left Sidebar + 3-Tab Workspace */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 sm:p-6 flex flex-col lg:flex-row gap-6">
        {/* Left Sidebar (280px): Brand Kit & Settings */}
        <BrandKitSidebar
          brandKit={brandKit}
          onUpdateBrandKit={handleUpdateBrandKit}
          currentArchetype={currentArchetype}
          onSelectArchetype={setCurrentArchetype}
        />

        {/* Right Main Studio: 3 Clean Tabs */}
        <section className="flex-1 min-w-0 flex flex-col gap-5">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="bg-slate-200/70 border border-slate-200 p-1 rounded-lg self-start flex-wrap">
              <TabsTrigger
                value="mode_a"
                className="gap-2 text-xs font-medium px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-md text-slate-600"
              >
                <Video className="size-3.5 text-indigo-600" />
                <span>Lecture Video → Reels (Mode A)</span>
              </TabsTrigger>
              <TabsTrigger
                value="mode_b"
                className="gap-2 text-xs font-medium px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-md text-slate-600"
              >
                <Sparkles className="size-3.5 text-indigo-600" />
                <span>Topic Prompt → Explainer Video (Mode B)</span>
              </TabsTrigger>
              <TabsTrigger
                value="analytics"
                className="gap-2 text-xs font-medium px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-md text-slate-600"
              >
                <BarChart3 className="size-3.5 text-indigo-600" />
                <span>Analytics & AI Weight Tuning</span>
              </TabsTrigger>
            </TabsList>

            {/* Tab 1: Mode A */}
            <TabsContent value="mode_a" className="mt-4">
              <ModeAStudio
                brandKit={brandKit}
                currentArchetype={currentArchetype}
                onSelectArchetype={setCurrentArchetype}
              />
            </TabsContent>

            {/* Tab 2: Mode B */}
            <TabsContent value="mode_b" className="mt-4">
              <ModeBStudio brandKit={brandKit} />
            </TabsContent>

            {/* Tab 3: Analytics & AI Weight Tuning (Weapon 9) */}
            <TabsContent value="analytics" className="mt-4">
              <AnalyticsStudio />
            </TabsContent>
          </Tabs>
        </section>
      </main>

      {/* Clean Minimal Footer */}
      <footer className="w-full bg-white border-t border-slate-200 px-6 py-3.5 mt-auto text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-3 font-mono">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800">SnipShot Studio</span>
          <span className="text-slate-300">•</span>
          <span>100% On-Device AI Video Engine</span>
        </div>
        <div className="flex items-center gap-3 text-[11px]">
          <span>Intel Core Ultra 5 125H</span>
          <span className="text-slate-300">•</span>
          <span className="text-emerald-600 font-semibold">₹0.00 Cloud Cost Billed</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
