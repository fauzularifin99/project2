import os
from datetime import datetime
import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI
from pypdf import PdfReader
import math
from supabase import create_client

st.set_page_config(page_title="Admin Belajar", layout="wide")

# =========================
# KONFIGURASI
# =========================
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
OPENAI_KEY = st.secrets["OPENAI_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

client = OpenAI(api_key=OPENAI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# LOGIN ADMIN
# =========================
if "admin_login" not in st.session_state:
    st.session_state.admin_login = False

st.title("Halaman Admin Belajar")

if st.session_state.admin_login is False:
    password = st.text_input("Password admin", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_login = True
            st.rerun()
        else:
            st.error("Password salah")
    st.stop()


# =========================
# FUNGSI BANTU
# =========================
def ambil_text_dari_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text("\n")
        lines = [x.strip() for x in text.splitlines()]
        lines = [x for x in lines if x != ""]
        hasil = "\n".join(lines)
        return hasil[:50000]
    except Exception as e:
        return f"ERROR_URL: {str(e)}"


def ringkas_text(text):
    if text.strip() == "":
        return ""

    prompt = f"""

Anda adalah asisten knowledge base untuk chatbot pendamping siswa, konseling sekolah, dan asesmen awal berbasis DASS-21.

Baca seluruh materi berikut secara teliti dan buat ringkasan yang lengkap, faktual, dan dapat dipakai sebagai referensi chatbot.

Aturan penting:

1. Jangan mengarang informasi di luar materi.
2. Jangan membuat ringkasan terlalu pendek.
3. Jangan hanya merangkum bagian awal.
4. Ambil seluruh informasi penting dari materi inti.
5. Abaikan bagian yang tidak berkaitan langsung dengan materi inti, seperti kata pengantar, daftar isi, daftar pustaka, informasi hak cipta, informasi penerbit, ucapan terima kasih, biodata penulis, nomor ISBN, riwayat cetakan, lampiran administratif, atau bagian lain yang hanya bersifat formalitas dokumen.
6. Jangan memasukkan informasi administratif dokumen ke dalam ringkasan kecuali memang berpengaruh langsung terhadap pemahaman materi.
7. Pertahankan istilah psikologi, definisi, gejala, indikator, risiko, rekomendasi, dan langkah penanganan.
8. Jika materi membahas depresi, kecemasan, stres, self-harm, bunuh diri, bullying, keluarga, sekolah, atau remaja, jelaskan dengan detail.
9. Jika ada skala, kategori, skor, kriteria, atau klasifikasi, tuliskan kembali dengan jelas.
10. Jika ada rekomendasi untuk guru BK, orang tua, wali kelas, psikolog, atau tenaga profesional, tuliskan secara lengkap.
11. Jika ada kondisi darurat atau tanda bahaya, tuliskan secara tegas.
12. Tulis dengan Bahasa Indonesia yang rapi dan mudah dipakai oleh chatbot.

Format ringkasan:
1. Topik Utama Materi
Jelaskan topik utama dari materi.
2. Tujuan Materi
Jelaskan tujuan atau kegunaan materi.
3. Konsep dan Definisi Penting
Tuliskan semua konsep, istilah, dan definisi penting.
4. Gejala, Indikator, atau Tanda-Tanda
Tuliskan semua gejala, indikator, ciri, atau tanda yang disebutkan.
5. Kategori, Level, atau Klasifikasi
Tuliskan semua kategori, level risiko, jenis gangguan, skor, atau klasifikasi yang ada.
6. Faktor Penyebab atau Faktor Risiko
Tuliskan faktor penyebab, pemicu, atau faktor risiko yang dijelaskan.
7. Dampak yang Mungkin Terjadi
Tuliskan dampak terhadap siswa, emosi, perilaku, akademik, relasi sosial, keluarga, dan kesehatan.
8. Rekomendasi Penanganan
Tuliskan langkah penanganan, dukungan, intervensi, atau saran praktis.
9. Tanda Bahaya / Kondisi Darurat
Tuliskan kondisi yang harus segera mendapat perhatian, terutama jika terkait menyakiti diri sendiri, bunuh diri, kekerasan, atau kondisi krisis.
10. Panduan untuk Chatbot
Tuliskan bagaimana chatbot sebaiknya menggunakan materi ini saat menjawab siswa.
11. Kesimpulan
Buat kesimpulan akhir yang lengkap dan faktual.    

Materi:
{text}
"""

    response = client.responses.create(
        model="gpt-5.4-nano",
        input=prompt
    )
    return response.output_text


def ambil_konteks_aktif():
    result = supabase.table("sumber_belajar").select("judul,isi").eq("status", "AKTIF").order("id", desc=True).execute()

    konteks = ""
    nomor = 1
    for row in result.data:
        judul = row["judul"]
        isi = row["isi"] or ""
        konteks += f"\n\nSUMBER {nomor}: {judul}\n{isi[:5000]}"
        nomor += 1

    return konteks


def simpan_sumber_belajar(jenis, judul, sumber, isi, ringkasan, catatan):
    supabase.table("sumber_belajar").insert({
        "jenis": jenis,
        "judul": judul,
        "sumber": sumber,
        "isi": isi,
        "ringkasan": ringkasan,
        "catatan": catatan,
        "status": "AKTIF",
        "dibuat_pada": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }).execute()


# =========================
# MENU
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "Paste Text",
    "Upload File Text atau PDF",
    "Input URL",
    "History Belajar"
])


# =========================
# TAB 1 - PASTE TEXT
# =========================
with tab1:
    st.subheader("Tambah Materi dari Paste Text")
    judul_text = st.text_input("Judul materi", key="judul_text")
    isi_text = st.text_area("Paste text di sini", height=300, key="isi_text")
    catatan_text = st.text_input("Catatan / ChatGPT nanti dipakai untuk apa", key="catatan_text")

    if st.button("Simpan Paste Text"):
        if judul_text == "" or isi_text == "":
            st.error("Judul dan isi wajib diisi")
        else:
            ringkasan = ringkas_text(isi_text)
            simpan_sumber_belajar(
                "TEXT",
                judul_text,
                "PASTE_TEXT",
                isi_text,
                ringkasan,
                catatan_text
            )
            st.success("Materi text berhasil disimpan")


# =========================
# TAB 2 - UPLOAD FILE TEXT / PDF
# =========================
with tab2:
    st.subheader("Tambah Materi dari Upload File")
    judul_file = st.text_input("Judul file", key="judul_file")
    file_upload = st.file_uploader("Upload file txt / md / pdf", type=["txt", "md", "pdf"])
    catatan_file = st.text_input("Catatan / dipakai untuk apa", key="catatan_file")

    if st.button("Simpan File Upload"):
        if judul_file == "" or file_upload is None:
            st.error("Judul dan file wajib diisi")
        else:
            if file_upload.name.endswith(".pdf"):
                reader = PdfReader(file_upload)
                isi_file = ""

                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        isi_file += page_text + "\n"
            else:
                isi_file = file_upload.read().decode("utf-8", errors="ignore")

            ringkasan = ringkas_text(isi_file)
            simpan_sumber_belajar(
                "FILE",
                judul_file,
                file_upload.name,
                isi_file,
                ringkasan,
                catatan_file
            )
            st.success("File berhasil disimpan")


# =========================
# TAB 3 - INPUT URL
# =========================
with tab3:
    st.subheader("Tambah Materi dari URL")
    judul_url = st.text_input("Judul URL", key="judul_url")
    input_url = st.text_input("URL", key="input_url")
    catatan_url = st.text_input("Catatan / dipakai untuk apa", key="catatan_url")

    if st.button("Ambil dan Simpan URL"):
        if judul_url == "" or input_url == "":
            st.error("Judul dan URL wajib diisi")
        else:
            isi_url = ambil_text_dari_url(input_url)
            if isi_url.startswith("ERROR_URL:"):
                st.error(isi_url)
            else:
                ringkasan = ringkas_text(isi_url)
                simpan_sumber_belajar(
                    "URL",
                    judul_url,
                    input_url,
                    isi_url,
                    ringkasan,
                    catatan_url
                )
                st.success("Materi dari URL berhasil disimpan")


# =========================
# TAB 4 - HISTORY BELAJAR
# =========================
with tab4:
    st.subheader("History Belajar")

    result = supabase.table("sumber_belajar").select("id,jenis,judul,sumber,ringkasan,catatan,status,dibuat_pada").order("id", desc=True).execute()
    rows = result.data

    if len(rows) == 0:
        st.info("Belum ada materi")
    else:
        for row in rows:
            id_data = row["id"]
            jenis = row["jenis"]
            judul = row["judul"]
            sumber = row["sumber"]
            ringkasan = row["ringkasan"]
            catatan = row["catatan"]
            status = row["status"]
            dibuat_pada = row["dibuat_pada"]

            with st.expander(f"{id_data} | {jenis} | {judul} | {status}"):
                st.text(f"Sumber: {sumber}")
                st.text(f"Dibuat pada: {dibuat_pada}")
                st.text(f"Catatan: {catatan}")
                st.text("Ringkasan:")
                st.write(ringkasan)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("Aktifkan", key=f"aktif_{id_data}"):
                        supabase.table("sumber_belajar").update({"status": "AKTIF"}).eq("id", id_data).execute()
                        st.rerun()

                with col2:
                    if st.button("Nonaktifkan", key=f"nonaktif_{id_data}"):
                        supabase.table("sumber_belajar").update({"status": "NONAKTIF"}).eq("id", id_data).execute()
                        st.rerun()

                with col3:
                    if st.button("Hapus", key=f"hapus_{id_data}"):
                        supabase.table("sumber_belajar").delete().eq("id", id_data).execute()
                        st.rerun()

    st.divider()
    st.subheader("Preview Konteks Aktif (Debug)")
    konteks = ambil_konteks_aktif()
    st.text_area("Copy ini untuk dipakai sebagai knowledge base context di page chat", value=konteks, height=300)

    st.caption("Catatan: ini bukan membuat model belajar permanen. Ini membuat knowledge base lokal yang nanti dipakai saat chat.")
