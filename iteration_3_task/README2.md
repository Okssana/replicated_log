**What to add?**

1. **Retry Mechanism for Message Delivery**

Implement a retry mechanism in the master service (master.py) to handle cases where message delivery fails. This involves:

* Catching exceptions related to connection errors or server unavailability.
* Retrying the delivery to the secondary node(s) until it succeeds.
* Implementing a "smart" delay logic between retries to avoid overwhelming the network or the secondary nodes.

**Retry Mechanism** : Your current implementation does not
have a retry mechanism. If the replication to a secondary fails, it does
 not attempt to resend the message. You would need to add a loop or a
recursive call within `replicate_to_secondary` to handle retries with a back-off strategy.

Do you mean I have to imprive and add try and except to this function

defreplicate_to_secondary(secondary,message,acks,required_acks):

"""It handles the replication of a message from the master to a secondary node in a distributed system.

    Args:

    secondary : The URL of the secondary node to which the message is to be replicated.

    message :  The message that needs to be replicated.

    acks : A list that keeps track of which secondary nodes have successfully acknowledged the replication.

    required_acks : The number of acknowledgments required for the write operation to be considered successful (part of write concern).

"""

try:

response=requests.post(f"{secondary}/replicate",json={'message':message})

ifresponse.status_code==200:

acks.append(secondary)

else:

app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")

exceptrequests.RequestExceptionase:

app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")

---

**Blocking Writes with Write Concern `w=3`** : The `wait_for_acks`
 function does block until the required number of acknowledgments is
received, but it does not handle the case where a node is down (it will
simply time out after 10 seconds). You would need to implement a more
sophisticated waiting mechanism that can block indefinitely until the
node is available again.

he `wait_for_acks` function you've shown is indeed
responsible for waiting until the required number of acknowledgments
(ACKs) are received or until a timeout occurs. The function as written
will only wait for a maximum of 10 seconds before giving up. Here's a
potential issue and improvement for this function:

```python

def wait_for_acks(acks, required_acks):
    # Wait until the required number of ACKs are received or a timeout occurs
    start_time = time.time()
    while len(acks) < required_acks and (time.time() - start_time) < 10:
        time.sleep(0.1)  
  
    return len(acks) >= required_acks

```

**Improved version:**

The `wait_for_acks` function you've shown is indeed responsible for waiting until the required number of acknowledgments (ACKs) are received or until a timeout occurs. The function as written will only wait for a maximum of 10 seconds before giving up. Here's a potential issue and improvement for this function:

### Potential Issue:

If the `required_acks` is not met within 10 seconds, the function returns `False`, potentially before all replication attempts have completed. This could happen if the secondary nodes are slow to respond or temporarily unreachable.

### Improvement:

To handle scenarios where secondaries are down and `required_acks` is more than 1 (e.g., `w=3`), the function needs to be able to wait indefinitely (or for a much longer configured time) until the secondaries are back up and have acknowledged the replication. Additionally, this waiting should not block other incoming client requests, which requires asynchronous handling of the replication process.

### Explanation:

* We use an `Event` from the `threading` module, which allows one thread to signal an event while other threads wait for that event to occur.
* A background thread (`ack_waiter`) checks for the required number of ACKs in a loop.
* The main thread waits for the event to be set (indicating that the required number of ACKs has been received) or for the timeout to expire, whichever comes first.
* The `wait()` method on the `Event` object is used to block until the required ACKs are received or until the timeout period is over. This method does not actively consume CPU resources while waiting because it's designed to wait efficiently.

Note: The `timeout` value is set to a default of 30 seconds, but you can adjust this based on your system's needs. If you need to wait indefinitely, you could omit the timeout or set it to `None`. However, in a real-world scenario, you would typically want to have a reasonable timeout to handle cases where a secondary node might be down for an extended period.

Here’s an enhanced version of the `wait_for_acks` function that waits longer and does not block other operations:

