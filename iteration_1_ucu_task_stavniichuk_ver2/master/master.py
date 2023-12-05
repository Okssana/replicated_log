from flask import Flask, request, jsonify
import requests
from threading import Thread
import requests

app = Flask(__name__)
log = []

secondaries = ["http://secondary1:5001", "http://secondary2:5002"]  # name of services in docker-compose.yaml, don't use localhost

def replicate_to_secondary(secondary, message):
    # It doesn't matter if the replication fails, the message will still be logged in the master
    try:
        response = requests.post(f"{secondary}/replicate", json={'message': message})
        if response.status_code != 200:
            app.logger.error(f"Replication failed for {secondary}. Status code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        app.logger.error(f"Failed to communicate with {secondary}. Error: {str(e)}")

@app.route('/messages', methods=['POST'])
def post_message():
    """
    Asynchronous Operation for POST:
    When a message is posted to the master, it will be replicated to the secondaries asynchronously.
    Messages are replicated to the secondaries even if the replication to one of the secondaries fails.
    """
    # Asynchronous Operation for POST
    try:
        message = request.json['message']
        print("Received message:", message)
        log.append(message)
        threads = []  # list to keep track of all threads
        # for secondary in secondaries:
            
        #     replication_thread = Thread(target=replicate_to_secondary, args=(secondary, message)) 
        #     replication_thread.start()

        # Start all threads 
        for secondary in secondaries:
            print("Creating thread for:", secondary)
            replication_thread = Thread(target=replicate_to_secondary, args=(secondary, message))
            replication_thread.start()
            print("Started thread:", replication_thread.name, replication_thread)
            threads.append(replication_thread)

         # Wait for all threads to finish
        for thread in threads:
            # thread.join() blocks the main thread until the thread finishes
            print("Waiting for thread to finish:", thread.name, thread)
            thread.join()
            print("Thread finished:", thread.name, thread) 
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        app.logger.error(f"Error while processing message: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Internal Server Error: {str(e)}'}), 500

@app.route("/messages", methods=['GET']) # get from http://secondary1:5001/messages and http://secondary2:5002/messages
def get_messages():
    return jsonify({'messages': log}), 200

@app.route('/', methods=['GET'])
def home():
    """
    With this route, visiting http://127.0.0.1:5000/ in your browser will display the message "Welcome to the Master Server!" instead of a 404 error.
    """
    return "Welcome to the Master Server!", 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True) 
