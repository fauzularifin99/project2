import streamlit as st
import openai
import base64
from io import BytesIO
from elevenlabs.client import ElevenLabs # Library resmi ElevenLabs
import asyncio #suara microsoft
import edge_tts #suara microsoft
import io #suara microsoft

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dokter Faw-AI - Konsultan Senior", layout="wide")

st.title("🩺 Dokter Faw-AI: Video Call Konsultasi Holistik")
st.markdown("Integrasi Medis, Psikologi, dan Spiritual (UI & Johns Hopkins)")

# --- SIDEBAR: KONFIGURASI API ---
with st.sidebar:
    st.header("⚙️ Pengaturan API")
    openai_key = st.text_input("Masukkan OpenAI API Key", type="password")
    eleven_key = st.text_input("Masukkan ElevenLabs API Key", type="password")
    
    st.markdown("---")
    if st.button("🗑️ Reset Konsultasi (Mulai Ulang)"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### 📎 Upload Lampiran")
    uploaded_file = st.file_uploader("Upload Hasil Lab/Foto Gejala", type=['txt', 'png', 'jpg'])

# --- FUNGSI BANTUAN ---

#def text_to_speech_eleven(text, api_key):
#    """Menggunakan SDK resmi ElevenLabs untuk suara Dokter Faw-AI"""
#    if not api_key:
#        return None
#    try:
#        client_el = ElevenLabs(api_key=api_key)
#        # Suara 'Marcus' (Pria, Tua, Bijaksana, Berwibawa)
#        audio_generator = client_el.text_to_speech.convert(
#            text=text,
#            voice_id="pNInz6obpgDQGcFmaJgB", 
#            model_id="eleven_multilingual_v2",
#            output_format="mp3_44100_128",
#            voice_settings={
#                "stability": 0.6,
#                "similarity_boost": 0.8,
#                "style": 0.0,
#                "use_speaker_boost": True
#            }
#        )
#        return b"".join(list(audio_generator))
#    except Exception as e:
#        st.error(f"Gagal generate suara: {e}")
#        return None

#def text_to_speech(text):
#    """Mengubah respon text AI menjadi suara"""
#    response = client.audio.speech.create(
#        #model="tts-1",
#        #voice="nova", # Pilihan suara: alloy, echo, fable, onyx, nova, shimmer
#        #input=text
#        model="gpt-4o-mini-tts",     # ganti dari "tts-1"
#        voice="sage",               # coba: sage / coral / alloy / nova (tiap voice beda nuansa)
#        instructions="Gunakan Bahasa Indonesia baku, aksen Indonesia netral, intonasi natural seperti penutur lokal. Jangan terdengar seperti aksen asing.",
#        input=text,
#        response_format="mp3"
#   )
#    return response.content

def text_to_speech(text):
    """Menggunakan Microsoft Edge TTS (Gratis & Aksen Indo Alami)"""
    # Nama suara untuk pria Indonesia yang berwibawa
    VOICE = "id-ID-ArdiNeural"
    #VOICE = "id-ID-GadisNeural" 
    rate_str = f"20%"
    
    async def _generate():
        communicate = edge_tts.Communicate(text, VOICE)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    # Menjalankan fungsi async di dalam fungsi sync Streamlit
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_generate())
        loop.close()
        return audio_bytes
    except Exception as e:
        st.error(f"Gagal generate suara Edge-TTS: {e}")
        return None

def audio_to_text(audio_file, client):
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        language="id"
    )
    return transcription.text

def encode_image(image_buffer):
    return base64.b64encode(image_buffer.getvalue()).decode('utf-8')

# --- INITIALIZE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LAYOUT UTAMA ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("👤 Pasien")
    camera_input = st.camera_input("Kamera (Scan Gejala/Wajah)")
    audio_input = st.audio_input("Bicara dengan Dokter")

with col2:
    st.header("👨‍⚕️ Dokter Faw-AI")
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=120)
    ai_response_container = st.empty()

# --- LOGIKA PEMROSESAN ---
chat_input = st.chat_input("Ketik pesan di sini...")

if chat_input or audio_input or camera_input:
    if not openai_key:
        st.error("Masukkan OpenAI API Key di sidebar!")
    else:
        client = openai.OpenAI(api_key=openai_key)
        prompt_text = ""

        if audio_input:
            prompt_text += f" [Suara Pasien]: {audio_to_text(audio_input, client)}"
        if chat_input:
            prompt_text += f" {chat_input}"

        image_data = encode_image(camera_input) if camera_input else None

        # SYSTEM PROMPT (Identitas 35 Kriteria)
        SYSTEM_PROMPT = """Anda adalah Dokter Faw-AI, Konsultan Medis, Psikologi, dan Spiritual Senior dengan praktik 30 tahun.
Lulusan: Dokter Umum UI, Spesialis ganda UI & Johns Hopkins (26 Spesialisasi), S1 & S2 Psikologi UI, Hafiz 30 Juz Al-Qur'an.

PROSEDUR WAJIB:
1. PERKENALAN: Di awal, perkenalkan diri sebagai Dokter Faw-AI dan kualifikasi Anda secara singkat dan berwibawa. cukup sekali saja pas awal sekali.
2. PENDAFTARAN: Wajib tanyakan Nama, Umur, Email, dan No HP. 
3. VALIDASI HP: Jika No HP tidak diawali '08', minta ulang dengan sopan. Jangan lanjut ke medis sebelum data ini valid.
4. ANAMNESIS: Lakukan tanya jawab medis mendalam secara bertahap (satu pertanyaan setiap satu respon dan jangan dibilang explisit satu pertanyaan lagi. mengalir saja).
5. REFERENSI: Gunakan riset mutakhir (Scopus/Alodokter atau materi kuliah kedokteran). Hubungkan psikologi dengan dalil Al-Qur'an/Hadist.
6. FORMAT LAPORAN AKHIR: Gejala, Anamnesis, Diagnosis, Pengobatan, dan Saran Holistik (Medis, Psikologi, Agama).

Gaya bicara: Profesional, tenang, empati, fasih Bahasa Indonesia tanpa logat asing."""

        # Bangun Payload dengan History
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            messages_payload.append({"role": msg["role"], "content": msg["content"]})

        user_content = [{"type": "text", "text": prompt_text if prompt_text else "Analisis gambar ini."}]
        if image_data:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
        
        messages_payload.append({"role": "user", "content": user_content})

        with st.spinner("Dokter Faw-AI sedang menganalisis..."):
            try:
                response = client.chat.completions.create(model="gpt-5.2",messages=messages_payload,max_completion_tokens=1200,temperature=0.2)
                ai_text = response.choices[0].message.content
                
                # Simpan ke history
                st.session_state.messages.append({"role": "user", "content": prompt_text})
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

                # Tampilkan & Putar Suara
                with col2:
                    st.success("Tanggapan Dokter:")
                    st.write(ai_text)
                    #audio_bytes = text_to_speech_eleven(ai_text, eleven_key)
                    audio_bytes = text_to_speech(ai_text)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            except Exception as e:
                st.error(f"Kesalahan: {e}")

# --- HISTORY ---
st.markdown("---")
st.subheader("📜 Riwayat Konsultasi")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])