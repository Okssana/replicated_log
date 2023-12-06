from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
log = []
secondaries = ["http://localhost:5004", "http://localhost:5005"]  # List of secondary servers


@app.route('/messages', methods=['POST']) # endpoint for the client to send messages
def post_message(): # The client sends a message to the master server
    message = request.json['message'] # The master server appends the message to its log
    log.append(message) 

    for secondary in secondaries:
        try:
            response = requests.post(f"{secondary}/replicate", json={'message': message})
            if response.status_code != 200:
                return jsonify({'status': 'error', 'message': f'Replication failed for {secondary}, status code: {response.status_code}, response: {response.text}'}), 500
        except requests.RequestException as e:
            return jsonify({'status': 'error', 'message': f'Failed to communicate with {secondary}. Error: {str(e)}'}), 500
        
    return jsonify({'status': 'success'}), 200

@app.route("/messages", methods=['GET']) # endpoint for the client to get all messages
def get_messages():
    return jsonify({'messages': log}), 200

@app.route('/', methods=['GET'])
def home():
    """
    If you want to provide a response when visiting http://127.0.0.1:5000/, you can add a route for / in your Flask app.

    With this route, visiting http://127.0.0.1:5000/ in your browser will display the message "Welcome to the Master Server!" instead of a 404 error.
    """
    return "Welcome to the Master Server!", 200 # 200 is the HTTP status code for "OK"



# http://127.0.0.1:5007/messages -- for testing purposes
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5007, debug=True)
