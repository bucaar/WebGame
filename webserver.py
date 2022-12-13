import asyncio
from dataclasses import dataclass
import logging
from typing import AsyncGenerator
import json

@dataclass
class Request:
    method: str
    path: str
    version: str
    headers: dict[str, str]

@dataclass
class Response:
    body: "str | dict"
    status: str = "200"
    version: str = "HTTP/1.1"

    def body_as_string(self) -> str:
        if isinstance(self.body, str):
            return self.body
        
        return json.dumps(self.body)

class Server:
    def __init__(self) -> None:
        self.server: asyncio.base_events.Server = None
        self.chunk_size: int = 100

        self.status_codes = {
            "200": "OK",
            "400": "Bad Request",
            "404": "Not Found",
            "500": "Internal Server Error"
        }

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            addr = writer.get_extra_info("peername")
            name = "%s:%d" % (addr[0], addr[1])

            # GET / HTTP/1.1
            # Host: 192.168.99.108:12345
            # Upgrade-Insecure-Requests: 1
            # Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
            # User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15
            # Accept-Language: en-US,en;q=0.9
            # Accept-Encoding: gzip, deflate
            # Connection: keep-alive
            # 

            method = ""
            path = ""
            version = ""
            headers = {}

            async for line in self.read_until_empty(reader, name, self.chunk_size):
                if not line:
                    continue

                if not method:
                    method, path, version = line.split()
                elif ":" in line:
                    header_name, data = line.split(":", 1)
                    headers[header_name] = data
                else:
                    logging.warning("WEBSERVER unhandled HTTP line %s" % line)

            logging.info("WEBSERVER handling request from %s: %s %s" % (name, method, path))
            request = Request(method, path, version, headers)
            response = self.connection_handler(request)
            if not response:
                logging.warning("WEBSERVER unhandled request from %s" % name)
                response = Response("Unhandled Request", "500")

        except Exception as ex:
            logging.error("WEBSERVER ERROR while handling connection from %s" % name, exc_info=ex)
            response = Response("Unexpected Server Error", "500")

        await self.write(writer, "%s %s %s\r\n\r\n%s" % (response.version, response.status, self.status_codes[response.status], response.body_as_string()), name)
        writer.close()

    def connection_handler(self, request: Request) -> Response:
        logging.warning("WEBSERVER default connection handler was used. Request: %s %s" % (request.method, request.path))

    async def read_until_empty(self, reader: asyncio.StreamReader, conn_name: str, chunk_size: int) -> AsyncGenerator[str, None]:
        try:
            message: str = ""
            EOL = "\r\n"

            while True:
                data = await reader.read(chunk_size)
                message += data.decode()
                if not message:
                    return

                while EOL in message:
                    line, message = message.split(EOL, 1)
                    
                    logging.debug("WEBSERVER read from %s: %s" % (conn_name, line))
                    yield line

                    if not line:
                        if message:
                            logging.warning("WEBSERVER read empty line from %s, but there is more data in message: %s" % (conn_name, message))
                        return

        except ConnectionResetError as ex:
            logging.error("WEBSERVER ERROR reading from %s - connection reset error" % conn_name, exc_info=ex)

    async def write(self, writer: asyncio.StreamWriter, data: str, conn_name: str) -> None:
        try:
            logging.debug("WEBSERVER write to %s: %s" % (conn_name, data))

            writer.write(data.encode())
            await writer.drain()

        except ConnectionResetError as ex:
            logging.error("WEBSERVER ERROR writing to %s - connection reset error" % conn_name, exc_info=ex)

    def stop_server(self) -> None:
        logging.debug("WEBSERVER stopping server")
        self.server.close()
        logging.debug("WEBSERVER server stopped")

    async def start_server(self) -> None:
        try:
            self.server = await asyncio.start_server(self.handle_connection, "192.168.99.108", 12345)
        except asyncio.CancelledError as ex:
            logging.warning("WEBSERVER ERROR start server cancelled", exc_info=ex)
            return
        except Exception as ex:
            logging.error("WEBSERVER ERROR server could not be started", exc_info=ex)
            return

        addr = self.server.sockets[0].getsockname() if self.server.sockets else "unknown"
        logging.info("WEBSERVER serving on %s" % (addr,))

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.CancelledError as ex:
                logging.warning("WEBSERVER ERROR server cancelled", exc_info=ex)
