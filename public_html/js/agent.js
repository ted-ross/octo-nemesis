var octoApp = angular.module('octoApp', ['ui.bootstrap']);

octoApp.controller('ModalInstanceCtrl', function ($scope, $modalInstance, commandAddress, deploy, type) {

    $scope.commandAddress = commandAddress;
    $scope.deploy = deploy;
    $scope.type = type;

    $scope.deployDetails = {
        serviceAddress: 'logAgent',
        desiredThroughput: 100,
        backlog: 10
    };

    $scope.ok = function () {

        $scope.deploy($scope.commandAddress, $scope.deployDetails.serviceAddress, $scope.deployDetails.desiredThroughput, $scope.deployDetails.backlog, $scope.type);
        $modalInstance.close();
    };

    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
});

octoApp.controller('AgentController', function ($scope, $modal) {
    var messenger;
    var message;
    var STATE_FREE = "FREE";
    var STATE_CLIENT = "CLIENT";
    var STATE_SERVER = "SERVER";
    var STATE_SERVER_CLOSING = "SERVER_CLOSING";

    var DEPLOY_TYPE_CLIENT = "DEPLOY_AS_CLIENT";
    var DEPLOY_TYPE_SERVER = "DEPLOY_AS_SERVER";
    var DEPLOY_TYPE_UNDEPLOY = "UNDEPLOY";
    var DEPLOY_TYPE = "QUIESCE";

    var stats_holder = new Object();
    $scope.servers = new Object();
    $scope.clients = new Object();
    $scope.hideServerDeploy = true;
    $scope.hideClientDeploy = true;

    $scope.animationsEnabled = true;

    $scope.serverOpen = function (size) {
        var modalInstance = $modal.open({
          animation: $scope.animationsEnabled,
          templateUrl: 'serverContent.html',
          controller: 'ModalInstanceCtrl',
          size: size,
          resolve: {
            commandAddress: function () {
               return $scope.getAvailableAgentCommandAddress();
            },
            type: function () {
               return "SERVER";
            },
            deploy: function () {
               return $scope.deploy;
            }
          }
        });
    };

    $scope.clientOpen = function (size) {
        var modalInstance = $modal.open({
          animation: $scope.animationsEnabled,
          templateUrl: 'clientContent.html',
          controller: 'ModalInstanceCtrl',
          size: size,
          resolve: {
            commandAddress: function () {
               return $scope.getAvailableAgentCommandAddress();
            },
            type: function () {
               return "CLIENT";
            },
            deploy: function () {
               return $scope.deploy;
            }
          }
        });
    };

    $scope.availableAgents = 0;

    $scope.showDeployButtons = function() {
        if($scope.availableAgents > 0) {
            return true;
        }
        else {
            return false;
        }
    };

    var errorHandler = function(error) {
        console.log("Received error " + error);
    };

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
     * @public
     */
    $scope.getAvailableAgentCommandAddress = function() {
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

    $scope.deploy = function(to_address, name, throughput, backlog, type) {
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

    $scope.undeploy = function(to_address) {
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
                    $scope.servers[containerId] = specific_stat;
                    if($scope.clients[containerId]!=null) {
                        delete $scope.clients[containerId];
                    }
                }
                else if(specific_stat.state == STATE_CLIENT) {
                    $scope.clients[containerId] = specific_stat;
                    if($scope.servers[containerId]!=null) {
                        delete $scope.servers[containerId];
                    }
                }
                else if(specific_stat.state == STATE_FREE) {
                    delete $scope.clients[containerId];
                    delete $scope.servers[containerId];
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
            specific_stat.actual_throughput = parseFloat(output.actual_throughput).toFixed(2);
            specific_stat.outstanding_requests = output.outstanding_requests
            specific_stat.acknowledged = output.acknowledged

            $scope.availableAgents = getAvailableAgentCount();
            $scope.$apply();

            messenger.accept(t);
        }
    };

    $scope.initStatsService = function() {
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

    $scope.initStatsService();
});