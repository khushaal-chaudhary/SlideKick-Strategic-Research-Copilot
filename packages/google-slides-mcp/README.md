# Google Slides MCP Server

MCP (Model Context Protocol) server for Google Slides integration with Strategic Research Copilot. Uses the [`@bohachu/google-slides-mcp`](https://github.com/bohachu/botrun-google-slides-mcp) package with **Service Account authentication** for improved security and easier deployment.

## Features

- **Create Presentations**: Create new Google Slides presentations
- **Batch Updates**: Apply complex updates to presentations (text, shapes, layouts)
- **Get Presentation**: Retrieve presentation details and structure
- **Get Page**: Extract information from specific slides
- **Summarize Presentation**: Extract all text content for analysis
- **Move Presentation**: Transfer presentations to Google Drive folders
- **Auto-Sharing**: Automatically share presentations with configured email addresses

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Add your service account key (see setup below)
# Place google_service_account_key.json in keys/

# 3. Configure sharing (optional but recommended)
export GOOGLE_SLIDES_SHARE_EMAIL="your.email@example.com"
```

## Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Note your project ID

### 2. Enable APIs

Enable the following APIs in your project:
- **Google Slides API**
- **Google Drive API**

Go to **APIs & Services > Library** and search for each API to enable.

### 3. Create a Service Account

1. Go to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
3. Name it (e.g., "slides-mcp-service")
4. Grant role: **Editor** (or more restrictive: Slides Editor + Drive File Creator)
5. Click **Done**

### 4. Generate Service Account Key

1. Click on your newly created service account
2. Go to **Keys** tab
3. Click **Add Key > Create new key**
4. Select **JSON** format
5. Download the key file

### 5. Install the Key

Move the downloaded key to the `keys/` directory:

```bash
# Rename and move the key file
mv ~/Downloads/your-project-*.json keys/google_service_account_key.json
```

**Important**: Never commit this file to version control!

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_SLIDES_SHARE_EMAIL` | Email address to auto-share presentations with | Recommended |
| `GOOGLE_APPLICATION_CREDENTIALS` | Alternative path to service account key | Optional |

### Setting Up Auto-Sharing

Since presentations are created by the service account (not your personal account), you won't see them in your Google Drive by default. Configure auto-sharing:

```bash
# Add to your .env or shell profile
export GOOGLE_SLIDES_SHARE_EMAIL="your.email@example.com"
```

When a presentation is created:
- If email is configured: Presentation is automatically shared with you (you'll receive an email)
- If email is not configured: The agent will ask for your email to share the presentation

## Usage with Claude Desktop

Add to your Claude Desktop configuration:

**macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-slides": {
      "command": "google-slides-mcp"
    }
  }
}
```

Or if running from this directory:

```json
{
  "mcpServers": {
    "google-slides": {
      "command": "npm",
      "args": ["start"],
      "cwd": "/path/to/packages/google-slides-mcp"
    }
  }
}
```

## Available Tools

### `create_presentation`
Create a new empty presentation.

```json
{
  "title": "My Presentation"
}
```

### `get_presentation`
Get details about a presentation.

```json
{
  "presentationId": "1abc..."
}
```

### `batch_update_presentation`
Apply multiple updates to a presentation (add slides, text, shapes).

```json
{
  "presentationId": "1abc...",
  "requests": [
    {
      "createSlide": {
        "slideLayoutReference": {
          "predefinedLayout": "TITLE_AND_BODY"
        }
      }
    }
  ]
}
```

### `get_page`
Get information about a specific slide.

```json
{
  "presentationId": "1abc...",
  "pageObjectId": "slide123"
}
```

### `summarize_presentation`
Extract all text content from a presentation.

```json
{
  "presentationId": "1abc...",
  "includeSpeakerNotes": true
}
```

### `move_presentation`
Move or copy a presentation to a Drive folder.

```json
{
  "presentationId": "1abc...",
  "folderId": "folder123"
}
```

## Slide Layouts

Available predefined layouts:
- `TITLE` - Title slide with large centered text
- `TITLE_AND_BODY` - Standard slide with title and bullet points
- `SECTION_HEADER` - Section divider slide
- `BLANK` - Empty slide for custom content
- `TITLE_AND_TWO_COLUMNS` - Two-column layout
- `ONE_COLUMN_TEXT` - Single column text layout

## Integration with Strategic Research Copilot

This MCP server integrates with the Strategic Research Copilot agent:

```
Research Query → Planner → Retriever → Analyzer → Critic → Generator → Google Slides
```

The Generator node:
1. Creates aesthetically pleasing slide content (max 5 bullets, concise text)
2. Uses the Google Slides API via service account
3. Auto-shares with configured email or asks user for email
4. Returns the presentation URL

### Aesthetic Design Guidelines

The agent follows these principles when creating slides:
- Maximum 5 bullets per slide
- Bullets under 10 words each
- Action verbs to start bullets
- Clear visual hierarchy
- Speaker notes with talking points

## Troubleshooting

### "Service Account not configured"
Ensure the key file exists:
```bash
ls keys/google_service_account_key.json
```

### "Permission denied" when sharing
The service account needs the Drive API enabled and proper permissions. Check:
1. Google Drive API is enabled in your project
2. The target email is a valid Google account

### "API not enabled"
Enable both APIs in Google Cloud Console:
- Google Slides API
- Google Drive API

### Presentation created but can't access
Set the `GOOGLE_SLIDES_SHARE_EMAIL` environment variable to auto-share presentations with your account.

## File Structure

```
packages/google-slides-mcp/
├── keys/
│   └── google_service_account_key.json  # Your service account key (DO NOT COMMIT)
├── backup/                               # Old implementation backup
├── node_modules/                         # Dependencies (after npm install)
├── package.json                          # Package configuration
├── .gitignore                            # Ignores keys and node_modules
├── README.md                             # This file
└── QUICKSTART.md                         # Quick setup guide
```

## License

MIT
