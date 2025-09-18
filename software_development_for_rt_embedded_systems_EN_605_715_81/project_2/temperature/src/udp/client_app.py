# client_app.py

import threading
import time
import socket
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


from data_handler import DataManager
from networking import setup_socket, send_unix_time, receive_data
from plotting import setup_plot, update_plot

# NOTE: SET THE IP ADDRESS TO WHATEVER THE MICROCONTROLLER OUTPUTS
HOST = "192.168.1.37"
PORT = 12345
PLOT_INTERVAL_MS = 1000

stop_receiving = threading.Event() # Use a thread-safe Event for stopping
user_input_value = None 

def input_thread(stop_event):
    """Thread to get user input (e.g., '2' to stop) without blocking the plot."""
    global user_input_value
    print("\n--- Input Thread Started ---")
    while not stop_event.is_set():
        try:
            user_input_value = input().strip()
            if user_input_value == "2":
                stop_event.set()
                print("Stopping data reception and closing plot.")
                break
        except EOFError:
            stop_event.set()
            break
        except Exception as e:
            if not stop_event.is_set():
                print(f"Input thread error: {e}")
                stop_event.set()
                break

def main():
    # 1. Initialize data manager (handles lists and lock)
    data_manager = DataManager()
    
    # 2. Setup socket
    my_socket = setup_socket(PORT)
    if not my_socket:
        return

    # 3. Initial Communication Workflow
    print("Starting initial communication...")
    my_socket.settimeout(1) 
    while True:
        if send_unix_time(my_socket, HOST, PORT):
            break
        else:
            print("Retrying time sync...")
            time.sleep(2)

    print("Waiting for menu options from server...")
    my_socket.settimeout(None) # Temporarily block until menu is received
    try:
        data, _ = my_socket.recvfrom(1024)
        response = data.decode().strip()
        print(f"Received response from server: {response}")
    except Exception as e:
        print(f"Error receiving menu: {e}")
        my_socket.close()
        return
        
    my_socket.settimeout(1) # Restore timeout

    option_input = input("Provide option choice (e.g., '1' for data, '2' to exit): ").strip()
    my_socket.sendto(option_input.encode(), (HOST, PORT))
    if option_input == "2":
        my_socket.close()
        return

    # 4. Start threads
    receiver_thread = threading.Thread(
        target=receive_data, 
        args=(my_socket, data_manager, stop_receiving), 
        daemon=True
    )
    receiver_thread.start()

    input_thread_obj = threading.Thread(
        target=input_thread, 
        args=(stop_receiving,), 
        daemon=True
    )
    input_thread_obj.start()

    # 5. Setup Matplotlib plot
    fig, ax, line = setup_plot()

    print("\n--- Real-time Plotting Started ---")
    print(f"Receiving data from {HOST}:{PORT}. Type '2' + Enter to stop.")
    
    # 6. Start animation
    # Use lambda to pass data_manager into the update_plot function
    ani = FuncAnimation(
        fig, 
        lambda frame: update_plot(frame, ax, line, data_manager), 
        interval=PLOT_INTERVAL_MS, 
        cache_frame_data=False
    )
    
    # 7. Show plot and cleanup
    try:
        plt.show()
    except Exception as e:
        print(f"Plotting error: {e}")
    finally:
        stop_receiving.set()
        print("Plotting ended. Cleaning up resources.")
        if receiver_thread.is_alive():
            receiver_thread.join(timeout=2)
        my_socket.close()

if __name__ == "__main__":
    main()