import serial
import socket
import threading
import time
import sys
import random

SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200
HOST = '0.0.0.0'
PORT = 65432

latest_data = "No data yet"
data_lock = threading.Lock() # <--- The Mutex
running = True



def generate_dummy_data():
    """Replaces read_serial() for testing without hardware"""
    global latest_data, running
    
    heading = 0.0
    roll = 0.0
    pitch = 0.0
    
    print("RUNNING IN DUMMY MODE (No Arduino required)")
    
    while running:
        # Simulate Drift (Random Walk)
        # Heading rotates slowly (0-360)
        heading = (heading + random.uniform(-1.0, 1.0)) % 360 
        
        # Roll/Pitch wobble around 0 (Clamped to +/- 30 degrees for realism)
        roll = max(-30, min(30, roll + random.uniform(-2.0, 2.0)))
        pitch = max(-30, min(30, pitch + random.uniform(-2.0, 2.0)))
        
        # 2. Format as CSV matching the BNO055 format
        # "{Heading},{Roll},{Pitch}"
        line = f"{heading:.2f},{roll:.2f},{pitch:.2f}"
        
        # 3. Update Shared Memory
        with data_lock:
            latest_data = line
            
        # 4. Simulate Sample Rate (e.g., 20Hz = 0.05s)
        time.sleep(0.05)

def read_serial():
    """Runs in background thread to keep Serial buffer empty"""
    global latest_data, running
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.reset_input_buffer()
        print(f"Serial connected on {SERIAL_PORT}")
    except Exception as e:
        print(f"Serial Error: {e}")
        running = False
        return

    while running:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').rstrip()
                if line:
                    with data_lock:
                        latest_data = line
            except Exception as e:
                print(f"Serial Read Error: {e}")

def start_server():
    """Main thread: Handles Network Connections"""
    global latest_data, running
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"📡 Server listening on {HOST}:{PORT}")
        
        while running:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")
            
            try:
                while running:
                    with data_lock:
                        current_payload = latest_data
                    
                    message = f"{current_payload}\n"
                    print(message)
                    conn.sendall(message.encode('utf-8'))
                    time.sleep(0.5) 
            except (BrokenPipeError, ConnectionResetError):
                print(f"🔌 Client {addr} disconnected.")
            finally:
                conn.close()
                
    except KeyboardInterrupt:
        running = False
    finally:
        server_socket.close()

if __name__ == "__main__":
    serial_thread = threading.Thread(target=generate_dummy_data, daemon=True)
    # serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()
    start_server()