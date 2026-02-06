
import React, { useState, useEffect } from 'react';
import SettingsPage from './components/SettingsPage';
import { UserSettings } from './types';

const App: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings>({
    username: "Alex Fibonacci",
    membership: "BİREYSEL",
    autoAudio: true,
    showImages: true,
    audioSpeed: 1.0,
    dailyGoal: 10,
    activeCourse: "Business Communication",
    themeColor: "purple",
    isDarkMode: false,
    focusMode: 'standard',
  });

  const [activeScreen, setActiveScreen] = useState<'dashboard' | 'settings'>('settings');

  useEffect(() => {
    if (settings.isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings.isDarkMode]);

  const updateSettings = (updates: Partial<UserSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  return (
    <div className="relative min-h-screen">
      {/* Background Decorations */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-5%] w-[40vw] h-[40vw] rounded-full bg-brand-500/10 blur-[120px] animate-blob"></div>
        <div className="absolute bottom-[-10%] right-[-5%] w-[50vw] h-[50vw] rounded-full bg-accent-500/10 blur-[150px] animate-blob" style={{ animationDelay: '2s' }}></div>
      </div>

      <main className="relative z-10">
        {activeScreen === 'settings' ? (
          <SettingsPage 
            settings={settings} 
            onUpdate={updateSettings} 
            onBack={() => console.log('Going back to dashboard...')} 
          />
        ) : (
          <div className="flex items-center justify-center min-h-screen">
            <button 
              onClick={() => setActiveScreen('settings')}
              className="px-6 py-3 bg-brand-600 text-white rounded-xl shadow-xl font-bold"
            >
              Open Settings
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
