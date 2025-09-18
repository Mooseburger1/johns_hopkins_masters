# data_handler.py

import threading
from datetime import datetime

class DataManager:
    """Manages the shared data points and timestamps in a thread-safe manner."""
    def __init__(self):
        self.data_points = []
        self.timestamps = []
        self.lock = threading.Lock()

    def parse_and_add(self, csv_string):
        """Parses the 'date, value' string and adds data to the lists."""
        try:
            # 1. Split the string
            parts = [p.strip() for p in csv_string.split(',')]
            if len(parts) != 2:
                print(f"Warning: Data format error. Expected 'DATE, VALUE', got: {csv_string}")
                return

            date_str, value_str = parts[0], parts[1]
            
            # 2. Convert value to float
            numeric_value = float(value_str)

            # 3. Parse timestamp and format for graph label
            dt_object = datetime.fromisoformat(date_str)
            time_label = dt_object.strftime("%H:%M:%S")

            # Acquire lock before modifying shared lists
            with self.lock:
                self.data_points.append(numeric_value)
                self.timestamps.append(time_label) 

        except ValueError as e:
            print(f"Warning: Data parsing error ({e}). Ignoring message: {csv_string}")
        except Exception as e:
             print(f"Unexpected error during data parsing: {e}")

    def get_data(self):
        """Returns copies of the data lists in a thread-safe manner."""
        with self.lock:
            # Return copies to prevent external modification during plot drawing
            return self.data_points[:], self.timestamps[:]