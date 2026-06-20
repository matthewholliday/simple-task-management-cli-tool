# simple-task-manager

A tiny CLI task manager. The task list lives in `tasks.json`, which is the
single source of truth — every command reads it, applies the change, and
atomically writes it back, so the file is always up to date.

## Usage

```bash
python3 tasks.py add "Buy milk"       # add a task
python3 tasks.py list                 # list all tasks
python3 tasks.py list --pending       # only unfinished
python3 tasks.py list --done          # only completed
python3 tasks.py done 1               # mark task #1 complete
python3 tasks.py undone 1             # reopen task #1
python3 tasks.py remove 1             # delete task #1
python3 tasks.py clear                # drop all completed tasks
```

Use a different store with `-f/--file` or the `TASKS_FILE` env var:

```bash
python3 tasks.py -f work.json add "Ship release"
```
