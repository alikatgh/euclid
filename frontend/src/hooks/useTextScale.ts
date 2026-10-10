import { useEffect, useState } from 'react';

/** Shared preference across reference and curriculum players; storage may be unavailable. */
export function useTextScale() {
  const [fontScale, setFontScale] = useState(() => {
    try {
      const saved = Number(localStorage.getItem('alg-e-font-scale'));
      if (Number.isFinite(saved) && saved >= .85 && saved <= 1.35) return saved;
    } catch { /* Private browsing can disable storage. */ }
    return 1;
  });
  useEffect(() => {
    document.documentElement.style.fontSize = `${Math.round(fontScale * 100)}%`;
    document.documentElement.style.setProperty('--app-font-scale', String(fontScale));
    try { localStorage.setItem('alg-e-font-scale', String(fontScale)); } catch { /* Keep the in-memory preference. */ }
  }, [fontScale]);
  return { fontScale, setFontScale };
}
