
from flask import Flask, request, jsonify
import requests
from threading import Thread, Lock
import time
import logging
import threading

# Initialize Flask app and configure logging
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Global variables
next_seq_num = 0
full_log = []
log = []
secondaries = ["http://secondary1:5001", "http://secondary2:5002"]
seq_num_lock = Lock()

backoff_factor = 2 

## Version-3: Replication with Threads

def replicate_to_secondary(secondary, seq_message, acks, write_concern):
    # It doesn't matter if the replication fails, the message will still be logged in the master
    # The ACKs are used to determine if the write concern is satisfied
    for i in range(10): # Try 10 times
        try:
            response = requests.post(f"{secondary}/replicate", json=seq_message)
            if response.status_code == 200:
                acks.append(secondary)
            
            else:
                app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            logging.error(f"Error replicating to {secondary}: {e}")



def wait_for_acks(acks, required_acks):
    # Wait until the required number of ACKs are received or a timeout occurs
    start_time = time.time()
    while len(acks) < required_acks and (time.time() - start_time) < 10:
        time.sleep(0.1)  
        
    return len(acks) >= required_acks


@app.route('/messages', methods=['POST'])
def post_message():
    global next_seq_num
    try:
        message = request.json['message']
        write_concern = int(request.json.get('w', 1))

        with seq_num_lock:
            seq_message = {'sequence_number': next_seq_num, 'message': message}
            next_seq_num += 1

        full_log.append(seq_message) # Log the message in the master

        if seq_message not in log: # Deduplication 
            log.append(seq_message)

        acks = []
        threads = []
        for secondary in secondaries:
            # Start a thread for each secondary
            thread = Thread(target=replicate_to_secondary, args=(secondary, seq_message, acks, write_concern))
            # Make the thread daemon so that it doesn't block the main thread
            thread.start()
            # Keep track of the threads
            threads.append(thread)
        
        # Wait for the threads to finish
        success = wait_for_acks(acks, write_concern)
        
        # Wait for the threads to finish and then continue. Joining the threads blocks the main thread until the threads finish.
        for thread in threads:
            thread.join()

        if success:
            return jsonify({'status': 'success', 'message': 'Message replicated with required write concern'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Write concern not satisfied'}), 500

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500





### HEALTH CHECKS ###
    
# @app.route('/health', methods=['GET'])
# def health_check():
#     """
#     http://localhost:5000/health -- check if the service is up
#     """
#     return "Service is up", 200

@app.route('/health', methods=['GET'])
def get_health_status():
    return jsonify(secondaries_status)


SECONDARY_CHECK_INTERVAL = 10  # Time interval between health checks in seconds
secondaries_status = {url: "Healthy" for url in secondaries}

def check_secondary_health():
    while True:
        for secondary in secondaries:
            try:
                response = requests.get(f"{secondary}/health")
                if response.status_code == 200:
                    secondaries_status[secondary] = "Healthy"
                else:
                    secondaries_status[secondary] = "Suspected"
            except requests.RequestException:
                secondaries_status[secondary] = "Unhealthy"
        time.sleep(SECONDARY_CHECK_INTERVAL)

# Start the health check thread
health_check_thread = threading.Thread(target=check_secondary_health)
health_check_thread.daemon = True  # Daemonize thread
health_check_thread.start()



### MASTER ENDPOINTS ###

@app.route('/', methods=['GET'])
def home():
    """
    With this route, visiting http://127.0.0.1:5000/ in your browser will display the message "Welcome to the Master Server!" instead of a 404 error.
    Or you can use http://localhost:5000/
    """
    return "Welcome to the Master Server!", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
