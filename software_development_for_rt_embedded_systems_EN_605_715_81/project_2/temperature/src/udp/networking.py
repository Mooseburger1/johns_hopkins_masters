# networking.py

import socket
import time
from data_handler import DataManager
from datetime import datetime

def setup_socket(port):
    """Initializes and binds the UDP socket."""
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Bind the socket to the local port to listen for incoming UDP data
        my_socket.bind(('', port))
        return my_socket
    except OSError as e:
        print(f"Error binding socket: {e}. Check if port {port} is already in use.")
        return None

def send_unix_time(my_socket, host, port):
    """Sends current Unix time to the server for synchronization and waits for 'OK'."""
    unix_time = int(time.time())
    payload = str(unix_time).encode()
    print(f"Sending current Unix time: {unix_time}")
    my_socket.sendto(payload, (host, port))

    try:
        # Wait for "OK" response from the server
        data, _ = my_socket.recvfrom(1024)
        response = data.decode().strip()
        print(f"Received response from server: {response}")
        return response == "OK"
    except socket.timeout:
        # This socket.timeout is handled in the calling function (client_app.py)
        return False

def receive_data(my_socket, data_manager, stop_event):
    """Thread to continuously receive UDP data and parse the 'date, value' CSV string."""
    while not stop_event.is_set():
        try:
            # Set a small timeout for the thread to check the stop_event periodically
            my_socket.settimeout(0.1) 
            data, _ = my_socket.recvfrom(1024)
            if data:
                csv_string = data.decode().strip()
                print(f"[UDP] Received: {csv_string}")
                data_manager.parse_and_add(csv_string)

        except socket.timeout:
            continue
        except Exception as e:
            if not stop_event.is_set():
                print(f"Error in receive_data: {e}")
            break