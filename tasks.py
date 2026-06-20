#!/usr/bin/env python3
"""A simple CLI task manager backed by a live-updated JSON file.

The JSON file is the single source of truth: every command reads the
current state from disk, mutates it, and atomically writes it back, so
the file always reflects the task list after each invocation.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime

DEFAULT_STORE = os.environ.get(
    "TASKS_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
)


def load(path):
    """Read the task list from disk, returning an empty list if absent."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        sys.exit(f"error: could not read {path}: {e}")
    if not isinstance(data, list):
        sys.exit(f"error: {path} is not a valid task store")
    return data


def save(path, tasks):
    """Atomically write the task list to disk.

    Writes to a temp file in the same directory, then renames it over the
    target so the JSON file is never left half-written if interrupted.
    """
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tasks-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


def find(tasks, task_id):
    for t in tasks:
        if t["id"] == task_id:
            return t
    return None


def now():
    return datetime.now().isoformat(timespec="seconds")


# ---- commands -------------------------------------------------------------


def cmd_add(args):
    tasks = load(args.file)
    task = {
        "id": next_id(tasks),
        "title": args.title,
        "done": False,
        "created": now(),
        "completed": None,
    }
    tasks.append(task)
    save(args.file, tasks)
    print(f"added #{task['id']}: {task['title']}")


def cmd_list(args):
    tasks = load(args.file)
    if args.pending:
        tasks = [t for t in tasks if not t["done"]]
    elif args.done:
        tasks = [t for t in tasks if t["done"]]
    if not tasks:
        print("no tasks")
        return
    for t in tasks:
        box = "[x]" if t["done"] else "[ ]"
        print(f"{box} #{t['id']:<3} {t['title']}")


def cmd_done(args):
    tasks = load(args.file)
    t = find(tasks, args.id)
    if t is None:
        sys.exit(f"error: no task #{args.id}")
    if t["done"]:
        print(f"#{t['id']} already done")
        return
    t["done"] = True
    t["completed"] = now()
    save(args.file, tasks)
    print(f"completed #{t['id']}: {t['title']}")


def cmd_undone(args):
    tasks = load(args.file)
    t = find(tasks, args.id)
    if t is None:
        sys.exit(f"error: no task #{args.id}")
    t["done"] = False
    t["completed"] = None
    save(args.file, tasks)
    print(f"reopened #{t['id']}: {t['title']}")


def cmd_remove(args):
    tasks = load(args.file)
    t = find(tasks, args.id)
    if t is None:
        sys.exit(f"error: no task #{args.id}")
    tasks = [x for x in tasks if x["id"] != args.id]
    save(args.file, tasks)
    print(f"removed #{t['id']}: {t['title']}")


def cmd_clear(args):
    tasks = load(args.file)
    remaining = [t for t in tasks if not t["done"]]
    removed = len(tasks) - len(remaining)
    save(args.file, remaining)
    print(f"cleared {removed} completed task(s)")


def build_parser():
    p = argparse.ArgumentParser(
        prog="tasks", description="A simple JSON-backed CLI task manager."
    )
    p.add_argument(
        "-f", "--file", default=DEFAULT_STORE, help="path to the JSON store"
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="add a new task")
    a.add_argument("title", help="task description")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="list tasks")
    g = l.add_mutually_exclusive_group()
    g.add_argument("--pending", action="store_true", help="only unfinished tasks")
    g.add_argument("--done", action="store_true", help="only completed tasks")
    l.set_defaults(func=cmd_list)

    d = sub.add_parser("done", help="mark a task complete")
    d.add_argument("id", type=int)
    d.set_defaults(func=cmd_done)

    u = sub.add_parser("undone", help="reopen a completed task")
    u.add_argument("id", type=int)
    u.set_defaults(func=cmd_undone)

    r = sub.add_parser("remove", help="delete a task")
    r.add_argument("id", type=int)
    r.set_defaults(func=cmd_remove)

    c = sub.add_parser("clear", help="remove all completed tasks")
    c.set_defaults(func=cmd_clear)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
