
import React, { useState } from 'react';
import { UserSettings } from '../types';
import { THEMES, COURSES } from '../constants';

interface SettingsPageProps {
  settings: UserSettings;
  onUpdate: (updates: Partial<UserSettings>) => void;
  onBack: () => void;
}

const SettingsPage: React.FC<SettingsPageProps> = ({ settings, onUpdate, onBack }) => {
  const [isDangerZoneOpen, setIsDangerZoneOpen] = useState(false);
  
  const handleToggle = (key: keyof UserSettings) => {
    onUpdate({ [key]: !settings[key] });
  };

  return (
    <div className="min-h-screen pb-20">
      {/* Sticky Header Section */}
      <div className="sticky top-0 z-50 w-full glass-panel border-b border-gray-100/20 dark:border-white/5 py-4 px-6 md:px-12 mb-8">
        <div className="max-w-[900px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button 
              onClick={onBack}
              className="group relative size-11 flex items-center justify-center rounded-2xl glass-panel hover:bg-white dark:hover:bg-brand-900/40 transition-all duration-300"
            >
              <span className="material-symbols-outlined text-gray-600 dark:text-gray-300 group-hover:-translate-x-1 transition-transform">arrow_back</span>
            </button>
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight leading-none">Ayarlar</h1>
              <div className="flex items-center gap-2 mt-1">
                 <span className="size-1.5 rounded-full bg-green-500 animate-pulse"></span>
                 <p className="text-gray-400 text-[10px] font-bold uppercase tracking-wider">Sistem Çevrimiçi</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[900px] mx-auto px-6 space-y-8 transition-all duration-500">
        {/* Profile Identity Widget */}
        <section className="md:col-span-12 glass-panel rounded-[2.5rem] p-8 flex flex-col md:flex-row items-center gap-10 shadow-2xl relative overflow-hidden group">
          <div className="absolute -top-10 -right-10 size-40 bg-brand-500/5 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-1000"></div>
          
          <div className="relative shrink-0">
            <div className="size-28 rounded-[2rem] bg-gradient-to-br from-brand-500 to-accent-500 p-1 shadow-2xl rotate-3 group-hover:rotate-0 transition-transform duration-500">
              <div className="w-full h-full bg-white dark:bg-gray-900 rounded-[1.8rem] overflow-hidden flex items-center justify-center">
                <img src={`https://picsum.photos/seed/${settings.username}/300`} alt="Avatar" className="w-full h-full object-cover opacity-90 hover:scale-110 transition-transform duration-700" />
              </div>
            </div>
          </div>

          <div className="text-center md:text-left flex-1 space-y-4">
            <div className="space-y-1">
              <div className="flex flex-wrap justify-center md:justify-start items-center gap-3">
                <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white leading-none">{settings.username}</h2>
                <div className="bg-brand-500 px-3 py-1 rounded-full text-white text-[10px] font-black uppercase tracking-widest shadow-lg shadow-brand-500/20">
                  BİREYSEL
                </div>
              </div>
              <p className="text-gray-400 font-medium text-sm">Günde ortalama 45 dakika odaklanıyorsun.</p>
            </div>
            
            <div className="flex flex-wrap justify-center md:justify-start gap-4">
               <div className="flex items-center gap-2 py-2 px-4 rounded-xl bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5">
                  <span className="material-symbols-outlined text-yellow-500 text-sm">workspace_premium</span>
                  <span className="text-xs font-bold text-gray-600 dark:text-gray-300">#12 Liderlik</span>
               </div>
               <div className="flex items-center gap-2 py-2 px-4 rounded-xl bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5">
                  <span className="material-symbols-outlined text-brand-500 text-sm">local_fire_department</span>
                  <span className="text-xs font-bold text-gray-600 dark:text-gray-300">12 Gün Serisi</span>
               </div>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Algorithm & Flow (Left Side - Balanced) */}
          <section className="md:col-span-6">
            <div className="glass-panel rounded-[2.5rem] p-8 space-y-6 shadow-xl h-full">
              <div className="flex items-center gap-4">
                 <div className="size-10 rounded-xl bg-brand-500/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-brand-500">neurology</span>
                 </div>
                 <h3 className="text-lg font-bold text-gray-800 dark:text-white tracking-tight">Algoritma & Akış</h3>
              </div>

              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <p className="font-bold text-gray-800 dark:text-gray-200 text-sm">Otomatik Telaffuz</p>
                  </div>
                  <Toggle checked={settings.autoAudio} onChange={() => handleToggle('autoAudio')} />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <p className="font-bold text-gray-800 dark:text-gray-200 text-sm">Görsel Destek</p>
                  </div>
                  <Toggle checked={settings.showImages} color="bg-accent-500" onChange={() => handleToggle('showImages')} />
                </div>

                <div className="space-y-3 pt-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-gray-700 dark:text-gray-300 text-xs uppercase tracking-wider">Hedef</span>
                    <span className="px-2 py-0.5 bg-accent-500/10 text-accent-500 rounded text-[10px] font-black">
                      {settings.dailyGoal === 0 ? 'YOK' : `${settings.dailyGoal} KELİME`}
                    </span>
                  </div>
                  <input 
                    type="range" min="0" max="20" step="1" 
                    value={settings.dailyGoal}
                    onChange={(e) => onUpdate({ dailyGoal: parseInt(e.target.value) })}
                    className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full appearance-none cursor-pointer accent-accent-500"
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-gray-700 dark:text-gray-300 text-xs uppercase tracking-wider">Hız</span>
                    <span className="px-2 py-0.5 bg-brand-500/10 text-brand-500 rounded text-[10px] font-black">
                      {settings.audioSpeed.toFixed(2)}x
                    </span>
                  </div>
                  <input 
                    type="range" min="0.75" max="1.25" step="0.05" 
                    value={settings.audioSpeed}
                    onChange={(e) => onUpdate({ audioSpeed: parseFloat(e.target.value) })}
                    className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full appearance-none cursor-pointer accent-brand-500"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Interface (Right Side - Balanced) */}
          <section className="md:col-span-6">
            <div className="glass-panel rounded-[2.5rem] p-8 space-y-6 shadow-xl h-full flex flex-col">
               <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                     <div className="size-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
                        <span className="material-symbols-outlined text-orange-500">brush</span>
                     </div>
                     <h3 className="text-lg font-bold text-gray-800 dark:text-white tracking-tight">Arayüz</h3>
                  </div>
                  <button 
                    onClick={() => handleToggle('isDarkMode')}
                    className={`size-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                      settings.isDarkMode ? 'bg-indigo-500 text-white' : 'bg-yellow-100 text-yellow-600'
                    }`}
                  >
                    <span className="material-symbols-outlined text-lg">{settings.isDarkMode ? 'dark_mode' : 'light_mode'}</span>
                  </button>
               </div>

               <div className="space-y-4 flex-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Renk Teması</p>
                  <div className="grid grid-cols-2 gap-3">
                    {THEMES.map((t) => (
                      <button 
                        key={t.id}
                        onClick={() => onUpdate({ themeColor: t.id })}
                        className={`relative aspect-[16/9] rounded-2xl border-2 transition-all duration-300 flex flex-col items-center justify-center gap-2 overflow-hidden ${
                          settings.themeColor === t.id 
                          ? 'border-brand-500 shadow-lg shadow-brand-500/10 scale-105 z-10' 
                          : 'border-gray-100 dark:border-white/5 hover:border-brand-300'
                        }`}
                      >
                        {settings.themeColor === t.id && (
                          <div className="absolute inset-0 opacity-10 blur-xl animate-pulse-slow" style={{ backgroundColor: t.primary }}></div>
                        )}
                        <div className="size-5 rounded-full shadow-inner ring-4 ring-white/20" style={{ backgroundColor: t.primary }}></div>
                        <span className="text-[9px] font-bold text-gray-500 dark:text-gray-300 uppercase tracking-tight">{t.name}</span>
                      </button>
                    ))}
                  </div>
               </div>
            </div>
          </section>

          {/* Education (Bottom - Wide) */}
          <section className="md:col-span-12">
            <div className="glass-panel rounded-[2.5rem] p-8 space-y-6 shadow-xl relative overflow-hidden">
               <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                  <div className="flex items-center gap-4">
                    <div className="size-12 rounded-2xl bg-blue-500/10 flex items-center justify-center">
                      <span className="material-symbols-outlined text-blue-500 text-2xl">school</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white tracking-tight">Eğitim Müfredatı</h3>
                      <p className="text-xs text-gray-400 font-medium">Aktif olarak çalıştığın öğrenme yolunu seç.</p>
                    </div>
                  </div>

                  <div className="relative min-w-[300px]">
                      <select 
                      className="w-full bg-gray-50 dark:bg-white/5 border-2 border-transparent focus:border-brand-500 rounded-2xl py-4 px-6 font-bold text-gray-700 dark:text-gray-200 text-sm transition-all cursor-pointer"
                      value={settings.activeCourse}
                      onChange={(e) => onUpdate({ activeCourse: e.target.value })}
                      >
                      {COURSES.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                  </div>
               </div>
               <div className="pt-4 border-t border-gray-100 dark:border-white/5">
                  <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-widest text-center">Fibonacci SRS algoritması bu müfredat üzerinden optimize edilmektedir.</p>
               </div>
            </div>
          </section>

          {/* Danger Zone */}
          <section className="md:col-span-12">
             <div className="glass-panel rounded-3xl overflow-hidden shadow-lg border-red-500/10">
                <button 
                  onClick={() => setIsDangerZoneOpen(!isDangerZoneOpen)}
                  className="w-full px-8 py-5 flex items-center justify-between text-gray-500 dark:text-gray-400 hover:bg-red-50/10 transition-colors"
                >
                   <div className="flex items-center gap-3">
                     <span className={`material-symbols-outlined text-xl transition-colors ${isDangerZoneOpen ? 'text-red-500' : ''}`}>security</span>
                     <span className="text-xs font-bold uppercase tracking-widest">Gelişmiş & Güvenlik</span>
                   </div>
                   <span className={`material-symbols-outlined transition-transform duration-500 ${isDangerZoneOpen ? 'rotate-180' : ''}`}>
                     keyboard_arrow_down
                   </span>
                </button>
                
                <div className={`overflow-hidden transition-all duration-500 ease-in-out ${isDangerZoneOpen ? 'max-h-64 opacity-100 border-t border-red-500/10' : 'max-h-0 opacity-0'}`}>
                   <div className="p-8">
                      <button className="w-full group h-16 bg-white dark:bg-white/5 border border-red-500/20 rounded-2xl flex items-center px-6 gap-4 font-bold text-red-500 hover:bg-red-500 hover:text-white transition-all duration-300" onClick={() => alert('İlerleme sıfırlandı!')}>
                        <div className="size-10 rounded-xl bg-red-500/10 group-hover:bg-white/20 flex items-center justify-center">
                          <span className="material-symbols-outlined">refresh</span>
                        </div>
                        <div className="text-left">
                          <p className="text-sm leading-tight">İlerlemeyi Sıfırla</p>
                          <p className="text-[10px] opacity-70 font-medium">Bu işlem geri alınamaz.</p>
                        </div>
                      </button>
                   </div>
                </div>
             </div>
          </section>
        </div>

        <footer className="w-full py-10 text-center">
            <div className="h-px w-20 bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-700 to-transparent mx-auto mb-6"></div>
            <p className="text-[10px] font-black uppercase tracking-[0.5em] text-gray-400 dark:text-gray-600">EnglishBus Advanced SRS • v2.4.1</p>
        </footer>
      </div>
    </div>
  );
};

// --- Custom Components ---

const Toggle: React.FC<{ checked: boolean; onChange: () => void; color?: string }> = ({ checked, onChange, color = "bg-brand-500" }) => (
  <button 
    onClick={onChange}
    className={`relative inline-flex h-7 w-12 items-center rounded-2xl transition-all duration-500 focus:outline-none shadow-inner ${
        checked ? color : 'bg-gray-200 dark:bg-white/10'
    }`}
  >
    <span className={`inline-block h-5 w-5 transform rounded-xl bg-white shadow-xl transition-all duration-300 ease-out ${
        checked ? 'translate-x-6' : 'translate-x-1'
    }`} />
  </button>
);

export default SettingsPage;
