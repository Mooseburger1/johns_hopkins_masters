import socket
import json
import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
from threading import Thread
import logging

# --- CONFIGURATION (UPDATE THESE) ---
# IP address of your Raspberry Pi (where gpsd is running)
GPSD_IP = '192.168.1.44' 
GPSD_PORT = 2947 
# How often to refresh the graphs in the browser (in milliseconds)
REFRESH_INTERVAL_MS = 1000 
# Max data points to show in history charts
MAX_DATA_POINTS = 50 
# ------------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global thread-safe data store
data_columns = ['Time', 'Latitude', 'Longitude', 'Altitude', 'Speed', 'Track', 'Satellites']
data_store = pd.DataFrame(columns=data_columns)
data_lock = 0 # Simple lock: 0=unlocked, 1=locked
connection_status = "CONNECTING"

# --- GPSD CONNECTION AND DATA HANDLING THREAD ---

def connect_and_stream():
    """Manages the TCP connection to gpsd and continuously streams data."""
    global data_store, data_lock, connection_status

    while True:
        try:
            # Connect to the remote gpsd daemon
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((GPSD_IP, GPSD_PORT))
            s.settimeout(1.0)
            
            watch_command = '?WATCH={"enable":true,"json":true}\n'
            s.sendall(watch_command.encode())
            
            connection_status = "LIVE"
            logging.info(f"Successfully connected to gpsd at {GPSD_IP}:{GPSD_PORT}")

            buffer = b''
            
            while True:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        raise ConnectionResetError("GPSD closed the connection.")

                    buffer += chunk
                    
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        try:
                            data = json.loads(line.decode('utf-8').strip())
                            
                            # Process TPV (position/velocity) and SKY (satellite) reports
                            if data.get('class') in ['TPV', 'SKY']:
                                process_gps_report(data)

                        except json.JSONDecodeError:
                            pass # Ignore incomplete or malformed JSON
                        
                except socket.timeout:
                    # Timeout is expected when no data is available, continue reading
                    continue
                
                except Exception as e:
                    logging.error(f"Stream error: {e}")
                    break # Exit inner loop to trigger reconnect

        except ConnectionRefusedError:
            connection_status = "REFUSED"
            logging.error(f"Connection refused by {GPSD_IP}:{GPSD_PORT}. Retrying in 5s...")
        except socket.error as e:
            connection_status = "ERROR"
            logging.error(f"Socket error: {e}. Retrying in 5s...")
        except Exception as e:
            connection_status = "FATAL"
            logging.error(f"Fatal error in streaming thread: {e}. Retrying in 5s...")
        
        s.close()
        time.sleep(5)


def process_gps_report(data):
    """Processes incoming JSON data and updates the global data_store."""
    global data_store, data_lock

    if data_lock:
        return

    # Use 'Time' (TPV time) or current time if TPV isn't present
    # Convert 'time' field from gpsd (ISO 8601 string) to datetime
    report_time_str = data.get('time')
    if report_time_str:
        try:
            report_time = pd.to_datetime(report_time_str, utc=True)
        except Exception:
            report_time = pd.to_datetime(time.time(), unit='s')
    else:
        # Fallback to current time if no 'time' is provided in the report
        report_time = pd.to_datetime(time.time(), unit='s')


    # --- Data Extraction ---
    current_lat = data.get('lat', float('nan'))
    current_lon = data.get('lon', float('nan'))
    current_alt = data.get('altMSL', float('nan'))
    # Convert speed (m/s) to kph (1 m/s = 3.6 kph)
    current_speed = data.get('speed', float('nan')) * 3.6 if pd.notna(data.get('speed')) else float('nan')
    current_track = data.get('track', float('nan'))

    # Get satellite count from SKY report (only 'used' satellites count)
    satellites = 0
    if data.get('class') == 'SKY' and data.get('satellites'):
        satellites = sum(1 for s in data['satellites'] if s.get('used'))

    data_lock = 1

    if data.get('class') == 'TPV':
        # TPV report: Create new row
        new_row = pd.Series({
            'Time': report_time,
            'Latitude': current_lat,
            'Longitude': current_lon,
            'Altitude': current_alt,
            'Speed': current_speed,
            'Track': current_track,
            'Satellites': data_store.iloc[-1]['Satellites'] if not data_store.empty else 0, # Carry over last Sat count
        })
        data_store = pd.concat([data_store, new_row.to_frame().T], ignore_index=True)

    elif data.get('class') == 'SKY' and satellites > 0 and not data_store.empty:
        # SKY report: Update the latest TPV row with the satellite count
        # This assumes SKY follows TPV very quickly, which is typical.
        data_store.iloc[-1, data_store.columns.get_loc('Satellites')] = satellites
    
    # Trim data store to max size
    if len(data_store) > MAX_DATA_POINTS:
        data_store = data_store.iloc[-MAX_DATA_POINTS:].reset_index(drop=True)
        
    data_lock = 0 # Unlock


