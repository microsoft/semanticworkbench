#!/usr/bin/env python3
"""
run-routine - Command-line utility to execute routines from the skill_library

Usage:
  run-routine ROUTINE_NAME [OPTIONS]
  run-routine --list
  run-routine --usage
  cat input.txt | run-routine ROUTINE_NAME [OPTIONS]

Arguments:
  ROUTINE_NAME    Name of the routine to run (e.g., "research2.research")

Options:
  --home PATH           Path to skills home directory (default: .skills in current or home dir)
  --engine ID           Engine ID to use (default: "cli")
  --param KEY=VALUE     Parameter to pass to the routine (can be used multiple times)
  --timeout SECONDS     Maximum seconds to allow the routine to run (default: 600)
  --non-interactive     Run in non-interactive mode, fail if user input is needed
  --list                List all available routines
  --usage               Show detailed usage information for all routines
  --quiet               Suppress log output to stderr in interactive mode

Environment Variables:
  SKILLS_HOME_DIR       Override skills home directory path
  SKILLS_ENGINE_ID      Override engine ID

Examples:
  # Run a research routine with a specific topic
  run-routine research2.research --param plan_name="AI-trends" --param topic="Latest AI trends"

  # Pipe content as input
  echo "What is quantum computing?" | run-routine research2.research

  # List all available routines
  run-routine --list

  # See detailed usage for all routines
  run-routine --usage

  # Run with a 5-minute timeout
  run-routine research2.research --param plan_name="climate" --param topic="Climate change" --timeout 300

  # Run in non-interactive mode (will fail if user input is needed)
  run-routine research2.research --param plan_name="ai-ethics" --param topic="AI ethics" --non-interactive
"""

import asyncio
import datetime
import importlib
import json
import os
import sys
import time
import traceback
import uuid
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from skill_library.skills.meta.meta_skill import MetaSkill, MetaSkillConfig

# Import skill library dependencies
try:
    from assistant_drive import Drive, DriveConfig
    from events import events as skill_events
    from semantic_workbench_api_model.workbench_model import (
        ParticipantRole,
    )
    from skill_library import Engine
    from skill_library.cli.azure_openai import create_azure_openai_client
    from skill_library.cli.conversation_history import ConversationHistory
    from skill_library.cli.settings import Settings
    from skill_library.cli.skill_logger import SkillLogger

    # Import skill implementations
    from skill_library.skills.common import CommonSkill, CommonSkillConfig
    from skill_library.skills.posix import PosixSkill, PosixSkillConfig
    from skill_library.skills.research import ResearchSkill, ResearchSkillConfig
    from skill_library.skills.web_research import WebResearchSkill, WebResearchSkillConfig
except ImportError as e:
    print(f"Error: Required dependency not found - {e}", file=sys.stderr)
    print("Please ensure skill_library and its dependencies are installed.", file=sys.stderr)
    sys.exit(1)


