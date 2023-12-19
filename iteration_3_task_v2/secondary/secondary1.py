from flask import Flask, request, jsonify
import os
import time
import logging

# Initialize Flask application
app = Flask(__name__)

# Global variables
log = []  # Stores messages
last_processed_sequence = -1  # Tracks the last processed sequence number

# Read the artificial delay from an environment variable
ARTIFICIAL_DELAY = int(os.environ.get('ARTIFICIAL_DELAY', 1))

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return "Hello, this is Secondary 1!"


@app.route('/health', methods=['GET'], endpoint='health_secondary1')
def health_secondary1():
    # http://localhost:5001/health
    return "Healthy Secondary 1!", 200


@app.route('/replicate', methods=['POST'])
def replicate():
    global last_processed_sequence
    logging.info("Replicate endpoint hit with a POST request.")
    try:
        # Extracting message and sequence number from the request
        message_data = request.json
        message = message_data['message']
        sequence_number = message_data['sequence_number']

        # Validation message format
        if not message or not isinstance(message, str):
            logging.warning("Invalid message format")
            return jsonify({'status': 'error', 'message': 'Invalid message format'}), 400

        # Handling total ordering and deduplication
        if sequence_number == last_processed_sequence + 1:
            if message not in log:
                log.append(message)
                last_processed_sequence = sequence_number
                logging.info(f"Appended message: {message}")
            else:
                logging.info(f"Duplicate message received: {message}")
        elif sequence_number <= last_processed_sequence:
            logging.warning(f"Old or duplicate message received. Sequence: {sequence_number}")
        else:
            # Do not process messages that are out of order
            logging.warning(f"Out-of-order message received. Sequence: {sequence_number}")

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