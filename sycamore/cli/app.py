from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from sycamore import __version__
from sycamore.core.capture_service import create_capture, list_inbox
from sycamore.core.doctor_service import run_doctor
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import PromoteError, promote_capture
from sycamore.core.query_service import query_cheatsheet
from sycamore.core.sync_service import sync_nodes
from sycamore.models.enums import CaptureKind, ClaimedLevel
from sycamore.storage.database import DatabaseError

app = typer.Typer(
    help="Sycamore: local-first CLI for capability capture and recovery.",
    no_args_is_help=True,
)
console = Console()


def _not_implemented(command_name: str) -> None:
    console.print(f"[yellow]{command_name} is planned for the P0 capture-first loop.[/yellow]")
    raise typer.Exit(code=2)


def _handle_database_error(error: DatabaseError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


def _handle_promote_error(error: PromoteError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


@app.command()
def version() -> None:
    """Show Sycamore version."""
    console.print(f"syca {__version__}")


@app.command()
def init() -> None:
    """Initialize a local Sycamore data directory."""
    result = initialize_sycamore()
    console.print(f"[green]Sycamore home:[/green] {result.home}")

    if result.created_directories:
        for directory in result.created_directories:
            console.print(f"[green]Created directory:[/green] {directory.name}/")
    if result.created_config:
        console.print("[green]Created config.toml[/green]")
    if result.created_database:
        console.print("[green]Initialized SQLite schema[/green]")
    if not any((result.created_directories, result.created_config, result.created_database)):
        console.print("[yellow]Already initialized. No changes made.[/yellow]")


@app.command()
def capture(
    note: Annotated[str | None, typer.Option("--note", help="Capture a quick note.")] = None,
    cheat: Annotated[str | None, typer.Option("--cheat", help="Capture a cheatsheet entry.")] = None,
    link: Annotated[str | None, typer.Option("--link", help="Capture a reference link.")] = None,
    context: Annotated[
        str | None,
        typer.Option("--context", help="Optional scenario or context for this capture."),
    ] = None,
) -> None:
    """Capture a low-friction fragment into Inbox."""
    if sum(value is not None for value in (note, cheat, link)) != 1:
        console.print("[red]Choose exactly one of --note, --cheat, or --link.[/red]")
        raise typer.Exit(code=1)

    if note is not None:
        kind = CaptureKind.NOTE
        content = note
        source = None
    elif cheat is not None:
        kind = CaptureKind.CHEAT
        content = cheat
        source = None
    else:
        kind = CaptureKind.LINK
        content = link or ""
        source = link

    try:
        item = create_capture(kind=kind, content=content, context=context, source=source)
    except DatabaseError as error:
        _handle_database_error(error)

    console.print(f"[green]Captured[/green] {item.id}")
    console.print(f"Kind: {item.kind.value}")
    console.print(f"Status: {item.status.value}")


@app.command()
def inbox() -> None:
    """List pending CaptureItems."""
    try:
        items = list_inbox()
    except DatabaseError as error:
        _handle_database_error(error)

    if not items:
        console.print("[yellow]Inbox is empty.[/yellow]")
        return

    table = Table(title="Inbox")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Kind")
    table.add_column("Content")
    table.add_column("Created")

    for item in items:
        preview = item.content.replace("\n", " ")
        if len(preview) > 60:
            preview = f"{preview[:57]}..."
        table.add_row(item.id, item.kind.value, preview, item.created_at)

    console.print(table)


@app.command()
def promote(
    capture_id: str,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Capability assertion title for the new node."),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option("--domain", help="Optional domain label, e.g. shell or docker."),
    ] = None,
    claimed_level: Annotated[
        ClaimedLevel,
        typer.Option("--claimed-level", help="Initial claimed level for the node."),
    ] = ClaimedLevel.L0,
) -> None:
    """Promote a CaptureItem into an AbilityNode."""
    try:
        result = promote_capture(
            capture_id,
            title=title,
            domain=domain,
            claimed_level=claimed_level,
        )
    except DatabaseError as error:
        _handle_database_error(error)
    except PromoteError as error:
        _handle_promote_error(error)

    console.print(f"[green]Promoted[/green] {result.capture.id} -> {result.node.id}")
    console.print(f"Title: {result.node.title}")
    console.print(f"Slug: {result.node.slug}")
    console.print(f"Node file: {result.node_file}")
    if title is None:
        console.print("[yellow]Tip: refine the title and sections in the Markdown file.[/yellow]")


@app.command()
def query(
    term: str,
    cheat: Annotated[bool, typer.Option("--cheat", help="Show only Cheatsheet content.")] = False,
) -> None:
    """Query promoted AbilityNodes."""
    if not cheat:
        console.print("[red]P0 query currently requires --cheat.[/red]")
        raise typer.Exit(code=1)

    try:
        matches = query_cheatsheet(term)
    except DatabaseError as error:
        _handle_database_error(error)

    if not matches:
        console.print(f"[yellow]No cheatsheet matches for '{term}'.[/yellow]")
        return

    for match in matches:
        console.print(f"[bold cyan]{match.node.title}[/bold cyan] ({match.node.slug})")
        if match.cheatsheet.strip():
            console.print(match.cheatsheet.strip())
        else:
            console.print("[yellow]Cheatsheet is empty. Add practical commands in the node file.[/yellow]")
        console.print()


@app.command()
def sync() -> None:
    """Synchronize Markdown AbilityNodes into the SQLite index."""
    try:
        result = sync_nodes()
    except DatabaseError as error:
        _handle_database_error(error)

    console.print(f"[green]Synced[/green] {result.synced} node(s)")
    if result.created:
        console.print(f"Created index entries: {result.created}")
    if result.updated:
        console.print(f"Updated index entries: {result.updated}")
    if result.skipped:
        console.print(f"[yellow]Skipped invalid files: {result.skipped}[/yellow]")


@app.command()
def doctor() -> None:
    """Check local data consistency."""
    try:
        report = run_doctor()
    except DatabaseError as error:
        _handle_database_error(error)

    if report.ok:
        console.print("[green]No consistency issues found.[/green]")
        return

    for issue in report.issues:
        location = f" ({issue.path})" if issue.path else ""
        console.print(f"[red]{issue.code}[/red]{location}: {issue.message}")

    raise typer.Exit(code=1)


def main() -> None:
    app()
