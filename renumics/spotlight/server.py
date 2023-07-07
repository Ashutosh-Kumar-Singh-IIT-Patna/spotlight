"""
Local proxy object for the spotlight server process
"""

import threading
from queue import Queue, Empty
import socket
import atexit

import os
import sys
import secrets
import multiprocessing
import multiprocessing.connection
import subprocess
from typing import Optional, Any

import pandas as pd

from renumics.spotlight.logging import logger
from renumics.spotlight.settings import settings

from renumics.spotlight.develop.vite import Vite

from renumics.spotlight.app_config import AppConfig


class Server:
    """
    Local proxy object for the spotlight server process
    """

    # pylint: disable=too-many-instance-attributes

    _host: str
    _port: int
    _requested_port: int

    _vite: Optional[Vite]

    process: Optional[subprocess.Popen]

    _startup_event: threading.Event

    connection: Optional[multiprocessing.connection.Connection]
    _connection_message_queue: Queue
    _connection_thread: threading.Thread
    _connection_thread_online: threading.Event
    _connection_authkey: str
    _connection_listener: multiprocessing.connection.Listener

    _df_receive_queue: Queue

    connected_frontends: int
    _all_frontends_disconnected: threading.Event
    _any_frontend_connected: threading.Event

    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        self._vite = None

        self._app_config = AppConfig()

        self._host = host
        self._requested_port = port
        self._port = self._requested_port
        self.process = None

        self.connected_frontends = 0
        self._any_frontend_connected = threading.Event()
        self._all_frontends_disconnected = threading.Event()

        self.connection = None
        self._connection_message_queue = Queue()
        self._connection_authkey = secrets.token_hex(16)
        self._connection_listener = multiprocessing.connection.Listener(
            ("127.0.0.1", 0), authkey=self._connection_authkey.encode()
        )

        self._startup_event = threading.Event()
        self._startup_complete_event = threading.Event()

        self._connection_thread_online = threading.Event()
        self._connection_thread = threading.Thread(
            target=self._handle_connections, daemon=True
        )

        self._df_receive_queue = Queue()

        atexit.register(self.stop)

    def __del__(self) -> None:
        atexit.unregister(self.stop)

    def start(self, config: AppConfig) -> None:
        """
        Start the server process, if it is not running already
        """
        if self.process:
            return

        self._app_config = config

        # launch connection thread
        self._connection_thread = threading.Thread(
            target=self._handle_connections, daemon=True
        )
        self._connection_thread.start()
        self._connection_thread_online.wait()
        env = {
            **os.environ.copy(),
            "CONNECTION_PORT": str(self._connection_listener.address[1]),
            "CONNECTION_AUTHKEY": self._connection_authkey,
        }

        # start vite in dev mode
        if settings.dev:
            self._vite = Vite()
            self._vite.start()
            env["VITE_URL"] = self._vite.url

        # automatic port selection
        if self._requested_port == 0:
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self._host, self._port))
            self._port = sock.getsockname()[1]

        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "renumics.spotlight.app:SpotlightApp",
            "--host",
            self._host,
            "--port",
            str(self._port),
            "--log-level",
            "critical",
            "--http",
            "httptools",
            "--ws",
            "websockets",
            "--timeout-graceful-shutdown",
            str(2),
            "--factory",
        ]

        if settings.dev:
            command.extend(["--reload"])

        # start uvicorn
        # pylint: disable=consider-using-with
        self.process = subprocess.Popen(command, env=env)

        self._startup_complete_event.wait(timeout=120)

    def stop(self) -> None:
        """
        Stop the server process if it is running
        """
        if not self.process:
            return

        if self._vite:
            self._vite.stop()

        self.process.terminate()
        try:
            self.process.wait(3)
        except subprocess.TimeoutExpired:
            self.process.kill()
        self.process = None

        self._connection_thread.join(0.1)
        self._connection_thread_online.clear()

        self._port = self._requested_port

        self._startup_event.clear()
        self._startup_complete_event.clear()

    @property
    def running(self) -> bool:
        """
        Is the server process running?
        """
        return self.process is not None

    @property
    def port(self) -> int:
        """
        The server's tcp port
        """
        return self._port

    def update(self, config: AppConfig) -> None:
        """
        Update app config
        """
        self._app_config = config
        self.send({"kind": "update", "data": config})

    def get_df(self) -> Optional[pd.DataFrame]:
        """
        Request and return the current DafaFrame from the server process (if possible)
        """
        self.send({"kind": "get_df"})
        return self._df_receive_queue.get(block=True)

    def _handle_message(self, message: Any) -> None:
        try:
            kind = message["kind"]
        except KeyError:
            logger.error(f"Malformed message from client process:\n\t{message}")
            return

        if kind == "startup":
            self._startup_event.set()
            self.update(self._app_config)
        elif kind == "startup_complete":
            self._startup_complete_event.set()
        elif kind == "frontend_connected":
            self.connected_frontends = message["data"]
            self._all_frontends_disconnected.clear()
            self._any_frontend_connected.set()
        elif kind == "frontend_disconnected":
            self.connected_frontends = message["data"]
            if self.connected_frontends == 0:
                self._any_frontend_connected.clear()
                self._all_frontends_disconnected.set()
        elif kind == "df":
            self._df_receive_queue.put(message["data"])
        else:
            logger.warning(f"Unknown message from client process:\n\t{message}")

    def send(self, message: Any, queue: bool = False) -> None:
        """
        Send a messge to the server process
        """
        if self.connection:
            self.connection.send(message)
        elif queue:
            self._connection_message_queue.put(message)

    def refresh_frontends(self) -> None:
        """
        Refresh all connected frontends
        """
        self.send({"kind": "refresh_frontends"})

    def _handle_connections(self) -> None:
        self._connection_thread_online.set()
        while True:
            self.connection = self._connection_listener.accept()

            # send messages from queue
            while True:
                try:
                    message = self._connection_message_queue.get(block=False)
                except Empty:
                    break
                else:
                    self.connection.send(message)
                    self._connection_message_queue.task_done()

            while True:
                try:
                    msg = self.connection.recv()
                except EOFError:
                    self.connection = None
                    break
                self._handle_message(msg)

    def wait_for_frontend_disconnect(self, grace_period: float = 5) -> None:
        """
        Wait for all frontends to disconnect
        """

        while True:
            self._all_frontends_disconnected.wait()
            if not self._any_frontend_connected.wait(timeout=grace_period):
                return