import streamlit as st
import openai
import base64
from io import BytesIO
from elevenlabs.client import ElevenLabs # Library resmi ElevenLabs
import asyncio #suara microsoft
import edge_tts #suara microsoft
import io #suara microsoft

#v1labsbuddies streaming
# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="LabsBuddies - Kami Ada Untuk Kamu", layout="wide")

st.title("🩺 LabsBuddies: Video Call Konsultasi Psikologi")
st.markdown("Ada Masalah, Curhatin Aja)")

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
    """Menggunakan Microsoft Edge TTS dengan efisiensi tinggi"""
    VOICE = "id-ID-ArdiNeural"
    # Meningkatkan kecepatan sedikit (rate=+10%) agar tidak terlalu lambat saat teks panjang
    rate = "+10%" 
    
    async def _generate():
        communicate = edge_tts.Communicate(text, VOICE, rate=rate)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    try:
        # Optimasi loop agar tidak membuat loop baru terus-menerus jika sudah ada
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        audio_bytes = loop.run_until_complete(_generate())
        return audio_bytes
    except Exception as e:
        st.error(f"Gagal generate suara: {e}")
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
    camera_input = st.camera_input("Kamera")
    audio_input = st.audio_input("Bicara dengan LabsBuddies")

with col2:
    st.header("LabsBuddies")
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
        SYSTEM_PROMPT = """Anda adalah LabsBuddies, sistem kecerdasan buatan (AI) pendamping siswa yang ahli dalam Psikologi Pendidikan dan Deteksi Dini Kesehatan Mental. Anda merupakan instrumen pendukung Sekolah Ramah Anak (SRA) yang dirancang untuk mendeteksi pola perundungan (bullying) dan gangguan emosional (distress).

        IDENTITAS & MISI:
        1. Membangun ekosistem sekolah yang aman sesuai semangat SE Mendikdasmen No. 4 Tahun 2026 dan lagu "Rukun Sama Teman".
        2. Menjadi pendengar yang empati, tidak menghakimi, dan mampu memahami bahasa gaul/slang remaja tanpa kehilangan sisi profesional.

        PROSEDUR ANALISIS (ALGORITMA NLP):
        1. PERKENALAN: Sapa pengguna dengan hangat sebagai "Sahabat LabsBuddies". Jelaskan bahwa ini adalah ruang aman untuk bercerita.
        2. PENGUMPULAN DATA: Tanyakan Nama (atau Inisial), Kelas, alamat e-mail dan nomer HP ( format diawali dengan 08) dan apa yang sedang dirasakan saat ini. (Lakukan secara mengalir). alamat e-mail dan nomer HP sangat penting harus diisi untuk kondisi emergency.
        3. DETEKSI MULTIMODAL: 
        - Analisis teks/suara untuk mencari pola intimidasi, sarkasme, isolasi sosial, atau ancaman fisik.
        - Analisis input gambar jika ada, untuk melihat ekspresi distress atau bukti perundungan visual.
        - Jika analisa teks, gambar dan suara menunjukkan hal darurat, segera munculkan alert (misal ada darah, gunting, silet, benda tajam ) dan minta pengguna untuk berhenti melakukan tindakan yang tidak diinginkan. 
        4. DIALOG SKRINING: Lakukan tanya jawab bertahap (satu per satu) untuk mendalami apakah masalahnya bersifat verbal, fisik, atau cyber-bullying.
        5. Berikan jawaban maksimal 3 paragraf kecuali diminta mendalam 
        6. KLASIFIKASI STATUS (WAJIB ADA DI AKHIR): 
        Setiap sesi harus menghasilkan penilaian risiko internal:
        - [STATUS: AMAN] Jika interaksi bersifat positif/normal.
        - [STATUS: PERINGATAN] Jika ada indikasi perundungan ringan atau kesedihan mendalam.
        - [STATUS: BAHAYA] Jika ada ancaman fisik, pelecehan berat, atau indikasi menyakiti diri sendiri.

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

        # Bangun Payload dengan History
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            messages_payload.append({"role": msg["role"], "content": msg["content"]})

        user_content = [{"type": "text", "text": prompt_text if prompt_text else "Analisis gambar ini."}]
        if image_data:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})
        
        messages_payload.append({"role": "user", "content": user_content})

        with st.spinner("LabsBuddies sedang berpikir..."):
            try:
                # Gunakan stream=True pada API OpenAI
                stream = client.chat.completions.create(
                    model="gpt-5.2",
                    messages=messages_payload,
                    temperature=0.5,
                    stream=True # Mengaktifkan streaming teks
                )
                
                # Tampilkan teks secara streaming
                with col2:
                    st.success("Tanggapan LabsBuddies:")
                    # placeholder untuk menampung teks yang mengalir
                    ai_text = st.write_stream(stream) 
                    
                # --- DI DALAM LOGIKA PEMROSESAN (setelah mendapatkan ai_text) ---
                # Simpan ke history dengan struktur yang mendukung gambar
                user_message = {"role": "user", "content": prompt_text}
                if camera_input:
                    user_message["image"] = camera_input # Simpan objek gambar ke history

                st.session_state.messages.append(user_message)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

                # Baru jalankan audio setelah teks selesai (masking latency)
                audio_bytes = text_to_speech(ai_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            except Exception as e:
                st.error(f"Kesalahan: {e}")



# --- HISTORY (DIBUAT SCROLLABLE & MENDUKUNG GAMBAR) ---
st.markdown("---")
st.subheader("📜 Riwayat Konsultasi")

with st.container(height=500):
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Tampilkan teks jika ada
            if "content" in msg and msg["content"]:
                st.write(msg["content"])
            
            # Tampilkan gambar jika ada (khusus pesan user)
            if "image" in msg and msg["image"]:
                st.image(msg["image"], caption="Lampiran Foto/Tangkapan Kamera", width=200)