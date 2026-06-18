import streamlit as st
import openai
import base64
import asyncio
import edge_tts

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="LabsBuddies", layout="wide")
st.title("LabsBuddies: Sahabat Pendamping Siswa")

# --- 2. INISIALISASI MEMORI (STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Kita butuh memori untuk mencatat input TERAKHIR supaya tidak diproses ulang
if "last_img_id" not in st.session_state:
    st.session_state.last_img_id = None
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Pengaturan")
    openai_key = st.text_input("OpenAI API Key", type="password")
    if st.button("Hapus Riwayat"):
        st.session_state.messages = []
        st.session_state.last_img_id = None
        st.session_state.last_audio_id = None
        st.rerun()

# --- 4. FUNGSI PENTING ---
def text_to_speech(text):
    """Mengubah teks jadi suara (Ardi)"""
    VOICE = "id-ID-ArdiNeural"
    async def _generate():
        communicate = edge_tts.Communicate(text, VOICE, rate="+10%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_generate())
    except: return None

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def audio_to_text(audio_file, client):
    audio_file.seek(0)
    return client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="id").text

# --- 5. SYSTEM PROMPT ---
SYSTEM_PROMPT = """pip install flask openai.
IDENTITAS & MISI:
1. Membangun ekosistem sekolah yang aman sesuai semangat SE Mendikdasmen No. 4 Tahun 2026 dan lagu "Rukun Sama Teman".
2. Menjadi pendengar yang empati, tidak menghakimi, dan mampu memahami bahasa gaul/slang remaja tanpa kehilangan sisi profesional.
PROSEDUR WAJIB:
1. PERKENALAN: Sapa sebagai "Sahabat LabsBuddies". Jelaskan ini ruang aman. Perkenalan hanya 1x saja. tidak perlu diulang-ulang
2. PENGUMPULAN DATA: Wajib tanyakan Nama/Inisial, Kelas, Email, dan No HP (format 08). Ini krusial untuk emergency.
3. KONSULTASI : tanya apa yang sedang dirasakan saat ini. (Lakukan secara mengalir, satu pertanyaan lalu dijawab dan baru tanya 1 pertanyaan lain lagi. dilarang bertanya lebih dari 1 pertanyaan di satu response)
4. Setelah 3 pertanyaan, tawarkan apakah mau berhenti tanya jawab dan langsung ke rekomendasi atau lanjut tanya jawab.
5. DETEKSI DARURAT: Jika melihat darah, senjata, atau tanda bahaya di gambar/teks, segera beri alert keras dan minta berhenti.
6. KLASIFIKASI (WAJIB DI AKHIR): 
   - [STATUS: AMAN] (Normal)
   - [STATUS: PERINGATAN] (Indikasi bullying ringan/sedih)
   - [STATUS: BAHAYA] (Ancaman fisik/self-harm)
7. Gaya bicara: Empati, Gen-Z friendly, santai tapi sopan. Maksimal 3 paragraf.
8. Sesuai SE Mendikdasmen No. 4 Tahun 2026 tentang Rukun Sama Teman.

REFERENSI & TONE:
- Gunakan pendekatan psikologi remaja yang berlandaskan empati.
- Jika terdeteksi masalah, selipkan pesan moral tentang kebersamaan (Rukun Sama Teman).
- Gaya bicara: Santai tapi sopan, cerdas, dan suportif. Hindari bahasa yang terlalu klinis seperti dokter medis.

FORMAT LAPORAN AKHIR (Dashboard Guru BK dan hanya di akhir sesi):
Berikan ringkasan di akhir sesi (hanya untuk log sistem):
- Identitas Siswa:
- Jenis Temuan: (Cyberbullying/Verbal/Emotional Distress)
- Skor Risiko: (Aman/Warning/Danger)
- Rekomendasi Tindakan: (Pendampingan Guru BK/Mediasi/Dukungan Psikologis)"""

# --- 6. LAYOUT INPUT ---
col1, col2 = st.columns([1, 1])

with col1:
    #st.info("📸 Ambil Foto (Klik 'Clear' aman, tidak akan error)")
    camera_input = st.camera_input("Kamera")
    
    #st.info("mic Rekam Suara")
    audio_input = st.audio_input("Rekam")

with col2:
    st.subheader("Respons LabsBuddies")
    ai_container = st.container()

# Input Chat (Paling Bawah)
chat_input = st.chat_input("Ketik curhatanmu di sini...")

# --- 7. LOGIKA PROSES (VALIDASI KETAT) ---

# Variabel penentu
input_type = None
final_content = ""

# A. Cek Input Teks (Prioritas 1)
if chat_input:
    input_type = "text"
    final_content = chat_input

# C. Cek Input Audio (Hanya proses jika ADA AUDIO dan AUDIONYA BARU)
elif audio_input is not None:
    current_audio_bytes = audio_input.getvalue()
    
    if current_audio_bytes != st.session_state.last_audio_id:
        st.session_state.last_audio_id = current_audio_bytes # Update memori
        if openai_key:
            # Kita proses transkrip di sini agar tidak memanggil API jika audionya lama
            client = openai.OpenAI(api_key=openai_key)
            final_content = f"[Suara]: {audio_to_text(audio_input, client)}"
            input_type = "audio"
    else:
        pass

# B. Cek Input Kamera (Hanya proses jika ADA GAMBAR dan GAMBARNYA BARU)
elif camera_input is not None:
    # Ambil data gambar
    current_img_bytes = camera_input.getvalue()
    
    # Cek: Apakah ini gambar baru? Atau gambar lama yang belum dicari?
    if current_img_bytes != st.session_state.last_img_id:
        st.session_state.last_img_id = current_img_bytes # Update memori
        input_type = "image"
        final_content = "Tolong analisis gambar yang saya kirim ini."
    else:
        # Kalau gambarnya sama persis dengan yang barusan diproses, JANGAN PROSES LAGI.
        pass


# D. JIKA KAMERA DI-CLEAR (camera_input jadi None)
elif camera_input is None:
    # Reset memori gambar supaya kalau ambil foto baru dianggap baru
    st.session_state.last_img_id = None


# --- 8. EKSEKUSI KE CHATGPT ---
# Kita hanya jalan kalau input_type SUDAH TERISI (Artinya valid)
if input_type and final_content:
    if not openai_key:
        st.error("⚠️ Masukkan API Key dulu!")
    else:
        client = openai.OpenAI(api_key=openai_key)

        # 1. Masukkan ke Riwayat User
        user_msg = {"role": "user", "content": final_content}
        if input_type == "image":
            user_msg["image"] = camera_input # Simpan objek gambar
        st.session_state.messages.append(user_msg)

        # 2. Susun Payload
        payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in st.session_state.messages:
            content = [{"type": "text", "text": m["content"]}]
            if "image" in m:
                # Encode gambar hanya jika ada
                b64 = encode_image(m["image"])
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
            payload.append({"role": m["role"], "content": content})

        # 3. Kirim ke AI
        with ai_container:
            with st.spinner("LabsBuddies sedang menganalisis..."):
                try:
                    stream = client.chat.completions.create(
                        model="gpt-5.2", messages=payload, stream=True, temperature=0.5
                    )
                    response_text = st.write_stream(stream)
                    
                    # Simpan Jawaban
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    # 4. Putar Suara
                    audio_bytes = text_to_speech(response_text)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

# --- 9. TAMPILKAN RIWAYAT ---
st.markdown("---")
st.subheader("📜 Riwayat")
with st.container(height=400):
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "image" in msg:
                st.image(msg["image"], width=200)