# -*- coding: utf-8 -*-
import time

import paramiko
from paramiko.client import SSHClient, AutoAddPolicy

from .server_data import ServerData
from .logger import log_out


class Connection:
    def __init__(self, server_data: ServerData):
        self.client = self._create_client()
        self.server = server_data
        self.__connected = False

    def create(self):
        start_time = time.time()
        while (time.time() - start_time) < self.server.connection_timeout and not self.__connected:
            try:
                self.client.connect(self.server.ip, username=self.server.username, password=self.server.password)
                self.__connected = True

            except paramiko.AuthenticationException:
                self._handle_error(f'Authentication failed')
                continue

            except paramiko.SSHException as e:
                self._handle_error(f'SSH error: {e}')
                continue

            except ConnectionError as e:
                self._handle_error(f"Connection Error: {e}")
                continue

    def connection_check(self) -> bool:
        return self.__connected

    def delete(self):
        if self.__connected:
            self.client.close()
            self.__connected = False

    @staticmethod
    def _create_client():
        _client = SSHClient()
        _client.set_missing_host_key_policy(AutoAddPolicy())
        _client.load_system_host_keys()
        return _client

    def _handle_error(self, message: str):
        log_out(f"{message}\nWaiting and retrying...", self.server, log_type='error')
        time.sleep(1)
