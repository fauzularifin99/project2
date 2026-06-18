import streamlit as st
import openai
import base64
import asyncio
import edge_tts
import io
#v2 record gambar
# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="LabsBuddies - Kami Ada Untuk Kamu", layout="wide")

# Custom CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .stChatFloatingInputContainer {padding-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ LabsBuddies: Sahabat Pendamping Siswa")
st.markdown("### Ekosistem Sekolah Ramah Anak Berbasis AI (NLP)")

# --- INITIALIZE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: KONFIGURASI API ---
with st.sidebar:
    st.header("⚙️ Pengaturan Sistem")
    openai_key = st.text_input("Masukkan OpenAI API Key", type="password")
    
    st.markdown("---")
    if st.button("🗑️ Reset Konsultasi (Mulai Ulang)"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### 📎 Lampiran Tambahan")
    uploaded_file = st.file_uploader("Upload Bukti/Tangkapan Layar", type=['png', 'jpg', 'jpeg'])

# --- FUNGSI BANTUAN ---

def text_to_speech(text):
    """Menggunakan Microsoft Edge TTS dengan efisiensi tinggi"""
    VOICE = "id-ID-ArdiNeural"
    rate = "+10%" 
    
    async def _generate():
        communicate = edge_tts.Communicate(text, VOICE, rate=rate)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        audio_bytes = loop.run_until_complete(_generate())
        return audio_bytes
    except Exception as e:
        return None

def audio_to_text(audio_file, client):
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        language="id"
    )
    return transcription.text

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# --- SYSTEM PROMPT (Inti Logika Penelitian) ---
SYSTEM_PROMPT = """Anda adalah LabsBuddies, sistem kecerdasan buatan (AI) pendamping siswa yang ahli dalam Psikologi Pendidikan dan Deteksi Dini Kesehatan Mental. Anda merupakan instrumen pendukung Sekolah Ramah Anak (SRA).
IDENTITAS & MISI:
1. Membangun ekosistem sekolah yang aman sesuai semangat SE Mendikdasmen No. 4 Tahun 2026 dan lagu "Rukun Sama Teman".
2. Menjadi pendengar yang empati, tidak menghakimi, dan mampu memahami bahasa gaul/slang remaja tanpa kehilangan sisi profesional.
PROSEDUR WAJIB:
1. PERKENALAN: Sapa sebagai "Sahabat LabsBuddies". Jelaskan ini ruang aman.
2. PENGUMPULAN DATA: Wajib tanyakan Nama/Inisial, Kelas, Email, dan No HP (format 08). Ini krusial untuk emergency.
3. KONSULTASI : tanya apa yang sedang dirasakan saat ini. (Lakukan secara mengalir)
3. DETEKSI DARURAT: Jika melihat darah, senjata, atau tanda bahaya di gambar/teks, segera beri alert keras dan minta berhenti.
4. KLASIFIKASI (WAJIB DI AKHIR): 
   - [STATUS: AMAN] (Normal)
   - [STATUS: PERINGATAN] (Indikasi bullying ringan/sedih)
   - [STATUS: BAHAYA] (Ancaman fisik/self-harm)
5. Gaya bicara: Empati, Gen-Z friendly, santai tapi sopan. Maksimal 3 paragraf.
Sesuai SE Mendikdasmen No. 4 Tahun 2026 tentang Rukun Sama Teman.

REFERENSI & TONE:
- Gunakan pendekatan psikologi remaja yang berlandaskan empati.
- Jika terdeteksi masalah, selipkan pesan moral tentang kebersamaan (Rukun Sama Teman).
- Gaya bicara: Santai tapi sopan, cerdas, dan suportif. Hindari bahasa yang terlalu klinis seperti dokter medis.

FORMAT LAPORAN AKHIR (Dashboard Guru BK):
Berikan ringkasan di akhir sesi (hanya untuk log sistem):
- Identitas Siswa:
- Jenis Temuan: (Cyberbullying/Verbal/Emotional Distress)
- Skor Risiko: (Aman/Warning/Danger)
- Rekomendasi Tindakan: (Pendampingan Guru BK/Mediasi/Dukungan Psikologis)"""

# --- LAYOUT UTAMA ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("👤 Input Siswa")
    camera_input = st.camera_input("Ambil Foto (Jika ada bukti/gejala visual)")
    audio_input = st.audio_input("Cerita lewat Suara")

with col2:
    st.header("🤖 LabsBuddies")
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    ai_response_container = st.empty()

# --- LOGIKA PEMROSESAN ---
chat_input = st.chat_input("Ketik di sini (misal: 'Aku lagi sedih karena di kelas...')")

if chat_input or audio_input or camera_input:
    if not openai_key:
        st.error("Silakan masukkan API Key di sidebar!")
    else:
        client = openai.OpenAI(api_key=openai_key)
        
        # 1. Kumpulkan Teks
        user_text = ""
        if audio_input:
            user_text += f" [Audio]: {audio_to_text(audio_input, client)}"
        if chat_input:
            user_text += f" {chat_input}"
        if not user_text and camera_input:
            user_text = "Analisis gambar yang saya lampirkan."

        # 2. Simpan ke History (SEGERA)
        new_user_message = {"role": "user", "content": user_text}
        if camera_input:
            new_user_message["image"] = camera_input
        st.session_state.messages.append(new_user_message)

        # 3. Siapkan Payload untuk AI
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Masukkan history sebelumnya
        for msg in st.session_state.messages:
            content_list = [{"type": "text", "text": msg["content"]}]
            if "image" in msg:
                img_b64 = encode_image(msg["image"])
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
            messages_payload.append({"role": msg["role"], "content": content_list})

        # 4. Panggil AI dengan Streaming
        try:
            with col2:
                st.info("LabsBuddies sedang menganalisis...")
                stream = client.chat.completions.create(
                    model="gpt-5.2",
                    messages=messages_payload,
                    temperature=0.5,
                    stream=True
                )
                ai_text = st.write_stream(stream)
                
            # Simpan jawaban AI ke history
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

            # Putar Suara
            audio_bytes = text_to_speech(ai_text)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
            
            # Rerun untuk update scroll history di bawah
            st.rerun()

        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")

# --- HISTORY (SCROLLABLE) ---
st.markdown("---")
st.subheader("📜 Riwayat Percakapan")

with st.container(height=500):
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "image" in msg and msg["image"]:
                st.image(msg["image"], caption="Lampiran Visual", width=250)

# --- FOOTER (OPSI) ---
st.caption("Penelitian OPSI 2026 - Pengembangan Purwarupa Deteksi Dini Bullying & Distress")