```python
from threading import Event

def wait_for_acks(acks, required_acks, timeout=30):
    """
    Waits for a specified number of acknowledgments from secondary nodes.

    Args:
        acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.
        required_acks (int): The number of acknowledgments required for the write operation to be considered successful.
        timeout (int): The maximum time to wait for the required acknowledgments.

    Returns:
        bool: True if the required number of acks is received within the timeout, False otherwise.
    """
    wait_event = Event()

    # Check if the required ACKs are already present
    if len(acks) >= required_acks:
        return True

    # Start a background thread to wait for ACKs
    def ack_waiter():
        while len(acks) < required_acks:
            time.sleep(0.1)
        wait_event.set()  # Signal that the required ACKs have been received

    Thread(target=ack_waiter).start()
    # Wait for the required ACKs to be received or for the timeout
    is_acked = wait_event.wait(timeout)
    return is_acked

```

---

**Non-blocking Parallel Writes** : The code does not show
any explicit handling of parallel client requests. However, since Flask
handles each request in a separate thread, clients are naturally not
blocked by each other unless you introduce global locks or other
blocking mechanisms.

### Explanation:

To address the requirement of non-blocking parallel writes in your master service while ensuring that write concerns are respected, you'll need to modify your `master.py` code to handle replication and acknowledgment checking in a way that doesn't block the Flask server's ability to handle incoming requests. Let's simplify the problem and then provide a solution:

### The Problem Simplified:

1. **Clients Waiting** : When a client sends a message to the master with a write concern (`w`), the client needs to wait until the required number of secondaries have acknowledged the message.
2. **Clients Not Blocking Each Other** : While one client is waiting, other clients should still be able to send their messages and get responses without being delayed by the first client's wait.

### Solution Steps:

1. **Asynchronous Handling** : Use an asynchronous approach to handle the acknowledgment waiting process. This way, the Flask thread that handles a client request can start the replication process and then immediately free up to handle another request.
2. **Background Processing** : Perform the acknowledgment waiting in a background process or thread, which can independently monitor the secondaries' acknowledgments without blocking the main server thread.
3. **Communication Between Threads** : Use thread-safe mechanisms such as threading events or queues to communicate the status of the acknowledgments between the background process and the main server thread.

### Code Implementation:

Here's how you can modify your `replicate_to_secondary` function and add a new function for waiting for acknowledgments in a non-blocking manner:

```python
from threading import Thread, Event
from queue import Queue
import requests
import time

# ... (Other parts of your Flask app)

ack_events = Queue()  # This queue will hold events for each replication attempt

def replicate_to_secondary(secondary, message, ack_event):
    """
    Attempts to replicate a message to a secondary node. Signals an event when done.
  
    Args:
        secondary (str): The URL of the secondary node.
        message (str): The message to replicate.
        ack_event (Event): An event to signal when the secondary has acknowledged.
    """
    try:
        response = requests.post(f"{secondary}/replicate", json={'message': message})
        if response.status_code == 200:
            ack_event.set()  # Signal successful replication
        else:
            app.logger.error(f"Replication failed for {secondary}. Status: {response.text}")
    except requests.RequestException as e:
        app.logger.error(f"Communication failed with {secondary}. Error: {str(e)}")

@app.route('/messages', methods=['POST'])
def post_message():
    message = request.json['message']
    write_concern = int(request.json.get('w', 1))
    ack_events_list = []

    # Start replication threads and create an event for each
    for secondary in secondaries:
        ack_event = Event()
        ack_events.put(ack_event)
        ack_events_list.append(ack_event)
        replication_thread = Thread(target=replicate_to_secondary, args=(secondary, message, ack_event))
        replication_thread.start()

    # Now we wait for the required number of acks
    acks_received = 0
    while acks_received < write_concern:
        ack_event = ack_events.get()  # Get the next event
        ack_event.wait()  # Wait for the event to be set
        acks_received += 1

    # If we get here, we have received the required number of acks
    return jsonify({'status': 'success', 'message': 'Message replicated with required write concern'}), 200

# ... (The rest of your Flask app)

```

---

**Replicating Missed Messages** : There's no mechanism to
catch up missed messages when a secondary node rejoins the cluster. You
would need to implement a way for secondaries to sync up with the
master's log upon reconnection.

The "Replicating Missed Messages" feature is crucial for maintaining
data consistency across your distributed system. Here's what it entails:

