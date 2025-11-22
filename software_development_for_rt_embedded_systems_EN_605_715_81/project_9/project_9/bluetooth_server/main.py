import serial
import socket
import threading
import time
import sys
import random

# ==========================================
#              CONFIGURATION
# ==========================================
# Set to True to generate fake data. 
# Set to False to read from the actual Arduino.
USE_SIMULATION = False 

# Serial Settings (Real Hardware)
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200

# Bluetooth Settings
BT_ADDR = "2C:CF:67:EF:C4:EB"
BT_PORT = 1    # Standard RFCOMM channel

# Shared Memory
latest_data = "0.00,0.00,0.00"
data_lock = threading.Lock()
running = True

# ==========================================
#        DATA SOURCE 1: DUMMY DATA
# ==========================================
def generate_dummy_data():
    """Generates drifting random values to mimic a hovering drone"""
    global latest_data, running
    
    heading, roll, pitch = 0.0, 0.0, 0.0
    print("SIMULATION MODE: Generating synthetic IMU data...")
    
    while running:
        # Simulate Random Walk (Drift)
        heading = (heading + random.uniform(-2.0, 2.0)) % 360 
        roll = max(-30, min(30, roll + random.uniform(-1.5, 1.5)))
        pitch = max(-30, min(30, pitch + random.uniform(-1.5, 1.5)))
        
        line = f"{heading:.2f},{roll:.2f},{pitch:.2f}"
        
        with data_lock:
            latest_data = line
            
        time.sleep(0.05) # 20Hz update rate

# ==========================================
#        DATA SOURCE 2: REAL SERIAL
# ==========================================
def read_serial():
    """Reads real data from Arduino via USB with auto-reconnect"""
    global latest_data, running
    
    print("HARDWARE MODE: Looking for Arduino...")
    
    while running:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            ser.reset_input_buffer()
            print(f"Serial connected on {SERIAL_PORT}")
            
            while running:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8').rstrip()
                        if line:
                            with data_lock:
                                latest_data = line
                    except UnicodeDecodeError:
                        pass
                    except OSError:
                        print("Serial connection lost.")
                        break
                else:
                    time.sleep(0.001)
                    
        except serial.SerialException:
            print(f"Arduino not found on {SERIAL_PORT}. Retrying in 2s...")
            time.sleep(2)
            
    if 'ser' in locals() and ser.is_open:
        ser.close()

# ==========================================
#          BLUETOOTH TRANSMITTER
# ==========================================
def start_bluetooth_server():
    """Broadcasts the latest data via Bluetooth RFCOMM"""
    global latest_data, running
    
    # Setup Bluetooth Socket
    try:
        server_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    except AttributeError:
        print("Error: This Python installation does not support Bluetooth sockets.")
        return

    try:
        server_socket.bind((BT_ADDR, BT_PORT))
        server_socket.listen(1)
        print(f"Bluetooth Server listening on Channel {BT_PORT}")
        print("You can now pair/connect from Windows.")
        
        while running:
            print("Waiting for client...")
            try:
                conn, addr = server_socket.accept()
                print(f"Client connected: {addr}")
                
                while running:
                    # Fetch safest data
                    with data_lock:
                        current_payload = latest_data
                    
                    message = f"{current_payload}\n"
                    conn.sendall(message.encode('utf-8'))
                    
                    # Transmission Rate (Adjust for latency vs bandwidth)
                    time.sleep(0.05) 
                    
            except (BrokenPipeError, ConnectionResetError, OSError):
                print(f"Client disconnected.")
            finally:
                try:
                    conn.close()
                except:
                    pass
                
    except KeyboardInterrupt:
        print("\nStopping server...")
        running = False
    finally:
        server_socket.close()

# ==========================================
#               MAIN ENTRY
# ==========================================
if __name__ == "__main__":
    # Choose the data source based on the flag at the top
    if USE_SIMULATION:
        source_thread = threading.Thread(target=generate_dummy_data, daemon=True)
    else:
        source_thread = threading.Thread(target=read_serial, daemon=True)
        
    source_thread.start()
    
    # Start the Bluetooth Server (Main Thread)
    start_bluetooth_server()