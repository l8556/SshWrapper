# -*- coding: utf-8 -*-
import time
from functools import wraps

import paramiko
from paramiko.client import SSHClient

from ..data import ServerData
from ..logger import log_out
from ..exceptions import SshException

def connected_channel_only(func):
    """
    Decorator to ensure that the SSH channel is opened before executing a method.
    :param func: The function to decorate.
    :return: The decorated function.
    """
    @wraps(func)
    def _check(self, *args, **kwargs):
        if not self.ssh_channel:
            raise SshException("Ssh chanel is not opened")

        return func(self, *args, **kwargs)

    return _check

class Channel:
    """
    Represents an SSH channel to a remote server.
    This class provides methods to interact with the SSH channel.
    :param client: The SSH client object.
    :param server_data: The server data containing information about the remote server.
    """

    def __init__(self, client: SSHClient, server_data: ServerData):
        self.client = client
        self.server = server_data
        self.ssh_channel = None

    def __enter__(self):
        """
        Method invoked when entering a context block using `with` statement.
        Opens the SSH channel.

        :return: The SSH channel object.
        """
        self.open()
        return self.ssh_channel

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Method invoked when exiting a context block using `with` statement.
        Closes the SSH channel.
        """
        self.close()

    def open(self):
        """
        Opens the SSH channel.
        """
        start_time = time.time()
        while (time.time() - start_time) < self.server.connection_timeout and self.ssh_channel is None:
            try:
                self.ssh_channel = self.client.invoke_shell()

            except paramiko.SSHException as e:
                log_out(f'SSH error: {e}. Waiting and retrying...', self.server, log_type='error')
                time.sleep(1)
                continue

    @connected_channel_only
    def exec_command(self, command: str, encoding: str = 'utf-8', stdout: bool = False):
        """
        Executes a command on the remote server through the SSH channel.

        :param command: The command to execute.
        :param encoding: The character encoding to decode the command output. Defaults to 'utf-8'.
        :param stdout: Whether to print the standard output. Defaults to False.
        """
        self.ssh_channel.send(command + '\n')
        while not self.ssh_channel.recv_ready():
            time.sleep(0.5)
            pass
        output = self.ssh_channel.recv(1024).decode(encoding)
        print(output) if stdout else None

    def close(self):
        """
        Closes the SSH channel.
        """
        self.ssh_channel.close()
