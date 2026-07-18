from huggingface_hub import HfApi

print("🚀 Preparing upload...")
print("ℹ️  Ignoring 'venv', '.git', and '__pycache__' to speed things up.")

api = HfApi()

try:
    api.upload_folder(
        folder_path=".",
        repo_id="Khushaal/slidekick-agentic-system",
        repo_type="space",
        # NB: patterns are fnmatch on the full relative path — "web" alone
        # does NOT exclude "web/src/...", hence the explicit /** globs
        ignore_patterns=[
            ".git/**", "**/.venv/**", "venv/**", "**/venv/**",
            "**/__pycache__/**", "*.pyc", "**/node_modules/**", ".DS_Store",
            # secrets must never reach the Space repo
            ".env", "**/.env", "*.env", "packages/google-slides-mcp/keys/**",
            "notebooks/**", "**/.ipynb_checkpoints/**", "*.ipynb",
            "web/**", "*.db", "*.log",
        ]
    )
    print("✅ Upload complete!")
    print("👉 Check your Space here: https://huggingface.co/spaces/Khushaal/slidekick-agentic-system")
    
except Exception as e:
    print(f"❌ Error: {e}")