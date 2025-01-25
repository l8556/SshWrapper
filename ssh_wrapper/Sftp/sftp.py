# -*- coding: utf-8 -*-
import os
import stat
from functools import wraps
from os.path import exists, basename
from posixpath import join

from ..connection import Connection
from ..data import ServerData
from ..logger import log_out
from ..exceptions import SftpExceptions


def connected_sftp_only(func):
    """
    Decorator that checks SFTP connections before executing the method.

    :param func: The function to decorate.
    :return: The function to decorate.
    """
    @wraps(func)
    def _check(self, *args, **kwargs):
        if not self.client:
            raise SftpExceptions(f'|{self.server.custom_name}|{self.server.ip}| Sftp channel not created.')

        return func(self, *args, **kwargs)

    return _check

class Sftp:
    """
    A class for interacting with an SFTP server.
    This class provides methods to upload and download files using SFTP protocol.

    :param server_data: The server data containing information about the SFTP server.
    :param connection: The connection object used to establish SFTP connection. Defaults to None.
    """
    def __init__(self, server_data: ServerData, connection: Connection = None):
        self.connection = connection or Connection(server_data=server_data)
        self.server = server_data
        self.client = None

    def __enter__(self):
        """
        Method invoked when entering a context block using `with` statement.
        Establishes the SFTP connection.

        :return: The SFTP object.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Method invoked when exiting a context block using `with` statement.
        Closes the SFTP connection.
        """
        self.close()

    def connect(self):
        """
        Establishes the SFTP connection.
        If the connection is not yet established, creates it and opens an SFTP client.
        """
        if not self.connection.connection_check():
            self.connection.create()

        self.client = self.connection.client.open_sftp()

    def close(self):
        """
        Closes the SFTP connection.
        """
        if self.client:
            self.client.close()

    @connected_sftp_only
    def upload_file(self, local: str, remote: str, stdout: bool = False):
        """
        Uploads a file to the SFTP server.

        :param local: The local path of the file to upload.
        :param remote: The remote path where the file will be uploaded on the server.
        :param stdout: Whether to log output to stdout. Defaults to False.
        :raises FileNotFoundError: If the local file does not exist.
        """
        if not exists(local):
            raise FileNotFoundError(f"|{self.server.custom_name}|{self.server.ip}|Local file does not exist: {local}")

        log_out(
            f'Uploading file: [cyan]{local}[/] to [cyan]{remote}[/]', self.server, log_type='info', stdout=stdout
        )

        self.client.put(localpath=local, remotepath=remote, confirm=True)

    @connected_sftp_only
    def download(self, remote: str, local: str, stdout: bool = False):
        """
        Downloads a file or directory from the SFTP server.

        :param remote: The remote path of the file or directory on the server.
        :param local: The local path where the file or directory will be downloaded.
        :param stdout: Whether to log output to stdout. Defaults to False.
        """
        if stat.S_ISDIR(self.client.lstat(remote).st_mode):
            return self.download_dir(remote, local, stdout)
        return self.download_file(remote, local, stdout)

    @connected_sftp_only
    def download_dir(self, remote: str, local: str, stdout: bool = False):
        """
        Recursively downloads a directory from the SFTP server.

        :param remote: The remote path of the directory on the server.
        :param local: The local path where the directory will be downloaded.
        :param stdout: Whether to log output to stdout. Defaults to False.
        :raises SftpExceptions: If the remote object is not a directory.
        """
        if not stat.S_ISDIR(self.client.lstat(remote).st_mode):
            raise SftpExceptions(f"|ERROR| Remote object is not a directory: {remote}")

        log_out(
            f'Downloading dir: [cyan]{remote}[/] to [cyan]{local}[/]',
            self.server,
            log_type='info',
            stdout=stdout
        )

        os.makedirs(local, exist_ok=True)

        for entry in self.client.listdir_attr(remote):
            remote_filename = join(remote, entry.filename)
            local_filename = join(local, entry.filename)

            if stat.S_ISDIR(entry.st_mode):
                self.download_dir(remote_filename, local_filename)
            else:
                self.download_file(remote_filename, local_filename)

    @connected_sftp_only
    def download_file(self, remote: str, local: str, stdout: bool = False):
        """
        Downloads a file from the SFTP server.

        :param remote: The remote path of the file on the server.
        :param local: The local path where the file will be downloaded.
        :param stdout: Whether to log output to stdout. Defaults to False.
        """
        log_out(
            f'Downloading file: [cyan]{remote}[/] to [cyan]{local}[/]',
            self.server,
            log_type='info',
            stdout=stdout
        )

        os.makedirs(os.path.dirname(local), exist_ok=True)
        self.client.get(remotepath=remote, localpath=local)
