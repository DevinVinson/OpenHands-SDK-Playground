"""CLI entry point for OpenHands Lab."""

import argparse
import sys
from pathlib import Path

from lab.core import ConfigLoader, SessionManager


def cmd_run(args: argparse.Namespace) -> int:
    """Run an agent with a specific agent config and task."""
    manager = SessionManager(config_dir=args.config_dir)

    # Show available agents if none specified
    if not args.agent:
        print("Available agents:")
        for name, agent in manager.agents.items():
            print(f"  - {name}: {agent.description}")
        return 0

    try:
        session = manager.create_session(
            agent_name=args.agent,
            workspace_dir=args.workspace,
        )
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Starting session '{session.session_id}' with agent '{args.agent}'")
    print(f"Workspace: {session.workspace_dir}")
    print("-" * 50)

    if args.task:
        session.send_message(args.task)
        session.run()

        trace_path = session.save_trace()
        print("-" * 50)
        print(f"Session trace saved to: {trace_path}")
    else:
        print("No task provided. Use --task to specify a task.")
        return 1

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available agents."""
    config = ConfigLoader(config_dir=args.config_dir)

    if not config.agents:
        print("No agents configured. Create config/agents.yaml")
        return 0

    print("Available agents:")
    print("-" * 50)
    for name, agent in config.agents.items():
        print(f"\n[{name}]")
        if agent.description:
            print(f"  Description: {agent.description}")
        if agent.model:
            print(f"  Model: {agent.model}")
        if agent.tools:
            tools_str = ", ".join(t.name for t in agent.tools if t.enabled)
            print(f"  Tools: {tools_str}")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Show current configuration."""
    config = ConfigLoader(config_dir=args.config_dir)
    settings = config.settings

    print("Current Configuration:")
    print("-" * 50)
    print(f"\n[LLM]")
    print(f"  Model: {settings.llm.model}")
    print(f"  API Key Env: {settings.llm.api_key_env}")
    if settings.llm.base_url:
        print(f"  Base URL: {settings.llm.base_url}")

    print(f"\n[Runtime]")
    print(f"  Environment: {settings.runtime.environment}")
    print(f"  Working Dir: {settings.runtime.working_dir}")
    if settings.runtime.docker_image:
        print(f"  Docker Image: {settings.runtime.docker_image}")

    print(f"\n[Session]")
    print(f"  Log Dir: {settings.session_log_dir}")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="lab",
        description="OpenHands Lab - Local-first agent orchestration",
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory (default: config)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run an agent session")
    run_parser.add_argument(
        "--agent",
        "-a",
        help="Agent name from agents.yaml",
    )
    run_parser.add_argument(
        "--task",
        "-t",
        help="Task to execute",
    )
    run_parser.add_argument(
        "--workspace",
        "-w",
        default=".",
        help="Workspace directory (default: current directory)",
    )

    # List command
    subparsers.add_parser("list", help="List available agents")

    # Config command
    subparsers.add_parser("config", help="Show current configuration")

    args = parser.parse_args()

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
