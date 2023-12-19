from threading import Thread, Event
from queue import Queue
import requests
import time
from flask import Flask, request, jsonify
import requests
from threading import Thread
import time
from threading import Event
import logging

app = Flask(__name__)
log = []

secondaries = ["http://secondary1:5001", "http://secondary2:5002"]
ack_events = Queue()  # This queue will hold events for each replication attempt


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
    backoff_factor = 2  # Determines the rate of increase for backoff -- added in log-3 version -- Timeouts
    for attempt in range(1, max_attempts + 1):
        # Add a try-except block to handle network errors
        try:
            # Post the message to the secondary's replication endpoint with the message to be replicated.
            response = requests.post(f"{secondary}/replicate", json=seq_message, timeout=5) # json={'message': message},
            #response = requests.post(f"{secondary}/replicate", json=seq_message, timeout=5)
            if response.status_code == 200:
                # If the replication was successful, add the secondary to the list of ACKs and exit the loop.
                acks.append(secondary)
                #break  # Exit the loop if successful ????? why not this -- chech Timeouts
                return  # Successful replication, exit function
            else:
                # Log the error but don't exit, to allow for retries
                app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")

        except requests.RequestException as e:
            # Log communication errors
            app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")

        except Exception as e:
            logging.error(f"An error occurred in replication: {str(e)}")


        # Exponential backoff: wait longer after each failed attempt
        time.sleep(backoff_factor ** attempt)

        # Wait before retrying with an exponential backoff strategy
        #time.sleep(2 ** attempt)

    # If the loop completes without a break, then replication has failed after max_attempts
    if len(acks) < required_acks:
        app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")



def wait_for_acks(acks, required_acks, timeout=30):
    """
    Waits for a specified number of acknowledgments from secondary nodes.

    Args:
        acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.
        required_acks (int): The number of acknowledgments required for the write operation to be considered successful.
        timeout (int): The maximum time to wait for the required acknowledgments.

    Returns:
        bool: True if the required number of acks is received within the timeout, False otherwise.


    Why it's not ok for log-3 version? =>
    The wait_for_acks function is used to wait synchronously for the required number of ACKs. 
    This means the function will block (i.e., wait without doing anything else) 
    until the required number of ACKs is received or until a timeout occurs.
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


# Global log to keep all messages
# Maintain a log of messages on the master node, which keeps a record of all messages sent, not just the latest.
full_log = []

# Global variable to track the next sequence number
next_seq_num = 0 # it was 1


@app.route('/messages', methods=['POST'])
def post_message():
    global next_seq_num

    try:
        message = request.json['message']
        write_concern = int(request.json.get('w', 1))

        seq_num = next_seq_num
        
        #seq_message = {'seq_num': seq_num, 'message': message}
        seq_message = {'sequence_number': seq_num, 'message': message}
        next_seq_num += 1

        full_log.append(seq_message)  #  full_log is a global list

        if seq_message not in log:
            log.append(seq_message)

        #ack_events_list = []

        acks = []  # Initialize the list to keep track of ACKs from secondaries
        ack_events_list = [] # Initialize the list to keep track of events for each replication attempt

        for secondary in secondaries:
            ack_event = Event()
            ack_events.put(ack_event)
            ack_events_list.append(ack_event)

            # Pass the required_acks argument to the replicate_to_secondary function
            #replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event, write_concern))
            #replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event))
            #replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event, write_concern))
            replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, acks, write_concern))
            #replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, acks, write_concern))

            replication_thread.start()

        acks_received = 0
        while acks_received < write_concern:
            ack_event = ack_events.get()
            ack_event.wait()
            acks_received += 1

        return jsonify({'status': 'success', 'message': 'Message replicated with required write concern'}), 200

    except Exception as e:
        #logging.error(f"An error occurred: {str(e)}")
        return jsonify({'status': 'fail', 'message': str(e)}), 500


# @app.route('/messages', methods=['POST']) # # message is an endpoint http://localhost:5000/messages
# def post_message():
#     """
#     The post_message() function will be called when a POST request is made to the /messages endpoint.
#     This is the declaration of a route in your Flask application. 
#     @app.route is a decorator that tells Flask that this function should be called when a POST request is made to the /messages endpoint.

    
#     This function handles POST requests to replicate messages to secondary nodes. 
#     It uses a non-blocking approach where each replication attempt is done in a separate thread, 
#     and the main thread waits for acknowledgments (using events) to ensure the required write concern level is met
#     before responding to the client.


