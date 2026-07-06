from huggingface_hub import HfApi

print("🚀 Preparing upload...")
print("ℹ️  Ignoring 'venv', '.git', and '__pycache__' to speed things up.")

api = HfApi()

try:
    api.upload_folder(
        folder_path=".",
        repo_id="Khushaal/slidekick-agentic-system",
        repo_type="space",
        ignore_patterns=[
            ".git", ".venv", "venv", "__pycache__", "*.pyc", "node_modules", ".DS_Store",
            # secrets must never reach the Space repo
            ".env", ".env.*", "*.env", "packages/google-slides-mcp/keys",
            "notebooks", ".ipynb_checkpoints", "web",
        ]
    )
    print("✅ Upload complete!")
    print("👉 Check your Space here: https://huggingface.co/spaces/Khushaal/slidekick-agentic-system")
    
except Exception as e:
    print(f"❌ Error: {e}")