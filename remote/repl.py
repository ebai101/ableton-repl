from __future__ import absolute_import, print_function, unicode_literals

import code
import logging
import select
import socket
import sys
from io import StringIO

from ableton.v3.control_surface import (
    ControlSurface,
    ControlSurfaceSpecification,
    ElementsBase,
)

logger = logging.getLogger("repl")


class Elements(ElementsBase):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)


class Specification(ControlSurfaceSpecification):
    elements_type = Elements


class REPL(ControlSurface):
    def __init__(self, c_instance, host="localhost", port=13254):
        self.host = host
        self.port = port
        self.locals = {}
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.server = None
        self.inputs = []
        self.message_queues = {}
        self.command_buffers = {}

        try:
            import Live

            self.locals["Live"] = Live
        except ImportError as e:
            logger.info(f"Could not import Live: {e}")

        super().__init__(c_instance=c_instance, specification=Specification)

    def create_server(self):
        """Initialize the server socket"""
        if self.server is None:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(1)
            self.server.setblocking(False)
            self.inputs = [self.server]
            logger.info(f"REPL server listening on {self.host}:{self.port}")

    def setup(self):
        self.schedule_message(0, self.tick)

    def tick(self):
        try:
            if self.server is None:
                self.create_server()

            readable, _, exceptional = select.select(self.inputs, [], self.inputs, 0)

            for s in readable:
                if s is self.server:
                    try:
                        client, addr = s.accept()
                        logger.info(f"Connection from {addr}")
                        client.setblocking(False)
                        self.inputs.append(client)
                        self.message_queues[client] = []
                        self.command_buffers[client] = ""
                        client.send(b">>> ")
                    except Exception as e:
                        logger.info(f"Error accepting connection: {e}")
                else:
                    self._handle_client_data(s)

            for s in exceptional:
                self._cleanup_client(s)

            self._process_message_queues()

        except Exception as e:
            logger.info(f"Error in tick: {e}")

        self.schedule_message(1, self.tick)

    def _handle_client_data(self, client):
        try:
            data = client.recv(4096).decode("utf-8")
            if not data:
                self._cleanup_client(client)
                return

            self.command_buffers[client] += data
            if "\n" in self.command_buffers[client]:
                command = self.command_buffers[client].strip()
                self.command_buffers[client] = ""

                if command.lower() in ("exit", "quit"):
                    self._cleanup_client(client)
                    return

                output = StringIO()
                sys.stdout = output
                sys.stderr = output

                try:
                    console = code.InteractiveConsole(self.locals)
                    console.push(command)

                    response = output.getvalue()
                    if response:
                        self.message_queues[client].append(response)
                    self.message_queues[client].append(">>> ")
                finally:
                    sys.stdout = self.stdout
                    sys.stderr = self.stderr

        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Error handling client data: {e}")
            self._cleanup_client(client)

    def _process_message_queues(self):
        """Process pending messages for all clients"""
        for client in list(self.message_queues.keys()):
            queue = self.message_queues[client]
            while queue:
                try:
                    msg = queue[0]
                    client.send(msg.encode("utf-8"))
                    queue.pop(0)
                except BlockingIOError:
                    break  # try again next tick
                except Exception as e:
                    print(f"Error sending message: {e}")
                    self._cleanup_client(client)
                    break

    def _cleanup_client(self, client):
        """Clean up resources when a client disconnects"""
        try:
            addr = client.getpeername()
            print(f"Client {addr} disconnected")
        except:
            pass

        if client in self.inputs:
            self.inputs.remove(client)
        if client in self.message_queues:
            del self.message_queues[client]
        if client in self.command_buffers:
            del self.command_buffers[client]
        try:
            client.close()
        except:
            pass
