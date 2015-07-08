##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##

##
## Build command: (from project root)
##   docker build -t octo-nemesis-agent -f dockerfiles/octo-nemesis-agent/Dockerfile .
##

FROM fedora:21
MAINTAINER Ted Ross <tross@apache.org>
RUN yum -y update
RUN yum -y install net-tools nc python-qpid-proton
ADD agent /
CMD python agent.py

