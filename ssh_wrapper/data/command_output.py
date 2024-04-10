# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class CommandOutput:
    """
    Represents the output of a command execution.

    :param stdout: The standard output of the command.
    :param stderr: The standard error of the command.
    :param exit_code: The exit code returned by the command.
    """
    stdout: str
    stderr: str
    exit_code: int
