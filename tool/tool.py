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

class Tool(MessagingHandler):
    def __init__(self, url):
        super(Tool, self).__init__()
        self.url = url
        self.senders = {}

    def on_start(self, event):
        self.container   = event.container
        self.conn        = event.container.connect(self.url)
        self.discover_rx = event.container.create_receiver(self.conn, "broadcast/ON_DISCOVER")
        self.reply_rx    = event.container.create_receiver(self.conn, None, dynamic=True)
        self.reply_addr  = None
        self.relay       = None

    def on_connection_opened(self, event):
        if event.connection.remote_offered_capabilities and 'ANONYMOUS-RELAY' in event.connection.remote_offered_capabilities:
            self.relay = self.container.create_sender(self.conn, None)

    def on_link_opened(self, event):
        if event.receiver == self.reply_rx:
            self.reply_addr = self.reply_rx.remote_source.address
        elif event.sender == self.relay:
            self.send_message("broadcast/ON_SERVER", {'OPCODE':'DISCOVER'})

    def on_message(self, event):
        if event.receiver in (self.reply_rx, self.discover_rx):
            self.process_message(event)

    def process_message(self, event):
        print "Message received: body=%r" % event.message.body

    def send_message(self, to, body):
        sender = self.relay or self.senders.get(to)
        if not sender:
            sender = self.container.create_sender(self.conn, to)
            self.senders[to] = sender
        sender.send(Message(address=to, body=body, reply_to=self.reply_addr))

try:
    Container(Tool("0.0.0.0:5672")).run()
except KeyboardInterrupt: pass



