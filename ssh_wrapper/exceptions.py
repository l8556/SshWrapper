# -*- coding: utf-8 -*-
from rich import print

class SshException(Exception):
    def __init__(self, message: str = ''):
        super().__init__(message)
        self.message = message

    def __str__(self):
        print(f"[bold red]{self.__class__.__name__}[/bold red] {self.message}")
        return ''

class SftpExceptions(SshException): ...
