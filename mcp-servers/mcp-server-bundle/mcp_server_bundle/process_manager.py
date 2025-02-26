"""
Process Manager for MCP Server Bundle.

This module provides functionality for managing child processes,
handling signals, and ensuring graceful shutdown.
"""

import signal
import subprocess
import sys
import threading
import time
from typing import Any


class ProcessManager:
    """
    Manages child processes for the MCP Server Bundle.

    Handles starting, monitoring, and gracefully shutting down processes.
    """

    def __init__(self):
        """Initialize the ProcessManager."""
        self.processes: dict[str, subprocess.Popen] = {}
        self.should_terminate = threading.Event()

    def start_process(self, name: str, command: list[str], env: dict[str, str] | None = None) -> bool:
        """
        Start a child process with the given name and command.

        Args:
            name: A unique name for the process.
            command: The command to run as a list of strings.
            env: Optional environment variables for the process.

        Returns:
            True if the process was started successfully, False otherwise.
        """
        if name in self.processes:
            print(f"Process {name} is already running")
            return False

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env=env,
            )

            self.processes[name] = process

            # Start threads to monitor stdout and stderr
            # These are daemon threads, so they'll terminate automatically when the program exits
            stdout_thread = threading.Thread(
                target=self._output_reader, args=(name, process.stdout, "stdout"), daemon=True
            )
            stderr_thread = threading.Thread(
                target=self._output_reader, args=(name, process.stderr, "stderr"), daemon=True
            )

            stdout_thread.start()
            stderr_thread.start()

            print(f"Started process {name} (PID: {process.pid})")
            return True

        except Exception as e:
            print(f"Error starting process {name}: {str(e)}")
            return False

    def _output_reader(self, process_name: str, stream: Any, stream_name: str):
        """
        Thread function to read output from a process stream and print it.

        Args:
            process_name: The name of the process.
            stream: The stream to read from (stdout or stderr).
            stream_name: The name of the stream ("stdout" or "stderr").
        """
        prefix = f"[{process_name}:{stream_name}] "

        while not self.should_terminate.is_set():
            line = stream.readline()
            if not line:
                break

            line_text = line.rstrip()
            print(f"{prefix}{line_text}")

        # Make sure we read any remaining output after termination signal
        remaining_lines = list(stream)
        for line in remaining_lines:
            line_text = line.rstrip()
            print(f"{prefix}{line_text}")

    def terminate_processes(self) -> None:
        """
        Terminate all running processes gracefully.

        First sends SIGTERM to all processes, then waits for them to terminate.
        If they don't terminate within the timeout, sends SIGKILL.
        """
        if not self.processes:
            return

        print("\nShutting down all processes...")
        self.should_terminate.set()

        # First send SIGTERM to all processes
        for name, process in self.processes.items():
            print(f"Terminating {name} (PID: {process.pid})...")
            try:
                process.terminate()
            except Exception as e:
                print(f"Error terminating {name}: {str(e)}")

        # Wait for processes to terminate gracefully
        for _ in range(5):  # Wait up to 5 seconds
            if all(process.poll() is not None for process in self.processes.values()):
                break
            time.sleep(1)

        # Force kill any remaining processes
        for name, process in list(self.processes.items()):
            if process.poll() is None:
                print(f"Force killing {name} (PID: {process.pid})...")
                try:
                    process.kill()
                    process.wait()
                except Exception as e:
                    print(f"Error killing {name}: {str(e)}")

        self.processes.clear()
        print("All processes shut down.")

    def signal_handler(self, sig, frame) -> None:
        """
        Handle Ctrl+C and other termination signals.

        Args:
            sig: The signal number.
            frame: The current stack frame.
        """
        print(f"\nReceived signal {sig}. Shutting down...")
        self.terminate_processes()
        sys.exit(0)

    def monitor(self) -> None:
        """
        Monitor all processes.

        This method runs in a loop until should_terminate is set.
        It checks if any process has terminated.
        """
        while not self.should_terminate.is_set():
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"Process {name} terminated unexpectedly with code {process.returncode}")

            time.sleep(1)

    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
