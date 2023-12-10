from flask import Flask, request, jsonify
import os
import time
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
log = []
#  last_received_time = 0  # Track the time of the last received message

# Environment variable for artificial delay, with a default of 1 second
ARTIFICIAL_DELAY = int(os.environ.get('ARTIFICIAL_DELAY', 1))

@app.route("/")
def home():
    return "Hello, this is Secondary 1!"

@app.route("/health")
def health():
    # Implement actual health check logic here
    return "Healthy!", 200

@app.route('/replicate', methods=['POST'])
def replicate():
    logging.info("Replicate endpoint hit with a POST request.")
    try:
        message = request.json['message']
        if not message or not isinstance(message, str):
            logging.warning("Invalid message format")
            return jsonify({'status': 'error', 'message': 'Invalid message format'}), 400

        if message not in log:
            log.append(message)
            logging.info(f"Appended message: {message}")
        else:
            logging.info(f"Duplicate message received: {message}")

        time.sleep(ARTIFICIAL_DELAY)
        return jsonify({'status': 'ACK'}), 200
    except (TypeError, KeyError):
        logging.exception("Failed to replicate message")
        return jsonify({'status': 'error', 'message': 'Bad request'}), 400

@app.route('/messages', methods=['GET'])
def get_messages():
    logging.info("Received GET request to /messages")
    return jsonify({'messages': log}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
