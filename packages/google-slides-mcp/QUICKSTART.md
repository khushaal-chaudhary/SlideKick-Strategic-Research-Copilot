# Google Slides MCP - Quick Start Guide

Get up and running with Google Slides integration in 5 minutes using **Service Account authentication**.

## 5-Minute Setup

### Step 1: Google Cloud Setup (3 min)

1. Go to https://console.cloud.google.com
2. Create new project → "Google Slides MCP"
3. Enable APIs:
   - Search "Google Slides API" → Enable
   - Search "Google Drive API" → Enable
4. Create Service Account:
   - Go to **IAM & Admin > Service Accounts**
   - Click **Create Service Account**
   - Name: "slides-mcp-service"
   - Role: **Editor**
   - Click **Done**
5. Generate Key:
   - Click on the service account
   - **Keys** tab → **Add Key** → **Create new key**
   - Choose **JSON** → Download

### Step 2: Install & Configure (1 min)

```bash
# Navigate to the MCP package
cd packages/google-slides-mcp

# Install dependencies
npm install

# Move your service account key
mv ~/Downloads/your-project-*.json keys/google_service_account_key.json
```

### Step 3: Configure Sharing (30 sec)

Since the service account owns the presentations, configure auto-sharing:

```bash
# Add to your .env or shell profile
export GOOGLE_SLIDES_SHARE_EMAIL="your.email@example.com"
```

Without this, the agent will ask for your email when creating presentations.

### Step 4: Add to Claude Desktop (Optional)

Edit your Claude Desktop config:

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

Restart Claude Desktop.

## Test It!

### With Strategic Research Copilot

Request slides output when running a research query:
```
"Research Microsoft's AI strategy and create a presentation"
```

The agent will:
1. Research the topic
2. Create aesthetically pleasing slides
3. Share the presentation with your email
4. Return the Google Slides URL

### With Claude Desktop

Try these commands:
- "Create a new Google Slides presentation called 'Test Presentation'"
- "Get details about presentation ID xyz123"

## Tools Available

| Tool | Purpose |
|------|---------|
| `create_presentation` | Create empty presentation |
| `get_presentation` | Get presentation details |
| `batch_update_presentation` | Add slides, text, shapes |
| `get_page` | Get specific slide info |
| `summarize_presentation` | Extract all text content |
| `move_presentation` | Move to Drive folder |

## Common Issues

**"Service Account not configured"**
→ Ensure `keys/google_service_account_key.json` exists

**"Permission denied" when sharing**
→ Check Drive API is enabled and email is valid

**"API not enabled"**
→ Enable Slides API and Drive API in Google Cloud Console

**"Can't access presentation"**
→ Set `GOOGLE_SLIDES_SHARE_EMAIL` environment variable

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_SLIDES_SHARE_EMAIL` | Email to auto-share presentations with |
| `GOOGLE_APPLICATION_CREDENTIALS` | Alternative path to service account key |

## Integration Flow

```
Research Query → Planner → Retriever → Analyzer → Critic → Generator → Google Slides
                                                              ↓
                                                    Creates presentation
                                                              ↓
                                                    Auto-shares with you
                                                              ↓
                                                    Returns URL
```

## Aesthetic Design

The agent creates visually appealing slides:
- Max 5 bullets per slide
- Concise text (under 10 words per bullet)
- Action verbs for impact
- Clear visual hierarchy
- Speaker notes included
