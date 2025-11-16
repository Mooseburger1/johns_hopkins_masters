import socket
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque


PI_IP = '192.168.1.44'
PORT = 65432
MAX_POINTS = 200

data_x = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)
data_y = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)
data_z = deque([0.0] * MAX_POINTS, maxlen=MAX_POINTS)

running = True

def data_listener():
    """Background thread to fetch data from Pi without blocking the plot"""
    global running
    print(f"Attempting to connect to {PI_IP}:{PORT}...")
    
    while running:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((PI_IP, PORT))
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                print("Connected! Streaming data...")
                buffer = ""
                
                while running:
                    try:
                        chunk = s.recv(1024).decode('utf-8')
                        print(chunk)
                        if not chunk: break
                        
                        buffer += chunk
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if "," in line:
                                try:
                                    # Parse CSV: Heading, Roll, Pitch
                                    parts = line.split(',')
                                    if len(parts) == 3:
                                        val_x = float(parts[0])
                                        val_y = float(parts[1])
                                        val_z = float(parts[2])
                                        
                                        # Update shared buffers
                                        data_x.append(val_x)
                                        data_y.append(val_y)
                                        data_z.append(val_z)
                                except ValueError:
                                    pass
                    except socket.error:
                        break
        except (ConnectionRefusedError, TimeoutError):
            print("Connection failed. Retrying in 1s...")
            import time; time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            break

# SETUP PLOTS
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(8, 8))
plt.subplots_adjust(hspace=0.3)
fig.suptitle(f'Real-Time IMU Data from {PI_IP}')

# Heading Plot
line1, = ax1.plot(list(data_x), label='Heading (X)', color='r')
ax1.set_ylabel('Degrees')
ax1.set_ylim(0, 360)
ax1.legend(loc='upper right')
ax1.grid(True)

# Roll Plot
line2, = ax2.plot(list(data_y), label='Roll (Y)', color='g')
ax2.set_ylabel('Degrees')
ax2.set_ylim(-180, 180)
ax2.legend(loc='upper right')
ax2.grid(True)

# Pitch Plot
line3, = ax3.plot(list(data_z), label='Pitch (Z)', color='b')
ax3.set_ylabel('Degrees')
ax3.set_ylim(-180, 180)
ax3.legend(loc='upper right')
ax3.grid(True)

def update_plot(frame):
    """Called periodically by FuncAnimation to update lines"""
    line1.set_ydata(list(data_x))
    line2.set_ydata(list(data_y))
    line3.set_ydata(list(data_z))
    return line1, line2, line3


t = threading.Thread(target=data_listener, daemon=True)
t.start()

# Start Animation (Interval is in milliseconds)
# 20ms = 50 FPS refresh rate
ani = animation.FuncAnimation(fig, update_plot, interval=20, blit=False)

print("Close the plot window to exit.")
plt.show()
running = False