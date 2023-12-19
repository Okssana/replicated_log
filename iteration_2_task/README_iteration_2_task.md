
###### secondary1.py and secondary2.py are different, is it right?

Yes, based on the information provided and the modifications suggested, `secondary1.py` and `secondary2.py` would have different implementations, particularly in *how they handle the replication and manage message logs. T*he differences reflect the specific requirements and functionalities you want to achieve in each secondary node.v.3

Here are the key differences:

1. **Artificial Delay** : Both scripts introduce an artificial delay to simulate asynchronous behavior and eventual consistency, but this delay can be configured differently in each script using an environment variable. This allows you to test different delay scenarios in your replicated system.
2. **Message Deduplication** : Both scripts include logic to prevent the duplication of messages in their respective logs. This ensures that even if the same message is sent multiple times to a secondary, it is only stored once.
3. **Total Ordering of Messages in `secondary2.py`** : The `secondary2.py` script has an additional mechanism to ensure the total ordering of messages. It uses a timestamp check to ensure that messages are appended to the log in the order they are received. This feature is specifically designed to handle scenarios where network delays might cause messages to arrive out of order.
4. **Response Behavior on Message Receipt** : The `secondary2.py` script includes additional checks and responses, such as returning an error if a message is received out of order. This is part of its mechanism to maintain total ordering.
5. **Logging and Error Handling** : Both scripts include logging and error handling, but the exact implementation and the level of detail in the logs can vary based on the specific needs of each secondary service.

These differences are tailored to your requirements for iteration 2 of your task, focusing on semi-synchronous replication with tunable parameters (like the write concern in the master and artificial delay in the secondaries) and ensuring data consistency and ordering. If there are any specific functionalities that you want to be uniform across both `secondary1.py` and `secondary2.py`, or if there are additional features you want to implement, please let me know!


## Testing

* In the folder where your `docker-compose.yml` file is located. Step by step

```bash
docker-compose build

docker-compose up
```

This command will start all the services (master, secondary1,
secondary2) defined in the Docker Compose file. Make sure they all start
 up without errors.

Visit `http://localhost:5000/health to check the status `


### Functional Testing

**Send a POST request to the master service** with a message and check if it gets replicated to the secondary services.

```bash
curl -X POST http://localhost:5000/messages -H "Content-Type: application/json" -d '{"message": "Your test message", "w": 2}'
```

Response was:

```
{"message":"Message replicated with required write concern","status":"success"}
```


**Second check**

`curl -X POST -H "Content-Type: application/json" -d '{"message":"Your test message to check 5000 and w 1", "w": 2}' http://localhost:5001/replicate`

**`{"status":"ACK"}`**

More:

` curl -X POST -H "Content-Type: application/json" -d '{"message":"Your test message to check 5000 and w 1", "w": 3}' http://localhost:5001/replicate`



Your test POST request to the master service appears to have been successful. The response `{"message":"Message replicated with required write concern","status":"success"}` indicates that the master service has processed your request and replicated the message according to the write concern level specified (`"w": 1`).

In this case, a write **concern of `1` **means the **master did not wait for acknowledgments (ACKs)** from any secondary services before responding. It only ensured that the message was processed on the master itself.


**w value specifies how many ACKs the master should receive from secondaries before responding to the client**

* w = 1 - only from master
* w = 2 - from master and one secondary
* w = 3 - from master and two secondaries

### Levels of Write Concerns

The value of the write concern (`w`) determines how many nodes must acknowledge the write operation:

* **`w = 1`** : The write operation is considered successful as soon as the master node has written the data. There's no need to wait for any secondary nodes to replicate the data.
* **`w = 2`** : The write operation is considered successful only after both the master node and at least one secondary node have successfully written the data.
* **`w = 3`, `w = n`** : This continues similarly, increasing the number of nodes that must acknowledge the write operation before it is considered successful.


### Implications of Different Write Concerns

* **Higher Write Concern (`w > 1`)** : This provides stronger guarantees of data durability and consistency. If a write operation is acknowledged, you can be more confident that multiple nodes have the data. However, this can lead to increased latency for write operations, as the system needs to wait for multiple nodes to respond.
* **Lower Write Concern (`w = 1`)** : This offers faster write operations since the system doesn't wait for multiple nodes to confirm. However, it comes with a higher risk of data loss if the master node fails immediately after the write operation, before the data is replicated to secondary nodes.

**Repeat with Different `w` Values** :







***But if I go to http://localhost:5000/messages in my browser I can see only "Method Not Allowed. The method is not allowed for the requested URL."*** Is it ok behaviour?