class RoutineRunner:
    """Manages the execution of skill routines."""

    def __init__(
        self,
        routine_name: str,
        params: Dict[str, Any],
        input_text: Optional[str],
        skills_home_dir: Path,
        engine_id: str,
        history: ConversationHistory,
        logger: SkillLogger,
    ):
        self.routine_name = routine_name
        self.params = params.copy()
        self.input_text = input_text
        self.skills_home_dir = skills_home_dir
        self.engine_id = engine_id
        self.history = history
        self.logger = logger

        # Extract special parameters
        self.non_interactive = self.params.pop("__non_interactive", False)
        self.timeout_seconds = self.params.pop("__timeout", 600)

        # Handle input text
        if self.input_text:
            try:
                if self.input_text:
                    input_json = json.loads(self.input_text)
                    if isinstance(input_json, dict):
                        self.params.update(input_json)
                    elif isinstance(input_json, list):
                        self.params["input_list"] = input_json
            except json.JSONDecodeError:
                self.params["input_text"] = self.input_text

            # Record input text as user message
            self.history.add_message(self.input_text, ParticipantRole.user)

        # Runtime state
        self.engine = None
        self.user_interaction_queue = asyncio.Queue()
        self.user_interaction_active = asyncio.Event()
        self.start_time = 0

    def initialize_engine(self) -> Optional[Engine]:
        """Initialize the engine with configured skills."""
        # Create settings from the skills home directory
        settings = Settings(self.skills_home_dir, self.logger)

        # Ensure data folder exists
        data_folder = settings.data_folder
        data_folder.mkdir(parents=True, exist_ok=True)

        drive = Drive(DriveConfig(root=data_folder))

        try:
            language_model = create_azure_openai_client(
                settings.azure_openai_endpoint, settings.azure_openai_deployment
            )
            reasoning_language_model = create_azure_openai_client(
                settings.azure_openai_endpoint, settings.azure_openai_reasoning_deployment
            )
            self.logger.info("Created Azure OpenAI client")
        except Exception as e:
            self.logger.error(f"Failed to create Azure OpenAI client: {e}")
            return None

        drive_root = data_folder / self.engine_id / "drive"
        metadata_drive_root = data_folder / self.engine_id / "metadata"

        drive_root.mkdir(parents=True, exist_ok=True)
        metadata_drive_root.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Initializing engine with ID: {self.engine_id}")
        self.logger.debug(f"Drive root: {drive_root}", {"drive_root": str(drive_root)})

        try:
            engine = Engine(
                engine_id=self.engine_id,
                message_history_provider=self.history.get_message_list,
                drive_root=drive_root,
                metadata_drive_root=metadata_drive_root,
                skills=[
                    (
                        MetaSkill,
                        MetaSkillConfig(
                            name="meta",
                            drive=drive.subdrive("meta"),
                            language_model=language_model,
                        ),
                    ),
                    (
                        CommonSkill,
                        CommonSkillConfig(
                            name="common",
                            language_model=language_model,
                            drive=drive.subdrive("common"),
                            bing_subscription_key=settings.bing_subscription_key,
                            bing_search_url=settings.bing_search_url,
                        ),
                    ),
                    (
                        PosixSkill,
                        PosixSkillConfig(
                            name="posix",
                            sandbox_dir=data_folder / self.engine_id,
                            mount_dir="/mnt/data",
                        ),
                    ),
                    (
                        ResearchSkill,
                        ResearchSkillConfig(
                            name="research",
                            language_model=language_model,
                            drive=drive.subdrive("research"),
                        ),
                    ),
                    (
                        WebResearchSkill,
                        WebResearchSkillConfig(
                            name="web_research",
                            language_model=language_model,
                            reasoning_language_model=reasoning_language_model,
                            drive=drive.subdrive("web_research"),
                        ),
                    ),
                    # Additional skills would be loaded based on config
                ],
            )
            self.logger.info("Engine initialized successfully with 4 skills")
            return engine
        except Exception as e:
            self.logger.error(f"Failed to initialize engine: {e}")
            return None

    async def monitor_events(self):
        """Monitor and process engine events."""
        if not self.engine:
            self.logger.error("Engine not initialized before monitoring events")
            return

        try:
            self.logger.info("Starting event monitoring")

            async for event in self.engine.events:
                event_type = type(event).__name__.replace("Event", "")
                event_meta: dict[str, Any] = {"event_type": event_type}
                if event.message:
                    # Check if this is a message event (ask_user prompt)
                    if isinstance(event, skill_events.MessageEvent):
                        # Put the message in the queue for handling
                        await self.user_interaction_queue.put(event.message)
                        # Record the message in conversation history
                        self.history.add_message(event.message, ParticipantRole.assistant)
                        self.user_interaction_active.set()

                        # Log the event for user interaction
                        if event.metadata:
                            event_meta.update({"event_metadata": event.metadata})
                        self.logger.info(f"User interaction requested: {event.message}", event_meta)
                    elif isinstance(event, skill_events.StatusUpdatedEvent):
                        # Log status updates
                        self.logger.info(f"Status updated: {event.message}", {"event_metadata": event.metadata})
                    else:
                        # Log other events at debug level
                        if event.metadata:
                            event_meta.update({"event_metadata": event.metadata})
                        self.logger.debug(f"{event_type}: {event.message}", event_meta)
        except Exception as e:
            self.logger.error(f"Error monitoring events: {e}")

    async def handle_user_interactions(self):
        """Handle interactive user prompts during routine execution."""
        if not self.engine:
            self.logger.error("Engine not initialized before handling user interactions")
            return

        try:
            self.logger.info("Starting user interaction handler")
            while True:
                # Wait for a prompt from ask_user
                prompt = await self.user_interaction_queue.get()

                if self.non_interactive:
                    # In non-interactive mode, fail the routine
                    self.logger.error("Routine requires user input but --non-interactive was specified")
                    response = "ERROR: Non-interactive mode enabled but user input was requested"

                    # Check if engine is initialized before calling resume_routine
                    if self.engine:
                        await self.engine.resume_routine(response)
                    else:
                        self.logger.error("Cannot resume routine - engine not initialized")

                    # Record the error response
                    self.history.add_message(response, ParticipantRole.user)
                    self.user_interaction_queue.task_done()
                    self.user_interaction_active.clear()
                    continue

                # Prompt the user for input via stderr - this bypasses quiet mode
                self.logger.prompt_user(prompt)

                while True:
                    # Read from stdin in a way that doesn't block the event loop
                    response = await asyncio.to_thread(sys.stdin.readline)
                    response = response.strip()

                    # Check for special commands
                    if response.lower() == ":q":
                        self.logger.info("User requested to quit")
                        raise KeyboardInterrupt("User requested to quit")
                    elif response.lower() == ":h":
                        self._show_help()
                        continue
                    elif response.lower() == ":s":
                        self._show_status()
                        continue
                    elif response.lower() == ":history":
                        self.history.display_history()
                        print("Enter your response: ", file=sys.stderr, end="", flush=True)
                        continue

                    # Got a valid response
                    break

                # Record the user's response in conversation history
                self.history.add_message(response, ParticipantRole.user)
                self.logger.debug(f"User provided response: {response[:50]}...")

                # Resume the routine with the user's input
                if self.engine:
                    await self.engine.resume_routine(response)
                else:
                    self.logger.error("Cannot resume routine - engine not initialized")

                # Mark this task as done
                self.user_interaction_queue.task_done()
                self.user_interaction_active.clear()
        except KeyboardInterrupt:
            # Propagate the interrupt
            raise
        except asyncio.CancelledError:
            # Task was cancelled, clean exit
            self.logger.debug("User interaction handler cancelled")
            pass
        except Exception as e:
            self.logger.error(f"Error handling user interaction: {e}")

    def _show_help(self):
        """Display help for interactive commands."""
        self.logger.info("\nHelp:")
        self.logger.info("  :q - Quit the routine")
        self.logger.info("  :h - Show this help message")
        self.logger.info("  :s - Show current routine status")
        self.logger.info("  :history - Show conversation history")
        print("Enter your response: ", file=sys.stderr, end="", flush=True)

    def _show_status(self):
        """Display current routine status."""
        elapsed = int(time.time() - self.start_time)
        self.logger.info("\nCurrent routine status:")
        self.logger.info(f"  Routine: {self.routine_name}")
        self.logger.info(f"  Parameters: {json.dumps(self.params, indent=2)}")
        self.logger.info(f"  Elapsed time: {elapsed} seconds")
        self.logger.info(f"  Timeout: {self.timeout_seconds} seconds")
        print("Enter your response: ", file=sys.stderr, end="", flush=True)

    async def run(self) -> str:
        """Run the routine with monitoring and user interaction handling."""
        self.logger.info(f"Starting routine: {self.routine_name}")

        # Initialize engine
        self.engine = self.initialize_engine()
        if not self.engine:
            self.logger.error("Failed to initialize engine")
            return "ERROR: Failed to initialize engine"

        # Verify the routine exists
        try:
            available_routines = self.engine.list_routines()
            if self.routine_name not in available_routines:
                self.logger.error(f"Routine '{self.routine_name}' not found")
                available = "\n  ".join(sorted(available_routines))
                return f"ERROR: Routine '{self.routine_name}' not found. Available routines:\n  {available}"
        except AttributeError:
            self.logger.error("Engine does not support listing routines")
            return "ERROR: Engine does not support listing routines"

        # Start monitoring tasks
        monitor_task = asyncio.create_task(self.monitor_events())
        interaction_task = asyncio.create_task(self.handle_user_interactions())

        # Track start time for timeout reporting
        self.start_time = time.time()

        try:
            # Run the routine with timeout
            self.logger.info(f"Running {self.routine_name} with params: {self.params}")
            try:
                result = await asyncio.wait_for(
                    self.engine.run_routine(self.routine_name, **self.params), timeout=self.timeout_seconds
                )
                elapsed = int(time.time() - self.start_time)
                self.logger.info(f"Routine completed successfully in {elapsed} seconds.")

                # Record the final result in conversation history
                self.history.add_message(str(result), ParticipantRole.assistant)

                return result
            except asyncio.TimeoutError:
                elapsed = int(time.time() - self.start_time)
                error_msg = f"Routine timed out after {elapsed} seconds (limit: {self.timeout_seconds}s)"
                self.logger.error(error_msg)

                # Record the timeout error in conversation history
                self.history.add_message(f"ERROR: {error_msg}", ParticipantRole.service)

                return f"ERROR: Routine execution timed out after {self.timeout_seconds} seconds"

        except KeyboardInterrupt:
            error_msg = "Operation cancelled by user"
            self.logger.warning(error_msg)

            # Record the cancellation in conversation history
            self.history.add_message(f"ERROR: {error_msg}", ParticipantRole.service)

            return f"ERROR: {error_msg}"
        except Exception as e:
            error_msg = f"Failed to run routine: {str(e)}"
            self.logger.error(error_msg, {"exception": traceback.format_exc()})

            # Record the error in conversation history
            self.history.add_message(f"ERROR: {error_msg}", ParticipantRole.service)

            return f"ERROR: {error_msg}"
        finally:
            # Clean up the tasks
            for task in [monitor_task, interaction_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=2.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass

            # If we're in the middle of a user interaction, print a message
            if self.user_interaction_active.is_set():
                self.logger.warning("Routine execution ended while waiting for user input.")

            # Finalize logging
            self.logger.finalize()


def find_skills_home_dir() -> Path:
    """Find the skills home directory based on environment or defaults."""
    # Check environment variable first
    if env_home_dir := os.environ.get("SKILLS_HOME_DIR"):
        return Path(env_home_dir)

    # Check current directory
    cwd_skills_home = Path.cwd() / ".skills"
    if cwd_skills_home.exists() and cwd_skills_home.is_dir():
        return cwd_skills_home

    # Fall back to home directory
    home_skills_dir = Path.home() / ".skills"
    # Create directory if it doesn't exist
    home_skills_dir.mkdir(parents=True, exist_ok=True)

    # Ensure config and data subdirectories exist
    (home_skills_dir / "config").mkdir(exist_ok=True)
    (home_skills_dir / "data").mkdir(exist_ok=True)

    return home_skills_dir


def parse_args() -> Tuple[str, Dict[str, Any], Path, str, bool, bool]:
    """Parse command line arguments."""
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)

    # Allow routine name to be optional when using --list or --usage
    parser.add_argument(
        "routine_name", nargs="?", default="", help="Name of the routine to run (e.g., 'research2.research')"
    )

    parser.add_argument("--list", action="store_true", help="List all available routines")

    parser.add_argument("--usage", action="store_true", help="Show detailed usage information for all routines")

    parser.add_argument(
        "--home", help="Path to skills home directory (default: .skills in current or home dir)", type=Path
    )

    parser.add_argument(
        "--engine", help="Engine ID to use (default: 'cli')", default=os.environ.get("SKILLS_ENGINE_ID", "cli")
    )

    parser.add_argument(
        "--param", action="append", help="Parameter in KEY=VALUE format (can be used multiple times)", default=[]
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode. The routine will fail if it needs user input.",
    )

    parser.add_argument(
        "--timeout", type=int, default=600, help="Timeout in seconds for the routine execution (default: 600)"
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress log output to stderr in interactive mode")

    args = parser.parse_args()

    # Process skills home directory
    skills_home_dir = args.home if args.home else find_skills_home_dir()

    # We have special commands like --list and --usage
    if args.list:
        return "__list__", {}, skills_home_dir, args.engine, args.non_interactive, args.quiet

    if args.usage:
        return "__usage__", {}, skills_home_dir, args.engine, args.non_interactive, args.quiet

    # No routine specified and no special command
    if not args.routine_name:
        parser.print_help()
        sys.exit(1)

    # Process parameters
    params = {}
    for param in args.param:
        try:
            key, value = param.split("=", 1)
            # Try to parse as JSON for complex types
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass  # Keep as string if not valid JSON
            params[key] = value
        except ValueError:
            print(f"Warning: Ignoring invalid parameter format: {param}", file=sys.stderr)

    # Store non-interactive mode and timeout in params so they can be accessed by run-routine
    params["__non_interactive"] = args.non_interactive
    params["__timeout"] = args.timeout

    return args.routine_name, params, skills_home_dir, args.engine, args.non_interactive, args.quiet


def setup_console_input():
    """
    Configure input handling for interactive use even when stdin is redirected.
    Returns the original stdin if modified.
    """
    # If stdin is already a TTY, no need to change anything
    if sys.stdin.isatty():
        return None

    # Save the original stdin for later restoration
    original_stdin = sys.stdin

    # Try to open a direct connection to the terminal
    try:
        # This works on Unix-like systems
        tty_stdin = open("/dev/tty", "r")
        sys.stdin = tty_stdin
        return original_stdin
    except Exception:
        # For Windows, we need a different approach
        if os.name == "nt":
            try:
                # Try to use msvcrt for Windows
                if importlib.util.find_spec("msvcrt"):
                    # We can't actually replace stdin on Windows easily,
                    # but we'll set a flag to use a custom input method
                    print("Warning: Using Windows console input handling", file=sys.stderr)
                    return original_stdin
            except ImportError:
                pass


async def main() -> None:
    """Main entry point for the command."""
    # Parse arguments
    routine_name, params, skills_home_dir, engine_id, non_interactive, quiet = parse_args()

    # Generate run ID
    timestamp: str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"

    # Create the logger
    logger = SkillLogger(skills_home_dir=skills_home_dir, run_id=run_id, interactive=not non_interactive, quiet=quiet)

    # Log startup information
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Skills home directory: {skills_home_dir}")

    # Create history object for all paths
    history = ConversationHistory(logger)

    # Check if there's input on stdin
    input_text = None
    # Read from the original stdin for the initial input if stdin was redirected
    if "original_stdin" in globals() and globals()["original_stdin"] is not None:
        input_text = globals()["original_stdin"].read().strip()
    elif not sys.stdin.isatty():
        # This case should generally not happen since we handle stdin redirection
        # in the __main__ block, but just in case
        input_text = sys.stdin.read().strip()

    # Create a runner for initializing the engine
    runner = RoutineRunner(
        routine_name=routine_name,
        params=params,
        input_text=input_text,
        skills_home_dir=skills_home_dir,
        engine_id=engine_id,
        history=history,
        logger=logger,
    )

    engine = runner.initialize_engine()
    if not engine:
        logger.error("Failed to initialize engine")
        return

    # Special commands
    if routine_name == "__list__":
        try:
            logger.info("Listing available routines")
            available_routines = sorted(engine.list_routines())
            if available_routines:
                print("Available routines:")
                for routine in available_routines:
                    print(f"  {routine}")
            else:
                print("No routines available.")
        except AttributeError:
            logger.error("Engine does not support listing routines")
            print("ERROR: Engine does not support listing routines", file=sys.stderr)
        finally:
            logger.finalize()
        return

    if routine_name == "__usage__":
        try:
            logger.info("Retrieving routine usage information")
            usage_text = engine.routines_usage()
            if usage_text:
                print(usage_text)
            else:
                print("No routine usage information available.")
        except AttributeError:
            logger.error("Engine does not support retrieving routine usage")
            print("ERROR: Engine does not support retrieving routine usage", file=sys.stderr)
        finally:
            logger.finalize()
        return

    # Announce the start of execution
    logger.info(f"Executing routine: {routine_name}")
    if input_text:
        input_preview = input_text[:100] + "..." if len(input_text) > 100 else input_text
        logger.info(f"Input text: {input_preview}")

    # Run the routine
    result = await runner.run()

    # Output result to stdout
    print(result)


def entry_point():
    """Entry point for the command-line interface when installed as a package."""

    # Need to import for dynamic import checking on Windows
    import importlib.util  # noqa: F401

    # Save the program start time
    program_start_time = time.time()

    # Set up console input handling
    original_stdin = None

    try:
        # Configure input handling for interactive use
        original_stdin = setup_console_input()

        # Make the original stdin available to the main function
        if original_stdin:
            globals()["original_stdin"] = original_stdin

        # Run the main async function
        asyncio.run(main())

        # Show execution time
        execution_time = time.time() - program_start_time
        print(f"Total execution time: {execution_time:.2f} seconds", file=sys.stderr)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        # Print traceback for debugging
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        # Restore original stdin if we modified it
        if original_stdin:
            try:
                original_stdin.close()
            except Exception:
                pass
            sys.stdin = original_stdin


if __name__ == "__main__":
    # Need to import for dynamic import checking on Windows
    import importlib.util

    # Save the program start time
    program_start_time = time.time()

    # Set up console input handling
    original_stdin = None

    try:
        # Configure input handling for interactive use
        original_stdin = setup_console_input()

        # Make the original stdin available to the main function
        if original_stdin:
            globals()["original_stdin"] = original_stdin

        # Run the main async function
        asyncio.run(main())

        # Show execution time
        execution_time = time.time() - program_start_time
        print(f"Total execution time: {execution_time:.2f} seconds", file=sys.stderr)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        # Print traceback for debugging
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        # Restore original stdin if we modified it
        if original_stdin:
            try:
                original_stdin.close()
            except Exception:
                pass
            sys.stdin = original_stdin
