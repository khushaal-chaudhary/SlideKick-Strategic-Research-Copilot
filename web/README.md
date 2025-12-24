# Strategic Research Copilot - Web Interface

Modern, Apple-inspired web interface for the Strategic Research Copilot showcase.

## Features

- Sleek, light-themed design with smooth animations
- Real-time log streaming as agent processes queries
- Interactive query interface with example prompts
- Portfolio sections (About, Tech Stack, Future Iterations)
- Fully responsive design

## Tech Stack

- **Next.js 14** - App Router with React Server Components
- **Tailwind CSS v4** - Utility-first styling
- **shadcn/ui** - High-quality UI components
- **Framer Motion** - Smooth animations
- **Geist Font** - Clean, modern typography

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/
│   ├── layout.tsx      # Root layout with metadata
│   ├── page.tsx        # Main page
│   └── globals.css     # Global styles & design system
├── components/
│   ├── ui/             # shadcn/ui components
│   ├── layout/         # Layout components (Header, Footer)
│   ├── sections/       # Page sections (Hero, TechStack, etc.)
│   └── agent/          # Agent-specific components (LogViewer, QueryInput)
├── hooks/              # Custom React hooks
└── lib/
    ├── constants.ts    # Site config, personal info, tech stack data
    └── utils.ts        # Utility functions
```

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://your-hf-space.hf.space
```

## Deployment

Deploy to Vercel with one click:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/khushaal-chaudhary/strategic-research-copilot)

Or manually:

```bash
npm run build
vercel --prod
```

## Design System

- **Colors**: Light theme with subtle grays, black text
- **Typography**: Geist Sans (body), Geist Mono (code)
- **Animations**: Fade-in, slide-up, hover-lift effects
- **Spacing**: Consistent padding/margins following 4px grid