* **Scenario** : A secondary node might go offline or become temporarily unavailable due to network issues, maintenance, etc. During this downtime, it misses out on messages replicated from the master.
* **Challenge** : When the secondary node comes back online, it needs to catch up with all the messages it missed.
* **Solution** : Implement a mechanism for the secondary node to synchronize its log with the master's log upon reconnection.

### Checking Your Current Code

Your current `master.py` code, based on the snippets you've provided, does not seem to include a mechanism for handling this scenario. The master sends messages to secondaries as they come, but there's no process for updating a secondary that has been offline with the missed messages.

### Implementing the Feature

To implement this, you'll need to:

1. **Track Message History** : Maintain a log of messages on the master node, which keeps a record of all messages sent, not just the latest.
2. **Sync Mechanism on Reconnection** : When a secondary node reconnects, it should either request the missed messages from the master or the master should automatically start a synchronization process.

### Sample Code Implementation

Here's a conceptual implementation. This assumes your secondary nodes can communicate back to the master when they come online and request missed messages:

#### On the Master Node:

```python
# Global log to keep all messages
full_log = []

@app.route('/messages', methods=['POST'])
def post_message():
    # ... [existing code to handle message replication]
    # Append the message to the full log
    full_log.append(message)
    # ... [rest of your function]

@app.route('/sync', methods=['POST'])
def sync_node():
    """
    Endpoint for syncing a secondary node with missed messages.
    """
    secondary_url = request.json.get('secondary_url')
    last_known_msg = request.json.get('last_known_msg')
  
    # Find the index of the last known message in the full log
    try:
        last_index = full_log.index(last_known_msg) + 1
    except ValueError:
        # If the message is not found, start from the beginning
        last_index = 0

    # Send all messages from the last known index
    missed_messages = full_log[last_index:]
    for message in missed_messages:
        replicate_to_secondary(secondary_url, message, acks=[], required_acks=1)

    return jsonify({'status': 'success', 'message': 'Node synced'}), 200

```

#### On the Secondary Node:

When a secondary node comes back online, it would need to:

1. Determine the last message it successfully received.
2. Send a request to the master's `/sync` endpoint with its last known message.

### Simple Explanation

Think of your system as a group chat. When someone's phone is off, they miss out on messages. When they turn their phone back on, they need to catch up on what they missed. In your system, the master node is like the chat server that keeps track of all messages. When a secondary node (like the phone) comes back online, it asks the server, "What did I miss?" The server then sends all the messages that the secondary missed while it was offline.

This way, every node in your system stays updated with all the messages, ensuring data consistency across your distributed system.

*So this implemented using def sync_node():?*

Yes, the `sync_node` function in the master service is designed to handle the synchronization of missed messages for a secondary node that has been offline or disconnected. Here's how it works:

1. **Triggering Sync** : When a secondary node comes back online, it should determine the last message it successfully received and then make a request to the master's `/sync` endpoint, providing information about its last known state.
2. **Functionality of `sync_node`** :

* The function receives this request, which includes the last message the secondary node knows about.
* It locates where this message is in the master's full log of messages.
* If the message is found, the function calculates which messages the secondary node missed.
* The master then replicates these missed messages to the secondary node to update its log.

1. **Purpose** : This synchronization ensures that the secondary node's log is consistent with the master's log, even after a period of disconnection or unavailability.
2. **Endpoint on Master** : The `/sync` endpoint on the master is specifically for secondary nodes to catch up on missed messages.

### Example Scenario:

1. **Secondary Node Offline** : Let's say Secondary Node A goes offline after receiving `Msg1` and `Msg2`.
2. **Master Continues to Work** : While Node A is offline, the master receives and logs `Msg3`, `Msg4`, and `Msg5`.
3. **Node A Reconnects** : When Node A comes back online, it knows `Msg2` was the last message it received.
4. **Sync Request** : Node A sends a request to the master's `/sync` endpoint with `Msg2` as its last known message.
5. **Master Responds** : The master finds `Msg2` in its log and identifies `Msg3`, `Msg4`, and `Msg5` as the missed messages. It then sends these messages to Node A.

By implementing this syncing process, you ensure that all nodes in your system eventually have a complete and consistent set of messages, aligning with the principles of distributed systems and eventual consistency.

