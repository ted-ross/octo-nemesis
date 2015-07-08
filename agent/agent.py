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

import time

from proton import Message, Delivery
from proton.handlers import MessagingHandler
from proton.reactor import Container
from utils import AGENT_BROADCAST_ADDRESS, STATE_FREE, STATE_CLIENT, STATE_SERVER, STATE_QUIESCE, \
    STATE_SERVER_CLOSING, DEPLOY_TYPE_CLIENT, DEPLOY_TYPE_SERVER, DEPLOY_TYPE_UNDEPLOY, DEPLOY_TYPE_QUIESCE


class Agent(MessagingHandler):
    """
    Our own custom message handler called Agent that implements reactive message handling semantics.
    An agent could be a client or a server
    """

    def __init__(self, url):
        super(Agent, self).__init__(prefetch=0, auto_accept=False)
        self.url = url
        self.senders = {}

        self.container = None
        self.connection = None

        # This receiver is mainly used is mainly used to receive client requests
        self.receiver = None

        # Used to receive command requests. This receives commands such a DEPLOY_AS_CLIENT, DEPLOY_AS_SERVER, QUIESCE
        self.command_receiver = None
        self.command_address = None

        # This like an abstract sender. You can supply the sender to this relay_sender and have it send messages.
        self.relay_sender = None
        self.sender = None

        self.desired_throughput = 0

        self.period = 0
        self.total_requests_received = 0
        self.outstanding_requests = 0
        self.sent = 0
        self.acknowledged = 0
        self.messages_to_send = 0
        self.backlog = 0
        self.allowed_backlog = 0

        # Default the state of the newly instantiated agent to FREE
        self.state = STATE_FREE
        self.address = None
        self.service_name = None

        self.work_queue = list()
        self.actual_throughput = []
        self.epoch_time_milliseconds_start = 0

    def calculate_actual_throughput(self):
        act_throughput = 0.0
        if self.actual_throughput:
            total_time = 0
            total_messages = 0
            for tup in self.actual_throughput:
                total_time += tup[0]
                total_messages += tup[1]
            if total_messages and total_time:
                act_throughput = (total_messages * 1000.0) / (total_time * 1.0)

        return act_throughput

    def clear_stats(self):
        self.total_requests_received = 0
        self.sent = 0
        self.desired_throughput = 0
        self.outstanding_requests = 0
        self.actual_throughput = []
        self.backlog = 0
        self.state = STATE_FREE

    def get_stats(self):
        current_stats = dict() # Is creating a new dict everytime going to lead a memory leak?
        current_stats['total_requests_received'] = self.total_requests_received

        current_stats['state'] = self.state
        current_stats['sent'] = self.sent

        current_stats['service_address'] = self.service_name
        current_stats['desired_throughput'] = self.desired_throughput

        current_stats['backlog'] = self.backlog

        if self.container:
            current_stats['container_id'] = self.container._attrs['container_id']

        if self.command_address:
            current_stats['command_address'] = self.command_address

        current_stats['outstanding_requests'] = self.sent - self.acknowledged
        current_stats['actual_throughput'] = self.calculate_actual_throughput()

        return current_stats

    def set_agent_state(self, event):
        deploy_type = event.message.body.get('deploy_type')
        name = event.message.body.get('name')
        throughput = event.message.body.get('throughput')
        backlog = 0
        if event.message.body.get('backlog'):
            backlog = event.message.body.get('backlog')

        if self.state == STATE_FREE and deploy_type == DEPLOY_TYPE_SERVER:
            # Change the state of this agent to SERVER
            self.state = STATE_SERVER
            self.service_name = name
            self.allowed_backlog = backlog
            # Open receiver on name
            if throughput:
                self.desired_throughput = int(throughput)
            self.receiver = self.container.create_receiver(self.connection, source=name)
        elif self.state == STATE_FREE and deploy_type == DEPLOY_TYPE_CLIENT:
            # Change the state of this agent to CLIENT
            self.state = STATE_CLIENT
            self.service_name = name
            if throughput:
                self.desired_throughput = int(throughput)
            # Open sender to name
            self.sender = self.container.create_sender(self.connection, self.service_name)
        elif self.state == STATE_SERVER and deploy_type == DEPLOY_TYPE_UNDEPLOY:
            # Change the state of this agent to FREE
            self.state = STATE_SERVER_CLOSING
            # Stop issuing credit for receiver with name
            #TODO - Check examples to see how you can stop issuing credits
        elif self.state == STATE_CLIENT and deploy_type == DEPLOY_TYPE_UNDEPLOY:
            self.clear_stats()
            # Close sender 'name'
            self.sender.close()
        elif self.state == STATE_SERVER_CLOSING and deploy_type == DEPLOY_TYPE_UNDEPLOY:
            self.clear_stats()
            self.receiver.close()

    def calculate_backlog(self):
        actual_backlog = 0

        if self.receiver:
            actual_backlog = self.receiver.queued

        self.backlog = actual_backlog + len(self.work_queue)

    def send(self, to_address, body, correlation_id=None):
        sender = self.relay_sender or self.senders.get(to_address)

        if not sender:
            sender = self.container.create_sender(self.connection, to_address)
            self.senders[to_address] = sender

        sender.send(Message(address=to_address,
                            body=body,
                            correlation_id=correlation_id))

    def process_command(self, event):
        self.set_agent_state(event)

    def on_disconnected(self, event):
        pass

    def on_connection_closed(self, event):
        pass

    def on_session_closed(self, event):
        print 'Hello'

    def on_link_closed(self, event):
        if event.receiver and event.receiver == self.receiver and self.state == STATE_SERVER_CLOSING:
            self.clear_stats()

    def on_accepted(self, event):
        self.acknowledged += 1

    def on_start(self, event):
        self.connection = event.container.connect(self.url)
        self.container = event.container
        # self.broadcast_receiver = event.container.create_receiver(self.conn, AGENT_BROADCAST_ADDRESS)
        # This receiver is mainly used is mainly used to receive client requests
        self.command_receiver = event.container.create_receiver(self.connection, None, dynamic=True)

    def on_connection_opened(self, event):
        if event.connection.remote_offered_capabilities and 'ANONYMOUS-RELAY' in event.connection.remote_offered_capabilities:
            self.relay_sender = self.container.create_sender(self.connection, None)

    def calc_time_between_calls(self, message_count):
        time_between_calls = 0
        if not self.epoch_time_milliseconds_start:
            self.epoch_time_milliseconds_start = int(time.time() * 1000)
        else:
            current_time = int(time.time() * 1000)
            time_between_calls = current_time - self.epoch_time_milliseconds_start
            self.epoch_time_milliseconds_start = current_time

        time_between_calls_tuple = (time_between_calls, message_count)

        if len(self.actual_throughput) > 10:
            del(self.actual_throughput[0])

        self.actual_throughput.append(time_between_calls_tuple)

    def send_messages(self):
        if self.state == STATE_CLIENT:

            message_to_send = "Hello World"
            if self.sender:
                message_count = self.sender.credit
            else:
                message_count = 0
            if self.messages_to_send < message_count:
                message_count = self.messages_to_send

            self.calc_time_between_calls(message_count)

            for x in range(message_count):
                self.sent += 1
                self.send(self.service_name, message_to_send)

            self.messages_to_send -= message_count

    def on_sendable(self, event):
        self.send_messages()

    def on_link_opened(self, event):
        if event.receiver == self.command_receiver:
            event.receiver.flow(10)
            if event.receiver and event.receiver.remote_source:
                self.command_address = event.receiver.remote_source.address
        if event.receiver and event.receiver == self.receiver:
            if self.allowed_backlog:
                event.receiver.flow(int(self.allowed_backlog))

    def on_reactor_init(self, event):
        event.reactor.schedule(self.period, self)
        super(Agent, self).on_reactor_init(event)

    def on_timer_task(self, event):
        if self.relay_sender and self.period == 9:
            self.calculate_backlog()
            self.send(AGENT_BROADCAST_ADDRESS, self.get_stats())
            self.period = 0
        else:
            self.period += 1

        if self.state == STATE_CLIENT:
            self.messages_to_send = self.desired_throughput / 10
            self.send_messages()
        elif self.state == STATE_SERVER or self.state == STATE_SERVER_CLOSING:
            messages_to_process = self.desired_throughput / 10

            if self.state == STATE_SERVER_CLOSING and self.backlog == 0:
                self.state = STATE_FREE
                self.clear_stats()

            process_count = 0
            for x in range(messages_to_process):
                try:
                    if self.work_queue:
                        process_count += 1
                        delivery = self.work_queue[0]

                        delivery.update(Delivery.ACCEPTED)
                        delivery.settle()

                        del(self.work_queue[0])

                        if self.state == STATE_SERVER:
                            self.receiver.flow(1)
                except:
                    pass

            self.calc_time_between_calls(process_count)
        event.reactor.schedule(0.1, self)

    def on_message(self, event):
        # We will only process if the receiver is present in our list of expected receivers.
        if event.receiver == self.command_receiver:
            self.set_agent_state(event)
            event.receiver.flow(1)
        elif event.receiver == self.receiver:
            # Increment the total_requests_received by 1 and add simply add the message to out local work_queue
            self.total_requests_received += 1
            self.work_queue.append(event.delivery)

try:
    agent = Agent("0.0.0.0:5672")
    container = Container(agent)
    container.run()
    # Container(Agent("0.0.0.0:5672")).run()
except KeyboardInterrupt:
    container.stop()



