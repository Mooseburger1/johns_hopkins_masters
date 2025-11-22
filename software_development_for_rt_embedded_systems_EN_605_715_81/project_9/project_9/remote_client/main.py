import serial
import threading
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# ==========================================
#              CONFIGURATION
# ==========================================
BLUETOOTH_COM_PORT = 'COM10' 
BAUD_RATE = 115200
MAX_POINTS = 200

# Shared Data Containers
data_x = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)
data_y = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)
data_z = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)

running = True

def data_listener():
    """Background thread: Reads from Bluetooth Virtual Serial Port"""
    global running
    print(f"Attempting to connect to {BLUETOOTH_COM_PORT}...")
    
    while running:
        try:
            # CONNECT TO BLUETOOTH VIA SERIAL
            # We use a timeout so the read loop doesn't block forever if data stops
            ser = serial.Serial(BLUETOOTH_COM_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to {BLUETOOTH_COM_PORT}! Streaming data...")
            
            while running:
                try:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        
                        if line and "," in line:
                            try:
                                # Parse CSV: Heading, Roll, Pitch
                                parts = line.split(',')
                                if len(parts) == 3:
                                    val_x = float(parts[0])
                                    val_y = float(parts[2])
                                    val_z = float(parts[1])
                                    
                                    # Update shared buffers
                                    data_x.append(val_x)
                                    data_y.append(val_y)
                                    data_z.append(val_z)

                            except ValueError:
                                pass
                    else:
                        # Small sleep to prevent this thread from eating 100% CPU
                        time.sleep(0.01)
                        
                except UnicodeDecodeError:
                    pass
                except serial.SerialException:
                    print("Connection lost.")
                    break
                    
        except serial.SerialException:
            print(f"Could not open {BLUETOOTH_COM_PORT}. Retrying in 2s...")
            print("Hint: Check Windows Bluetooth Settings > COM Ports (Outgoing).")
            time.sleep(2)
            
    if 'ser' in locals() and ser.is_open:
        ser.close()

# ==========================================
#              PLOTTING SETUP
# ==========================================
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(8, 8))
plt.subplots_adjust(hspace=0.3)
fig.suptitle(f'Real-Time IMU Data (Bluetooth: {BLUETOOTH_COM_PORT})')

# Heading Plot
line1, = ax1.plot(list(data_x), label='Heading (X)', color='r')
ax1.set_ylabel('Degrees')
ax1.set_ylim(0, 360)
ax1.legend(loc='upper right')
ax1.grid(True)

# Roll Plot
line2, = ax2.plot(list(data_y), label='Roll (Y)', color='g')
ax2.set_ylabel('Degrees')
ax2.set_ylim(-45, 90) # Adjusted range for typical drone tilt
ax2.legend(loc='upper right')
ax2.grid(True)

# Pitch Plot
line3, = ax3.plot(list(data_z), label='Pitch (Z)', color='b')
ax3.set_ylabel('Degrees')
ax3.set_ylim(-45, 90) # Adjusted range for typical drone tilt
ax3.legend(loc='upper right')
ax3.grid(True)

def update_plot(frame):
    """Called periodically by FuncAnimation to update lines"""
    # Update data from deque
    line1.set_ydata(list(data_x))
    line2.set_ydata(list(data_y))
    line3.set_ydata(list(data_z))
    return line1, line2, line3

# Start Background Thread
t = threading.Thread(target=data_listener, daemon=True)
t.start()

# Start Animation (50 FPS)
ani = animation.FuncAnimation(fig, update_plot, interval=20, blit=False)

print("Close the plot window to exit.")
plt.show()
running = False