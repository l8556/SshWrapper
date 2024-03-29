# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class ServerData:
    ip: str
    username: str
    password: str = None
    custom_name: str = ''
    connection_timeout: int = 300
