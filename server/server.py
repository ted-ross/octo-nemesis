#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

class Server(MessagingHandler):
    def __init__(self, url):
        super(Server, self).__init__()
        self.url = url
        self.senders = {}

    def on_start(self, event):
        self.container = event.container
        self.conn = event.container.connect(self.url)
        self.broadcast_rx = event.container.create_receiver(self.conn, "broadcast/ON_SERVER")
        self.command_rx   = event.container.create_receiver(self.conn, None, dynamic=True)
        self.command_addr = None
        self.relay = None

    def on_connection_opened(self, event):
        if event.connection.remote_offered_capabilities and 'ANONYMOUS-RELAY' in event.connection.remote_offered_capabilities:
            self.relay = self.container.create_sender(self.conn, None)

    def on_link_opened(self, event):
        if event.receiver == self.command_rx:
            self.command_addr = self.command_rx.remote_source.address
            print "Server established on command address: %s" % self.command_addr

    def on_message(self, event):
        if event.receiver in (self.command_rx, self.broadcast_rx):
            self.process_command(event)


    def process_command(self, event):
        print "Command received: body=%r" % event.message.body

        sender = self.relay or self.senders.get(event.message.reply_to)
        if not sender:
            sender = self.container.create_sender(self.conn, event.message.reply_to)
            self.senders[event.message.reply_to] = sender
        sender.send(Message(address=event.message.reply_to, body="Declare Server on: %s" % self.command_addr,
                            correlation_id=event.message.correlation_id))

try:
    Container(Server("0.0.0.0:5672")).run()
except KeyboardInterrupt: pass



