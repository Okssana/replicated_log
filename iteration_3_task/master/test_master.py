from flask import Flask, request, jsonify
import requests
from threading import Thread
import time

app = Flask(__name__)
log = []

secondaries = ["http://secondary1:5001", "http://secondary2:5002"]


### Version-1
def replicate_to_secondary(secondary, message, acks, required_acks):
    """It handles the replication of a message from the master to a secondary node in a distributed system.

    Args:
        secondary : The URL of the secondary node to which the message is to be replicated.
        message :  The message that needs to be replicated.
        acks : A list that keeps track of which secondary nodes have successfully acknowledged the replication.
        required_acks : The number of acknowledgments required for the write operation to be considered successful (part of write concern).
    """

    try:
        response = requests.post(f"{secondary}/replicate", json={'message': message})
        if response.status_code == 200:
            acks.append(secondary)
        else:
            app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")


### Version-2 
def replicate_to_secondary(secondary, message, acks, required_acks):
    """
    Handles the replication of a message from the master to a secondary node in a distributed system,
    with retries in case of failure.

    In log-3 version try and except is added to the function. Max attempts is 9.

    Args:
        secondary (str): The URL of the secondary node to which the message is to be replicated.
        message (str): The message that needs to be replicated.
        acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.
        required_acks (int): The number of acknowledgments required for the write operation to be considered successful (part of write concern).
    """
    max_attempts = 9
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(f"{secondary}/replicate", json={'message': message}, timeout=5)
            if response.status_code == 200:
                acks.append(secondary)
                break  # Exit the loop if successful
            else:
                app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")
                # if attempt < attempt:
                #     time.sleep(2**attempt)
                #     replicate_to_secondary(secondary, message, acks, required_acks, attempt + 1)
        except requests.RequestException as e:
            app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")
            # if attempt < attempt:
            #     time.sleep(2**attempt)
            #     replicate_to_secondary(secondary, message, acks, required_acks, attempt + 1)
        
         # Wait before retrying with an exponential backoff strategy
        time.sleep(2 ** attempt)

         # If the loop completes without a break, then replication has failed after max_attempts
        if len(acks) < required_acks:
            app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")


### Version-2

"""
Problems here:
1)Recursive Calls: The function is calling itself recursively inside the for loop, 
which could lead to an excessive number of threads being spawned and potential stack overflow due 
to deep recursion if a secondary is persistently failing. 
Instead, you should rely on the loop to handle retries without recursion.


2)Condition in the Loop: The condition if attempt < attempt: 
will always be false because you are comparing the variable to itself. 
This condition should be removed, as the loop already ensures that the code will attempt to replicate up to 9 times.


Summary: 

In this version, the function attempts to replicate the message up to max_attempts times. 
It uses a loop to perform the retries with an exponential backoff delay (time.sleep(2 ** attempt)). 
If the replication is successful, it breaks out of the loop. 
If not, it logs an error after the maximum number of attempts is reached.

This function will no longer spawn additional threads on each retry, instead, 
it will simply wait a longer period of time before each subsequent retry attempt.
"""

def replicate_to_secondary(secondary, message, acks, required_acks):
    """
    Handles the replication of a message from the master to a secondary node in a distributed system,
    with retries in case of failure.

    Args:
        secondary (str): The URL of the secondary node to which the message is to be replicated.
        message (str): The message that needs to be replicated.
        acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.
        required_acks (int): The number of acknowledgments required for the write operation to be considered successful (part of write concern).
        attempt (int): The current attempt number for message replication.
    """
    # max_attempts = 5  # You can decide on the maximum number of attempts
    # delay = 2 ** attempt  # Exponential backoff strategy

    for attempt in range(1, 10):
        try:
            response = requests.post(f"{secondary}/replicate", json={'message': message}, timeout=5)
            if response.status_code == 200:
                acks.append(secondary)
            else:
                app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")
                # if attempt < attempt:
                #     time.sleep(2**attempt)
                #     replicate_to_secondary(secondary, message, acks, required_acks, attempt + 1)
        except requests.RequestException as e:
            app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")
            # if attempt < attempt:
            #     time.sleep(2**attempt)
            #     replicate_to_secondary(secondary, message, acks, required_acks, attempt + 1)

        # Wait before retrying with an exponential backoff strategy
        time.sleep(2 ** attempt)

    # If the loop completes without a break, then replication has failed after max_attempts
    if len(acks) < required_acks:
        app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")



### Version-3
# Check out the the following code snippet from master/master.py:
def replicate_to_secondary(secondary, message, acks, required_acks):
    """
    Handles the replication of a message from the master to a secondary node in a distributed system,
    with retries in case of failure.

    In log-3 version try and except is added to the function. Max attempts is 9.

    Args:
        secondary (str): The URL of the secondary node to which the message is to be replicated.
        message (str): The message that needs to be replicated.
        acks (list): A list that keeps track of which secondary nodes have successfully acknowledged the replication.
        required_acks (int): The number of acknowledgments required for the write operation to be considered successful (part of write concern).
    """
    max_attempts = 9
    for attempt in range(1, max_attempts + 1):
        # Add a try-except block to handle network errors
        try:
            # Post the message to the secondary's replication endpoint with the message to be replicated.
            response = requests.post(f"{secondary}/replicate", json={'message': message}, timeout=5)
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
        app.logger.error(f"Failed to replicate to {secondary} after {max_attempts} attempts.")






Fix the following code snippet from master/master.py:


# Assuming these are defined at the top of your file
next_seq_num = 0
full_log = []

@app.route('/messages', methods=['POST'])
def post_message():
    # ... [your comments and existing code]

    global next_seq_num
    try:
        message = request.json['message']
        write_concern = int(request.json.get('w', 1))

        seq_num = next_seq_num
        next_seq_num += 1

        seq_message = {'seq_num': seq_num, 'message': message}

        # Append to full_log for complete history
        full_log.append(seq_message)

        if seq_message not in log:
            log.append(seq_message)  # Deduplication check

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
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'status': 'fail', 'message': str(e)}), 500
