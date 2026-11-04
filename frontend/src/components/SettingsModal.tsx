import React, { useRef, useState } from 'react';
import { BackgroundSettings } from '../types';

export const DEFAULT_BG_SETTINGS: BackgroundSettings = {
  glassEnabled: true,
  wallpaperUrl: '/backgrounds/default_glass.jpg',
  blurIntensity: 'medium',
  overlayOpacity: 0.82,
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: BackgroundSettings;
  onUpdateSettings: (newSettings: BackgroundSettings) => void;
  archivistName: string;
  onUpdateArchivistName: (name: string) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onUpdateSettings,
  archivistName,
  onUpdateArchivistName,
}) => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'profile'>('appearance');
  const [customUrlInput, setCustomUrlInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleCustomFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please select a valid image file (.jpg, .png, .webp).');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        onUpdateSettings({
          ...settings,
          glassEnabled: true,
          wallpaperUrl: dataUrl,
        });
      }
    };
    reader.readAsDataURL(file);
  };

  const handleApplyCustomUrl = () => {
    if (!customUrlInput.trim()) return;
    onUpdateSettings({
      ...settings,
      glassEnabled: true,
      wallpaperUrl: customUrlInput.trim(),
    });
    setCustomUrlInput('');
  };

  const handleRemoveBackground = () => {
    onUpdateSettings({
      ...settings,
      glassEnabled: false,
      wallpaperUrl: null,
    });
  };

  const handleResetToDefaultGlass = () => {
    onUpdateSettings(DEFAULT_BG_SETTINGS);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-palette-eggplant/50 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-surface-container-lowest border border-surface-container-high rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-space-xl py-space-lg border-b border-surface-container-high bg-surface-container-low/50">
          <div className="flex items-center gap-space-sm">
            <div className="w-9 h-9 rounded-xl bg-palette-plum flex items-center justify-center text-palette-peach shadow-sm">
              <span className="material-symbols-outlined text-[22px]">settings</span>
            </div>
            <div>
              <h2 className="font-headline-md text-headline-md text-primary font-normal leading-tight">
                Desk Preferences &amp; Settings
              </h2>
              <span className="font-citation-code text-citation-code text-outline">
                Corpus Ledger A-1 · Grounding Engine 4.2
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-surface-container flex items-center justify-center text-outline hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-space-md px-space-xl border-b border-surface-container-high bg-surface-container-low/30 pt-2">
          <button
            onClick={() => setActiveTab('appearance')}
            className={`pb-2.5 font-ui-label-md text-ui-label-md transition-all flex items-center gap-1.5 ${
              activeTab === 'appearance'
                ? 'border-b-2 border-palette-plum text-palette-plum font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[17px]">wallpaper</span>
            <span>Glass Background &amp; Aesthetics</span>
          </button>

          <button
            onClick={() => setActiveTab('profile')}
            className={`pb-2.5 font-ui-label-md text-ui-label-md transition-all flex items-center gap-1.5 ${
              activeTab === 'profile'
                ? 'border-b-2 border-palette-plum text-palette-plum font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[17px]">badge</span>
            <span>Archivist Profile</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-space-xl overflow-y-auto max-h-[68vh] flex flex-col gap-space-lg">
          {activeTab === 'appearance' && (
            <div className="flex flex-col gap-space-lg">
              {/* Master Glass Toggle */}
              <div className="flex items-center justify-between p-space-md rounded-xl bg-surface-container-low border border-surface-container-high">
                <div className="flex flex-col">
                  <span className="font-ui-label-lg text-ui-label-lg text-on-surface font-semibold">
                    Glass Surface Background
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Render workspace elements with translucent frosted glass over custom artwork
                  </span>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.glassEnabled}
                    onChange={(e) => {
                      const enabled = e.target.checked;
                      onUpdateSettings({
                        ...settings,
                        glassEnabled: enabled,
                        wallpaperUrl: enabled
                          ? (settings.wallpaperUrl || DEFAULT_BG_SETTINGS.wallpaperUrl)
                          : null,
                      });
                    }}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-surface-container-highest peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-palette-plum"></div>
                </label>
              </div>

              {/* Wallpaper Presets Selection */}
              <div className="flex flex-col gap-space-sm">
                <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                  Background Wallpapers
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                  {/* Preset 1: Default Toothless & Light Fury Artwork */}
                  <div
                    onClick={() =>
                      onUpdateSettings({
                        ...settings,
                        glassEnabled: true,
                        wallpaperUrl: DEFAULT_BG_SETTINGS.wallpaperUrl,
                      })
                    }
                    className={`group relative rounded-xl overflow-hidden border-2 cursor-pointer transition-all ${
                      settings.glassEnabled && settings.wallpaperUrl === DEFAULT_BG_SETTINGS.wallpaperUrl
                        ? 'border-palette-plum ring-2 ring-palette-rose/40 shadow-md'
                        : 'border-surface-container-high hover:border-palette-plum/60'
                    }`}
                  >
                    <div className="h-28 bg-cover bg-center" style={{ backgroundImage: `url(${DEFAULT_BG_SETTINGS.wallpaperUrl})` }} />
                    <div className="p-space-sm bg-surface-container-lowest flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="font-ui-label-md text-ui-label-md text-on-surface font-semibold">
                          Default Glass Art
                        </span>
                        <span className="font-citation-code text-[11px] text-outline">
                          Toothless &amp; Light Fury Artwork
                        </span>
                      </div>
                      {settings.glassEnabled && settings.wallpaperUrl === DEFAULT_BG_SETTINGS.wallpaperUrl && (
                        <span className="material-symbols-outlined text-palette-plum text-[18px]">check_circle</span>
                      )}
                    </div>
                  </div>

                  {/* Preset 2: Clean Archival Paper (Image 1 style) */}
                  <div
                    onClick={handleRemoveBackground}
                    className={`group relative rounded-xl overflow-hidden border-2 cursor-pointer transition-all ${
                      !settings.glassEnabled || !settings.wallpaperUrl
                        ? 'border-palette-plum ring-2 ring-palette-rose/40 shadow-md'
                        : 'border-surface-container-high hover:border-palette-plum/60'
                    }`}
                  >
                    <div className="h-28 bg-[#FDF9F6] flex items-center justify-center border-b border-surface-container-high">
                      <span className="material-symbols-outlined text-[32px] text-palette-plum/40">description</span>
                    </div>
                    <div className="p-space-sm bg-surface-container-lowest flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="font-ui-label-md text-ui-label-md text-on-surface font-semibold">
                          Clean Archival Paper
                        </span>
                        <span className="font-citation-code text-[11px] text-outline">
                          Solid #FDF9F6 (Default Clean Paper)
                        </span>
                      </div>
                      {(!settings.glassEnabled || !settings.wallpaperUrl) && (
                        <span className="material-symbols-outlined text-palette-plum text-[18px]">check_circle</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Upload Custom Wallpaper */}
              <div className="flex flex-col gap-space-sm pt-space-xs border-t border-surface-container-high">
                <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                  Choose Custom Wallpaper
                </span>

                <div className="flex flex-col sm:flex-row items-center gap-space-sm">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleCustomFileUpload}
                  />

                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full sm:w-auto px-space-md py-2 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-ui-label-md text-ui-label-md border border-surface-container-high flex items-center justify-center gap-2 transition-colors shadow-sm"
                  >
                    <span className="material-symbols-outlined text-[18px] text-palette-plum">add_photo_alternate</span>
                    <span>Upload Image from Device</span>
                  </button>

                  <div className="w-full sm:flex-1 flex items-center gap-1">
                    <input
                      type="url"
                      value={customUrlInput}
                      onChange={(e) => setCustomUrlInput(e.target.value)}
                      placeholder="Or paste image URL (https://...)..."
                      className="flex-1 bg-surface-container-low border border-surface-container-high px-3 py-2 rounded-lg text-xs font-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:border-palette-plum"
                    />
                    <button
                      onClick={handleApplyCustomUrl}
                      disabled={!customUrlInput.trim()}
                      className="px-3 py-2 rounded-lg bg-palette-plum text-palette-peach font-ui-label-sm text-ui-label-sm disabled:opacity-40 transition-all font-semibold"
                    >
                      Apply
                    </button>
                  </div>
                </div>

                {settings.glassEnabled &&
                  settings.wallpaperUrl &&
                  settings.wallpaperUrl !== DEFAULT_BG_SETTINGS.wallpaperUrl && (
                    <div className="mt-2 p-2 rounded-lg bg-palette-peach/20 border border-palette-coral/30 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-on-surface truncate">
                        <span className="material-symbols-outlined text-[16px] text-palette-plum">image</span>
                        <span className="truncate">Custom wallpaper active</span>
                      </div>
                      <button
                        onClick={handleResetToDefaultGlass}
                        className="text-[11px] text-palette-plum hover:underline font-semibold"
                      >
                        Reset to Default
                      </button>
                    </div>
                  )}
              </div>

              {/* Frosting & Blur Controls */}
              {settings.glassEnabled && settings.wallpaperUrl && (
                <div className="flex flex-col gap-space-sm pt-space-xs border-t border-surface-container-high animate-in fade-in">
                  <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                    Glass Frosting &amp; Surface Opacity
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                    {/* Blur Strength */}
                    <div className="flex flex-col gap-1">
                      <label className="font-ui-label-sm text-ui-label-sm text-outline">Blur Intensity</label>
                      <div className="grid grid-cols-3 gap-1 bg-surface-container-low p-1 rounded-lg border border-surface-container-high">
                        {(['low', 'medium', 'high'] as const).map((level) => (
                          <button
                            key={level}
                            onClick={() => onUpdateSettings({ ...settings, blurIntensity: level })}
                            className={`py-1 rounded text-xs capitalize transition-all ${
                              settings.blurIntensity === level
                                ? 'bg-palette-plum text-palette-peach font-semibold shadow-sm'
                                : 'text-on-surface-variant hover:text-on-surface'
                            }`}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Translucency / Tint */}
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between items-center">
                        <label className="font-ui-label-sm text-ui-label-sm text-outline">Surface Opacity</label>
                        <span className="font-citation-code text-xs text-palette-plum font-semibold">
                          {Math.round(settings.overlayOpacity * 100)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0.60"
                        max="0.95"
                        step="0.05"
                        value={settings.overlayOpacity}
                        onChange={(e) =>
                          onUpdateSettings({
                            ...settings,
                            overlayOpacity: parseFloat(e.target.value),
                          })
                        }
                        className="w-full accent-palette-plum cursor-pointer h-2 bg-surface-container-high rounded-lg mt-2"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="flex flex-col gap-space-lg">
              {/* Archivist Identity Dossier */}
              <div className="flex items-center gap-space-md p-space-md rounded-xl bg-surface-container-low border border-surface-container-high">
                <div className="w-14 h-14 rounded-full bg-palette-plum text-palette-peach flex items-center justify-center flex-shrink-0 shadow-md ring-4 ring-palette-rose/20">
                  <span className="material-symbols-outlined text-[32px]">person</span>
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="font-headline-md text-[18px] text-on-surface font-semibold truncate">
                    {archivistName || 'Archivist Desk'}
                  </span>
                  <span className="font-citation-code text-citation-code text-palette-plum">
                    Station: Corpus Ledger A-1 · Active
                  </span>
                  <span className="text-xs text-outline mt-0.5">
                    Authorized for Corpus Ingestion, Synthesis, &amp; Golden Evaluations
                  </span>
                </div>
              </div>

              {/* Name Edit Input */}
              <div className="flex flex-col gap-1">
                <label className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                  Archivist Call-Sign / Name
                </label>
                <input
                  type="text"
                  value={archivistName}
                  onChange={(e) => onUpdateArchivistName(e.target.value)}
                  placeholder="e.g. Archivist Desk"
                  className="bg-surface-container-low border border-surface-container-high px-space-md py-2 rounded-lg font-ui-label-md text-ui-label-md text-on-surface focus:outline-none focus:border-palette-plum"
                />
              </div>

              {/* Active Color Palette Display */}
              <div className="flex flex-col gap-space-sm pt-space-xs border-t border-surface-container-high">
                <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                  Active Archival Sunset Plum Palette (6 Tokens)
                </span>
                <div className="grid grid-cols-6 gap-2 text-center font-citation-code text-[10px]">
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-full h-8 rounded bg-palette-peach shadow-sm border border-black/10" />
                    <span className="text-outline">#FFBB94</span>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-full h-8 rounded bg-palette-coral shadow-sm border border-black/10" />
                    <span className="text-outline">#FB9590</span>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-full h-8 rounded bg-palette-rose shadow-sm" />
                    <span className="text-outline">#DC586D</span>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-full h-8 rounded bg-palette-plum shadow-sm" />
                    <span className="text-outline">#A33757</span>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-full h-8 rounded bg-palette-wine shadow-sm" />
                    <span className="text-outline">#852E4E</span>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-full h-8 rounded bg-palette-eggplant shadow-sm" />
                    <span className="text-outline">#4C1D3D</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-space-xl py-space-md border-t border-surface-container-high bg-surface-container-low/50">
          <div className="flex items-center gap-space-xs">
            <button
              onClick={handleRemoveBackground}
              className="px-space-md py-2 rounded-lg font-ui-label-sm text-ui-label-sm text-outline hover:text-on-surface transition-colors"
              title="Remove glass background and revert to clean paper"
            >
              Remove Background (Clean Paper)
            </button>
            <button
              onClick={handleResetToDefaultGlass}
              className="px-space-md py-2 rounded-lg font-ui-label-sm text-ui-label-sm text-palette-plum hover:underline transition-colors font-medium"
            >
              Reset to Default Glass Art
            </button>
          </div>

          <button
            onClick={onClose}
            className="px-space-lg py-2 rounded-lg bg-palette-plum hover:bg-palette-wine text-palette-peach font-ui-label-md text-ui-label-md font-semibold transition-colors shadow-sm"
          >
            Apply &amp; Close
          </button>
        </div>
      </div>
    </div>
  );
};

