# -*- coding: utf-8 -*-
from functools import wraps

from .channel import Channel
from ..connection import Connection
from ..server_data import ServerData
from ..exceptions import SshException
from ..command_output import CommandOutput


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