---

**Deduplication** : The master's log does not deduplicate
messages. If the same message is sent multiple times, it will be
appended to the log multiple times. Deduplication logic needs to be
added.

### What is Deduplication?

* **Deduplication** means preventing the same message from being stored more than once in your log.
* It's like a diary where you don't want to write down the same event twice.

### Problem in Your Code:

* Currently, your code appends every incoming message to the log, regardless of whether it's a duplicate.

### Solution Steps:

1. **Check for Duplicates** : Before appending a message, check if it's already in the log.
2. **Append Only Unique Messages** : Only append the message if it's not a duplicate.

### Code Implementation:

Let's modify the `post_message` function in your `master.py`:

```python

@app.route('/messages', methods=['POST'])
def post_message():
    """
    Handles incoming POST requests to replicate messages to secondary nodes.
    """
    try:
        message = request.json['message']
        write_concern = int(request.json.get('w', 1))  # Default write concern is 1

        # Check for duplication
        if message not in log:
            log.append(message)  # Append only if message is unique
  
        # The rest of your existing replication logic
        # ...

        # Assuming you have a replication mechanism here
        # ...

        return jsonify({'status': 'success', 'message': 'Message processed'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

```

### Explanation of Each Line:

1. `@app.route('/messages', methods=['POST'])`: This line sets up a route in your Flask app that listens for POST requests at the `/messages` endpoint.
2. `def post_message()`: Defines the function `post_message` that will be executed when the `/messages` endpoint is accessed.
3. `try:`: Begins a try block to catch any exceptions that may occur in the function for error handling.
4. `message = request.json['message']`: Extracts the 'message' part of the JSON payload from the incoming POST request.
5. `write_concern = int(request.json.get('w', 1))`: Retrieves the 'w' value (write concern level) from the request. If 'w' is not specified, it defaults to 1.
6. `if message not in log:`: Checks if the received message is already in the log.
7. `log.append(message)`: If the message is not a duplicate, it is appended to the log.
8. `# The rest of your existing replication logic`: Placeholder for your existing logic to replicate the message to secondary nodes.
9. `return jsonify(...), 200`: Sends a JSON response back to the client, indicating success.
10. `except Exception as e`: Catches any exceptions that occur during the function execution.
11. `return jsonify(...), 500`: Sends a JSON response back to the client in case of an error, indicating failure.

### Simple Explanation:

When your server receives a message, it first checks if it has seen this message before. If it's a new message, **it adds it to its list (log) and then follows the process to replicate it to secondary servers.** If the message is an old one (a duplicate), it doesn't add it to the list again. This way, your log doesn't have the same message multiple times.

By implementing this deduplication, you ensure the integrity of your data and prevent unnecessary replication of the same information.

---

**Total Ordering of Messages** : There is no explicit ordering mechanism in place. While the Flask service will naturally process requests in the order they're received, without a more robust ordering system (like a monotonically increasing sequence number), you *can't guarantee total order across all nodes,* especially in the face of retries and node failures.

To implement total ordering of messages in your master service, we'll need to ensure that messages are processed and replicated in the exact order they are received. This is important to maintain consistency across all nodes in your distributed system.

### Concept of Total Ordering

* **Total Ordering** : It means that all nodes in your system agree on the order of the messages.
* Think of it as writing entries in a diary. Even if you tell others about your day in a different order, everyone should be able to write these events in the same order in their diaries.

### Implementing Total Ordering

We'll use a sequence number to track the order of messages:

1. **Add a Sequence Number to Each Message** : When the master receives a message, it assigns a sequence number to it. This number is incremented for each new message.
2. **Replicate the Message with Its Sequence Number** : Send this sequence number along with the message to the secondary nodes.
3. **Secondary Nodes Process Messages in Sequence** : Each secondary node ensures that it processes messages in the order of their sequence numbers.

### Code Implementation in `master.py`

First, we'll modify the `post_message` function:

