# AppLogging

A drop-in, singleton logging module for Python applications. Wraps Python's standard `logging` library with session
tracking, timed log rotation, optional console output, and safe defaults — configured once at startup and accessible
anywhere in your project via `get_logger()`.

---

## Philosophy

`AppLogging` is intentionally scoped. It is not a feature-complete wrapper around everything Python's `logging` module
offers. It is designed for developers who want a consistent, reliable logger they can drop into any project with minimal
configuration — and get out of the way.

If your use case requires fine-grained handler control, custom filters, or complex logging topologies, Python's
`logging` module is the right tool. `AppLogging` is for everyone else.

---

## Requirements

- Python 3.10+
- [`pathvalidate`](https://github.com/thombashi/pathvalidate)

---

## Overview

`AppLogging` is a singleton class, meaning only one logger instance exists for the lifetime of your application. You
call `setup_logger()` once at your entry point to initialize and configure it — `setup_logger()` does not return a
logger instance, it only initializes one. After that, any module can call `get_logger(__name__)` to retrieve a named
child logger that inherits the root configuration.

Log files are written to a configurable directory, named by date, and rotated automatically. Each time your application
starts, a session header is written to the log file so you can visually distinguish runs within the same day's file.

---

## Quick Start

Call `setup_logger()` once, near the top of your entry point:

```python
from app_logging import AppLogging

AppLogging.setup_logger(name="my_app")
```

Then in any module, call `get_logger()` to retrieve a logger instance:

```python
from app_logging import AppLogging

logger = AppLogging.get_logger(__name__)

logger.debug("Detailed trace info")
logger.info("Application started")
logger.warning("Something looks off")
logger.error("Something went wrong")
logger.critical("Unrecoverable failure")
```

---

## API Reference

### `AppLogging.setup_logger(...)` — *classmethod*

Initializes the logger. Must be called before any other method. Raises `RuntimeError` if called after initialization —
call `reset()` first if you need to reinitialize. Returns `None`.

| Parameter            | Type          | Default               | Description                                                                                                    |
|----------------------|---------------|-----------------------|----------------------------------------------------------------------------------------------------------------|
| `name`               | `str`         | *(required)*          | Root logger name. Used as the log file name prefix and parent namespace.                                       |
| `file_level`         | `str`         | `"DEBUG"`             | Minimum level written to the log file. Accepts: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.               |
| `console_level`      | `str`         | `"INFO"`              | Minimum level written to the console (if enabled). Same accepted values.                                       |
| `handlers`           | `str`         | `"FILE"`              | Which handlers to activate. Accepts: `"FILE"`, `"CONSOLE"`, `"BOTH"`.                                          |
| `dir_log`            | `str \| Path` | `./logs`              | Directory where log files are written. Created automatically if it doesn't exist.                              |
| `backup_count_log`   | `int`         | `15`                  | Number of rotated log files to retain before deletion.                                                         |
| `rotation_log`       | `str`         | `"midnight"`          | When to rotate the log file. Accepts: `"s"`, `"m"`, `"h"`, `"d"`, `"midnight"`, `"w0"`–`"w6"` (Monday–Sunday). |
| `interval_log`       | `int`         | `1`                   | How many units of `rotation_log` between rotations. Ignored when `rotation_log` is `"midnight"`.               |
| `format_file_log`    | `str`         | See below             | `logging`-style format string for file output.                                                                 |
| `format_console_log` | `str`         | See below             | `logging`-style format string for console output.                                                              |
| `format_date_log`    | `str`         | `"%Y-%m-%d %H:%M:%S"` | `strftime`-style format string for timestamps.                                                                 |

**Default file format:** `%(asctime)s - %(levelname)-8s - %(name)s - %(message)s`  
**Default console format:** `%(levelname)-8s - %(name)s - %(message)s`

---

### `AppLogging.get_logger(name)` — *classmethod*

Returns a `logging.Logger` instance. If `name` is provided and doesn't already start with the root logger name, it is
automatically namespaced as `root.name`. If `name` is `None`, returns the root logger directly.

Raises `RuntimeError` if called before `setup_logger()`.

---

### `AppLogging.set_levels(file_level, console_level)` — *classmethod*

Adjusts the log levels on the active handlers without reinitializing. Accepts the same level strings as
`setup_logger()`. Invalid values emit a `UserWarning` and fall back to defaults.

---

### `AppLogging.enable_console()` — *classmethod*

Activates console output at the configured `console_level`. If a console handler is already attached, it restores it to
the active level. If none exists, one is created and added.

---

### `AppLogging.disable_console()` — *classmethod*

Removes the console handler entirely. To restore console output, call `enable_console()`, which will create and attach a
new handler at the configured `console_level`.

---

### `AppLogging.reset()` — *classmethod*

Closes and removes all handlers, then resets the singleton state. After calling this, `setup_logger()` can be called
again with new configuration.

---

## Log Files

Log files are created in the configured directory using the naming pattern:

```
YYYY-MM-DD_<name>.log
```

Each application session writes a header block to the file:

```
==============================
    Session #3 - 14:22:07
------------------------------
```

This makes it easy to distinguish separate runs within the same day's log file without needing to parse timestamps.

Files are rotated on the configured schedule (`midnight` by default) and the configured number of backups is retained
before older files are deleted.

---

## Environment Variable Override

The file log level can be overridden at runtime via the `LOGLEVEL` environment variable:

```bash
LOGLEVEL=WARNING python main.py
```

This takes precedence over the `file_level` argument passed to `setup_logger()`.

---

## Input Validation

All parameters passed to `setup_logger()` are validated before being applied. If an invalid value is detected, a
`UserWarning` is emitted via Python's `warnings` module and the corresponding default is used instead. This applies to:

- Log level strings (must match a known level name)
- Handler value (must be `FILE`, `CONSOLE`, or `BOTH`)
- Log directory path (validated via `pathvalidate`)
- Backup count (must be a positive integer)
- Rotation and interval (rotation must be an accepted string; interval must be a positive integer)
- Log format strings (validated by constructing a formatter against a dummy log record)
- Date format strings (validated via `strftime`)

Because `warnings.warn` is used, warning behavior can be controlled programmatically via Python's `warnings` filter
system if needed.

---

## Notes

- `AppLogging` is a **singleton** — `setup_logger()` can only be called once per process lifecycle without an
  intervening `reset()`.
- `setup_logger()` returns `None` — use `get_logger()` to retrieve a logger instance.
- Child loggers retrieved via `get_logger(__name__)` are automatically namespaced under the root logger and inherit its
  handler configuration through Python's standard logger hierarchy.
- `get_logger()` raises `RuntimeError` if called before `setup_logger()`. Initialize at your entry point before any
  module calls it.
- `disable_console()` fully removes the console handler. `enable_console()` reconstructs and re-attaches it at the
  configured `console_level`.