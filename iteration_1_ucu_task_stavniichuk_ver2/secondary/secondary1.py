from flask import Flask, request, jsonify
import time
import logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
log = []


@app.route("/")
def home():
    return "Hello, this is Secondary 1!" # text to return to client when they visit http://secondary1:5001/

@app.route("/health")
def health():
    return "Healthy!", 200 # text to return to client when they visit http://secondary1:5001/health

@app.route('/replicate', methods=['POST'])
def replicate():
    app.logger.info("Replicate endpoint hit with a POST request.")
    logging.info("Received POST request to /replicate")
    message = request.json.get('message')
    if message is None:
        logging.warning("Message is None")
        return jsonify({'status': 'error', 'message': 'Message cannot be None'}), 400
    
    log.append(message)
    logging.info(f"Appended message: {message}")
    time.sleep(1)
    return jsonify({'status': 'ACK'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    logging.info("Received GET request to /messages")

    return jsonify({'messages': log}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)  # Change port for different secondaries
