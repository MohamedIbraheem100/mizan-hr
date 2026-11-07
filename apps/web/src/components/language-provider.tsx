"use client";

import { createContext, useContext, useEffect, useMemo, useSyncExternalStore } from "react";

import { type Dictionary, type Lang, dictionaries } from "@/lib/i18n";

type Ctx = { lang: Lang; dir: "ltr" | "rtl"; t: Dictionary; setLang: (l: Lang) => void };

const LanguageContext = createContext<Ctx | null>(null);
const STORAGE_KEY = "mizan.lang";

/* A tiny external store: the server renders "en", the client hydrates then
   switches to the saved/browser language without a setState-in-effect. */
const listeners = new Set<() => void>();
let current: Lang | null = null;

function detect(): Lang {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "ar" || saved === "en") return saved;
  } catch {
    /* storage may be blocked */
  }
  return navigator.language?.toLowerCase().startsWith("ar") ? "ar" : "en";
}
function getSnapshot(): Lang {
  if (current === null) current = detect();
  return current;
}
function getServerSnapshot(): Lang {
  return "en";
}
function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}
function setLang(l: Lang) {
  current = l;
  try {
    window.localStorage.setItem(STORAGE_KEY, l);
  } catch {
    /* ignore */
  }
  listeners.forEach((cb) => cb());
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const lang = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  }, [lang]);

  const value = useMemo<Ctx>(
    () => ({ lang, dir: lang === "ar" ? "rtl" : "ltr", t: dictionaries[lang], setLang }),
    [lang],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang(): Ctx {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLang must be used inside <LanguageProvider>");
  return ctx;
}
