import argparse
import shlex


class CommandArgumentParser(argparse.ArgumentParser):
    """
    argparse.ArgumentParser sub-class for parsing assistant commands.
    - Raises argparse.ArgumentError for all parsing failures instead of exiting the
      process.
    - Adds a --help option to show the help message.
    """

    def __init__(self, command: str, description: str, add_help=True):
        super().__init__(
            prog=command,
            description=description,
            exit_on_error=False,
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        if add_help:
            self.add_argument("-h", "--help", action="help", help="show this help message")

    @property
    def command(self) -> str:
        return self.prog

    def error(self, message):
        self._error_message = message

    def parse_args(self, arg_string: str):
        try:
            sys_args_like = shlex.split(arg_string)
        except ValueError as e:
            raise argparse.ArgumentError(None, f"Invalid command arguments: {e}")

        self._error_message = None
        try:
            result = super().parse_args(args=sys_args_like)
            if self._error_message:
                raise argparse.ArgumentError(None, self._error_message)
            return result

        except argparse.ArgumentError as e:
            message = f"{self.prog}: error: {e}\n\n{self.format_help()}"
            raise argparse.ArgumentError(None, message)

        except SystemExit:
            message = self.format_help()
            if self._error_message:
                message = f"{self.prog}: error: {self._error_message}\n\n{message}"
            raise argparse.ArgumentError(None, message)
