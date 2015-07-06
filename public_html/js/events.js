(function() {

    function drawBarGraph() {
        //var data = [10, 20, 30, 40, 42];
        var data = [50];

        for (var i = 0; i < data.length; i++) {
            $('.chart').empty();

            var val = data[i]
            var newData = [val];
            var x = d3.scale.linear()
            .domain([0, 5])
            .range([0, 100]);

            d3.select(".chart")
              .selectAll("div")
                .data(newData)
              .enter().append("div")
                .style("width", function(d) { return x(d) + "px"; })
                .text(function(d) { return d; });

        }
    }

    function resizeModal(modalHeight) {
        var topPx;
        topPx = ($(window).height() - modalHeight) / 2;
        if (topPx < 0) {
             topPx = 0;
        }
        $('#simplemodal-container').css('top', topPx + 'px');
        $('#simplemodal-container').css('height', modalHeight + 'px');
    }

    $(document).ready(function() {
        //drawBarGraph();
        $("#serverDeploy").hide();
        $("#clientDeploy").hide();

        $(".close").click(function(event) {
            event.preventDefault();
            $.modal.close();
        });

        $("#submitServerDeploy").click(function(event) {
            event.preventDefault();
            var serverName = $("#serverName").val();
            var throughput = $("#throughput").val();
            var backlog = $("#backlog").val();

            octonemesis.deploy(octonemesis.getAvailableAgentCommandAddress(), serverName, throughput, backlog, "SERVER");
            $.modal.close();
        });

        $("#submitClientDeploy").click(function(event) {
            event.preventDefault();
            var clientName = $("#clientName").val();
            var desiredThroughput = $("#desiredThroughput").val();

            octonemesis.deploy(octonemesis.getAvailableAgentCommandAddress(), clientName, desiredThroughput, 0, "CLIENT");
            $.modal.close();
        });

        $( "#deployService" ).on( "click", function(event) {
            event.preventDefault();
            $("#serverDeploy").modal({
                onShow: function() {
                    resizeModal(200);
                }
            });
            return false;
        });

         $( "#deployClient" ).on( "click", function(event) {
            event.preventDefault();
            $("#clientDeploy").modal({
                onShow: function() {
                    resizeModal(200);
                }
            });
            return false;
        });

        $('body').on('click', '.undeployAgent', function(event) {
            event.preventDefault();
            var commandAddress = this.id;
            octonemesis.undeploy(commandAddress);
        });
    });

})();