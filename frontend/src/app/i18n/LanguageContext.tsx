import { createContext, useContext, useEffect, useMemo, useState } from 'react';

export type Language = 'en' | 'hi' | 'mr';

const labels = {
  en: { language: 'Language', english: 'English', hindi: 'हिन्दी', marathi: 'मराठी' },
  hi: { language: 'भाषा', english: 'अंग्रेज़ी', hindi: 'हिन्दी', marathi: 'मराठी' },
  mr: { language: 'भाषा', english: 'इंग्रजी', hindi: 'हिंदी', marathi: 'मराठी' },
} as const;

type Labels = (typeof labels)[Language];
type Ctx = { language: Language; setLanguage: (l: Language) => void; t: Labels };
const LanguageContext = createContext<Ctx | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('ncct-language');
    return saved === 'hi' || saved === 'mr' ? saved : 'en';
  });
  const setLanguage = (l: Language) => {
    setLanguageState(l);
    localStorage.setItem('ncct-language', l);
    document.documentElement.lang = l;
  };
  const value = useMemo(() => ({ language, setLanguage, t: labels[language] }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used inside LanguageProvider');
  return ctx;
}
