from flask import Flask, request, jsonify
import os
import time
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
log = []
last_received_time = 0  # Track the time of the last received message

# Environment variable for artificial delay
ARTIFICIAL_DELAY = int(os.environ.get('ARTIFICIAL_DELAY', 5)) # : Make the artificial delay configurable via an environment variable instead of hardcoding the

@app.route("/")
def home():
    return "Hello, this is Secondary 2!"

@app.route("/health")
def health():
    # Implement actual health check logic here
    return "Healthy!", 200

@app.route('/replicate', methods=['POST'])
def replicate():
    global last_received_time
    current_time = time.time()
    logging.info("Received POST request to /replicate")
    
    # Introduce artificial delay
    time.sleep(ARTIFICIAL_DELAY)

    try:
        message = request.json['message']
        if not message or not isinstance(message, str):
            logging.warning("Invalid message format")
            return jsonify({'status': 'error', 'message': 'Invalid message format'}), 400

        # Ensure total ordering of messages
        if current_time > last_received_time:
            last_received_time = current_time
            """
            This simple check helps ensure that each unique message is only stored 
            once in the log, thus preventing duplication. 
            """
            # Each message is checked against the current log to prevent duplicates
            # from being appended.
            if message not in log: #  line checks if the received message is already present in the log list.
                log.append(message) # If the message is not in the log, it gets appended to the log list,
                logging.info(f"Appended message: {message}")
            else:
                # If the message is already in the log, it is ignored.
                logging.info(f"Duplicate message received: {message}")
        else:
            logging.warning("Message received out of order")
            return jsonify({'status': 'error', 'message': 'Message received out of order'}), 400

        return jsonify({'status': 'ACK'}), 200
    except (TypeError, KeyError):
        logging.exception("Failed to replicate message")
        return jsonify({'status': 'error', 'message': 'Bad request'}), 400

@app.route('/messages', methods=['GET'])
def get_messages():
    logging.info("Received GET request to /messages")
    return jsonify({'messages': log}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))
