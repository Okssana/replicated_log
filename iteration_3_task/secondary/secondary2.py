from flask import Flask, request, jsonify
import os
import time
import logging


# Initialize Flask application
app = Flask(__name__)

# Initialize log and sequence tracking
log = []
last_processed_sequence = -1

# Set up artificial delay from an environment variable
ARTIFICIAL_DELAY = int(os.environ.get('ARTIFICIAL_DELAY', 1))

logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return "Hello, this is Secondary 2!"


def process_message(message, sequence_number):
    """Process the message and update the last processed sequence number."""
    global last_processed_sequence
    log.append({'sequence_number': sequence_number, 'message': message})
    last_processed_sequence = sequence_number
    logging.info(f"Processed message: {message}")

#### Version-3: Replication with sequence numbers
@app.route('/replicate', methods=['POST'])
def replicate():
    global last_processed_sequence

    message_data = request.json
    message = message_data['message']
    sequence_number = message_data['sequence_number']

    if sequence_number == last_processed_sequence + 1:
        # Process the message (assume this function is defined)
        process_message(message, sequence_number)
    elif sequence_number > last_processed_sequence + 1:
        # Handle out-of-order messages (not shown here for brevity)
        pass
    else:
        # Log duplicate or old message
        logging.error(f"Duplicate or old message received. Sequence: {sequence_number}")

    return jsonify({'status': 'ACK'}), 200

    
    
@app.route('/health', methods=['GET'], endpoint='health_secondary2')
def health_secondary2():
    return "Healthy Secondary 2!", 200

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify({'messages': log}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)