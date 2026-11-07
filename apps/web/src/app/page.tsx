"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "motion/react";

import { useLang } from "@/components/language-provider";
import { PipelineRail } from "@/components/pipeline-rail";
import { Logo } from "@/components/site-header";
import { Button } from "@/components/ui/button";

const Scale3D = dynamic(() => import("@/components/scale-3d").then((m) => m.Scale3D), {
  ssr: false,
  loading: () => <Logo className="size-40 text-brass/40" />,
});

const ease = [0.2, 0.8, 0.2, 1] as const;
const rise = (delay = 0) => ({
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.7, ease, delay },
});

export default function Home() {
  const { t } = useLang();
  return (
    <main className="flex-1">
      {/* ---------------- Hero ---------------- */}
      <section className="ink-surface relative overflow-hidden">
        <div className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 pb-20 pt-16 sm:px-8 lg:grid-cols-[1.1fr_0.9fr] lg:pb-28 lg:pt-24">
          <div className="relative z-10">
            <motion.p
              className="eyebrow text-brass"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6 }}
            >
              {t.hero.eyebrow}
            </motion.p>
            <motion.h1
              className="display mt-5 max-w-3xl text-paper"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease, delay: 0.05 }}
            >
              {t.hero.title}
            </motion.h1>
            <motion.p
              className="mt-6 max-w-xl text-lg leading-relaxed text-paper/75"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease, delay: 0.15 }}
            >
              {t.hero.body}
            </motion.p>
            <motion.div
              className="mt-9 flex flex-wrap gap-3"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease, delay: 0.25 }}
            >
              <Button
                size="lg"
                nativeButton={false}
                render={<Link href="/screen" />}
                className="h-11 bg-brass px-6 text-base text-ink hover:bg-brass-strong"
              >
                {t.hero.cta}
              </Button>
              <Button
                size="lg"
                variant="outline"
                nativeButton={false}
                render={<Link href="/demo" />}
                className="h-11 border-white/25 bg-transparent px-6 text-base text-paper hover:bg-white/10"
              >
                {t.hero.secondary}
              </Button>
            </motion.div>

            <motion.dl
              className="mt-14 grid max-w-xl grid-cols-3 gap-6 border-t border-white/10 pt-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.45 }}
            >
              {[
                ["100%", t.hero.stat1],
                ["< 10", t.hero.stat2],
                ["0", t.hero.stat3],
              ].map(([n, label]) => (
                <div key={label}>
                  <dt className="num text-3xl font-semibold text-paper">{n}</dt>
                  <dd className="mt-1 text-xs leading-snug text-paper/60">{label}</dd>
                </div>
              ))}
            </motion.dl>
          </div>

          <div className="relative mx-auto aspect-square w-full max-w-md lg:max-w-none">
            <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_50%_40%,oklch(0.74_0.12_78/0.18),transparent_60%)]" />
            <Scale3D className="relative h-full w-full" />
          </div>
        </div>
      </section>

      {/* ---------------- Pillars ---------------- */}
      <section className="mx-auto w-full max-w-7xl px-5 py-20 sm:px-8 lg:py-28">
        <motion.h2 className="max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl" {...rise()}>
          {t.pillars.title}
        </motion.h2>
        <div className="mt-12 grid gap-px overflow-hidden rounded-xl border bg-border md:grid-cols-2">
          {t.pillars.items.map((item, i) => (
            <motion.article key={item.t} className="bg-card p-7 sm:p-9" {...rise(i * 0.08)}>
              <div className="num text-xs font-medium text-brass-strong">0{i + 1}</div>
              <h3 className="mt-3 text-xl font-semibold">{item.t}</h3>
              <p className="mt-3 leading-relaxed text-muted-foreground">{item.d}</p>
            </motion.article>
          ))}
        </div>
      </section>

      {/* ---------------- Pipeline ---------------- */}
      <section id="how" className="paper-grid border-y bg-paper-2/60">
        <div className="mx-auto w-full max-w-7xl px-5 py-20 sm:px-8 lg:py-28">
          <motion.div {...rise()}>
            <p className="eyebrow">{t.nav.how}</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">{t.pipeline.title}</h2>
            <p className="mt-3 max-w-2xl text-muted-foreground">{t.pipeline.subtitle}</p>
          </motion.div>
          <PipelineRail className="mt-12" />
        </div>
      </section>

      {/* ---------------- CTA ---------------- */}
      <section className="mx-auto w-full max-w-7xl px-5 py-20 sm:px-8 lg:py-28">
        <motion.div
          className="ink-surface relative overflow-hidden rounded-2xl px-7 py-12 sm:px-12 sm:py-16"
          {...rise()}
        >
          <Logo className="absolute -end-10 -top-10 size-64 text-brass/10" />
          <h2 className="relative max-w-xl text-3xl font-semibold tracking-tight text-paper sm:text-4xl">
            {t.cta.title}
          </h2>
          <p className="relative mt-4 max-w-xl text-paper/70">{t.cta.body}</p>
          <Button
            size="lg"
            nativeButton={false}
            render={<Link href="/screen" />}
            className="relative mt-8 h-11 bg-brass px-6 text-base text-ink hover:bg-brass-strong"
          >
            {t.cta.button}
          </Button>
        </motion.div>
      </section>
    </main>
  );
}
