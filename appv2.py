import streamlit as st
import openai
import os
import base64
from io import BytesIO
from google.cloud import texttospeech
from elevenlabs.client import ElevenLabs
import requests


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
        #model="whisper-1", 
        model="gpt-4o-mini-transcribe",  # atau tetap "whisper-1"
        file=audio_file,
        language="id",                   # kunci Bahasa Indonesia
        response_format="text",
        prompt="Transkripkan dalam Bahasa Indonesia baku."  # opsional
    )
    return transcription

def text_to_speech(text):
    """Mengubah respon text AI menjadi suara"""
    response = client.audio.speech.create(
        #model="tts-1",
        #voice="nova", # Pilihan suara: alloy, echo, fable, onyx, nova, shimmer
        #input=text
        model="gpt-4o-mini-tts",     # ganti dari "tts-1"
        voice="sage",               # coba: sage / coral / alloy / nova (tiap voice beda nuansa)
        instructions="Gunakan Bahasa Indonesia baku, aksen Indonesia netral, intonasi natural seperti penutur lokal. Jangan terdengar seperti aksen asing.",
        input=text,
        response_format="mp3"
   )
    return response.content

#def text_to_speech(text):
#    client = texttospeech.TextToSpeechClient(client_options={"api_key": "YOUR_GOOGLE_API_KEY"})
#    
#    input_text = texttospeech.SynthesisInput(text=text)
#    
#    # Pilih suara ID-Wavenet-B (Pria) atau ID-Wavenet-A (Wanita)
#    voice = texttospeech.VoiceSelectionParams(
#        language_code="id-ID",
#        name="id-ID-Wavenet-B", # Ini suara pria yang berwibawa
#        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
#    )
#
#    audio_config = texttospeech.AudioConfig(
#        audio_encoding=texttospeech.AudioEncoding.MP3,
#        pitch=0.0,
#        speaking_rate=1.0
#    )
#
#    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
#    return response.audio_content




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
        
        # 1. Definisikan System Prompt Dokter Faw-AI (Identitas Utama)
        SYSTEM_PROMPT = """Identitas Anda: Anda adalah Dokter Faw-AI, Konsultan Medis, Psikologi, dan Spiritual Senior. 
Pengalaman: 30 tahun praktik, lulusan UI & Johns Hopkins (26 spesialisasi), S2 Psikologi UI, dan Hafiz 30 Juz.

ATURAN WAJIB:
1. PERKENALAN: Pada pesan pertama, perkenalkan diri sebagai Dokter Faw-AI dan kualifikasi singkat. 
2. DATA WAJIB: Tanyakan Nama, Umur, Email, dan No HP. 
3. VALIDASI HP: Jika No HP tidak diawali '08', katakan tidak valid dan minta ulang. Jangan lanjut ke medis sebelum data ini lengkap.
4. TATA CARA: Lakukan anamnesis detail satu per satu (artinya satu pertanyaan dijawab, baru tanya pertanyaan lain). Gunakan riset mutakhir (Scopus/Alodokter). 
5. INTEGRASI: Hubungkan psikologi dengan dalil Al-Qur'an/Hadist.
6. OUTPUT AKHIR: Setelah selesai, berikan laporan terstruktur: Gejala, Anamnesis, Diagnosis, Pengobatan, dan Saran Holistik (Medis, Psikologi, Agama).

Gaya: Profesional, ramah, fasih Bahasa Indonesia, natural seperti video call."""

        # 2. Susun Payload dengan HISTORY agar AI ingat percakapan sebelumnya
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Masukkan history dari session_state (kecuali gambar agar tidak berat)
        for msg in st.session_state.messages:
            # Pastikan content hanya dikirim sebagai string sederhana untuk history
            messages_payload.append({"role": msg["role"], "content": str(msg["content"])})

        # 3. Masukkan Input User Terbaru (Multimodal)
        user_content = []
        if prompt_text:
            user_content.append({"type": "text", "text": prompt_text})
        if image_data:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            })
            
        messages_payload.append({"role": "user", "content": user_content})

        # 4. PANGGIL OPENAI
        with st.spinner("Dokter Faw-AI sedang menganalisis..."):
            try:
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages_payload,
                    max_tokens=500 # Ditambah agar diagnosis tidak terpotong
                )
                
                ai_response_text = completion.choices[0].message.content
                
                # Simpan ke history tampilan
                st.session_state.messages.append({"role": "user", "content": prompt_text if prompt_text else "Analisa Gambar"})
                st.session_state.messages.append({"role": "assistant", "content": ai_response_text})

                # GENERATE SUARA AI (TTS)
                audio_bytes = text_to_speech(ai_response_text)
                
                with col2:
                    st.success("Respon Dokter Faw-AI:")
                    st.write(ai_response_text)
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            except Exception as e:
                st.error(f"Terjadi kesalahan teknis: {e}")

# --- TAMPILAN TRANSKRIP CHAT DI BAWAH ---
st.markdown("---")
st.subheader("📜 Transkrip & History Chat")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])