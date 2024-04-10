# -*- coding: utf-8 -*-
from rich import print

from ssh_wrapper.data.server_data import ServerData


def log_out(msg: str, server: ServerData, log_type: str, color: str = None, stdout = True) -> None:
    if stdout:
        _type = log_type.lower()
        if _type in ['info']:
            msg = f'[{color or "green"}]|{_type.upper()}|{server.custom_name}|{server.ip}| {msg}'
        elif _type in ['error', 'warning']:
            msg = f'[{color or "red"}]|{_type.upper()}|{server.custom_name}|{server.ip}| {msg}'
        else:
            msg = f'{server.custom_name}|{server.ip}| {msg}'

        print(msg)
