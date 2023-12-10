# replicated_log

[https://docs.google.com/document/d/1D1C7dyNJan_6ssF2cC-16bWXn26TD5BlDQ1MCQu0S6Y/edit
](https://docs.google.com/document/d/1D1C7dyNJan_6ssF2cC-16bWXn26TD5BlDQ1MCQu0S6Y/edit)

###Iteration 0.

Choose a desirable language for implementation and try to implement (or find the implementation) a simple Echo Client-Server application.

###Iteration 1.

The Replicated Log should have the following deployment architecture: one Master and any number of Secondaries.

**Master** should expose a simple HTTP server (or alternative service with a similar API) with: 

> * POST method - appends a message into the in-memory list
> * GET method - returns all messages from the in-memory list

**Secondary** should expose a simple  HTTP server(or alternative service with a similar API)  with:

> * GET method - returns all replicated messages from the in-memory list

**Properties and assumptions:**

* after each POST request, the message should be replicated on every Secondary server
* Master should ensure that Secondaries have received a message via ACK
* Master’s POST request should be finished only after receiving ACKs from all Secondaries (blocking replication approach)
* to test that the replication is blocking, introduce the delay/sleep on the Secondary
* at this stage assume that the communication channel is a perfect link (no failures and messages lost)
* any RPC framework can be used for Master-Secondary communication (Sockets, language-specific RPC, HTTP, Rest, gRPC, …)
* your implementation should support logging 
* Master and Secondaries should run in Docker





`docker-compose up`

**What I see in the terminal:**


		[+] Running 4/1
		 ✔ Network iteration_1_ucu_task_stavniichuk_ver2_15oct_my_network      Created                                                                                                                                            0.0s 
		 ✔ Container iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      Created                                                                                                                                            0.1s 
		 ✔ Container iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  Created                                                                                                                                            0.0s 
		 ✔ Container iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  Created                                                                                                                                            0.0s 
		Attaching to iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1, iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1, iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  |  * Serving Flask app 'secondary1' (lazy loading)
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  |  * Environment: production
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  |    WARNING: This is a development server. Do not use it in a production deployment.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  |    Use a production WSGI server instead.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  |  * Debug mode: on
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  | WARNING:werkzeug: * Running on all addresses.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  |    WARNING: This is a development server. Do not use it in a production deployment.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  | INFO:werkzeug: * Running on http://172.22.0.2:5001/ (Press CTRL+C to quit)
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  | INFO:werkzeug: * Restarting with stat
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  |  * Serving Flask app 'secondary2' (lazy loading)
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  |  * Environment: production
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  |    WARNING: This is a development server. Do not use it in a production deployment.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  |    Use a production WSGI server instead.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  |  * Debug mode: on
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  | WARNING:werkzeug: * Running on all addresses.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  |    WARNING: This is a development server. Do not use it in a production deployment.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  | INFO:werkzeug: * Running on http://172.22.0.4:5002/ (Press CTRL+C to quit)
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  | INFO:werkzeug: * Restarting with stat
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Serving Flask app 'master' (lazy loading)
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Environment: production
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |    WARNING: This is a development server. Do not use it in a production deployment.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |    Use a production WSGI server instead.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Debug mode: on
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Running on all addresses.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |    WARNING: This is a development server. Do not use it in a production deployment.
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Running on http://172.22.0.3:5000/ (Press CTRL+C to quit)
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Restarting with stat
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  | WARNING:werkzeug: * Debugger is active!
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary1-1  | INFO:werkzeug: * Debugger PIN: 780-339-733
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  | WARNING:werkzeug: * Debugger is active!
		iteration_1_ucu_task_stavniichuk_ver2_15oct-secondary2-1  | INFO:werkzeug: * Debugger PIN: 104-499-142
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Debugger is active!
		iteration_1_ucu_task_stavniichuk_ver2_15oct-master-1      |  * Debugger PIN: 193-538-795





**Send a message and receive ACK**

	curl -X POST -H "Content-Type: application/json" -d '{"message":"Test to secondary!"}' http://localhost:5001/replicate


**Check ACK here**

[http://localhost:5001/messages
](http://localhost:5001/messages)


	{
	  "messages": [
	    "Test to secondary!", 
	    "Test to secondary 2!"
	  ]
	}


Same with [http://localhost:5002/messages](http://localhost:5002/messages)

In the terminal: 

	 curl -X POST -H "Content-Type: application/json" -d '{"message":"Test to secondary 22!"}' http://localhost:5002/replicate

Check results here: 

	http://localhost:5002/messages

###How I did it:


"""
Secondary servers should expose an HTTP API that supports GET methods and a replication endpoint for the Master to POST messages to.

When a message is received from the Master, it should be added to the Secondary's log and an ACK should be sent back.

Ensure that the secondary server is running on the port specified in your master server code (5001 in this case).


Secondary Server: The secondary server(s) are meant to replicate the data from the master server. If you're running the secondary server on the same machine as the master server, it needs to use a different port. In the example, it's set to run on port 5001

"""

"""
Secondary servers should expose an HTTP API that supports GET methods and a replication endpoint for the Master to POST messages to.
When a message is received from the Master, it should be added to the Secondary's log and an ACK should be sent back.

Ensure that the secondary server is running on the port specified in your master server code (5001 in this case).


**Secondary Server:** The secondary server(s) are meant to replicate the data from the master server. If you're running the secondary server on the same machine as the master server, it needs to use a different port. In the example, it's set to run on port 5001




	Localhost =  http://127.0.0.1
	
	http://localhost:5001/messages = http://127.0.0.1:5000/messages



"""
This is the application that you interact with to post new messages and get all messages.
"""


> * http://127.0.0.1:5000/messages
> * http://127.0.0.1:5000/messages -- for testing purposes