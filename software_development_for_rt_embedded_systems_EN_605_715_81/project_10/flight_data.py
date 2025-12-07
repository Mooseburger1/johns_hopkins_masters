import socket
import json
import time
import threading
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
from collections import deque
import logging

# --- CONFIGURATION ---
PI_IP = '192.168.1.44'

# Camera Settings
# Motion usually streams on 8081. If you view it on 8080 in your browser, change this to 8080.
CAMERA_URL = f"http://{PI_IP}:8081" 

# IMU Settings (Raw TCP)
IMU_PORT = 65432
IMU_MAX_POINTS = 200

# GPS Settings (GPSD JSON)
GPS_PORT = 2947
GPS_MAX_POINTS = 60

# UI Refresh Rate
REFRESH_INTERVAL_MS = 500 

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- THREAD-SAFE DATA STORAGE ---
imu_lock = threading.Lock()
gps_lock = threading.Lock()

imu_deque = deque(maxlen=IMU_MAX_POINTS)
gps_deque = deque(maxlen=GPS_MAX_POINTS)

status = {
    "IMU": "DISCONNECTED",
    "GPS": "DISCONNECTED"
}

# --- THREAD 1: IMU LISTENER ---
def imu_thread_func():
    global status
    while True:
        s = None
        try:
            status["IMU"] = "CONNECTING..."
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((PI_IP, IMU_PORT))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(None)
            
            status["IMU"] = "CONNECTED"
            buffer = ""
            
            while True:
                try:
                    chunk = s.recv(2048).decode('utf-8', errors='ignore')
                    if not chunk: break
                    buffer += chunk
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if "," in line:
                            parts = line.split(',')
                            if len(parts) >= 3:
                                try:
                                    row = {
                                        'Time': pd.Timestamp.now(),
                                        'Heading': float(parts[0]),
                                        'Roll': float(parts[1].strip()),
                                        'Pitch': float(parts[2].strip())
                                    }
                                    with imu_lock:
                                        imu_deque.append(row)
                                except ValueError:
                                    pass
                except socket.error:
                    break
        except Exception:
            status["IMU"] = "ERROR"
            time.sleep(2)
        finally:
            if s: s.close()

# --- THREAD 2: GPS LISTENER ---
def gps_thread_func():
    global status
    current_satellites = 0
    
    while True:
        s = None
        try:
            status["GPS"] = "CONNECTING..."
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((PI_IP, GPS_PORT))
            s.sendall(b'?WATCH={"enable":true,"json":true}\n')
            s.settimeout(None)
            
            status["GPS"] = "CONNECTED"
            buffer = ""
            
            while True:
                try:
                    chunk = s.recv(4096).decode('utf-8', errors='ignore')
                    if not chunk: break
                    buffer += chunk
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line: continue
                        
                        try:
                            data = json.loads(line)
                            
                            if data.get('class') == 'SKY':
                                satellites = sum(1 for sat in data.get('satellites', []) if sat.get('used'))
                                current_satellites = max(current_satellites, satellites)
                                
                            elif data.get('class') == 'TPV':
                                lat = data.get('lat')
                                lon = data.get('lon')
                                if lat is not None and lon is not None:
                                    speed = (data.get('speed', 0) or 0) * 3.6 # kph
                                    row = {
                                        'Time': pd.Timestamp.now(),
                                        'Latitude': lat,
                                        'Longitude': lon,
                                        'Altitude': data.get('altMSL', 0),
                                        'Speed': speed,
                                        'Satellites': current_satellites
                                    }
                                    with gps_lock:
                                        gps_deque.append(row)
                        except json.JSONDecodeError:
                            pass
                except socket.error:
                    break
        except Exception:
            status["GPS"] = "ERROR"
            time.sleep(2)
        finally:
            if s: s.close()

# --- START BACKGROUND THREADS ---
t1 = threading.Thread(target=imu_thread_func, daemon=True)
t2 = threading.Thread(target=gps_thread_func, daemon=True)
t1.start()
t2.start()
# --- DASH DASHBOARD ---
app = Dash(__name__)

# CSS Styles for consistency
card_style = {'background': '#374151', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}
text_gray = {'color': '#9ca3af', 'margin': 0}

app.layout = html.Div(style={'backgroundColor': '#1f2937', 'color': 'white', 'minHeight': '100vh', 'padding': '20px', 'fontFamily': 'sans-serif'}, children=[
    
    html.H1("🚀 Mission Control", style={'textAlign': 'center', 'marginBottom': '5px'}),
    html.Div(id='status-header', style={'textAlign': 'center', 'marginBottom': '20px', 'fontSize': '14px', 'color': '#9ca3af'}),

    dcc.Interval(id='interval-timer', interval=REFRESH_INTERVAL_MS, n_intervals=0),

    # --- ROW 1: KPI CARDS ---
    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px', 'marginBottom': '20px'}, children=[
        html.Div(className='card', style=card_style, children=[
            html.H4("Speed", style=text_gray),
            html.H2(id='val-speed', style={'margin': '5px 0', 'color': '#34d399'})
        ]),
        html.Div(className='card', style=card_style, children=[
            html.H4("Heading", style=text_gray),
            html.H2(id='val-heading', style={'margin': '5px 0', 'color': '#60a5fa'})
        ]),
        html.Div(className='card', style=card_style, children=[
            html.H4("Altitude", style=text_gray),
            html.H2(id='val-alt', style={'margin': '5px 0', 'color': '#fbbf24'})
        ]),
        html.Div(className='card', style=card_style, children=[
            html.H4("Satellites", style=text_gray),
            html.H2(id='val-sats', style={'margin': '5px 0', 'color': '#f87171'})
        ]),
    ]),

    # --- ROW 2: LIVE VIDEO & MAP (Split 50/50) ---
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
        
        # LEFT: LIVE VIDEO FEED
        html.Div(style={**card_style, 'padding': '0', 'overflow': 'hidden', 'display': 'flex', 'flexDirection': 'column'}, children=[
            html.Div("Live Camera Feed", style={'padding': '10px', 'background': '#111827', 'color': '#9ca3af', 'fontWeight': 'bold'}),
            # This IMG tag connects directly to the Pi's MJPEG stream
            html.Img(src=CAMERA_URL, style={'width': '100%', 'height': '100%', 'objectFit': 'contain', 'minHeight': '400px'})
        ]),

        # RIGHT: GPS MAP
        html.Div(style={**card_style, 'padding': '0', 'overflow': 'hidden'}, children=[
             dcc.Graph(id='gps-map', style={'height': '100%', 'minHeight': '430px'})
        ]),
    ]),

    # --- ROW 3: CHARTS & COMPASS ---
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '20px'}, children=[
        html.Div(style=card_style, children=[
            dcc.Graph(id='telemetry-charts', style={'height': '350px'})
        ]),
        html.Div(style=card_style, children=[
            dcc.Graph(id='compass-gauge', style={'height': '350px'})
        ])
    ])
])

