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
from utils import AGENT_BROADCAST_ADDRESS, STATE_FREE, STATE_CLIENT, STATE_SERVER, \
    STATE_SERVER_CLOSING, DEPLOY_TYPE_CLIENT, DEPLOY_TYPE_SERVER, DEPLOY_TYPE_UNDEPLOY


class Agent(MessagingHandler):
    """
    Our own custom message handler called Agent that implements reactive message handling semantics.
    An agent could be a client or a server
    """
    def __init__(self, url):
        super(Agent, self).__init__()
        self.url = url
        self.senders = {}

        self.container = None
        self.connection = None

        self.broadcast_receiver = None
        self.command_receiver = None

        self.receiver = None
        self.sender = None

        self.command_addr = None

        # This like an abstract sender. You can supply the sender to this relay and have it send messages.
        self.relay = None
        self.period = 1.0
        self.total_requests_received = 0
        # Default the state of the newly instantiated agent to FREE
        self.state = STATE_FREE
        self.address = None

    def get_stats(self):
        current_state = dict() # Is creating a new dict everytime going to lead a memory leak?
        current_state['total_requests_received'] = self.total_requests_received
        current_state['state'] = self.state
        current_state['outstanding_requests'] = self.receiver.queued
        # TODO - I am hoping to get the request_rate from ...
        current_state['request_rate'] = self.total_requests_received / total_uptime
        return current_state

    def change_state(self, event):
        deploy_type = event.message.body.get('deploy_type')
        if self.state == STATE_FREE and deploy_type == DEPLOY_TYPE_SERVER:
            # Change the state of this agent to SERVER
            self.state = STATE_SERVER
            # Open receiver on name
            self.receiver = event.container.create_receiver(self.connection, self.address)
        elif self.state == STATE_FREE and deploy_type == DEPLOY_TYPE_CLIENT:
            # Change the state of this agent to CLIENT
            self.state = STATE_CLIENT
            # Open sender to name
            self.container.create_sender(self.connection, self.address)
        elif self.state == STATE_SERVER and deploy_type == DEPLOY_TYPE_UNDEPLOY:
            # Change the state of this agent to FREE
            self.state = STATE_SERVER_CLOSING
            # Stop issuing credit for receiver with name
            #TODO - Check examples to see how you can stop issuing credits
        elif self.state == STATE_CLIENT and deploy_type == DEPLOY_TYPE_UNDEPLOY:
            self.state = STATE_FREE
            # Close sender 'name'
            self.sender.close()
        elif self.state == STATE_SERVER_CLOSING and deploy_type == DEPLOY_TYPE_UNDEPLOY:
            self.state == STATE_FREE
            self.receiver.close()

    def send_message(self, to, body, correlation_id=None):
        sender = self.relay or self.senders.get(to)

        if not sender:
            sender = self.container.create_sender(self.connection, to)
            self.senders[to] = sender

        sender.send(Message(address=to,
                            body=body,
                            correlation_id=correlation_id))

    def process_command(self, event):
        self.change_state(event)

    def on_start(self, event):
        self.container = event.container
        self.connection = event.container.connect(self.url)
        #self.broadcast_receiver = event.container.create_receiver(self.conn, AGENT_BROADCAST_ADDRESS)
        #self.command_receiver = event.container.create_receiver(self.connection, None, dynamic=True)

    def on_connection_opened(self, event):
        if event.connection.remote_offered_capabilities and 'ANONYMOUS-RELAY' in event.connection.remote_offered_capabilities:
            self.relay = self.container.create_sender(self.connection, None)

    def on_link_opened(self, event):
        pass
        #if event.receiver == self.command_receiver:
        #    self.command_addr = self.command_receiver.remote_source.address

    def on_message(self, event):
        """
        Invoked when messages are received.
        :param event:
        :return:
        """
        # Increment the total_requests_received by 1, this will include duplicate requests.
        self.total_requests_received += 1

        # We will only process if the receiver is present in our list of expected receivers.
        if event.receiver in (self.command_receiver, self.broadcast_receiver):
            self.process_command(event)
        else:
            pass

    def on_timer_task(self, event):
        # self.period is defaulted to 1 second. This timer will broadcast a message every one second.
        self.send_message(AGENT_BROADCAST_ADDRESS, self.get_stats())
        self.container.schedule(self.period, self)

    #def on_timer(self, event):
    #    self.period is defaulted to 1 second. This timer will broadcast its stats every one second.
    #    self.send_message(AGENT_BROADCAST_ADDRESS, self.get_stats())
    #    self.container.schedule(self.period, self)

try:
    agent = Agent("0.0.0.0:5672")
    container = Container(agent)
    container.run()
    #Container(Agent("0.0.0.0:5672")).run()
except KeyboardInterrupt:
    container.stop()



