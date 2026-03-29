"""Conversation replay CLI for demo purposes.

Usage:
    python -m src.cli replay <patient_name>
    python -m src.cli replay sarah
    python -m src.cli replay marcus
    python -m src.cli replay elena
"""

from __future__ import annotations

import sys

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.db.seed import get_seed_data

logger = structlog.get_logger(__name__)

console = Console()


def replay_conversation(patient_name: str) -> None:
    """Display a formatted conversation timeline for a patient using seed data."""
    data = get_seed_data()

    # Find the patient profile (case-insensitive)
    profile = None
    for p in data["profiles"]:
        if p["display_name"].lower() == patient_name.lower():
            profile = p
            break

    if not profile:
        console.print(f"[red]Patient '{patient_name}' not found.[/red]")
        console.print(
            "Available patients: " + ", ".join(p["display_name"] for p in data["profiles"])
        )
        sys.exit(1)

    user_id = profile["user_id"]
    display_name = profile["display_name"]

    # Get turns for this patient, sorted by turn_number
    turns = [t for t in data["conversation_turns"] if t["user_id"] == user_id]
    turns.sort(key=lambda t: t["turn_number"])

    # Get goals for this patient
    goals = [g for g in data["goals"] if g["user_id"] == user_id]

    # Get milestones for this patient
    milestones = [m for m in data["milestones"] if m["user_id"] == user_id]

    # Header
    console.print()
    header = Table.grid(padding=(0, 2))
    header.add_column(style="bold cyan")
    header.add_column()
    header.add_row("Patient:", display_name)
    header.add_row("Phase:", profile["phase"])
    header.add_row("Consent:", "Yes" if profile.get("consent_given_at") else "No")
    header.add_row("Goals:", str(len(goals)))
    ms_done = sum(1 for m in milestones if m["completed"])
    header.add_row("Milestones:", f"{ms_done}/{len(milestones)} completed")
    header.add_row("Turns:", str(len(turns)))

    console.print(
        Panel(header, title=f"[bold]{display_name} - Patient Summary[/bold]", border_style="cyan")
    )
    console.print()

    # Conversation timeline
    console.print("[bold underline]Conversation Timeline[/bold underline]\n")

    for turn in turns:
        role = turn["role"]
        content = turn["content"]
        phase = turn["phase"]
        timestamp = turn["created_at"]
        tool_calls = turn.get("tool_calls")

        # Format role label with color
        if role == "user":
            role_style = "bold green"
            role_label = f"{display_name}"
        elif role == "assistant":
            role_style = "bold blue"
            role_label = "Coach"
        else:
            role_style = "bold yellow"
            role_label = role.capitalize()

        # Build the turn display
        meta = Text()
        meta.append(f"[Turn {turn['turn_number']}] ", style="dim")
        meta.append(f"{timestamp[:16]} ", style="dim")
        meta.append(f"({phase})", style="dim italic")

        console.print(meta)

        turn_text = Text()
        turn_text.append(f"  {role_label}: ", style=role_style)
        turn_text.append(content)
        console.print(turn_text)

        if tool_calls:
            tool_name = tool_calls.get("name", "unknown")
            tool_args = tool_calls.get("args", {})
            tool_text = Text()
            tool_text.append(f"  [Tool: {tool_name}]", style="bold magenta")
            if tool_args:
                for k, v in tool_args.items():
                    tool_text.append(f" {k}={v}", style="magenta")
            console.print(tool_text)

        console.print()

    # Safety audit entries
    audit_entries = [a for a in data["safety_audit_log"] if a["user_id"] == user_id]
    if audit_entries:
        console.print("[bold underline]Safety Audit Log[/bold underline]\n")
        for entry in audit_entries:
            action = entry["action_taken"]
            action_style = (
                "green" if action == "passed" else "red" if action == "blocked" else "yellow"
            )
            console.print(
                f"  [{action_style}]{action.upper()}[/{action_style}] "
                f"(tier={entry['tier']}, class={entry['classification']}, "
                f"conf={entry['confidence']:.2f})"
            )
            console.print(f"    Text: {entry['input_text'][:80]}...")
            console.print(f"    Reason: {entry['reasoning']}")
            console.print()

    # Alerts
    alerts = [a for a in data["clinician_alerts"] if a["user_id"] == user_id]
    if alerts:
        console.print("[bold underline]Clinician Alerts[/bold underline]\n")
        for alert in alerts:
            urgency_style = "red" if alert["urgency"] == "urgent" else "yellow"
            console.print(
                f"  [{urgency_style}]{alert['urgency'].upper()}[/{urgency_style}] "
                f"type={alert['alert_type']} status={alert['status']}"
            )
            console.print(f"    {alert['message']}")
            console.print()

    # Reminders
    reminders = [r for r in data["reminders"] if r["user_id"] == user_id]
    if reminders:
        console.print("[bold underline]Reminders[/bold underline]\n")
        for reminder in reminders:
            status_style = "green" if reminder["status"] == "sent" else "yellow"
            console.print(
                f"  [{status_style}]{reminder['status'].upper()}[/{status_style}] "
                f"attempt #{reminder['attempt_number']} — "
                f"{reminder['message_template']}"
            )
            if reminder["sent_at"]:
                console.print(f"    Sent at: {reminder['sent_at']}")
            else:
                console.print(f"    Due at: {reminder['due_at']}")
            console.print()


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 3:
        console.print("[bold]AI Health Coach — Conversation Replay CLI[/bold]\n")
        console.print("Usage: python -m src.cli replay <patient_name>\n")
        console.print("Available commands:")
        console.print("  replay <name>  Show formatted conversation timeline")
        console.print("\nAvailable patients:")
        for p in get_seed_data()["profiles"]:
            console.print(f"  - {p['display_name']} ({p['phase']})")
        sys.exit(0)

    command = sys.argv[1]
    if command == "replay":
        patient_name = sys.argv[2]
        replay_conversation(patient_name)
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
