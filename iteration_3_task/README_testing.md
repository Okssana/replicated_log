
In the folder of the app (project) )you run: 

    **`docker-compose build`**

then you run

`	docker-compose up`




To test all the features implemented in the Log-3 version of your application using Docker, you'll need to simulate various scenarios that correspond to each feature. Here's a step-by-step guide on how to proceed:

### 1. Testing Message Replication and Write Concerns

1. **Send Messages with Different Write Concerns** :

* Use a tool like `curl` or Postman to send POST requests to the master node with different `w` (write concern) values.
* For example, send a message with `w=1`, which should return success immediately after being processed by the master.
* Then, try `w=2` or `w=3`, which should only return success after being acknowledged by the secondary nodes.

1. **Verify Replication** :

* After sending messages, use GET requests to each secondary to check if the messages have been replicated correctly.

### 2. Testing Retry Mechanism and Temporary Secondary Node Failure

1. **Simulate Secondary Node Failure** :

* Temporarily shut down one of the secondary services. You can do this by stopping the corresponding Docker container.

1. **Send Messages During the Downtime** :

* Continue to send messages to the master. The master should attempt to replicate to the offline secondary and retry based on your retry logic.

1. **Bring the Secondary Back Online** :

* After a short while, bring the secondary node back online by starting its Docker container again.

1. **Verify Message Catch-Up** :

* Once the secondary node is back, it should eventually receive all the messages it missed during the downtime.

### 3. Testing Deduplication and Total Order

1. **Send Duplicate Messages** :

* Send the same message multiple times to the master and verify that the secondary nodes do not store duplicates.

1. **Test Total Ordering** :

* Send messages in a specific order and ensure that all nodes maintain this order in their logs.

### 4. Check Health Endpoints

1. **Access Health Check Endpoints** :

* Send requests to the `/health` endpoints of both the master and secondary services to ensure they are functioning correctly.

### How to Use `curl` for Testing:

For sending POST requests, you can use `curl` like this:

```bash
curl -X POST http://localhost:5000/messages -H "Content-Type: application/json" -d '{"message": "Test Message", "w": 1}'
```

For getting messages from secondaries:

```
curl http://localhost:5001/messages
curl http://localhost:5002/messages
```


Replace `localhost` and port numbers with the appropriate values if different in your setup.

### Docker Commands to Control Services:

* To stop a container: `docker stop <container_name_or_id>`
* To start a container: `docker start <container_name_or_id>`

Remember, this testing will require you to monitor logs and responses closely to ensure each part of your system is behaving as expected under these different scenarios.
