import streamlit as st
import cv2
import numpy as np
import time
import threading
from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode

st.set_page_config(
    page_title="Dominant Color Detector",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom premium styling
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    h1 {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎨 Real-time Dominant Color Detector")
st.markdown("Monitor live webcam feeds, analyze RGB channel averages, and dynamically identify dominant colors.")

# Initialize session state for camera stream control
if "running" not in st.session_state:
    st.session_state.running = False

# Thread-safe state container for color metrics from background thread
lock = threading.Lock()
state_container = {
    "color_name": "Red",
    "bg_color": "linear-gradient(135deg, #cb2d3e 0%, #ef473a 100%)",
    "border_color": "#ef4444",
    "r_mean": 0.0,
    "g_mean": 0.0,
    "b_mean": 0.0,
    "has_data": False
}

RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {
                "urls": [
                    "turn:openrelay.metered.ca:80",
                    "turn:openrelay.metered.ca:443",
                    "turns:openrelay.metered.ca:443?transport=tcp"
                ],
                "username": "openrelayproject",
                "credential": "openrelayproject"
            }
        ]
    }
)

def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    # Compute mean RGB channel values
    b = img[:, :, 0]
    g = img[:, :, 1]
    r = img[:, :, 2]
    
    b_mean = float(np.mean(b))
    g_mean = float(np.mean(g))
    r_mean = float(np.mean(r))
    
    # Dominant color check logic
    if b_mean > g_mean and b_mean > r_mean:
        color_name = "Blue"
        bg_color = "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
        border_color = "#3b82f6"
    elif g_mean > r_mean and g_mean > b_mean:
        color_name = "Green"
        bg_color = "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"
        border_color = "#10b981"
    else:
        color_name = "Red"
        bg_color = "linear-gradient(135deg, #cb2d3e 0%, #ef473a 100%)"
        border_color = "#ef4444"
        
    print(color_name)
    
    with lock:
        state_container["color_name"] = color_name
        state_container["bg_color"] = bg_color
        state_container["border_color"] = border_color
        state_container["r_mean"] = r_mean
        state_container["g_mean"] = g_mean
        state_container["b_mean"] = b_mean
        state_container["has_data"] = True
        
    return frame

col1, col2 = st.columns([5, 3], gap="large")

with col2:
    st.subheader("Controls & Analysis")
    
    # Start and Stop Buttons side by side
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("▶ Start Stream", key="start_btn", type="primary", use_container_width=True):
            st.session_state.running = True
            st.rerun()
            
    with btn_col2:
        if st.button("⏹ Stop Stream", key="stop_btn", type="secondary", use_container_width=True):
            st.session_state.running = False
            st.rerun()

    # Pre-render state indicators
    status_card = st.empty()
    chart_container = st.empty()

with col1:
    st.subheader("Live Camera Feed")
    ctx = webrtc_streamer(
        key="color-detector",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_frame_callback=video_frame_callback,
        desired_playing_state=st.session_state.running,
        media_stream_constraints={"video": True, "audio": False},
        media_toggle_controls=False,
    )


if ctx.state.playing:
    # Polling loop to update custom HTML components in the main thread
    while ctx.state.playing:
        with lock:
            if state_container["has_data"]:
                color_name = state_container["color_name"]
                bg_color = state_container["bg_color"]
                border_color = state_container["border_color"]
                r_mean = state_container["r_mean"]
                g_mean = state_container["g_mean"]
                b_mean = state_container["b_mean"]
            else:
                r_mean = g_mean = b_mean = 0.0
                color_name = "None"
                bg_color = "rgba(255, 255, 255, 0.05)"
                border_color = "rgba(255, 255, 255, 0.1)"
        
        status_card.markdown(
            f"""
            <div class="metric-card" style="background: {bg_color}; border-color: {border_color}; border-width: 2px;">
                <div style="font-size: 14px; opacity: 0.8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Dominant Color</div>
                <div style="font-size: 32px; font-weight: 800; margin-top: 5px;">{color_name}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        chart_container.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size: 16px; font-weight: 600; margin-bottom: 15px; color: #94a3b8;">Channel Intensity Metrics</div>
                
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px;">
                        <span>🔴 Red Channel (Mean)</span>
                        <span style="font-family: monospace; font-weight: bold;">{r_mean:.1f}</span>
                    </div>
                    <div style="background-color: #334155; border-radius: 4px; height: 8px; width: 100%;">
                        <div style="background-color: #ef4444; border-radius: 4px; height: 100%; width: {min(100.0, (r_mean/255.0)*100.0)}%;"></div>
                    </div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px;">
                        <span>🟢 Green Channel (Mean)</span>
                        <span style="font-family: monospace; font-weight: bold;">{g_mean:.1f}</span>
                    </div>
                    <div style="background-color: #334155; border-radius: 4px; height: 8px; width: 100%;">
                        <div style="background-color: #10b981; border-radius: 4px; height: 100%; width: {min(100.0, (g_mean/255.0)*100.0)}%;"></div>
                    </div>
                </div>
                
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px;">
                        <span>🔵 Blue Channel (Mean)</span>
                        <span style="font-family: monospace; font-weight: bold;">{b_mean:.1f}</span>
                    </div>
                    <div style="background-color: #334155; border-radius: 4px; height: 8px; width: 100%;">
                        <div style="background-color: #3b82f6; border-radius: 4px; height: 100%; width: {min(100.0, (b_mean/255.0)*100.0)}%;"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(0.05)
else:
    status_card.info("Webcam stream is currently inactive.")
    chart_container.empty()