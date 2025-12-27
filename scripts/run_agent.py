"""
Agent CLI runner script.

Command-line interface for running the irrigation copilot agent interactively.
Loads .env file and runs agent in a conversational loop.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.agent import build_agent
from app.agents.schemas import IrrigationAgentResult


def main():
    """Run agent CLI interactively."""
    # Load .env file (only if it exists, no error if missing)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
    else:
        print("No .env file found. Using environment variables only.")

    # Check for API key (don't print it!)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "\n[ERROR] GOOGLE_API_KEY environment variable is required.\n"
            "Create a .env file in the project root with:\n"
            "  GOOGLE_API_KEY=your_key_here\n"
            "See .env.example for template.\n"
        )
        sys.exit(1)

    # Print config (never print API key!)
    model_id = os.environ.get("IRRIGATION_AGENT_MODEL", "gemini-2.5-flash")
    print(f"Model: {model_id}")

    # Build agent
    try:
        print("Building agent...")
        agent = build_agent()
        print("[OK] Agent ready!\n")
    except Exception as e:
        print(f"\n[ERROR] Failed to build agent: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Interactive loop
    print("=" * 60)
    print("Irrigation Copilot Agent")
    print("=" * 60)
    print("Type your question (or 'quit'/'exit' to stop)\n")
    print("Example: I have a 5 dunam tomato farm at lat 32.0, lon 34.8.")
    print("         What irrigation do I need today?\n")

    while True:
        try:
            # Read user input
            try:
                user_input = input("You: ").strip()
            except EOFError:
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break

            # Run agent with structured output
            print("\n[Thinking...]\n")
            result = agent.structured_output(IrrigationAgentResult, user_input)

            # Print answer (human text)
            print("Agent Answer:")
            print("-" * 20)
            print(result.answer_text)
            print("-" * 20)
            print()

            # Print structured JSON
            print("Structured Result (JSON):")
            print(result.model_dump_json(indent=2))
            print()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}\n")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