@app.callback(
    [Output('status-header', 'children'),
     Output('val-speed', 'children'),
     Output('val-heading', 'children'),
     Output('val-alt', 'children'),
     Output('val-sats', 'children'),
     Output('gps-map', 'figure'),
     Output('compass-gauge', 'figure'),
     Output('telemetry-charts', 'figure')],
    [Input('interval-timer', 'n_intervals')]
)
def update_dashboard(n):
    # READ DATA
    with imu_lock:
        df_imu = pd.DataFrame(list(imu_deque))
    with gps_lock:
        df_gps = pd.DataFrame(list(gps_deque))

    # STATUS
    status_text = f"IMU: {status['IMU']} | GPS: {status['GPS']} | Camera: {CAMERA_URL}"

    # VALUES
    curr_heading = df_imu.iloc[-1]['Heading'] if not df_imu.empty and 'Heading' in df_imu.columns else 0
    curr_speed = df_gps.iloc[-1]['Speed'] if not df_gps.empty else 0
    curr_alt = df_gps.iloc[-1]['Altitude'] if not df_gps.empty else 0
    curr_sats = df_gps.iloc[-1]['Satellites'] if not df_gps.empty else 0
    curr_lat = df_gps.iloc[-1]['Latitude'] if not df_gps.empty else 0
    curr_lon = df_gps.iloc[-1]['Longitude'] if not df_gps.empty else 0

    val_speed = f"{curr_speed:.1f} kph"
    val_heading = f"{curr_heading:.1f}°"
    val_alt = f"{curr_alt:.1f} m"
    val_sats = f"{curr_sats}"

    # MAP
    if not df_gps.empty:
        map_fig = go.Figure(go.Scattermap(
            lat=df_gps['Latitude'], lon=df_gps['Longitude'],
            mode='lines+markers',
            marker=dict(size=10, color='#ef4444'),
            line=dict(width=4, color='#3b82f6')
        ))
        map_center = {"lat": curr_lat, "lon": curr_lon}
        zoom = 15
    else:
        map_fig = go.Figure()
        map_center = {"lat": 0, "lon": 0}
        zoom = 1

    map_fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox_style="carto-darkmatter",
        mapbox_center=map_center,
        mapbox_zoom=zoom,
        paper_bgcolor='#1f2937',
        uirevision='static_map_ui'
    )

    # COMPASS
    gauge_fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = curr_heading,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Heading", 'font': {'color': 'white'}},
        number = {'font': {'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 360]},
            'bar': {'color': "#60a5fa"},
            'bgcolor': "#374151",
            'bordercolor': "#1f2937"
        }
    ))
    gauge_fig.update_layout(paper_bgcolor='#374151', font={'color': 'white'}, margin=dict(t=30, b=20, l=30, r=30))

    # CHARTS
    charts_fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.15,
                               subplot_titles=("IMU Attitude", "GPS Telemetry"))

    if not df_imu.empty and 'Roll' in df_imu.columns:
        charts_fig.add_trace(go.Scatter(x=df_imu['Time'], y=df_imu['Roll'], name='Roll', line=dict(color='#34d399')), row=1, col=1)
        charts_fig.add_trace(go.Scatter(x=df_imu['Time'], y=df_imu['Pitch'], name='Pitch', line=dict(color='#fbbf24')), row=1, col=1)

    if not df_gps.empty and 'Speed' in df_gps.columns:
        charts_fig.add_trace(go.Scatter(x=df_gps['Time'], y=df_gps['Speed'], name='Speed', line=dict(color='#f87171')), row=2, col=1)
        charts_fig.add_trace(go.Scatter(x=df_gps['Time'], y=df_gps['Altitude'], name='Alt', line=dict(color='#818cf8', dash='dot')), row=2, col=1)

    charts_fig.update_layout(
        paper_bgcolor='#374151', plot_bgcolor='#1f2937',
        font={'color': 'white'},
        margin=dict(t=30, b=20, l=40, r=20),
        height=350,
        showlegend=True,
        uirevision='telemetry_charts_ui' 
    )

    return status_text, val_speed, val_heading, val_alt, val_sats, map_fig, gauge_fig, charts_fig

if __name__ == '__main__':
    print(f"Starting Cockpit... Connecting to {PI_IP}")
    # DISABLE RELOADER TO FIX IMU DATA ISSUES
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8050)
