import logging
import os
import warnings
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from pathvalidate import is_valid_filepath


class AppLogging:
    _instance = None
    _initialized = False

    ROOT_LOGGER_NAME: str = ""

    DEFAULT_HANDLER: str = "FILE"
    DEFAULT_LOG_DIR: str | Path = Path("./logs")
    DEFAULT_LOG_LEVEL_FILE: int = logging.DEBUG
    DEFAULT_LOG_LEVEL_CONSOLE: int = logging.INFO
    DEFAULT_LOG_ROTATION: str = "midnight"
    DEFAULT_LOG_INTERVAL: int = 1
    DEFAULT_LOG_BACKUP_COUNT: int = 15
    DEFAULT_LOG_TO_CONSOLE: bool = False
    DEFAULT_LOG_FORMAT_FILE: str = (
        "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    )
    DEFAULT_LOG_FORMAT_CONSOLE: str = "%(levelname)-8s - %(name)s - %(message)s"
    DEFAULT_LOG_FORMAT_DATE: str = "%Y-%m-%d %H:%M:%S"

    LOG_DIR: str | Path = Path("./logs")
    LOG_LEVEL_FILE: int = logging.DEBUG
    LOG_LEVEL_CONSOLE: int = logging.INFO
    LOG_ROTATION: str = "midnight"
    LOG_INTERVAL: int = 1
    LOG_BACKUP_COUNT: int = 15
    LOG_TO_CONSOLE: bool = False
    LOG_FORMAT_FILE: str = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    LOG_FORMAT_CONSOLE: str = "%(levelname)-8s - %(name)s - %(message)s"
    LOG_FORMAT_DATE: str = "%Y-%m-%d %H:%M:%S"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._configure()

    def _get_session_count(self, filename: Path) -> int:
        """
        Used to obtain the session count for multi-run logs if ran on same day

        Parameters
        ----------
        filename : Path
            Path representation of the filepath for current log file

        Returns
        -------
        int
            Session Count
        """

        if not Path(filename).exists():
            return 1
        with open(filename, "r") as f:
            return sum(1 for line in f if "Session #" in line) + 1

    def _configure(self) -> None:
        """
        Creates log directory (if needed)
        Creates log file (if needed) and write Session #? data to file
        Sets minimum log level for execution
        Sets up File Handler
        Sets up Console Handler (if needed)

        Returns
        -------
        None
        """

        log_dir = Path(self.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        log_filename = (
            log_dir
            / f"{datetime.now().strftime('%Y-%m-%d')}_{self.ROOT_LOGGER_NAME}.log"
        )

        with open(log_filename, "a") as f:
            f.write(f"\n\n{'=' * 30}\n")
            f.write(
                f"\tSession #{self._get_session_count(log_filename)} - {datetime.now().strftime('%H:%M:%S')}"
            )
            f.write(f"\n{'-' * 30}\n\n")

        root = logging.getLogger(self.ROOT_LOGGER_NAME)

        env_level = os.environ.get("LOGLEVEL", "").upper()
        file_level = getattr(logging, env_level, self.LOG_LEVEL_FILE)
        root.setLevel(min(file_level, self.LOG_LEVEL_CONSOLE))

        file_handler = TimedRotatingFileHandler(
            filename=log_filename,
            when=self.LOG_ROTATION,
            backupCount=self.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )

        file_handler.setLevel(file_level)
        file_handler.setFormatter(
            logging.Formatter(self.LOG_FORMAT_FILE, datefmt=self.LOG_FORMAT_DATE)
        )
        root.addHandler(file_handler)

        if self.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.LOG_LEVEL_CONSOLE)
            console_handler.setFormatter(logging.Formatter(self.LOG_FORMAT_CONSOLE))
            root.addHandler(console_handler)

    @classmethod
    def _validate_logging_format(cls, logger_format: str, handler: str) -> bool:
        """
        Validates passed format with a dummy logger instance

        Outputs to console if a format error occurred

        Parameters
        ----------
        logger_format : str
            string object for desired logging format
        handler : str
            string representation of File/Console Handler

        Warns
        -------
        UserWarning
            Invalid Logging String Format detected with dummy logger instance

        Returns
        -------
        Bool
            value based on validity of {logger_format}
        """

        try:
            formatter = logging.Formatter(logger_format)
            dummy = logging.LogRecord(
                name="testing",
                level=logging.DEBUG,
                pathname="",
                lineno=0,
                msg="testing",
                args=None,
                exc_info=None,
            )
            formatter.format(dummy)
            return True
        except (KeyError, ValueError, TypeError) as e:

            if handler == "file":
                cls.LOG_FORMAT_FILE = cls.DEFAULT_LOG_FORMAT_FILE
                warnings.warn(
                    f"\n\t[AppLogging] Warning: Invalid Logging String Format '{logger_format}'"
                    f"\n\t\t{e}."
                    f"\n\t\tDefaulting to '%(asctime)s - %(levelname)-8s - %(name)s - %(message)s'"
                )

            elif handler == "console":
                cls.LOG_FORMAT_CONSOLE = cls.DEFAULT_LOG_FORMAT_CONSOLE
                warnings.warn(
                    f"\n\t[AppLogging] Warning: Invalid Logging String Format '{logger_format}'"
                    f"\n\t\t{e}."
                    f"\n\t\tDefaulting to '%(levelname)-8s - %(name)s - %(message)s'"
                )

            return False

    @classmethod
    def _handle_rotation_interval(
        cls, rotation: str = "midnight", interval: int = 1
    ) -> None:
        """
        Validates passed {rotation} arg first against accepted {rotation} string values
        If {rotation} is valid, it will validate {interval} next
        Will set Default values if either is deemed invalid

        Parameters
        ----------
        rotation : str
            string object for desired logging format
                -> Defaulted to 'midnight'
        interval : int
            integer value for rotation interval in terms of {rotation}
                -> Defaulted to 1 for 'midnight'

        Warns
        -------
        UserWarning
            Invalid Log Rotation detected
            Invalid Log Rotation Interval detected

        Returns
        -------
        None
        """

        log_rotation_lut = [
            "s",
            "m",
            "h",
            "d",
            "midnight",
            "w1",
            "w2",
            "w3",
            "w4",
            "w5",
            "w6",
            "w0",
        ]

        if rotation.lower() in log_rotation_lut:
            cls.LOG_ROTATION = rotation.lower()

            if rotation.lower() != "midnight":
                if isinstance(interval, int) and interval > 0:
                    cls.LOG_INTERVAL = interval
                else:
                    cls.LOG_ROTATION = cls.DEFAULT_LOG_ROTATION
                    cls.LOG_INTERVAL = cls.DEFAULT_LOG_INTERVAL
                    warnings.warn(
                        f"\n\t[AppLogging] Warning: Invalid Log Interval '{interval}'"
                        f"\n\t\tDefaulting to {cls.DEFAULT_LOG_ROTATION}"
                    )

        else:
            cls.LOG_ROTATION = cls.DEFAULT_LOG_ROTATION
            cls.LOG_INTERVAL = cls.DEFAULT_LOG_INTERVAL
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Log Rotation '{rotation}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_ROTATION}"
                f"\n\t\tSkipping Log Interval Check ({interval}) due to Invalid Log Rotation."
            )

    @classmethod
    def setup_logger(
        cls,
        name: str,
        file_level: str = "DEBUG",
        console_level: str = "INFO",
        handlers: str = "FILE",
        dir_log: str | Path = Path("./logs"),
        backup_count_log: int = 15,
        rotation_log: str = "midnight",
        interval_log: int = 1,
        format_file_log: str = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
        format_console_log: str = "%(levelname)-8s - %(name)s - %(message)s",
        format_date_log: str = "%Y-%m-%d %H:%M:%S",
    ) -> None:
        """
        Sets up Logger object based on the available passed parameters,
            defaulting to the pre-defined Defaults when needed.

        Parameters
        ----------
        name : str
            Passed name of module with __name__
                -> No Default
        file_level : str
            String representation of Logging Level for File Handler
                -> Default DEBUG
        console_level : str
            String representation of Logging Level for Console Handler
                -> Default INFO
        handlers : str
            String for FILE, CONSOLE, or BOTh
                -> Default FILE
        dir_log : str | Path
            String or Path representation of desired log directory
                -> Default ./logs
        backup_count_log : int
            Integer representation of how many days worth of logs are saved
                -> Default 15
        rotation_log : str
            String representation of Logging Rotation metric
                -> Default midnight
        interval_log : int
            Integer representation of Logging Rotation interval
                -> Default 1
        format_file_log : str
            String representation of Logging Format for File Handler
                -> Default %(asctime)s - %(levelname)-8s - %(name)s - %(message)s
        format_console_log : str
            String representation of Logging Format for Console Handler
                -> Default %(levelname)-8s - %(name)s - %(message)s
        format_date_log : str
            String representation of Datetime Format
                -> Default %Y-%m-%d %H:%M:%S

        Warns
        -------
        UserWarning
            Invalid Passed Parameters

        Raises
        -------
        RuntimeError
            Logger already initialized

        Returns
        -------
        None
        """

        if cls._instance:
            raise RuntimeError(
                f"Logger already initialized as '{cls.ROOT_LOGGER_NAME}'."
                "\nCall reset() first if needing to reinitialize."
                "\nOtherwise please use AppLogging.get_logger(__name__)"
            )

        cls.ROOT_LOGGER_NAME = name

        cls._handle_invalid_levels(file_level, console_level)

        valid_handlers = ["FILE", "CONSOLE", "BOTH"]
        if handlers.upper() not in valid_handlers:
            handlers = cls.DEFAULT_HANDLER
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Handlers Value '{handlers}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_HANDLER}"
            )

        if handlers.upper() == "BOTH" or handlers.upper() == "CONSOLE":
            cls.LOG_TO_CONSOLE = True

        if is_valid_filepath(dir_log):
            cls.LOG_DIR = dir_log
        else:
            cls.LOG_DIR = cls.DEFAULT_LOG_DIR
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Log Directory Path '{dir_log}'"
                f"\n\t\t\tDefaulting to {cls.DEFAULT_LOG_DIR}"
            )

        if isinstance(backup_count_log, int) and backup_count_log > 0:
            cls.LOG_BACKUP_COUNT = backup_count_log
        else:
            cls.LOG_BACKUP_COUNT = cls.DEFAULT_LOG_BACKUP_COUNT
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Backup Count '{backup_count_log}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_BACKUP_COUNT}"
            )

        cls._handle_rotation_interval(rotation_log, interval_log)

        if cls._validate_logging_format(format_file_log, "file"):
            cls.LOG_FORMAT_FILE = format_file_log

        if cls._validate_logging_format(format_console_log, "console"):
            cls.LOG_FORMAT_CONSOLE = format_console_log

        try:
            datetime.now().strftime(format_date_log)
            cls.LOG_FORMAT_DATE = format_date_log
        except ValueError:
            cls.LOG_FORMAT_DATE = cls.DEFAULT_LOG_FORMAT_DATE
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Datetime String Format '{format_date_log}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_FORMAT_DATE}"
            )
        cls()

    @classmethod
    def _handle_invalid_levels(
        cls, file_level: str = "DEBUG", console_level: str = "INFO"
    ) -> None:
        """
        Handles the logic for setting Handler levels

        Parameters
        ----------
        file_level : str
            String representation of Logging Level for File Handler
                -> Default DEBUG
        console_level : str
            String representation of Logging Level for Console Handler
                -> Default INFO

        Warns
        -------
        UserWarning
            Invalid File/Console Handler Levels

        Returns
        -------
        None
        """

        log_level_lut = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if file_level.upper() not in log_level_lut:
            cls.LOG_LEVEL_FILE = cls.DEFAULT_LOG_LEVEL_FILE
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid File Level '{file_level}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_LEVEL_FILE}"
            )
        else:
            cls.LOG_LEVEL_FILE = log_level_lut.get(file_level.upper(), logging.DEBUG)

        if console_level.upper() not in log_level_lut:
            cls.LOG_LEVEL_CONSOLE = cls.DEFAULT_LOG_LEVEL_CONSOLE
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Console Level '{console_level}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_LEVEL_CONSOLE}"
            )
        else:
            cls.LOG_LEVEL_CONSOLE = log_level_lut.get(
                console_level.upper(), logging.INFO
            )

    @classmethod
    def get_logger(cls, name: str | None = None) -> logging.Logger:
        """
        Method to get an already initialized logger object

        Parameters
        ----------
        name : str | None
            Used with no passed name, or with __name__ for per module logging

        Returns
        -------
        logging.Logger
            Logger object
        """

        cls._ensure_initialized()

        if name is None:
            return logging.getLogger(cls.ROOT_LOGGER_NAME)

        if not name.startswith(cls.ROOT_LOGGER_NAME):
            name = f"{cls.ROOT_LOGGER_NAME}.{name}"

        return logging.getLogger(name)

    @classmethod
    def set_levels(cls, file_level: str = "DEBUG", console_level: str = "INFO") -> None:
        """
        Used to set the levels of File/Console Handlers after initialization

        Parameters
        ----------
        file_level : str
            String representation of Logging Level for File Handler
                -> Default DEBUG
        console_level : str
            String representation of Logging Level for Console Handler
                -> Default INFO

        Warns
        -------
        UserWarning
            Invalid File/Console Handler Levels

        Returns
        -------
        None
        """

        cls._ensure_initialized()

        log_level_lut = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if file_level.upper() not in log_level_lut:
            cls.LOG_LEVEL_FILE = cls.DEFAULT_LOG_LEVEL_FILE
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid File Level '{file_level}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_LEVEL_FILE}"
            )
        else:
            cls.LOG_LEVEL_FILE = log_level_lut.get(file_level.upper(), logging.DEBUG)

        if console_level.upper() not in log_level_lut:
            cls.LOG_LEVEL_CONSOLE = cls.DEFAULT_LOG_LEVEL_CONSOLE
            warnings.warn(
                f"\n\t[AppLogging] Warning: Invalid Console Level '{console_level}'"
                f"\n\t\tDefaulting to {cls.DEFAULT_LOG_LEVEL_CONSOLE}"
            )
        else:
            cls.LOG_LEVEL_CONSOLE = log_level_lut.get(
                console_level.upper(), logging.INFO
            )

        root = logging.getLogger(cls.ROOT_LOGGER_NAME)
        for handler in root.handlers:
            if isinstance(handler, TimedRotatingFileHandler):
                cls.LOG_LEVEL_FILE = log_level_lut.get(
                    file_level.upper(), logging.DEBUG
                )
                handler.setLevel(cls.LOG_LEVEL_FILE)
            elif isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, TimedRotatingFileHandler
            ):
                cls.LOG_LEVEL_CONSOLE = log_level_lut.get(
                    console_level.upper(), logging.INFO
                )
                handler.setLevel(cls.LOG_LEVEL_CONSOLE)

    @classmethod
    def reset(cls) -> None:
        """
        Removes all Handlers from Logger object and resets Object back to uninitialized

        Returns
        -------
        None
        """

        root = logging.getLogger(cls.ROOT_LOGGER_NAME)
        for handler in root.handlers[:]:
            handler.close()
            root.removeHandler(handler)

        cls._instance = None
        cls._initialized = False

    @classmethod
    def enable_console(cls) -> None:
        """
        Used to ENABLE CONSOLE Logging after initialization of Logger Object

        Returns
        -------
        None
        """

        cls._ensure_initialized()

        root = logging.getLogger(cls.ROOT_LOGGER_NAME)
        for handler in root.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, TimedRotatingFileHandler
            ):
                handler.setLevel(cls.LOG_LEVEL_CONSOLE)
                return

        console_handler = logging.StreamHandler()
        console_handler.setLevel(cls.LOG_LEVEL_CONSOLE)
        console_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT_CONSOLE))
        root.addHandler(console_handler)

    @classmethod
    def disable_console(cls) -> None:
        """
        Used to DISABLE CONSOLE Logging after initialization of Logger Object

        Returns
        -------
        None
        """

        cls._ensure_initialized()

        root = logging.getLogger(cls.ROOT_LOGGER_NAME)
        for handler in root.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, TimedRotatingFileHandler
            ):
                handler.close()
                root.removeHandler(handler)

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Used to ensure Logger Object has been initialized, and not just setup, before return Logger Object

        Raises
        -------
        RuntimeError
            Logger not initialized

        Returns
        -------
        None
        """

        if not cls.ROOT_LOGGER_NAME:
            raise RuntimeError(
                "Logger not initialized.", "\n\tCall AppLogging.setup_logger() first."
            )
