import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const GITHUB_URL = "https://github.com/mohamedibraheem100/mizan-hr";

const features = [
  {
    title: "Evidence, not vibes",
    titleAr: "دليل مش انطباع",
    body: "Every criterion score links to the exact line in the CV that justifies it. No quote, no score.",
  },
  {
    title: "Blind mode",
    titleAr: "تقييم أعمى",
    body: "Name, age, gender, nationality and photo are removed before scoring to reduce bias.",
  },
  {
    title: "Arabic + English",
    titleAr: "عربي وإنجليزي",
    body: "Arabic CV against an English JD, or the other way round. The UI supports RTL.",
  },
];

const steps = [
  { n: "1", text: "Paste a Job Description" },
  { n: "2", text: "Edit the proposed rubric and weights" },
  { n: "3", text: "Upload up to 10 CVs" },
  { n: "4", text: "Get a ranked list with quoted evidence" },
];

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center px-4 py-16 sm:py-24">
      <section className="w-full max-w-3xl text-center">
        <Badge variant="secondary" className="mb-6">
          Day-1 MVP · in progress
        </Badge>
        <h1 className="text-5xl font-semibold tracking-tight sm:text-6xl">
          Mizan <span aria-hidden>⚖️</span>
        </h1>
        <p className="mt-2 text-lg text-muted-foreground" dir="rtl" lang="ar">
          ميزان: فرز CVs بدليل واضح من السيرة الذاتية نفسها
        </p>
        <p className="mx-auto mt-6 max-w-2xl text-balance text-xl text-foreground/90">
          Screen CVs against a Job Description in minutes, and see{" "}
          <span className="font-semibold">why</span> every score was given.
        </p>
        <p className="mx-auto mt-3 max-w-xl text-sm text-muted-foreground">
          Mizan is a decision-support tool. The recruiter always makes the
          final decision. No auto-reject, ever.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button size="lg" disabled title="Available after M5">
            Try the demo (soon)
          </Button>
          <Button
            size="lg"
            variant="outline"
            nativeButton={false}
            render={<a href={GITHUB_URL} target="_blank" rel="noreferrer" />}
          >
            View on GitHub
          </Button>
        </div>
      </section>

      <section className="mt-20 grid w-full max-w-5xl gap-6 sm:grid-cols-3">
        {features.map((f) => (
          <Card key={f.title}>
            <CardHeader>
              <CardTitle>{f.title}</CardTitle>
              <CardDescription dir="rtl" lang="ar">
                {f.titleAr}
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {f.body}
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="mt-20 w-full max-w-3xl">
        <h2 className="text-center text-2xl font-semibold">How it works</h2>
        <ol className="mt-8 grid gap-4 sm:grid-cols-2">
          {steps.map((s) => (
            <li
              key={s.n}
              className="flex items-start gap-4 rounded-lg border p-4"
            >
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                {s.n}
              </span>
              <span className="pt-1 text-sm">{s.text}</span>
            </li>
          ))}
        </ol>
      </section>

      <footer className="mt-24 max-w-2xl text-center text-xs text-muted-foreground">
        <p>
          Privacy: CV files are never stored. Only scores and quoted evidence
          are kept, and deleted after 24 hours. The public demo uses synthetic
          CVs only. Do not upload real candidates&apos; CVs.
        </p>
      </footer>
    </main>
  );
}
