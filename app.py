import streamlit as st
import openai
import os
import base64
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Zoom Clone", layout="wide")

st.title("🤖 AI Video Call Interface (GPT-4o)")
st.markdown("Interaksi Suara, Video, Chat, dan Dokumen dengan OpenAI")

# --- SIDEBAR: KONFIGURASI API ---
with st.sidebar:
    api_key = st.text_input("Masukkan OpenAI API Key Anda", type="password")
    if not api_key:
        st.warning("Mohon masukkan API Key untuk memulai.")
        st.stop()
    
    client = openai.OpenAI(api_key=api_key)
    
    st.markdown("---")
    st.markdown("### 📁 Upload Lampiran")
    uploaded_file = st.file_uploader("Upload PDF/TXT/Gambar", type=['txt', 'pdf', 'png', 'jpg', 'csv'])

# --- FUNGSI BANTUAN ---

def audio_to_text(audio_file):
    """Mengubah suara user menjadi text (Transkrip)"""
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcription.text

def text_to_speech(text):
    """Mengubah respon text AI menjadi suara"""
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova", # Pilihan suara: alloy, echo, fable, onyx, nova, shimmer
        input=text
    )
    return response.content

def encode_image(image_buffer):
    """Mengubah gambar kamera menjadi base64 untuk GPT-4 Vision"""
    return base64.b64encode(image_buffer.getvalue()).decode('utf-8')

# --- SESSION STATE (HISTORY CHAT) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LAYOUT UTAMA (SEPERTI ZOOM) ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📹 Anda (User)")
    
    # 1. INPUT KAMERA
    camera_input = st.camera_input("Kamera Anda")
    
    # 2. INPUT SUARA
    # Streamlit versi baru mendukung st.audio_input
    audio_input = st.audio_input("Bicara dengan AI")

with col2:
    st.header("🤖 OpenAI (AI Agent)")
    # Placeholder untuk video/avatar AI (Gambar statis karena OpenAI belum generate video real-time)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712027.png", width=150, caption="AI Agent Video Feed")
    
    # Area untuk memutar suara respon AI
    ai_audio_placeholder = st.empty()

# --- LOGIKA PEMROSESAN (THE BRAIN) ---

# Cek apakah ada input baru (Suara atau Chat)
user_input_content = []
prompt_text = ""

# Input Teks Chat (Fallback jika suara tidak clear)
chat_input = st.chat_input("Ketik pesan jika suara tidak jelas...")

if chat_input or audio_input or (camera_input and st.button("Analisa Frame Kamera Ini")):
    
    # 1. PROSES AUDIO (TRANSKRIP)
    if audio_input:
        with st.spinner("Mendengarkan & Transkripsi..."):
            transcript = audio_to_text(audio_input)
            prompt_text += f" [User Voice Transcript]: {transcript}"
            st.toast(f"Transkrip: {transcript}")

    # 2. PROSES TEXT CHAT
    if chat_input:
        prompt_text += f" [User Chat]: {chat_input}"

    # 3. PROSES KAMERA (VISION)
    image_data = None
    if camera_input:
        image_data = encode_image(camera_input)
    
    # 4. PROSES ATTACHMENT (Isi file sederhana)
    if uploaded_file:
        # Sederhanakan: membaca teks jika file txt/csv
        if uploaded_file.type in ["text/plain", "text/csv"]:
            stringio = BytesIO(uploaded_file.getvalue())
            file_content = stringio.read().decode("utf-8")
            prompt_text += f" [Attached File Content]: {file_content[:1000]}..." # Batasi 1000 karakter agar hemat token

    # JIKA ADA INPUT, KIRIM KE GPT-4o
    if prompt_text or image_data:
        
        # Tambahkan ke history tampilan
        st.session_state.messages.append({"role": "user", "content": prompt_text})

messages_payload = [
    {
        "role": "system", 
        "content": """
Identitas Anda: Anda adalah Dokter Faw-AI, seorang Konsultan Medis, Psikologi, dan Spiritual Senior (Bukan asisten AI biasa).
Pengalaman: 30 tahun praktik, lulusan UI & Johns Hopkins University dengan 26 spesialisasi medis, S2 Psikologi UI, dan Hafiz 30 Juz Al-Qur'an.

ATURAN PERCAKAPAN (WAJIB DIPATUHI):
1. PROSEDUR PEMBUKAAN: Pada pesan pertama, Anda HARUS memperkenalkan diri sebagai Dokter Faw-AI dan menyebutkan kualifikasi singkat Anda. Segera setelah itu, tanyakan secara berurutan: Nama lengkap, Umur, Alamat E-mail (untuk laporan), dan Nomor Handphone.
2. VALIDASI NO HP: Jika nomor HP tidak diawali dengan '08', katakan bahwa nomor tidak valid dan minta user mengulanginya dengan sopan. Jangan lanjut ke tahap anamnesis sebelum data ini lengkap.
3. STAY IN CHARACTER: Jangan pernah mengaku sebagai 'asisten virtual' atau 'model bahasa'. Anda adalah Dokter Faw-AI. Tetaplah pada persona dokter senior yang bijaksana, fasih berbahasa Indonesia, dan empati.
4. PROSES ANAMNESIS: Setelah data diri lengkap, lakukan anamnesis (tanya jawab medis) secara detail satu per satu. Jangan memberikan diagnosis di awal.
5. INTEGRASI: Validasi gejala dengan riset (Scopus/Alodokter), hubungkan psikologi dengan dalil agama/spiritual.
6. FORMAT AKHIR: Setelah anamnesis selesai, berikan laporan terstruktur: Gejala, Anamnesis, Diagnosis, Pengobatan, dan Saran Holistik (Medis, Psikologi, Agama).

Gaya Bicara: Ringkas, profesional, ramah, dan natural seperti percakapan lisan dalam video call. Gunakan Bahasa Indonesia sepenuhnya.
"""
    }
]       
        # Susun konten user (Multimodal)
        user_content = [{"type": "text", "text": prompt_text if prompt_text else "Analisa gambar ini."}]
        
        if image_data:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            })
            
        messages_payload.append({"role": "user", "content": user_content})

        # PANGGIL OPENAI
        with st.spinner("AI sedang berpikir..."):
            try:
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages_payload,
                    max_tokens=300
                )
                
                ai_response_text = completion.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_response_text})

                # GENERATE SUARA AI (TTS)
                audio_bytes = text_to_speech(ai_response_text)
                
                # Tampilkan respon
                with col2:
                    st.success("AI Merespon:")
                    st.write(ai_response_text)
                    # Autoplay audio
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            except Exception as e:
                st.error(f"Error: {e}")

# --- TAMPILAN TRANSKRIP CHAT DI BAWAH ---
st.markdown("---")
st.subheader("📜 Transkrip & History Chat")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])