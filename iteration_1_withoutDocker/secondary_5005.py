from flask import Flask, request, jsonify
import time

app = Flask(__name__)
log = []

"""
Secondary servers should expose an HTTP API that supports GET methods and a replication endpoint for the Master to POST messages to.
When a message is received from the Master, it should be added to the Secondary's log and an ACK should be sent back.

Ensure that the secondary server is running on the port specified in your master server code (5001 in this case).


Secondary Server: The secondary server(s) are meant to replicate the data from the master server. 
If you're running the secondary server on the same machine as the master server, it needs to use a different port. In the example, it's set to run on port 5001

"""

@app.route('/replicate', methods=['POST'])
def replicate():
    message = request.json['message']
    log.append(message)
    time.sleep(5)  # Introduce delay to test blocking replication
    return jsonify({'status': 'ACK'}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify({'messages': log}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005, debug=True)  # Change port for different secondaries
