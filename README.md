#Microservices over AMQP Demo

Microservices are independently deployables services that perform small tasks. A bunch of Microservices can be used provide high availability, reliabilty and throughput.

The purpose of this demo is to use Microservices to illustrate the features of the powerful [AMQP protocol](http://www.amqp.org/resources/download). This uses open source [Qpid Proton](http://qpid.apache.org/proton/) library to generate AMQP messages and the [Dispatch Router](http://qpid.apache.org/components/dispatch-router/) for routing messages.


##Installation Instructions

* Download the code into your `octo-project-install-folder` - Use the command `git clone https://github.com/ted-ross/octo-nemesis.git` to download the code.
* Install Node js using `sudo yum install nodejs` 
* Start the Websocket to TCP socket proxy - From your `proton-install-folder/examples/javascript/messenger` run `node proxy.js`. `proxy.js` is a simple `node.js` command line application that uses the ws2tcp.js library to proxy from a WebSocket to a TCP Socket or vice versa
* Install and setup Apache Web Server 
  * To install Apache on Fedora, please follow [these](https://fedoraproject.org/wiki/Apache_HTTP_Server) instructions
  * In the `/etc/httpd/conf.d` folder, create a new file called `www.octonemesis.com.conf` and add the following contents into the file.
  
   ```xml
        <VirtualHost *:80>
            <Directory />
                Options Indexes FollowSymLinks Includes ExecCGI
                AllowOverride None
                Require all granted
            </Directory>
            DocumentRoot /home/your-username/octo-project-install-folder/public_html
            ServerName www.octonemesis.com
            ServerAlias octonemesis.com
        </VirtualHost>
   ```
  * Add the following line to your /etc/hosts file - `127.0.0.1		www.octonemesis.com`
  * Restart Apache - `sudo /sbin/service httpd restart` (use `httpd -t` command to check for any errors in the httpd.conf file)
* Start the dispatch router - `qdrouterd`
* From the `octo-project-install-folder` start one or more agents using - `python agent/agent.py`
* Launch a browser and go to www.octonemesis.com
* If you are not able to launch the website, look in the Apache error logs at `/etc/httpd/logs/error_log`
* Turn off SELinux if you see any access issues in the Apache error log - run `setenforce 0` as root