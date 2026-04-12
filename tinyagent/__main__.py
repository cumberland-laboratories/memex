"""CLI entry point: python -m tinyagent "your task" """

import argparse
import os
import sys
from dotenv import load_dotenv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tinyagent",
        description="Minimal Claude-API coding assistant (design artifact)",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Start a new task")
    run_p.add_argument("task", help="Natural-language task description")
    run_p.add_argument("--max-iterations", type=int, default=20)
    run_p.add_argument("--model", default="claude-sonnet-4-20250514")

    resume_p = sub.add_parser("resume", help="Resume a saved session")
    resume_p.add_argument("session_id", help="Session ID to resume")
    resume_p.add_argument("--max-iterations", type=int, default=20)
    resume_p.add_argument("--model", default="claude-sonnet-4-20250514")

    return parser


def main() -> None:
    load_dotenv()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        # Bare invocation: treat first positional arg as "run"
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            args.command = "run"
            args.task = sys.argv[1]
            args.max_iterations = 20
            args.model = "claude-sonnet-4-20250514"
        else:
            parser.print_help()
            sys.exit(1)

    from tinyagent.client import Client
    from tinyagent.agent import Agent
    from tinyagent.session import Session
    from tinyagent.context import ContextManager

    client = Client(api_key=api_key, model=args.model)
    context = ContextManager(model=args.model)

    if args.command == "run":
        session = Session.new()
        agent = Agent(client=client, context=context,
                      session=session, max_iterations=args.max_iterations)
        agent.run(args.task)
    elif args.command == "resume":
        session = Session.load(args.session_id)
        agent = Agent(client=client, context=context,
                      session=session, max_iterations=args.max_iterations)
        agent.resume()


if __name__ == "__main__":
    main()