#     Handles incoming POST requests to replicate messages to secondary nodes.

#     """
#     # This line extracts the 'message' value from the JSON body of the request.
#     # When a client sends a POST request to this endpoint with a JSON payload, this line retrieves the part of that payload tagged 'message'.
    
#     global next_seq_num  # To modify the global variable

#     try:
#         message = request.json['message']  
#         # This line gets the 'w' value from the JSON body, which represents the write concern (the number of acknowledgments needed from secondaries).
#         write_concern = int(request.json.get('w', 1))

#         ## Ordering of messages
#         # Assign a sequence number to the message
#         # Each message is assigned a sequence number, which is incremented for each message. 
#         # The next_seq_num variable is used to keep track of the next sequence number.
#         seq_num = next_seq_num
#         next_seq_num += 1  # Increment for the next message

#         # Combine the message with its sequence number
#         seq_message = {'seq_num': seq_num, 'message': message}

#         # Append the message to the full log
#         full_log.append(message)

#         # Check for duplication +
#         if message not in log:
#             log.append(message)  # Append only if message is unique

#         # to keep track of events for each replication attempt
#         ack_events_list = []

#         # Start replication threads and create an event for each
#         # Run through  ["http://secondary1:5001", "http://secondary2:5002"]
#         for secondary in secondaries:
#             # For each secondary node, an Event object is created. 
#             ack_event = Event()
#             ack_events.put(ack_event) # add the event to the queue. This queue is used to keep track of all the events.
#             ack_events_list.append(ack_event) # The same event is also added to the ack_events_list. This list is a local collection of events for this specific request.
#             #                                                                secondary, seq_message, acks, required_acks
#             #replication_thread = Thread(target=replicate_to_secondary, args=(secondary, message, ack_event)) # The replication_thread is started for each secondary node.
#             #replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event))
#             replication_thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, ack_event, write_concern))
#             replication_thread.start() # This line starts the thread, beginning the replication process for each secondary node.

#         # Now we wait for the required number of acks
#         acks_received = 0 # A counter is initialized to track the number of successful replications that have occurred.
#         while acks_received < write_concern: # This while loop will keep running until the number of received acknowledgments meets the write concern level
#             ack_event = ack_events.get()  # The loop fetches an event from the ack_events queue. This is a blocking call; it will wait here until an event is available.
#             ack_event.wait()  # Wait for the event to be set
#             acks_received += 1

#         # If we get here, we have received the required number of acks
#         # After the loop exits (meaning the required number of acknowledgments has been received), the function sends a JSON response indicating success, along with an HTTP 200 status code.
#         return jsonify({'status': 'success', 'message': 'Message replicated with required write concern'}), 200
    
#     except Exception as e:
#         #logging.error(f"An error occurred: {str(e)}")
#         return jsonify({'status': 'fail', 'message': str(e)}), 500


# Added in log-3 version: sync mechanism on reconnection
@app.route('/sync', methods=['POST'])
def sync_node():
    """
    Endpoint for syncing a secondary node with missed messages.
    It handles the synchronization of missed messages for a secondary node that has been offline or disconnected. 
    
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


@app.route('/health', methods=['GET'])
def health_check():
    """
    http://localhost:5000/health -- check if the service is up
    """
    return "Service is up", 200

@app.route('/', methods=['GET'])
def home():
    """
    With this route, visiting http://127.0.0.1:5000/ in your browser will display the message "Welcome to the Master Server!" instead of a 404 error.
    Or http://localhost:5000/
    """
    return "Welcome to the Master Server!", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
