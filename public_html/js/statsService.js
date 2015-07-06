//Some javascript namespace related basics here - http://appendto.com/2010/10/how-good-c-habits-can-encourage-bad-javascript-habits-part-1/
(function(octonemesis, $, undefined) {
    var messenger;
    var message;
    var STATE_FREE = "FREE"
    var STATE_CLIENT = "CLIENT"
    var STATE_SERVER = "SERVER"
    var STATE_SERVER_CLOSING = "SERVER_CLOSING"

    var DEPLOY_TYPE_CLIENT = "DEPLOY_AS_CLIENT"
    var DEPLOY_TYPE_SERVER = "DEPLOY_AS_SERVER"
    var DEPLOY_TYPE_UNDEPLOY = "UNDEPLOY"
    var DEPLOY_TYPE = "QUIESCE"

    var stats_holder = new Object();
    var servers = new Object();
    var clients = new Object();

    var errorHandler = function(error) {
        console.log("Received error " + error);
    };

    var updateServers = function() {
        $(".allServerDetails").empty();
        for (var key in servers) {
            var server = servers[key];

            var command_address = server.command_address;
            var service_address = server.service_address;
            var backlog = server.backlog;
            var total_requests_received = server.total_requests_received;


            var divContent = '<div class="serverDetails"><ul><li><label class="fixed">Service Address</label>' + service_address + '</li>';
            //<li><label class="fixed">Request Rate</label>500</li>
            divContent = divContent + '<li><label class="fixed">Backlog</label>' + backlog +'</li><li><label class="fixed">Total Requests</label>' + total_requests_received +'</li></ul>';
            divContent = divContent + '<span class="serverActions"><button class="undeployAgent" id="'+ command_address + '" type="button">Undeploy</button>';
            divContent = divContent + '<button id="quiesceServer"  type="button">Quiesce</button></span></div>';
            $(".allServerDetails").append(divContent);
        }
    }

    var updateClients = function() {
        $(".allClientDetails").empty();
        for (var key in clients) {
            var client = clients[key];
            var service_address = client.service_address;
            var desiredThroughput = client.desired_throughput;
            var command_address = client.command_address;
            var actualThroughput=0;
            var sent = client.sent
            var divContent = '<div class="clientDetails"><ul><li><label class="fixed">Service Address</label>' + service_address + '</li>'
            divContent = divContent + '<li><label class="fixed">Desired Throughput</label>' + desiredThroughput + '</li>   ';
            divContent = divContent + '<li><label class="fixed">Actual Throughput</label>' + actualThroughput + '</li>   ';
            divContent = divContent + '<li><label class="fixed">Messages Sent</label>' + sent + '</li></ul>';
            divContent = divContent + '<span class="serverActions"><button class="undeployAgent" id="'+ command_address + '" type="button">Undeploy</button>';
            divContent = divContent + '<button id="quiesceClient"  type="button">Quiesce</button></span></div>';
            $(".allClientDetails").append(divContent);
        }
    }


    octonemesis.initStatsService = function() {

        var address = "amqp://0.0.0.0:5673/broadcast/agent/status";
        //var address = "amqp:/broadcast/agent/status";
        messenger = new proton.Messenger();

        //Route does not seem to work.
        //messenger.route("amqp:/*", "amqp://0.0.0.0:5673/$1");
        message = new proton.Message();

        messenger.setOutgoingWindow(1024);
        messenger.setIncomingWindow(1024);
        messenger.on('error', errorHandler);

        messenger.on('work', receiveData);

        messenger.recv();
        messenger.start();
        messenger.subscribe(address);
    };

    /**
     *
     */
    var sendMessage = function(to_address, body) {

        //TODO - Use Route instead of this crappy code.
        to_address = 'amqp://0.0.0.0:5673/' + to_address.substring(6);
        message = new proton.Message();

        message.setAddress(to_address);
        message.body = body;

        messenger.put(message);
        messenger.send();
    }

    var getServers = function() {
        var servers = []
        for (var key in stats_holder) {
            var specific_stat = stats_holder[key];
            if(specific_stat.state == STATE_SERVER) {
                servers.push(specific_stat);
            }
        }

        return servers;
    }

    /**
     *
     */
    octonemesis.getAvailableAgentCommandAddress = function() {
        for (var key in stats_holder) {
            var specific_stat = stats_holder[key];
            if(specific_stat.state == STATE_FREE) {
                return specific_stat.command_address
            }
        }

        return null;
    }

    /**
     * Returns the number of available agents that can be deployed. Agents that are in STATE_FREE are considered
     * free and deployable.
     */
    var getAvailableAgentCount = function() {
        var availableAgentCount = 0;
        for (var key in stats_holder) {
            var specific_stat = stats_holder[key];
            if(specific_stat.state == STATE_FREE) {
                availableAgentCount++;
            }
        }

        return availableAgentCount;
    }

    /**
     * Deploys an agent. An agent can be deployed as a client or a server.
     * @param {string} to_address - The address of listening server. This is usually the address of the receiver that was created with dynamic=True
     * @param {string} name - The name of the server.
     * @param {string} throughput - The desired throughput.
     * @param {string} backlog - The allowed backlog.
     * @param {string} type - The type can be one of "CLIENT" or "SERVER".
     * @public
     */
    octonemesis.deploy = function(to_address, name, throughput, backlog, type) {
        var deployInfo = {};
        deployInfo.name = name;
        deployInfo.throughput = throughput;
        deployInfo.backlog = backlog;

        if (type == "CLIENT") {
            var deployType = DEPLOY_TYPE_CLIENT;
        }
        else if (type == "SERVER") {
            var deployType = DEPLOY_TYPE_SERVER;
        }

        deployInfo.deploy_type = deployType;
        sendMessage(to_address, deployInfo);
    }

    octonemesis.undeploy = function(to_address) {
        var undeployInfo = {};
        undeployInfo.deploy_type = DEPLOY_TYPE_UNDEPLOY;
        sendMessage(to_address, undeployInfo);
    }

    var receiveData = function() {
        while (messenger.incoming()) {
            var t = messenger.get(message, true);
            var content = message.data.format()

            var formattedString = content.replace(/b"/g, '"');
            formattedString = formattedString.replace(/=/g, ':');
            var output = JSON.parse(formattedString);

            var specific_stat = stats_holder[output.container_id];

            if(specific_stat == null) {
                specific_stat = {};
                stats_holder[output.container_id] = specific_stat;
            }
            else {
                var containerId = specific_stat.container_id;

                if(specific_stat.state == STATE_SERVER) {
                    servers[containerId] = specific_stat;
                    if(clients[containerId]!=null) {
                        delete clients[containerId];
                    }
                }
                else if(specific_stat.state == STATE_CLIENT) {
                    clients[containerId] = specific_stat;
                    if(servers[containerId]!=null) {
                        delete servers[containerId];
                    }
                }
                else if(specific_stat.state == STATE_FREE) {
                    delete clients[containerId];
                    delete servers[containerId];
                }
            }

            specific_stat.total_requests_received = output.total_requests_received
            specific_stat.state = output.state
            specific_stat.container_id = output.container_id
            specific_stat.command_address = output.command_address
            specific_stat.outstanding_requests = output.outstanding_requests
            specific_stat.service_address = output.service_address
            specific_stat.sent = output.sent
            specific_stat.desired_throughput = output.desired_throughput
            specific_stat.backlog = output.backlog
            specific_stat.throughput = output.throughput
            specific_stat.outstanding_requests = output.outstanding_requests

            updateServers();
            updateClients();

            var availableAgentCount = getAvailableAgentCount();

            if(availableAgentCount > 0) {
                $(".deployButtons").show();
            }
            else {
                $(".deployButtons").hide();
            }

            $("#availableAgents").html(getAvailableAgentCount());

            messenger.accept(t);
        }
    };

}( window.octonemesis = window.octonemesis || {}, jQuery ));

//Kick off the initStatsService. This will start reading from the broadcast/agent and start displaying statistics.
octonemesis.initStatsService();