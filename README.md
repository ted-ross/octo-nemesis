#Microservices over AMQP Demo

Microservices are independently deployables services that perform small tasks. A bunch of Microservices can be used provide high availability, reliabilty and throughput.

The purpose of this demo is to use Microservices to illustrate the features of the powerful [AMQP protocol](http://www.amqp.org/resources/download). This uses open source [Qpid Proton](http://qpid.apache.org/proton/) library to generate AMQP messages and the [Dispatch Router](http://qpid.apache.org/components/dispatch-router/) for routing messages.


##Installation Instructions

* Download the code into your **octo-project-install-folder** - Use the command **git clone https://github.com/ted-ross/octo-nemesis.git** to download the code.
* Install Node js using **sudo yum install nodejs** - 
* Start the Websocket to TCP socket proxy - From your **proton-install-folder/examples/javascript/messenger** run **node proxy.js**. proxy.js is a simple node.js command line application that uses the ws2tcp.js library to proxy from a WebSocket to a TCP Socket or vice versa
* Install and setup Apache Web Server 
  * To install Apache on Fedora, please follow [these](https://fedoraproject.org/wiki/Apache_HTTP_Server) instructions
  * More instructions to come ...