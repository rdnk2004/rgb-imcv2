import streamlit as st
import cv2
import numpy as np
import av
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
    h, w, c = img.shape
    
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
        dot_color = (246, 130, 59) # BGR for Blue
    elif g_mean > r_mean and g_mean > b_mean:
        color_name = "Green"
        dot_color = (125, 233, 16) # BGR for Green
    else:
        color_name = "Red"
        dot_color = (68, 68, 239) # BGR for Red
        
    # Draw semi-transparent HUD background at the bottom
    overlay = img.copy()
    cv2.rectangle(overlay, (0, max(0, h - 120)), (w, h), (15, 23, 42), -1)
    alpha = 0.75
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    
    # Draw Dominant Color Text and indicator circle
    cv2.circle(img, (30, h - 85), 8, dot_color, -1)
    cv2.putText(img, f"DOMINANT COLOR: {color_name.upper()}", (50, h - 77), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Draw stacked progress bars for R, G, B
    # Red bar
    red_w = int((r_mean / 255.0) * 100)
    cv2.putText(img, "R", (30, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.rectangle(img, (55, h - 45), (155, h - 35), (50, 50, 50), -1)
    cv2.rectangle(img, (55, h - 45), (55 + red_w, h - 35), (68, 68, 239), -1)
    cv2.putText(img, f"{r_mean:.1f}", (165, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Green bar
    green_w = int((g_mean / 255.0) * 100)
    cv2.putText(img, "G", (220, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.rectangle(img, (245, h - 45), (345, h - 35), (50, 50, 50), -1)
    cv2.rectangle(img, (245, h - 45), (245 + green_w, h - 35), (125, 233, 16), -1)
    cv2.putText(img, f"{g_mean:.1f}", (355, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Blue bar
    blue_w = int((b_mean / 255.0) * 100)
    cv2.putText(img, "B", (410, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.rectangle(img, (435, h - 45), (535, h - 35), (50, 50, 50), -1)
    cv2.rectangle(img, (435, h - 45), (435 + blue_w, h - 35), (246, 130, 59), -1)
    cv2.putText(img, f"{b_mean:.1f}", (545, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    return av.VideoFrame.from_ndarray(img, format="bgr24")

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
    status_card.success("🟢 Webcam stream is active! Real-time color metrics and analysis are displayed directly on the video overlay.")
    chart_container.markdown(
        """
        <div class="metric-card">
            <div style="font-size: 16px; font-weight: 600; margin-bottom: 10px; color: #94a3b8;">Overlay Guide</div>
            <div style="font-size: 14px; opacity: 0.8; line-height: 1.5;">
                Look at the bottom HUD overlay on the live video stream:
                <br>• <b>Dominant Color</b> is identified on the left.
                <br>• <b>R, G, B Channel Averages</b> are shown via real-time progress bars.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    status_card.info("📷 Webcam stream is currently inactive.")
    chart_container.empty()