# --- DASHBOARD LAYOUT AND COMPONENTS ---

app = Dash(__name__)

# Start the background GPS streaming thread
gps_thread = Thread(target=connect_and_stream, daemon=True)
gps_thread.start()

app.layout = html.Div(style={'backgroundColor': '#f3f4f6', 'padding': '20px'}, children=[
    html.H1("Live GPS Data Dashboard (Plotly/Dash)", style={'textAlign': 'center', 'color': '#1f2937'}),
    html.Div(id='live-status', style={'textAlign': 'center', 'marginBottom': '15px'}),
    
    # Hidden component to trigger updates
    dcc.Interval(id='interval-component', interval=REFRESH_INTERVAL_MS, n_intervals=0),

    # Top Row: Current Metrics
    html.Div(className='grid grid-cols-1 md:grid-cols-4 gap-4 mb-4', style={'display': 'grid'}, children=[
        # Lat/Lon Card
        html.Div(className='p-4 bg-white rounded-lg shadow-lg border-t-4 border-indigo-500', children=[
            html.H3("Latitude", className='text-sm font-medium text-gray-500'),
            html.P(id='live-lat', className='text-xl font-bold text-gray-800'),
        ]),
        html.Div(className='p-4 bg-white rounded-lg shadow-lg border-t-4 border-indigo-500', children=[
            html.H3("Longitude", className='text-sm font-medium text-gray-500'),
            html.P(id='live-lon', className='text-xl font-bold text-gray-800'),
        ]),
        # Speed Card
        html.Div(className='p-4 bg-white rounded-lg shadow-lg border-t-4 border-green-500', children=[
            html.H3("Speed (kph)", className='text-sm font-medium text-gray-500'),
            html.P(id='live-speed', className='text-2xl font-extrabold text-green-600'),
        ]),
        # Altitude Card
        html.Div(className='p-4 bg-white rounded-lg shadow-lg border-t-4 border-yellow-500', children=[
            html.H3("Altitude (m)", className='text-sm font-medium text-gray-500'),
            html.P(id='live-alt', className='text-2xl font-extrabold text-yellow-600'),
        ]),
    ]),
    
    # Middle Row: Graphs
    html.Div(className='grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4', style={'display': 'grid'}, children=[
        # Map / Track
        dcc.Graph(id='track-map', style={'height': '450px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'}),
        # Speed / Altitude Chart
        dcc.Graph(id='speed-alt-chart', style={'height': '450px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'}),
    ]),
    
    # Bottom Row: Satellites and Compass
    html.Div(className='grid grid-cols-1 lg:grid-cols-3 gap-4', style={'display': 'grid'}, children=[
        # Compass/Heading
        dcc.Graph(id='compass-gauge', className='lg:col-span-1', style={'height': '300px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'}),
        # Satellites
        dcc.Graph(id='satellite-bar', className='lg:col-span-2', style={'height': '300px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'}),
    ])
])

# --- DASHBOARD CALLBACKS (Real-Time Updates) ---

