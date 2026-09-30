import { useLanguage, Language } from '../i18n/LanguageContext';

export function LanguageSelector() {
  const { language, setLanguage, t } = useLanguage();
  return (
    <label className="language-selector">
      <span className="sr-only">{t.language}</span>
      <select value={language} onChange={e => setLanguage(e.target.value as Language)} aria-label={t.language}>
        <option value="en">{t.english}</option>
        <option value="hi">{t.hindi}</option>
        <option value="mr">{t.marathi}</option>
      </select>
    </label>
  );
}