```python
# Global variables
next_seq_num = 1
full_log = []  # Assuming this is defined somewhere in your code

@app.route('/messages', methods=['POST'])
def post_message():
    global next_seq_num  # Access the global sequence number

    try:
        message = request.json['message']
        write_concern = int(request.json.get('w', 1))

        # Assign a sequence number to the message
        seq_num = next_seq_num
        next_seq_num += 1  # Increment for the next message

        # Combine the message with its sequence number
        seq_message = {'seq_num': seq_num, 'message': message}

        # Append the combined message to the full log (for synchronization purposes)
        full_log.append(seq_message)

        # Check for duplication in the basic log
        if message not in log:
            log.append(message)  # Append only if message is unique

        ack_events_list = []
        for secondary in secondaries:
            ack_event = Event()
            ack_events.put(ack_event)
            ack_events_list.append(ack_event)
            replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event))
            replication_thread.start()

        acks_received = 0
        while acks_received < write_concern:
            ack_event = ack_events.get()
            ack_event.wait()
            acks_received += 1

        return jsonify({'status': 'success', 'message': 'Message replicated with required write concern'}), 200

    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500


```

### Explanation of New/Modified Lines:

* `seq_num = next_seq_num`: Assigns the next available sequence number to the current message.
* `next_seq_num += 1`: Increments the sequence number for the next message.
* `seq_message = {'seq_num': seq_num, 'message': message}`: Combines the message with its sequence number in a dictionary.
* `full_log.append(seq_message)`: Appends the combined message (with sequence number) to `full_log` for synchronization purposes. The `full_log` should contain all messages with their sequence numbers.
* `replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event))`: Modifies the thread to replicate the combined message (including the sequence number).

### Simple Explanation:

* Each message gets a unique number (like a ticket number) when it arrives.
* This number is attached to the message.
* The message, along with its number, is stored and sent to other servers.
* This helps all servers keep messages in the same order.

### Note:

* Ensure that the `replicate_to_secondary` function and the secondary nodes' handling code are updated to work with the combined message (with sequence numbers).
* I updated replicate_to_secondary(secondary,seq_message,acks,required_acks) -- small changes:

  `seq_message` instead of message and `json=seq_message`

  ```python
  def replicate_to_secondary(secondary, seq_message, acks, required_acks):
      """
      Handles the replication of a message from the master to a secondary node in a distributed system,
      with retries in case of failure.

      In log-3 version try and except is added to the function. Max attempts is 9.

      Args:
          secondary (str): The URL of the secondary node to which the message is to be replicated.
          seq_message (dict): The message and its sequence number that needs to be replicated. It's a dictionary with 'seq_num' and 'message'.
          acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.
          required_acks (int): The number of acknowledgments required for the write operation to be considered successful (part of write concern).
      """
      max_attempts = 9
      for attempt in range(1, max_attempts + 1):
          # Add a try-except block to handle network errors
          try:
              # Post the message to the secondary's replication endpoint with the message to be replicated.
              response = requests.post(f"{secondary}/replicate", json=seq_message, timeout=5) # json={'message': message},
              if response.status_code == 200:
                  # If the replication was successful, add the secondary to the list of ACKs and exit the loop.
                  acks.append(secondary)
                  break  # Exit the loop if successful
              else:
                  app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")

          except requests.RequestException as e:
              app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")

          # Wait before retrying with an exponential backoff strategy
          time.sleep(2 ** attempt)

      # If the loop completes without a break, then replication has failed after max_attempts
      if len(acks) < required_acks:
          app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")span
  ```
* Secondary nodes should use the sequence number to maintain the order of messages.

---

**Timeouts** : There is a timeout mechanism in `wait_for_acks`, but it's a fixed timeout of 10 seconds. This could be improved with a configurable timeout passed as a parameter.

Let's tackle the implementation of a key feature in your distributed system: **handling retries with exponential backoff** in the `replicate_to_secondary` function. This feature is critical for ensuring reliable communication between the master and secondary nodes, especially in cases of temporary network issues or secondary node failures.

### What is Exponential Backoff with Retries?

* **Exponential Backoff** is a strategy where the time between retry attempts increases exponentially. This approach is used to avoid overwhelming the network or the secondary node.
* **Retries** refer to the process of attempting the same operation (in this case, message replication) multiple times in case of failures.

### Updating the `replicate_to_secondary` Function:

