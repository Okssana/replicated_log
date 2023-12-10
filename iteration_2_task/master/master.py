
from flask import Flask, request, jsonify
import requests
from threading import Thread
import time

app = Flask(__name__)
log = []

secondaries = ["http://secondary1:5001", "http://secondary2:5002"]

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

def wait_for_acks(acks, required_acks):
    # Wait until the required number of ACKs are received or a timeout occurs
    start_time = time.time()
    while len(acks) < required_acks and (time.time() - start_time) < 10:
        time.sleep(0.1)  
        
    return len(acks) >= required_acks

@app.route('/messages', methods=['POST'])
def post_message():
    """
    http://localhost:5000/messages  -- Post method only
    "Method Not Allowed. The method is not allowed for the requested URL." if you try to use GET method 
    """
    try:
        message = request.json['message']

        """
        Write Concern Parameter (w) - The number of acknowledgments required for the write operation to be considered successful
        http://localhost:5001/messages?w=1
        """


        write_concern = int(request.json.get('w', 1))  # 1 is the default write concern, if not specified

        log.append(message)
        
        acks = []  # list of ACKs from secondaries
        threads = []  # list of threads

        # Start replication threads
        for secondary in secondaries:
            replication_thread = Thread(target=replicate_to_secondary, args=(secondary, message, acks, write_concern))
            replication_thread.start()
            threads.append(replication_thread)

        # Wait for the required number of ACKs
        success = wait_for_acks(acks, write_concern)

        # Wait for all threads to finish (clean up)
        for thread in threads:
            thread.join()

        if success:
            return jsonify({'status': 'success', 'message': 'Message replicated with required write concern'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Write concern not satisfied'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
    """
    return "Welcome to the Master Server!", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
