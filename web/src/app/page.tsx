import { SITE_CONFIG, PERSONAL_INFO } from "@/lib/constants";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* Hero Section - Placeholder */}
      <section className="flex flex-col items-center justify-center min-h-screen px-6 text-center">
        <div className="animate-slide-up">
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
            {SITE_CONFIG.name}
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-8">
            {SITE_CONFIG.description}
          </p>
          <p className="text-sm text-muted-foreground">
            Created by{" "}
            <a
              href={PERSONAL_INFO.website}
              className="underline hover:text-foreground transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              {PERSONAL_INFO.name}
            </a>
          </p>
        </div>

        <div className="mt-12 flex gap-4">
          <div className="px-6 py-3 bg-primary text-primary-foreground rounded-full font-medium hover-lift cursor-pointer">
            Try Demo
          </div>
          <a
            href={PERSONAL_INFO.github}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 border border-border rounded-full font-medium hover-lift"
          >
            View Source
          </a>
        </div>

        {/* Coming soon indicator */}
        <div className="mt-24 text-sm text-muted-foreground">
          <p>Full interface coming soon...</p>
          <p className="mt-2 text-xs">
            Next.js + Tailwind + shadcn/ui + Framer Motion
          </p>
        </div>
      </section>
    </main>
  );
}