@app.callback(
    [Output('live-status', 'children'),
     Output('live-lat', 'children'),
     Output('live-lon', 'children'),
     Output('live-speed', 'children'),
     Output('live-alt', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_live_metrics(n):
    """Updates simple metrics and connection status."""
    global data_store, data_lock, connection_status
    
    if data_store.empty:
        lat, lon, speed, alt = 'N/A', 'N/A', 'N/A', 'N/A'
    else:
        data_lock = 1
        latest = data_store.iloc[-1]
        data_lock = 0
        
        lat = f"{latest['Latitude']:.6f}°"
        lon = f"{latest['Longitude']:.6f}°"
        speed = f"{latest['Speed']:.2f}"
        alt = f"{latest['Altitude']:.2f}"

    status_color = {'LIVE': 'text-green-600', 'CONNECTING': 'text-yellow-600', 'REFUSED': 'text-red-600', 'ERROR': 'text-red-600', 'FATAL': 'text-red-600'}.get(connection_status, 'text-gray-500')
    
    status_text = html.Span([
        html.Span(f"Connection Status: ", className='font-semibold text-gray-500'),
        html.Span(f"{connection_status} @ {GPSD_IP}:{GPSD_PORT}", className=f'font-bold {status_color}')
    ])
    
    return status_text, lat, lon, speed, alt


@app.callback(Output('speed-alt-chart', 'figure'), [Input('interval-component', 'n_intervals')])
def update_speed_alt_chart(n):
    """Updates the Speed and Altitude time-series chart."""
    global data_store, data_lock
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, 
                        subplot_titles=('Speed (kph)', 'Altitude (m)'))
    
    if not data_store.empty:
        data_lock = 1
        df = data_store.copy()
        data_lock = 0
        
        # Speed Trace
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Speed'], mode='lines', name='Speed', line=dict(color='#10b981', width=3)), row=1, col=1)
        
        # Altitude Trace
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Altitude'], mode='lines', name='Altitude', line=dict(color='#f59e0b', width=3)), row=2, col=1)
    
    fig.update_layout(
        margin=dict(l=40, r=20, t=40, b=20),
        plot_bgcolor='white', 
        paper_bgcolor='white',
        uirevision='speed-alt-chart'
    )
    fig.update_yaxes(title_text="kph", row=1, col=1)
    fig.update_yaxes(title_text="meters", row=2, col=1)
    fig.update_xaxes(tickformat="%H:%M:%S", row=2, col=1)
    
    return fig


@app.callback(Output('track-map', 'figure'), [Input('interval-component', 'n_intervals')])
def update_map(n):
    """Updates the GPS track history map."""
    global data_store, data_lock

    fig = go.Figure()

    if not data_store.empty:
        data_lock = 1
        df = data_store.dropna(subset=['Latitude', 'Longitude']).copy()
        data_lock = 0
        
        if not df.empty:
            # Main Track Line
            fig.add_trace(go.Scattermap(
                lon = df['Longitude'],
                lat = df['Latitude'],
                mode = 'lines',
                line = dict(width=3, color='#4f46e5'),
                name = 'Track'
            ))

            # Current Position Marker
            latest = df.iloc[-1]
            fig.add_trace(go.Scattermap(
                lon = [latest['Longitude']],
                lat = [latest['Latitude']],
                mode = 'markers',
                marker = dict(size=15, color='#dc2626', symbol='circle'),
                name = 'Current Fix'
            ))

            # Set Map Center to the latest point
            map_center = go.layout.mapbox.Center(lat=latest['Latitude'], lon=latest['Longitude'])
        else:
            map_center = go.layout.mapbox.Center(lat=0, lon=0)
            fig.add_annotation(text="Waiting for valid GPS Fix...", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

    else:
        map_center = go.layout.mapbox.Center(lat=0, lon=0)
        fig.add_annotation(text="Awaiting first data...", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

    # Note: Plotly requires a Mapbox token for high-quality maps, but uses a basic open-source map style by default.
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=14,
        mapbox_center=map_center,
        margin={"r":0,"t":0,"l":0,"b":0},
        uirevision='track-map'
    )
    return fig


@app.callback(Output('compass-gauge', 'figure'), [Input('interval-component', 'n_intervals')])
def update_compass_gauge(n):
    """Updates the directional gauge chart (compass)."""
    global data_store, data_lock

    current_track = 0
    
    if not data_store.empty:
        data_lock = 1
        current_track = data_store.iloc[-1]['Track'] if pd.notna(data_store.iloc[-1]['Track']) else 0
        data_lock = 0

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_track,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Heading/Track (°)"},
        number = {'suffix': "°", 'font': {'size': 36}},
        gauge = {
            'axis': {'range': [None, 360], 'tickvals': [0, 90, 180, 270], 'ticktext': ['N', 'E', 'S', 'W']},
            'bar': {'color': "#4f46e5"}, # Indigo
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 45], 'color': "rgba(255, 0, 0, 0.1)"},
                {'range': [315, 360], 'color': "rgba(255, 0, 0, 0.1)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': current_track
            }
        }
    ))
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), uirevision='compass-gauge')
    return fig


@app.callback(Output('satellite-bar', 'figure'), [Input('interval-component', 'n_intervals')])
def update_satellite_chart(n):
    """Updates the bar chart for satellite count."""
    global data_store, data_lock
    
    sat_count = 0
    if not data_store.empty:
        data_lock = 1
        sat_count = data_store.iloc[-1]['Satellites'] if pd.notna(data_store.iloc[-1]['Satellites']) else 0
        data_lock = 0

    fig = go.Figure(go.Bar(
        x=['Used Satellites'],
        y=[sat_count],
        marker_color='#3b82f6' # Blue
    ))
    
    fig.update_layout(
        title='Satellites Used for Fix',
        yaxis=dict(range=[0, 15], title='Count', tick0=0, dtick=1),
        margin=dict(l=40, r=20, t=50, b=20),
        plot_bgcolor='white',
        uirevision='satellite-bar'
    )
    return fig


if __name__ == '__main__':
    logging.info(f"Starting Dash server. Please open http://127.0.0.1:8050/ in your browser.")
    app.run(debug=True, host='0.0.0.0')
