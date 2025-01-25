# -*- coding: utf-8 -*-
import time
from rich.console import Console
from rich import print
from functools import wraps

from .channel import Channel
from ..connection import Connection
from ..data import ServerData, CommandOutput
from ..exceptions import SshException


def connected_ssh_client_only(func):
    """
    Decorator to ensure that the SSH connection is established before executing a method.

    :param func: The function to decorate.
    :return: The decorated function.
    """
    @wraps(func)
    def _check(self, *args, **kwargs):
        if not self.connection.connection_check():
            raise SshException("Connection is not created")

        return func(self, *args, **kwargs)

    return _check

class Ssh:
    """
    A class for interacting with a remote server via SSH.
    This class provides methods to execute commands on a remote server.
    """

    def __init__(self, server_data: ServerData):
        """
        Initializes an Ssh object.
        :param server_data: The server data containing information about the remote server.
        """
        self.connection = Connection(server_data=server_data)
        self.server = server_data
        self.channel = Channel(client=self.connection.client, server_data=self.server)
        self.console = Console()

    def __enter__(self):
        """
        Method invoked when entering a context block using `with` statement.
        Establishes the SSH connection.
        :return: The SSH object.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Method invoked when exiting a context block using `with` statement.
        Closes the SSH connection.
        """
        self.close()

    def connect(self):
        """
        Establishes the SSH connection.
        """
        self.connection.create()

    def close(self):
        """
        Closes the SSH connection.
        """
        self.connection.delete()

    @connected_ssh_client_only
    def exec_command(self, command, encoding='utf-8', stdout=True, stderr=True) -> CommandOutput:
        """
        Executes a command on the remote server.

        :param command: The command to execute.
        :param encoding: The character encoding to decode the command output. Defaults to 'utf-8'.
        :param stdout: Whether to print the standard output. Defaults to True.
        :param stderr: Whether to print the standard error. Defaults to True.
        :return: A CommandOutput object containing the command output, standard output, standard error, and exit status.
        """
        _stdin, _stdout, _stderr = self.connection.client.exec_command(command)

        output = CommandOutput(
            stdout=_stdout.read().decode(encoding).strip(),
            stderr=_stderr.read().decode(encoding).strip(),
            exit_code=_stdout.channel.recv_exit_status()
        )

        print(output.stdout) if stdout and output.stdout else None
        print(output.stderr) if stderr and output.stderr else None
        return output

    def wait_execute_service(
            self,
            service_name: str,
            timeout: int = None,
            stdout=True,
            status_bar=True,
            interval: int | float = 0.5
    ):
        """
        Wait for the specified service to execute, periodically checking its status and outputting logs. Only for Linux.

        :param service_name: Name of the service to monitor.
        :param timeout: Maximum time to wait for the service to execute. If None, wait indefinitely.
        :param stdout: Whether to print the service logs to standard output. Defaults to True.
        :param status_bar: Whether to show a status bar while waiting. Defaults to True.
        :param interval: Interval in seconds between status checks. Defaults to 0.5 seconds.
        :raises SshException: If the waiting time exceeds the specified timeout.
        """
        msg = f"[cyan]|INFO| Waiting for execute {service_name}"
        is_active_cmd = f'systemctl is-active {service_name}'

        status = self.console.status(msg)
        status.start() if status_bar else print(msg)

        start_time = time.time()
        try:
            while self.exec_command(is_active_cmd, stdout=False, stderr=False).stdout == 'active':
                status.update(f"{msg}\n{self.get_service_log(service_name)}") if status_bar else None
                time.sleep(interval)

                if isinstance(timeout, int) and (time.time() - start_time) >= timeout:
                    raise SshException(f'[bold red]|WARNING| The service {service_name} waiting time has expired.')

        finally:
            if status_bar:
                status.stop()

            print(
                f"[blue]{'-' * 90}\n|INFO| Service {service_name} log:\n"
                f"{'-' * 90}\n\n{self.get_service_log(service_name, 1000)}\n{'-' * 90}"
            ) if stdout else None

    def get_service_log(self, service_name: str, line_num: str | int = 20) -> str:
        """
        Retrieve the log entries for the specified service from the journal.

        :param service_name: Name of the service to retrieve logs for.
        :param line_num: Number of log lines to retrieve. Defaults to 20.
        :return: The service log entries.
        """
        command = f'journalctl -n {line_num} -u {service_name}'
        return self.exec_command(command, stdout=False, stderr=False).stdout

