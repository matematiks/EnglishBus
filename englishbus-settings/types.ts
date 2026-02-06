
export interface UserSettings {
  username: string;
  membership: string;
  autoAudio: boolean;
  showImages: boolean;
  audioSpeed: number;
  dailyGoal: number;
  activeCourse: string;
  themeColor: string;
  isDarkMode: boolean;
  focusMode: 'relaxed' | 'standard' | 'aggressive';
}

export type ThemeVariant = {
  name: string;
  primary: string;
  accent: string;
  id: string;
};
