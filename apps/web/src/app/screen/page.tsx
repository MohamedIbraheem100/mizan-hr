import type { Metadata } from "next";

import { Workspace } from "@/components/screen/workspace";

export const metadata: Metadata = { title: "Screening workspace" };

export default function ScreenPage() {
  return <Workspace />;
}
