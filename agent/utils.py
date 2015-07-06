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


AGENT_BROADCAST_ADDRESS = "broadcast/agent/status"
TOOL_COMMAND_ADDRESS = "tool/command"

STATE_FREE = "FREE"
STATE_CLIENT = "CLIENT"
STATE_SERVER = "SERVER"
STATE_SERVER_CLOSING = "SERVER_CLOSING"

DEPLOY_TYPE_CLIENT = "DEPLOY_AS_CLIENT"
DEPLOY_TYPE_SERVER = "DEPLOY_AS_SERVER"
DEPLOY_TYPE_UNDEPLOY = "UNDEPLOY"
DEPLOY_TYPE = "QUIESCE"

STATES = [STATE_FREE, STATE_CLIENT, STATE_SERVER, STATE_SERVER_CLOSING]