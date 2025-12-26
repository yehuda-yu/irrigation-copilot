"""
Agent CLI runner script.

Command-line interface for running the irrigation copilot agent interactively.
Loads .env file and runs agent in a conversational loop.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.agent import build_agent


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
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "\n[ERROR] OPENAI_API_KEY environment variable is required.\n"
            "Create a .env file in the project root with:\n"
            "  OPENAI_API_KEY=your_key_here\n"
            "See .env.example for template.\n"
        )
        sys.exit(1)

    # Print config (never print API key!)
    model = os.environ.get("IRRIGATION_AGENT_MODEL", "gpt-4o-mini")
    print(f"Model: {model}")

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
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break

            # Run agent
            print("\n[Thinking...]\n")
            result = agent(user_input)

            # Get the response message
            if hasattr(result, "message") and result.message:
                content = result.message.get("content", [])
                if content and isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    answer_text = "\n".join(text_parts)
                else:
                    answer_text = str(content)
            else:
                answer_text = str(result)

            # Print answer
            print("Agent:", answer_text)
            print()

            # Try to parse any JSON in the response for structured output
            if "{" in answer_text and "}" in answer_text:
                try:
                    start_idx = answer_text.find("{")
                    end_idx = answer_text.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = answer_text[start_idx:end_idx]
                        result_dict = json.loads(json_str)
                        print("=" * 60)
                        print("Parsed Structured Result:")
                        print("=" * 60)
                        print(json.dumps(result_dict, indent=2, default=str))
                        print()
                except (json.JSONDecodeError, Exception):
                    pass

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}\n")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
