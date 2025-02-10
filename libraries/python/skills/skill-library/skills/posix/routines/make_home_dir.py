from skill_library.engine import AskUserFn, PrintFn, RunContext


async def main(run_context: RunContext, ask_user: AskUserFn, print: PrintFn, username: str) -> None:
    posix = run_context.posix

    await posix.cd("/mnt/data")
    await posix.mkdir("{{username}}")
    await posix.cd("{{username}}")
    await posix.mkdir("Documents")
    await posix.mkdir("Downloads")
    await posix.mkdir("Music")
    await posix.mkdir("Pictures")
    await posix.mkdir("Videos")
    await posix.cd("/mnt/data")

    print(f"Home directory created for {username}.")
