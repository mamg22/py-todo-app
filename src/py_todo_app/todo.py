import argparse
from collections.abc import Callable
import cmd
from functools import partial
from pathlib import Path
import sys
import typing

import psycopg

from . import core


RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

eprint = partial(print, file=sys.stderr)


def setup_cmdline() -> argparse.ArgumentParser:
    progname = Path(sys.argv[0]).stem
    parser = argparse.ArgumentParser(progname)
    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument("-l", "--list", action="store_true")
    mode.add_argument("-a", "--add", metavar="TEXT", nargs="+")
    mode.add_argument("-d", "--done", metavar="ID")
    mode.add_argument("-u", "--undo", metavar="ID")
    mode.add_argument("-r", "--remove", metavar="ID")
    mode.add_argument("-R", "--remove-done", action="store_true")
    mode.add_argument("-i", "--interactive", action="store_true")

    return parser


class InteractiveMode(cmd.Cmd):
    intro = "py-todo interactive mode, type help or ? to list commands"
    prompt = f"{CYAN}todo>{RESET} "

    def __init__(
        self,
        todos: core.TodoModel,
        completekey: str = "tab",
        stdin: typing.TextIO | None = None,
        stdout: typing.TextIO | None = None,
        stderr: typing.TextIO | None = None,
    ) -> None:
        super().__init__(completekey, stdin, stdout)

        self.todos = todos
        if stderr is not None:
            self.stderr = stderr
        else:
            self.stderr = sys.stderr

    def cmdloop(self, intro=None) -> None:
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            print()
            return

    def list_todos(self) -> None:
        for id, _row_num, text, done in self.todos.get_all():
            mark = "✓" if done else "✗"
            if sys.stdout.isatty():
                color = BOLD + (GREEN if done else RED)
                mark = color + mark + RESET
            print(f"{mark} #{id:<4} {text}")

    def do_list(self, _args: str) -> None:
        "List all todo items: `list`"
        self.list_todos()

    def do_add(self, args: str) -> None:
        "Add a todo item: `add TEXT...`"
        todo_id = self.todos.add(args)
        print(f"Saved into todo item id #{todo_id}")

    @staticmethod
    def make_state_handler(
        state: bool, name: str, doc: str = ""
    ) -> Callable[["InteractiveMode", str], None]:
        def state_handler(self: "InteractiveMode", args: str):
            try:
                todo_id = int(args)
            except ValueError:
                print(f"Invalid id '{args}'")
            else:
                self.todos.set_status(todo_id, state)

        state_handler.__name__ = name
        state_handler.__doc__ = doc

        return state_handler

    do_done = make_state_handler(True, "do_done", "Mark an item as done: `done ID`")
    do_undo = make_state_handler(
        False, "do_undo", "Mark an item as not done: `undo ID`"
    )

    def do_remove(self, args: str) -> None:
        "Remove a todo item by ID: `remove ID`. Use 'remove done' to remove all done items."
        if args == "done":
            total = self.todos.remove_done()
            print(f"Removed {total} todo items")
        else:
            try:
                todo_id = int(args)
            except ValueError:
                print(f"Invalid id '{args}'")
            else:
                if not self.todos.remove(todo_id):
                    print(f"Item #{todo_id} not found")

    def do_exit(self, _args: str) -> bool:
        "Exit out of the application"
        return True

    @staticmethod
    def alias(
        name: str, target: Callable[["InteractiveMode", str], None]
    ) -> Callable[["InteractiveMode", str], None]:
        def alias_fn(self: "InteractiveMode", args: str) -> None:
            target(self, args)

        alias_fn.__name__ = name
        alias_fn.__doc__ = f"Alias for `{target.__name__[3:]}`\n\n{target.__doc__}"

        return alias_fn

    do_rm = alias("rm", do_remove)
    do_ls = alias("ls", do_list)

    def emptyline(self) -> bool:
        self.lastcmd = ""
        return False

    def default(self, line: str) -> bool:  # type:ignore[reportIncompatibleMethodOverride]
        if line == "EOF":
            print()
            return True
        command = line.split(maxsplit=1)[0]
        print(f"Unknown command: `{command}`")


def handle_commandline(todos: core.TodoModel, args: argparse.Namespace) -> None:
    if args.interactive:
        cmdline = InteractiveMode(todos)
        cmdline.cmdloop()
    elif args.add:
        todo_id = todos.add(" ".join(args.add))
        print(f"Saved into todo item id #{todo_id}")
    elif args.list:
        for id, _row_num, text, done in todos.get_all():
            mark = "✓" if done else "✗"
            if sys.stdout.isatty():
                color = BOLD + (GREEN if done else RED)
                mark = color + mark + RESET
            print(f"{mark} #{id:<4} {text}")
    elif todo_id := args.done or args.undo:
        todos.set_status(todo_id, args.done is not None)
    elif args.remove:
        if not todos.remove(args.remove):
            print(f"Item #{args.remove} not found")
    elif args.remove_done:
        total = todos.remove_done()
        print(f"Removed {total} todo items")
    else:
        raise RuntimeError("Invalid option combination")


def main() -> None:
    parser = setup_cmdline()
    args = parser.parse_args()

    try:
        with psycopg.connect("dbname=py_todo", autocommit=True) as conn:
            todos = core.TodoModel(conn)
            handle_commandline(todos, args)
    except psycopg.OperationalError:
        print("Could not connect to the database")


if __name__ == "__main__":
    main()