We will modify this function to implement retries with exponential backoff. I'll explain each part of the code for clarity.

```python
import requests
import time
from requests.exceptions import RequestException

def replicate_to_secondary(secondary, seq_message, acks, required_acks):
    """
    Attempts to replicate a sequenced message to a secondary node with retries.
  
    Args:
        secondary (str): The URL of the secondary node.
        seq_message (dict): The message and its sequence number.
        acks (list): Tracks which secondary nodes have acknowledged replication.
        required_acks (int): Required number of acknowledgments for success.
    """
    max_attempts = 9
    backoff_factor = 2  # Determines the rate of increase for backoff

    for attempt in range(max_attempts):
        try:
            response = requests.post(f"{secondary}/replicate", json=seq_message, timeout=5)
            if response.status_code == 200:
                acks.append(secondary)
                return  # Successful replication, exit function
            else:
                # Log the error but don't exit, to allow for retries
                app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")

        except RequestException as e:
            # Log communication errors
            app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")

        # Exponential backoff: wait longer after each failed attempt
        time.sleep(backoff_factor ** attempt)

    # If all attempts fail, log an error
    app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")

```

### Explanation:

1. **Function Definition** : We define `replicate_to_secondary` with necessary arguments, including the sequenced message and tracking for acknowledgments.
2. **Retry Parameters** : `max_attempts` and `backoff_factor` determine how many times to retry and how much to wait between retries, respectively.
3. **For Loop for Retries** : We loop up to `max_attempts` times to try replicating the message.
4. **Attempt Replication** : Within each loop iteration, we attempt to POST the message to the secondary node.
5. **Check Response** : If the secondary node acknowledges successfully (`response.status_code == 200`), we add it to `acks` and exit the function.
6. **Handle Failures** : If the POST fails, we log the error and proceed to the next iteration of the loop for a retry, rather than exiting the function.
7. **Exponential Backoff** : After each failed attempt, we wait for an increasing amount of time (`time.sleep(backoff_factor ** attempt)`), which helps in case the secondary node is temporarily unavailable or overloaded.
8. **All Attempts Failed** : If all retry attempts fail, we log a final error message.

### Simple Explanation:

Imagine you're trying to deliver a letter to a friend's house, but they're not home. You don't want to just leave the letter outside, so you decide to come back later and try again. Each time you return, you wait a bit longer before the next attempt, hoping they'll be back soon. After several tries, if they're still not back, you might decide to stop trying for the day.

In this code, each "visit" is like a retry attempt to send a message to a secondary server. If the server doesn't respond, the code waits a bit longer each time before trying again. This helps to avoid constantly bothering the server, giving it time to recover if it's temporarily down or busy.

---

**Heartbeats and Quorum Append** : These features are not
implemented in your code. Heartbeats are usually periodic signals sent
to check node status, and quorum append requires a majority of nodes to
acknowledge writes, which is more sophisticated than the simple write
concern mechanism you currently have.

defreplicate_to_secondary(secondary,seq_message,acks,required_acks):

"""

    Handles the replication of a message from the master to a secondary node in a distributed system,

    with retries in case of failure.

    In log-3 version try and except is added to the function. Max attempts is 9.

    Args:

    secondary (str): The URL of the secondary node to which the message is to be replicated.

    seq_message (dict): The message and its sequence number that needs to be replicated. It's a dictionary with 'seq_num' and 'message'.

    acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.

    required_acks (int): The number of acknowledgments required for the write operation to be considered successful (part of write concern).

"""

max_attempts=9

forattemptinrange(1,max_attempts+1):

# Add a try-except block to handle network errors

try:

# Post the message to the secondary's replication endpoint with the message to be replicated.

response=requests.post(f"{secondary}/replicate",json=seq_message,timeout=5)# json={'message': message},

ifresponse.status_code==200:

# If the replication was successful, add the secondary to the list of ACKs and exit the loop.

acks.append(secondary)

break# Exit the loop if successful

else:

app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")

exceptrequests.RequestExceptionase:

app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")

# Wait before retrying with an exponential backoff strategy

time.sleep(2**attempt)

# If the loop completes without a break, then replication has failed after max_attempts

iflen(acks)<required_acks:

app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")
