from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from sycamore import __version__
from sycamore.core.capture_service import create_capture, list_inbox
from sycamore.core.doctor_service import run_doctor
from sycamore.core.graph_service import GraphError, build_domain_graph
from sycamore.core.graph_render import format_domain_graph_text
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.level_service import LevelError, set_claimed_level
from sycamore.core.link_service import LinkError, create_link
from sycamore.core.practice_service import PracticeError, log_practice
from sycamore.core.promote_service import PromoteError, promote_capture
from sycamore.core.query_service import query_cheatsheet
from sycamore.core.recover_service import (
    FailType,
    RecoverError,
    RecoverMode,
    RecoverRating,
    preview_recovery_drill,
    record_recovery_outcome,
)
from sycamore.core.review_service import (
    ReviewError,
    decide_review,
    list_node_reviews,
    preview_review,
    run_review,
)
from sycamore.models.enums import CaptureKind, ClaimedLevel, EdgeType, UserDecision
from sycamore.core.status_service import list_domain_status, list_stale_nodes, list_weak_nodes
from sycamore.core.sync_service import sync_nodes
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


def _handle_review_error(error: ReviewError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


def _handle_practice_error(error: PracticeError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


def _handle_level_error(error: LevelError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


def _handle_recover_error(error: RecoverError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


def _handle_link_error(error: LinkError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


def _handle_graph_error(error: GraphError) -> None:
    console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error


level_app = typer.Typer(help="Manage claimed ability levels.")
app.add_typer(level_app, name="level")

reviews_app = typer.Typer(help="Inspect and decide ReviewRuns.")
app.add_typer(reviews_app, name="reviews")


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
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Kind")
    table.add_column("Content")
    table.add_column("Created")

    for position, item in enumerate(items, start=1):
        preview = item.content.replace("\n", " ")
        if len(preview) > 60:
            preview = f"{preview[:57]}..."
        short_id = item.id[:8]
        table.add_row(str(position), short_id, item.kind.value, preview, item.created_at)

    console.print(table)


@app.command()
def promote(
    capture_id: Annotated[
        str | None,
        typer.Argument(help="Capture id or unique prefix. Omit to promote the latest inbox item."),
    ] = None,
    latest: Annotated[
        bool,
        typer.Option("--latest", help="Promote the most recent inbox item."),
    ] = False,
    index: Annotated[
        int | None,
        typer.Option("--index", help="Promote inbox item by list number (see syca inbox)."),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Capability assertion title for the new node."),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option("--domain", help="Optional domain label, e.g. shell or docker."),
    ] = None,
    node_type: Annotated[
        str,
        typer.Option(
            "--type",
            help="Node type: capability, concept, theorem, or process.",
        ),
    ] = "capability",
    claimed_level: Annotated[
        ClaimedLevel,
        typer.Option("--claimed-level", help="Initial claimed level for the node."),
    ] = ClaimedLevel.L0,
) -> None:
    """Promote a CaptureItem into an AbilityNode."""
    try:
        result = promote_capture(
            capture_id,
            latest=latest,
            index=index,
            title=title,
            domain=domain,
            node_type=node_type,
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
def review(
    node_id: str,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview payload without calling Provider or saving."),
    ] = False,
) -> None:
    """Run a critique review on a node's Mental Model."""
    try:
        if dry_run:
            preview = preview_review(node_id)
        else:
            result = run_review(node_id)
    except DatabaseError as error:
        _handle_database_error(error)
    except ReviewError as error:
        _handle_review_error(error)

    if dry_run:
        assert preview is not None
        console.print(f"[bold]Node:[/bold] {preview.node.title} ({preview.node.slug})")
        console.print(f"[bold]Prompt version:[/bold] {preview.payload.prompt_version}")
        console.print(f"[bold]Provider:[/bold] {preview.provider_name} (dry-run)")
        console.print(f"[bold]Mental model hash:[/bold] {preview.payload.mental_model_hash[:12]}...")
        console.print("[bold]Mental Model preview:[/bold]")
        console.print(preview.payload.mental_model)
        return

    assert result is not None
    console.print(f"[green]Review completed[/green] {result.review_run.id}")
    console.print(f"Node status: {result.node.review_status.value}")
    console.print(f"Summary: {result.review_run.summary}")
    console.print(f"Raw output: {result.raw_output_file}")


@reviews_app.command("list")
def reviews_list(node_id: str) -> None:
    """List ReviewRuns for a node."""
    try:
        summaries = list_node_reviews(node_id)
    except DatabaseError as error:
        _handle_database_error(error)
    except ReviewError as error:
        _handle_review_error(error)

    if not summaries:
        console.print("[yellow]No review runs for this node.[/yellow]")
        return

    table = Table(title="Review Runs")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Created")
    table.add_column("Prompt")
    table.add_column("Decision")
    table.add_column("Outdated")

    for item in summaries:
        table.add_row(
            item.review.id,
            item.review.created_at,
            item.review.prompt_version,
            item.review.user_decision.value,
            "yes" if item.is_outdated else "no",
        )

    console.print(table)


def _review_decide(review_id: str, decision: UserDecision, label: str) -> None:
    try:
        result = decide_review(review_id, decision)
    except DatabaseError as error:
        _handle_database_error(error)
    except ReviewError as error:
        _handle_review_error(error)

    console.print(f"[green]{label}[/green] {result.review.id}")
    console.print(f"Node status: {result.node.review_status.value}")


@reviews_app.command("accept")
def reviews_accept(review_id: str) -> None:
    """Mark a ReviewRun as accepted by the user."""
    _review_decide(review_id, UserDecision.ACCEPTED, "Accepted review")


@reviews_app.command("ignore")
def reviews_ignore(review_id: str) -> None:
    """Mark a ReviewRun as ignored."""
    _review_decide(review_id, UserDecision.IGNORED, "Ignored review")


@reviews_app.command("revised")
def reviews_revised(review_id: str) -> None:
    """Mark a ReviewRun as needing revision."""
    _review_decide(review_id, UserDecision.REVISED, "Marked review as needs revision")


@app.command()
def practice(
    node_id: str,
    note: Annotated[str | None, typer.Option("--note", help="Quick practice note.")] = None,
    scenario: Annotated[str | None, typer.Option("--scenario")] = None,
    action: Annotated[str | None, typer.Option("--action")] = None,
    result: Annotated[str | None, typer.Option("--result")] = None,
    pitfall: Annotated[str | None, typer.Option("--pitfall")] = None,
) -> None:
    """Append a Practice Log entry to an AbilityNode."""
    try:
        practice_result = log_practice(
            node_id,
            note=note,
            scenario=scenario,
            action=action,
            result=result,
            pitfall=pitfall,
        )
    except DatabaseError as error:
        _handle_database_error(error)
    except PracticeError as error:
        _handle_practice_error(error)

    console.print(f"[green]Practice logged[/green] for {practice_result.node.title}")
    console.print(f"Entry time: {practice_result.entry_timestamp}")
    console.print(f"Node file: {practice_result.node_file}")


@level_app.command("set")
def level_set(
    node_id: str,
    level: ClaimedLevel,
) -> None:
    """Set the claimed level on an AbilityNode."""
    try:
        result = set_claimed_level(node_id, level)
    except DatabaseError as error:
        _handle_database_error(error)
    except LevelError as error:
        _handle_level_error(error)

    console.print(
        f"[green]Updated[/green] {result.node.title}: "
        f"{result.previous_level.value} -> {result.new_level.value}"
    )


@app.command()
def status(
    stale: Annotated[bool, typer.Option("--stale", help="Show nodes needing recovery practice.")] = False,
    domain: Annotated[str | None, typer.Option("--domain", help="Show freshness for a domain.")] = None,
    weak: Annotated[bool, typer.Option("--weak", help="Show weakness analysis (failure patterns).")] = False,
) -> None:
    """Show node status summaries (stale, domain freshness, or weakness analysis)."""
    flags = [stale, bool(domain), weak]
    if sum(flags) > 1:
        console.print("[red]Choose exactly one of --stale, --domain, or --weak.[/red]")
        raise typer.Exit(code=1)
    if sum(flags) == 0:
        console.print("[red]Provide --stale, --domain, or --weak.[/red]")
        raise typer.Exit(code=1)

    if stale:
        try:
            report = list_stale_nodes()
        except DatabaseError as error:
            _handle_database_error(error)

        if not report.nodes:
            console.print(
                f"[green]No stale nodes[/green] (threshold: {report.stale_after_days} days)."
            )
            return

        table = Table(title=f"Stale Nodes (>{report.stale_after_days} days)")
        table.add_column("Title")
        table.add_column("Slug")
        table.add_column("Level")
        table.add_column("Last Activity")
        table.add_column("Days")

        for item in report.nodes:
            table.add_row(
                item.node.title,
                item.node.slug,
                item.node.claimed_level.value,
                item.last_activity_at,
                str(item.days_since_activity),
            )

        console.print(table)
        return

    if weak:
        try:
            report = list_weak_nodes()
        except DatabaseError as error:
            _handle_database_error(error)

        if not report.nodes:
            console.print("[green]No weak nodes found — all recoveries passed.[/green]")
            return

        table = Table(title=f"Weakness Analysis ({report.total_fails} total failures)")
        table.add_column("Title")
        table.add_column("Domain")
        table.add_column("Fails")
        table.add_column("Top Fail Type")
        table.add_column("Risk")

        for w in report.nodes:
            risk_color = {"high": "red", "medium": "yellow", "low": "dim"}.get(w.risk_level, "")
            table.add_row(
                w.node.title,
                w.node.domain or "—",
                str(w.fail_count),
                w.top_fail_type or "—",
                f"[{risk_color}]{w.risk_level}[/{risk_color}]",
            )

        console.print(table)
        return

    assert domain is not None
    try:
        report = list_domain_status(domain)
    except DatabaseError as error:
        _handle_database_error(error)
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    table = Table(title=f"Domain: {report.domain} (stale > {report.stale_after_days} days)")
    table.add_column("Title")
    table.add_column("Slug")
    table.add_column("Level")
    table.add_column("Freshness")
    table.add_column("Days")

    for entry in report.entries:
        freshness_label = "[red]stale[/red]" if entry.freshness.is_stale else "[green]fresh[/green]"
        table.add_row(
            entry.node.title,
            entry.node.slug,
            entry.node.claimed_level.value,
            freshness_label,
            str(entry.freshness.days_since_activity),
        )

    console.print(table)


@app.command()
def recover(
    node_id: str,
    passed: Annotated[bool, typer.Option("--pass", help="Recovery passed — normal recall.")] = False,
    failed: Annotated[bool, typer.Option("--fail", help="Recovery failed — could not recall.")] = False,
    hard: Annotated[bool, typer.Option("--hard", help="Remembered but with significant effort.")] = False,
    easy: Annotated[bool, typer.Option("--easy", help="Recalled effortlessly.")] = False,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            help="Drill mode: recall-first (default), supported, or full.",
        ),
    ] = "recall-first",
    fail_type: Annotated[
        str | None,
        typer.Option(
            "--fail-type",
            help="Failure category: recall, concept, procedure, or transfer.",
        ),
    ] = None,
    note: Annotated[str | None, typer.Option("--note", help="Optional note for the outcome.")] = None,
) -> None:
    """Run a recovery drill — test your ability to recall a node's Mental Model."""
    rating_flags = [passed, failed, hard, easy]
    if sum(rating_flags) > 1:
        console.print("[red]Choose at most one of --pass, --fail, --hard, or --easy.[/red]")
        raise typer.Exit(code=1)

    if sum(rating_flags) == 1:
        if passed:
            rating = RecoverRating.PASS
        elif hard:
            rating = RecoverRating.HARD
        elif easy:
            rating = RecoverRating.EASY
        else:
            rating = RecoverRating.FAIL

        ft = None
        if fail_type and rating == RecoverRating.FAIL:
            try:
                ft = FailType(fail_type)
            except ValueError:
                console.print(
                    f"[red]Invalid --fail-type '{fail_type}'. "
                    f"Choose: recall, concept, procedure, or transfer.[/red]"
                )
                raise typer.Exit(code=1) from None
        elif fail_type and rating != RecoverRating.FAIL:
            console.print("[red]--fail-type is only valid with --fail.[/red]")
            raise typer.Exit(code=1)

        try:
            result = record_recovery_outcome(node_id, rating=rating, fail_type=ft, note=note)
        except DatabaseError as error:
            _handle_database_error(error)
        except RecoverError as error:
            _handle_recover_error(error)

        rating_label = {"pass": "passed", "fail": "failed", "hard": "hard", "easy": "easy"}
        label = rating_label.get(result.rating, result.rating)
        msg = f"[green]Recovery {label}[/green] for {result.node.title}"
        if result.fail_type:
            msg += f" ([yellow]{result.fail_type}[/yellow])"
        console.print(f"{msg} at {result.recorded_at}")
        return

    # Drill mode — no outcome flag given
    try:
        drill_mode = RecoverMode(mode)
    except ValueError:
        console.print(f"[red]Invalid --mode '{mode}'. Choose: recall-first, supported, or full.[/red]")
        raise typer.Exit(code=1) from None

    try:
        drill = preview_recovery_drill(node_id, mode=drill_mode)
    except DatabaseError as error:
        _handle_database_error(error)
    except RecoverError as error:
        _handle_recover_error(error)

    stale_hint = (
        f"[yellow]Stale[/yellow] ({drill.days_since_activity} days since activity)"
        if drill.is_stale
        else f"[green]Fresh[/green] ({drill.days_since_activity} days since activity)"
    )
    console.print(
        f"[bold]{drill.node.title}[/bold] "
        f"({drill.node.claimed_level.value}, {drill.node_type}) — {stale_hint}"
    )

    if drill_mode in (RecoverMode.RECALL_FIRST, RecoverMode.SUPPORTED):
        console.print(f"\n[bold cyan]Recall challenge:[/bold cyan] {drill.recall_prompt}")
        if drill_mode == RecoverMode.SUPPORTED and drill.cheatsheet:
            lines = drill.cheatsheet.strip().splitlines()
            hint = lines[0] if lines else drill.cheatsheet[:80]
            console.print(f"\n[dim]Hint (first line of Cheatsheet):[/dim] {hint[:120]}")
        console.print("\nPress Enter when ready to see the answer...")
        # In CLI: just show a separator; in interactive mode this would wait for input
        console.print("[dim]─" * 60 + "[/dim]")

    console.print("\n[bold]Mental Model[/bold]")
    console.print(drill.mental_model)
    if drill.cheatsheet:
        console.print("\n[bold]Cheatsheet[/bold]")
        console.print(drill.cheatsheet)
    else:
        console.print("\n[yellow]No Cheatsheet yet.[/yellow]")
    console.print(
        "\nRecord: [cyan]--pass[/cyan] | [cyan]--hard[/cyan] | [cyan]--easy[/cyan] | "
        "[cyan]--fail --fail-type recall|concept|procedure|transfer[/cyan]"
    )


@app.command()
def link(
    source: str,
    target: str,
    edge_type: Annotated[
        EdgeType,
        typer.Option("--type", help="Relationship type between nodes."),
    ] = EdgeType.PREREQUISITE,
    rationale: Annotated[
        str | None,
        typer.Option("--rationale", help="Optional reason for this relationship."),
    ] = None,
) -> None:
    """Link two ability nodes."""
    try:
        result = create_link(source, target, edge_type=edge_type, rationale=rationale)
    except DatabaseError as error:
        _handle_database_error(error)
    except LinkError as error:
        _handle_link_error(error)

    console.print(
        f"[green]Linked[/green] {result.source_title} -[{result.edge.edge_type.value}]-> "
        f"{result.target_title}"
    )
    if result.edge.rationale:
        console.print(f"Rationale: {result.edge.rationale}")


@app.command()
def graph(
    domain: Annotated[str, typer.Option("--domain", help="Domain to visualize.")],
) -> None:
    """Show ability relationships within a domain."""
    try:
        domain_graph = build_domain_graph(domain)
    except DatabaseError as error:
        _handle_database_error(error)
    except GraphError as error:
        _handle_graph_error(error)

    for line in format_domain_graph_text(domain_graph):
        console.print(line, markup=False)


@app.command()
def schedule(
    domain: Annotated[
        str | None, typer.Option("--domain", help="Filter to a specific domain.")
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", help="Max nodes to show.")
    ] = 20,
) -> None:
    """List nodes due for review, ordered by urgency (lowest R first)."""
    from sycamore.core.scheduler import (
        DEFAULT_DESIRED_RETENTION,
        SchedulerState,
        current_retrievability,
    )
    from sycamore.storage.config_store import load_config
    from sycamore.storage.database import open_initialized_database
    from sycamore.storage.node_repository import list_all_nodes, list_nodes_by_domain
    from sycamore.utils.paths import get_config_path, get_database_path, get_syca_home
    from sycamore.utils.time import utc_now_iso

    root = get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    now = utc_now_iso()

    try:
        nodes = list_nodes_by_domain(connection, domain) if domain else list_all_nodes(connection)

        config = load_config(get_config_path(root))
        scheduler_cfg = config.get("scheduler", {}) if isinstance(config, dict) else {}
        desired_retention = (
            scheduler_cfg.get("desired_retention")
            if isinstance(scheduler_cfg, dict)
            else None
        )
        if not isinstance(desired_retention, (int, float)):
            desired_retention = DEFAULT_DESIRED_RETENTION

        entries: list[tuple[float, str, str, str, str, str]] = []
        for node in nodes:
            row = connection.execute(
                "SELECT * FROM node_scheduler_state WHERE node_id = ?;",
                (node.id,),
            ).fetchone()
            if row is None:
                continue
            state = SchedulerState(
                node_id=row["node_id"],
                stability=row["stability"],
                difficulty=row["difficulty"],
                due_at=row["due_at"],
                last_review_at=row["last_review_at"],
                last_rating=row["last_rating"],
                review_count=row["review_count"],
                lapse_count=row["lapse_count"],
            )
            R = current_retrievability(state, now)
            entries.append((
                R,
                node.title,
                node.domain or "—",
                node.claimed_level.value,
                state.due_at or "—",
                f"{state.stability:.1f}",
            ))

        entries.sort(key=lambda e: e[0])  # lowest R first
        entries = entries[:limit]

        if not entries:
            console.print("[green]No nodes with scheduler state yet. Run some recovers first.[/green]")
            return

        table = Table(title=f"Schedule (desired retention: {desired_retention:.0%})")
        table.add_column("#", style="dim", no_wrap=True)
        table.add_column("Title")
        table.add_column("Domain")
        table.add_column("Level")
        table.add_column("R", justify="right")
        table.add_column("Due")
        table.add_column("S", justify="right")

        for i, (R, title, dom, lvl, due, S) in enumerate(entries, 1):
            r_style = "[red]" if R < 0.7 else "[yellow]" if R < 0.85 else "[green]"
            table.add_row(
                str(i),
                title,
                dom,
                lvl,
                f"{r_style}{R:.1%}[/{r_style}]",
                due,
                S,
            )

        console.print(table)
    finally:
        connection.close()


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
    from sycamore.utils.env import load_project_env

    load_project_env()
    app()
