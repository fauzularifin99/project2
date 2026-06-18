import streamlit as st
import cv2
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av

MODEL_PATH = "best.pt"
CONF_THRESHOLD = 0.50
ALERT_HOLD_FRAMES = 10

st.set_page_config(page_title="AI Danger Detection", layout="centered")
st.title("AI Danger Detection")
st.write("Deteksi benda berbahaya secara real-time melalui kamera.")

@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()

class DangerDetector(VideoProcessorBase):
    def __init__(self):
        self.alert_counter = 0

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        results = model(img, conf=CONF_THRESHOLD, imgsz=640, verbose=False)[0]
        detected = len(results.boxes) > 0

        if detected:
            self.alert_counter = ALERT_HOLD_FRAMES
        else:
            self.alert_counter = max(0, self.alert_counter - 1)

        if self.alert_counter > 0:
            cv2.rectangle(img, (0, img.shape[0] - 80), (img.shape[1], img.shape[0]), (0, 0, 255), -1)
            cv2.putText(img, "ALERT BAHAYA", (30, img.shape[0] - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 4)
        else:
            cv2.rectangle(img, (0, img.shape[0] - 80), (img.shape[1], img.shape[0]), (0, 180, 0), -1)
            cv2.putText(img, "AMAN", (30, img.shape[0] - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 4)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

webrtc_streamer(
    key="danger-detection",
    video_processor_factory=DangerDetector,
    media_stream_constraints={"video": True, "audio": False},
)
