#!/usr/bin/python3

import asyncio
import re
from threading import Timer

from .. import config
from .message_controller import MessageController
from .sender import IrcSender

re_message = re.compile(
    r'(?:(:[^ ]+) )?'
    r'([^:\r]+)'
    r'(?: :([^\r]+))?'
    r'\r\n'
)


class IrcClient(asyncio.Protocol, IrcSender):

    ready = False

    def __init__(self):
        IrcSender.__init__(self)
        asyncio.Protocol.__init__(self)

    def connection_made(self, transport):
        self.transport = transport
        self.send('PASS', config.password)
        self.send('NICK', config.nick)
        self.send_msg('USER', config.ircname, 'wr', '*', config.realname)

    def data_received(self, raw_messages):
        for message in self._parse_raw_messages(raw_messages):
            if not config.debug:
                print(' '.join(message))
    
            MessageController(self, message).execute_message()

    def connection_lost(self, exc):
        asyncio.get_event_loop().stop()

    @staticmethod
    def _parse_raw_messages(raw_messages):
        for codec in config.codec:
            try:
                encoded_data = raw_messages.decode(codec)
            except UnicodeDecodeError:
                continue
            else:
                break
        else:
            return

        for match in re_message.finditer(encoded_data):
            prefix, messages, long_message = match.groups()
            data = [prefix] if prefix else []
            data += messages.split()
            if long_message:
                data.append(long_message)
            yield data

def connect():
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(IrcClient, config.host, config.port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
