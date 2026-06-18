import streamlit as st
import openai
import base64

# --- KONFIGURASI HALAMAN (TAMPILAN) ---
st.set_page_config(page_title="AI Video Call", layout="wide", page_icon="📹")

# Custom CSS supaya tampilan lebih bersih (mirip aplikasi video call)
st.markdown("""
<style>
    .stApp { background-color: #1E1E1E; color: white; }
    .stAudioInput { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 999; width: 60%; background: #2b2b2b; padding: 10px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    h1, h2, h3 { color: white !important; }
    .stCameraInput video { border-radius: 15px; border: 2px solid #4CAF50; }
    .uploadedFile { display: none; }
</style>
""", unsafe_allow_html=True)

# --- INIT SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# --- SIDEBAR (SETTING) ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password")
    system_prompt = "Kamu adalah teman ngobrol yang asik. Jawab dalam Bahasa Indonesia yang gaul, santai, dan pendek saja."
    
    if not api_key:
        st.error("Masukkan API Key dulu!")
        st.stop()
        
    client = openai.OpenAI(api_key=api_key)

# --- FUNGSI UTAMA ---
def process_conversation(audio_prompt, image_input):
    """Otak dari aplikasi: Audio/Gambar -> GPT-4o -> Audio Balasan"""
    
    # 1. Transkrip Suara User (Whisper)
    with st.spinner("Mendengar..."):
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_prompt,
            language="id"
        )
        user_text = transcription.text

    if not user_text:
        return

    # 2. Siapkan Pesan untuk GPT-4o
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Masukkan history chat (biar nyambung)
    messages.extend(st.session_state.messages[-4:])
    
    # Masukkan input baru (Text + Gambar jika ada)
    content_payload = [{"type": "text", "text": user_text}]
    
    # Jika kamera aktif, kirim gambar ke AI
    if image_input:
        # Encode gambar ke base64
        bytes_data = image_input.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        content_payload.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })
    
    messages.append({"role": "user", "content": content_payload})

    # 3. Minta Jawaban AI
    with st.spinner("AI Mikir..."):
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=200
        )
        ai_reply = completion.choices[0].message.content

    # 4. Simpan ke History
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    # 5. Generate Suara AI (TTS)
    with st.spinner("AI Bicara..."):
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=ai_reply
        )
        # Trik Autoplay
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        audio_html = f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="autoplay" controls="controls"></audio>'
        return user_text, ai_reply, audio_html

# --- LAYOUT UTAMA (SPLIT SCREEN) ---
st.title("📹 Live AI Call")

col_user, col_ai = st.columns(2)

with col_user:
    st.subheader("Anda")
    # Native Camera Input (Lebih stabil daripada WebRTC)
    camera_val = st.camera_input("Kamera")

with col_ai:
    st.subheader("AI Assistant")
    # Gambar Avatar Statis (Bisa diganti GIF biar seolah bergerak)
    st.image("https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDdtY3Z4ZnBkODV4Y2dtY3Z4ZnBkODV4Y2dtY3Z4ZnBkODV4Y2cvYmRmL2dpcGh5LmdpZg/giphy.gif", width=300)
    
    # Area Text Chat
    chat_container = st.container(height=300)
    with chat_container:
        for msg in st.session_state.messages:
            role = "🧑" if msg["role"] == "user" else "🤖"
            st.write(f"{role}: {msg['content']}")

# --- INPUT SUARA (FLOATING DI BAWAH) ---
# Ini fitur baru Streamlit. Tekan mic -> Bicara -> Klik Stop -> Otomatis kirim.
audio_val = st.audio_input("Tekan Mic untuk bicara...")

if audio_val is not None:
    # Cek apakah ini audio baru (supaya tidak looping)
    if audio_val != st.session_state.last_audio:
        st.session_state.last_audio = audio_val
        
        user_text, ai_reply, audio_html = process_conversation(audio_val, camera_val)
        
        # Putar Suara
        st.markdown(audio_html, unsafe_allow_html=True)
        st.rerun() # Refresh halaman untuk update chat history