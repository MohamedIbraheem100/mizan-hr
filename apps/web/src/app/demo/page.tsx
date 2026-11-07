import type { Metadata } from "next";

import { DemoPage } from "@/components/screen/demo-page";

export const metadata: Metadata = { title: "Demo" };

export default function Page() {
  return <DemoPage />;
}
