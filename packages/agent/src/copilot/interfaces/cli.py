"""
Command-line interface for the Strategic Research Copilot.

Usage:
    copilot chat              # Interactive research session
    copilot research "query"  # Single research query
    copilot status            # Check connection status
"""

import logging
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="copilot",
    help="Strategic Research Copilot - AI-powered research analyst",
    add_completion=False,
)

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def setup_langsmith() -> None:
    """Configure LangSmith tracing."""
    from copilot.config.settings import settings
    
    if settings.langsmith_enabled:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        console.print("[dim]📊 LangSmith tracing enabled[/dim]")


@app.command()
def chat() -> None:
    """Start an interactive research session."""
    setup_langsmith()
    
    from copilot.agent.workflow import create_copilot
    
    console.print(Panel.fit(
        "[bold blue]Strategic Research Copilot[/bold blue]\n\n"
        "I'm your AI research analyst. Ask me strategic questions\n"
        "about the documents in the knowledge graph.\n\n"
        "I'll plan my research, gather data, analyze it, and\n"
        "even loop back if I need more information.\n\n"
        "Commands: [dim]/quit[/dim] to exit, [dim]/stream[/dim] to toggle streaming",
        title="Welcome",
    ))
    
    copilot = create_copilot()
    stream_mode = False
    
    while True:
        try:
            query = console.input("\n[bold green]You:[/bold green] ").strip()
            
            if not query:
                continue
            
            if query.lower() in ("/quit", "/exit", "/q"):
                console.print("[dim]Goodbye![/dim]")
                break
            
            if query.lower() == "/stream":
                stream_mode = not stream_mode
                console.print(f"[dim]Streaming mode: {stream_mode}[/dim]")
                continue
            
            if stream_mode:
                # Stream mode - show each step
                console.print("\n[bold blue]Copilot:[/bold blue]")
                for event in copilot.stream(query):
                    for node_name, update in event.items():
                        if node_name == "responder":
                            console.print(Markdown(update.get("final_response", "")))
                        else:
                            console.print(f"[dim]  → {node_name}[/dim]")
            else:
                # Regular mode - just show final response
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task("Researching...", total=None)
                    response = copilot.get_response(query)
                
                console.print("\n[bold blue]Copilot:[/bold blue]")
                console.print(Markdown(response))
                
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type /quit to exit.[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def research(
    query: str = typer.Argument(..., help="The research question"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """Run a single research query."""
    setup_langsmith()
    
    from copilot.agent.workflow import create_copilot
    
    if verbose:
        logging.getLogger("copilot").setLevel(logging.DEBUG)
    
    copilot = create_copilot()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Researching...", total=None)
        
        if verbose:
            result = copilot.research(query)
            console.print("\n[dim]Research Summary:[/dim]")
            console.print(f"  Query Type: {result.get('query_type')}")
            console.print(f"  Strategy: {result.get('retrieval_strategy')}")
            console.print(f"  Iterations: {result.get('iteration')}")
            console.print(f"  Quality: {result.get('quality_score', 0):.0%}")
            console.print(f"  Output Format: {result.get('output_format')}")
            response = result.get("final_response", "No response")
        else:
            response = copilot.get_response(query)
    
    console.print(Markdown(response))


@app.command()
def status() -> None:
    """Check connection status and configuration."""
    from copilot.config.settings import settings
    from copilot.graph.connection import graph_connection
    
    console.print("[bold]Strategic Research Copilot Status[/bold]\n")
    
    # Neo4j connection
    try:
        if graph_connection.health_check():
            console.print("[green]✅ Neo4j connection: OK[/green]")
            
            # Get some stats
            result = graph_connection.query(
                "MATCH (n) RETURN count(n) AS nodes"
            )
            nodes = result[0]["nodes"] if result else 0
            
            result = graph_connection.query(
                "MATCH ()-[r]->() RETURN count(r) AS rels"
            )
            rels = result[0]["rels"] if result else 0
            
            console.print(f"   Nodes: {nodes}")
            console.print(f"   Relationships: {rels}")
        else:
            console.print("[red]❌ Neo4j connection: FAILED[/red]")
    except Exception as e:
        console.print(f"[red]❌ Neo4j connection: {e}[/red]")
    
    # LangSmith
    if settings.langsmith_enabled:
        console.print(f"[green]✅ LangSmith: Enabled ({settings.langchain_project})[/green]")
    else:
        console.print("[yellow]⚠️ LangSmith: Not configured[/yellow]")
    
    # Configuration summary
    console.print(f"\n[dim]Model: {settings.llm_model}[/dim]")
    console.print(f"[dim]Quality threshold: {settings.quality_threshold}[/dim]")
    console.print(f"[dim]Max iterations: {settings.max_iterations}[/dim]")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
