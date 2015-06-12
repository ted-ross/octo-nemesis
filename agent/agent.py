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

class Agent(MessagingHandler):
    def __init__(self, url):
        super(Agent, self).__init__()
        self.url = url
        self.senders = {}
        self.container    = None
        self.conn         = None
        self.broadcast_rx = None
        self.command_rx   = None
        self.command_addr = None
        self.service_rx   = None
        self.relay        = None

    def on_start(self, event):
        self.container = event.container
        self.conn = event.container.connect(self.url)
        self.broadcast_rx = event.container.create_receiver(self.conn, "broadcast/ON_AGENT")
        self.command_rx   = event.container.create_receiver(self.conn, None, dynamic=True)

    def on_connection_opened(self, event):
        if event.connection.remote_offered_capabilities and 'ANONYMOUS-RELAY' in event.connection.remote_offered_capabilities:
            self.relay = self.container.create_sender(self.conn, None)

    def on_link_opened(self, event):
        if event.receiver == self.command_rx:
            self.command_addr = self.command_rx.remote_source.address
            print "Agent established on command address: %s" % self.command_addr

    def on_message(self, event):
        if event.receiver in (self.command_rx, self.broadcast_rx):
            self.process_command(event)
        elif event.receiver == self.service_rx:
            pass


    def process_command(self, event):
        body = event.message.body
        if body.__class__ != dict:
            return
        opcode = body['OPCODE']
        if opcode == 'DISCOVER':
            self.send_message(event.message.reply_to,
                              {'OPCODE':'DECLARE', 'ADDR':self.command_addr},
                              event.message.correlation_id)
        elif opcode == 'DEPLOY':
            self.deploy_service(body)

    def send_message(self, to, body, cid=None):
        sender = self.relay or self.senders.get(to)
        if not sender:
            sender = self.container.create_sender(self.conn, to)
            self.senders[to] = sender
        sender.send(Message(address=to, body={'OPCODE':'DECLARE', 'ADDR': "%s" % self.command_addr},
                            correlation_id=cid))

    def deploy_service(self, body):
        name = body['SVCNAME']
        self.service_rx = self.container.create_receiver(self.conn, name)

try:
    Container(Agent("0.0.0.0:5672")).run()
except KeyboardInterrupt: pass



