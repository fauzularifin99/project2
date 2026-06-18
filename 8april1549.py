import streamlit as st
from openai import OpenAI
from datetime import datetime
import uuid

st.set_page_config(page_title="DASS-21 Simple", layout="wide")

# isi api key langsung di sini
API_KEY = st.secrets["OPENAI_KEY"]
client = OpenAI(api_key=API_KEY)

if "halaman" not in st.session_state:
    st.session_state.halaman = 1

if "SESSION_ID" not in st.session_state:
    st.session_state.SESSION_ID = "ID" + str(uuid.uuid4()).replace("-", "")[:6].upper()

if "CHATGPT" not in st.session_state:
    st.session_state.CHATGPT = []

if "USERRESPONSE" not in st.session_state:
    st.session_state.USERRESPONSE = []

if "MESSAGES" not in st.session_state:
    st.session_state.MESSAGES = [
        {
            "role": "system",
            "content": "Anda adalah LabsBuddies, sistem kecerdasan buatan pendamping siswa. Gunakan pendekatan empati remaja, santai tapi sopan, suportif, dan hanya boleh bertanya satu pertanyaan di setiap response. Maksimal 5 pertanyaan, lalu tanyakan apakah mau lanjut atau berhenti. Jika berhenti, buat ringkasan: Identitas Siswa, Jenis Temuan, Skor Risiko, Rekomendasi Tindakan."
        }
    ]

if "RINGKASAN" not in st.session_state:
    st.session_state.RINGKASAN = ""

# logger sederhana
log_file = open("logger.txt", "a", encoding="utf-8")

def log(text):
    waktu = datetime.now().strftime("%d-%b-%Y-%H:%M:%S")
    log_file.write(f"{waktu}|{st.session_state.SESSION_ID}|{text}\n")
    log_file.flush()

# =========================
# HALAMAN 1 - IDENTITAS
# =========================
if st.session_state.halaman == 1:
    st.title("Form Identitas")

    NAMA = st.text_input("Input NAMA")
    KELAS = st.text_input("Input KELAS")
    HP = st.text_input("Input Nomor HP")
    EMAIL = st.text_input("Input E-mail")

    if st.button("Submit Identitas"):
        if NAMA == "" or KELAS == "" or HP == "" or EMAIL == "":
            st.error("Semua data harus diisi")
        elif not HP.startswith("+62"):
            st.error("Nomor HP harus dimulai dengan +62")
        elif "@" not in EMAIL:
            st.error("E-mail harus ada @")
        else:
            st.session_state.NAMA = NAMA
            st.session_state.KELAS = KELAS
            st.session_state.HP = HP
            st.session_state.EMAIL = EMAIL

            log(f"Nama={NAMA}")
            log(f"Kelas={KELAS}")
            log(f"HP={HP}")
            log(f"Email={EMAIL}")

            st.session_state.halaman = 2
            st.rerun()

# =========================
# HALAMAN 2 - DASS 21
# =========================
elif st.session_state.halaman == 2:
    st.title("Kuisioner DASS-21")
    pilihan = ["TIDAK PERNAH", "KADANG-KADANG", "CUKUP SERING", "SANGAT SERING"]

    DASSSOAL1 = "Saya merasa sulit untuk beristirahat"
    DASSSOAL2 = "Saya merasa bibir saya sering kering"
    DASSSOAL3 = "Saya sama sekali tidak dapat merasakan perasaan positif"
    DASSSOAL4 = "Saya mengalami kesulitan bernafas (misalnya: sesak atau tidak dapat bernafas padahal tidak melakukan aktivitas fisik sebelumnya)"
    DASSSOAL5 = "Saya merasa sulit untuk mengembangkan inisiatif untuk melakukan sesuatu."
    DASSSOAL6 = "Saya cenderung bereaksi berlebihan terhadap suatu situasi."
    DASSSOAL7 = "Saya mengalami gemetar (misalnya di tangan)."
    DASSSOAL8 = "Saya merasa sulit untuk bersantai."
    DASSSOAL9 = "Saya khawatir tentang situasi di mana saya mungkin panik dan membuat bodoh diriku sendiri"
    DASSSOAL10 = "Saya merasa tidak ada hal yang dapat diharapkan di masa depan."
    DASSSOAL11 = "Saya merasa gelisah."
    DASSSOAL12 = "Saya merasa sulit untuk bersantai."
    DASSSOAL13 = "Saya merasa sedih dan tertekan."
    DASSSOAL14 = "Saya menemukan diri saya menjadi tidak sabar ketika mengalami penundaan (misalnya: kemacetan lalu lintas, menunggu sesuatu)."
    DASSSOAL15 = "Saya merasa lemas seperti mau pingsan."
    DASSSOAL16 = "Saya merasa saya kehilangan minat akan segala hal."
    DASSSOAL17 = "Saya merasa bahwa saya tidak berharga sebagai seorang manusia."
    DASSSOAL18 = "Saya merasa bahwa saya mudah tersinggung."
    DASSSOAL19 = "Saya berkeringat secara berlebihan (misalnya: tangan berkeringat), padahal temperatur tidak panas atau tidak melakukan aktivitas fisik sebelumnya."
    DASSSOAL20 = "Saya merasa takut tanpa alasan yang jelas."
    DASSSOAL21 = "Saya merasa bahwa hidup tidak ada artinya."

    j1 = st.radio("1. " + DASSSOAL1, pilihan, index=None)
    j2 = st.radio("2. " + DASSSOAL2, pilihan, index=None)
    j3 = st.radio("3. " + DASSSOAL3, pilihan, index=None)
    j4 = st.radio("4. " + DASSSOAL4, pilihan, index=None)
    j5 = st.radio("5. " + DASSSOAL5, pilihan, index=None)
    j6 = st.radio("6. " + DASSSOAL6, pilihan, index=None)
    j7 = st.radio("7. " + DASSSOAL7, pilihan, index=None)
    j8 = st.radio("8. " + DASSSOAL8, pilihan, index=None)
    j9 = st.radio("9. " + DASSSOAL9, pilihan, index=None)
    j10 = st.radio("10. " + DASSSOAL10, pilihan, index=None)
    j11 = st.radio("11. " + DASSSOAL11, pilihan, index=None)
    j12 = st.radio("12. " + DASSSOAL12, pilihan, index=None)
    j13 = st.radio("13. " + DASSSOAL13, pilihan, index=None)
    j14 = st.radio("14. " + DASSSOAL14, pilihan, index=None)
    j15 = st.radio("15. " + DASSSOAL15, pilihan, index=None)
    j16 = st.radio("16. " + DASSSOAL16, pilihan, index=None)
    j17 = st.radio("17. " + DASSSOAL17, pilihan, index=None)
    j18 = st.radio("18. " + DASSSOAL18, pilihan, index=None)
    j19 = st.radio("19. " + DASSSOAL19, pilihan, index=None)
    j20 = st.radio("20. " + DASSSOAL20, pilihan, index=None)
    j21 = st.radio("21. " + DASSSOAL21, pilihan, index=None)

    if st.button("Submit DASS"):
        if None in [j1,j2,j3,j4,j5,j6,j7,j8,j9,j10,j11,j12,j13,j14,j15,j16,j17,j18,j19,j20,j21]:
            st.error("Semua pertanyaan harus dijawab")
        else:
            if j1 == "TIDAK PERNAH": DASSJAWABAN1 = 0
            elif j1 == "KADANG-KADANG": DASSJAWABAN1 = 1
            elif j1 == "CUKUP SERING": DASSJAWABAN1 = 2
            else: DASSJAWABAN1 = 3

            if j2 == "TIDAK PERNAH": DASSJAWABAN2 = 0
            elif j2 == "KADANG-KADANG": DASSJAWABAN2 = 1
            elif j2 == "CUKUP SERING": DASSJAWABAN2 = 2
            else: DASSJAWABAN2 = 3

            if j3 == "TIDAK PERNAH": DASSJAWABAN3 = 0
            elif j3 == "KADANG-KADANG": DASSJAWABAN3 = 1
            elif j3 == "CUKUP SERING": DASSJAWABAN3 = 2
            else: DASSJAWABAN3 = 3

            if j4 == "TIDAK PERNAH": DASSJAWABAN4 = 0
            elif j4 == "KADANG-KADANG": DASSJAWABAN4 = 1
            elif j4 == "CUKUP SERING": DASSJAWABAN4 = 2
            else: DASSJAWABAN4 = 3

            if j5 == "TIDAK PERNAH": DASSJAWABAN5 = 0
            elif j5 == "KADANG-KADANG": DASSJAWABAN5 = 1
            elif j5 == "CUKUP SERING": DASSJAWABAN5 = 2
            else: DASSJAWABAN5 = 3

            if j6 == "TIDAK PERNAH": DASSJAWABAN6 = 0
            elif j6 == "KADANG-KADANG": DASSJAWABAN6 = 1
            elif j6 == "CUKUP SERING": DASSJAWABAN6 = 2
            else: DASSJAWABAN6 = 3

            if j7 == "TIDAK PERNAH": DASSJAWABAN7 = 0
            elif j7 == "KADANG-KADANG": DASSJAWABAN7 = 1
            elif j7 == "CUKUP SERING": DASSJAWABAN7 = 2
            else: DASSJAWABAN7 = 3

            if j8 == "TIDAK PERNAH": DASSJAWABAN8 = 0
            elif j8 == "KADANG-KADANG": DASSJAWABAN8 = 1
            elif j8 == "CUKUP SERING": DASSJAWABAN8 = 2
            else: DASSJAWABAN8 = 3

            if j9 == "TIDAK PERNAH": DASSJAWABAN9 = 0
            elif j9 == "KADANG-KADANG": DASSJAWABAN9 = 1
            elif j9 == "CUKUP SERING": DASSJAWABAN9 = 2
            else: DASSJAWABAN9 = 3

            if j10 == "TIDAK PERNAH": DASSJAWABAN10 = 0
            elif j10 == "KADANG-KADANG": DASSJAWABAN10 = 1
            elif j10 == "CUKUP SERING": DASSJAWABAN10 = 2
            else: DASSJAWABAN10 = 3

            if j11 == "TIDAK PERNAH": DASSJAWABAN11 = 0
            elif j11 == "KADANG-KADANG": DASSJAWABAN11 = 1
            elif j11 == "CUKUP SERING": DASSJAWABAN11 = 2
            else: DASSJAWABAN11 = 3

            if j12 == "TIDAK PERNAH": DASSJAWABAN12 = 0
            elif j12 == "KADANG-KADANG": DASSJAWABAN12 = 1
            elif j12 == "CUKUP SERING": DASSJAWABAN12 = 2
            else: DASSJAWABAN12 = 3

            if j13 == "TIDAK PERNAH": DASSJAWABAN13 = 0
            elif j13 == "KADANG-KADANG": DASSJAWABAN13 = 1
            elif j13 == "CUKUP SERING": DASSJAWABAN13 = 2
            else: DASSJAWABAN13 = 3

            if j14 == "TIDAK PERNAH": DASSJAWABAN14 = 0
            elif j14 == "KADANG-KADANG": DASSJAWABAN14 = 1
            elif j14 == "CUKUP SERING": DASSJAWABAN14 = 2
            else: DASSJAWABAN14 = 3

            if j15 == "TIDAK PERNAH": DASSJAWABAN15 = 0
            elif j15 == "KADANG-KADANG": DASSJAWABAN15 = 1
            elif j15 == "CUKUP SERING": DASSJAWABAN15 = 2
            else: DASSJAWABAN15 = 3

            if j16 == "TIDAK PERNAH": DASSJAWABAN16 = 0
            elif j16 == "KADANG-KADANG": DASSJAWABAN16 = 1
            elif j16 == "CUKUP SERING": DASSJAWABAN16 = 2
            else: DASSJAWABAN16 = 3

            if j17 == "TIDAK PERNAH": DASSJAWABAN17 = 0
            elif j17 == "KADANG-KADANG": DASSJAWABAN17 = 1
            elif j17 == "CUKUP SERING": DASSJAWABAN17 = 2
            else: DASSJAWABAN17 = 3

            if j18 == "TIDAK PERNAH": DASSJAWABAN18 = 0
            elif j18 == "KADANG-KADANG": DASSJAWABAN18 = 1
            elif j18 == "CUKUP SERING": DASSJAWABAN18 = 2
            else: DASSJAWABAN18 = 3

            if j19 == "TIDAK PERNAH": DASSJAWABAN19 = 0
            elif j19 == "KADANG-KADANG": DASSJAWABAN19 = 1
            elif j19 == "CUKUP SERING": DASSJAWABAN19 = 2
            else: DASSJAWABAN19 = 3

            if j20 == "TIDAK PERNAH": DASSJAWABAN20 = 0
            elif j20 == "KADANG-KADANG": DASSJAWABAN20 = 1
            elif j20 == "CUKUP SERING": DASSJAWABAN20 = 2
            else: DASSJAWABAN20 = 3

            if j21 == "TIDAK PERNAH": DASSJAWABAN21 = 0
            elif j21 == "KADANG-KADANG": DASSJAWABAN21 = 1
            elif j21 == "CUKUP SERING": DASSJAWABAN21 = 2
            else: DASSJAWABAN21 = 3

            st.session_state.DASSSOAL1 = DASSSOAL1
            st.session_state.DASSSOAL2 = DASSSOAL2
            st.session_state.DASSSOAL3 = DASSSOAL3
            st.session_state.DASSSOAL4 = DASSSOAL4
            st.session_state.DASSSOAL5 = DASSSOAL5
            st.session_state.DASSSOAL6 = DASSSOAL6
            st.session_state.DASSSOAL7 = DASSSOAL7
            st.session_state.DASSSOAL8 = DASSSOAL8
            st.session_state.DASSSOAL9 = DASSSOAL9
            st.session_state.DASSSOAL10 = DASSSOAL10
            st.session_state.DASSSOAL11 = DASSSOAL11
            st.session_state.DASSSOAL12 = DASSSOAL12
            st.session_state.DASSSOAL13 = DASSSOAL13
            st.session_state.DASSSOAL14 = DASSSOAL14
            st.session_state.DASSSOAL15 = DASSSOAL15
            st.session_state.DASSSOAL16 = DASSSOAL16
            st.session_state.DASSSOAL17 = DASSSOAL17
            st.session_state.DASSSOAL18 = DASSSOAL18
            st.session_state.DASSSOAL19 = DASSSOAL19
            st.session_state.DASSSOAL20 = DASSSOAL20
            st.session_state.DASSSOAL21 = DASSSOAL21

            st.session_state.DASSJAWABAN1 = DASSJAWABAN1
            st.session_state.DASSJAWABAN2 = DASSJAWABAN2
            st.session_state.DASSJAWABAN3 = DASSJAWABAN3
            st.session_state.DASSJAWABAN4 = DASSJAWABAN4
            st.session_state.DASSJAWABAN5 = DASSJAWABAN5
            st.session_state.DASSJAWABAN6 = DASSJAWABAN6
            st.session_state.DASSJAWABAN7 = DASSJAWABAN7
            st.session_state.DASSJAWABAN8 = DASSJAWABAN8
            st.session_state.DASSJAWABAN9 = DASSJAWABAN9
            st.session_state.DASSJAWABAN10 = DASSJAWABAN10
            st.session_state.DASSJAWABAN11 = DASSJAWABAN11
            st.session_state.DASSJAWABAN12 = DASSJAWABAN12
            st.session_state.DASSJAWABAN13 = DASSJAWABAN13
            st.session_state.DASSJAWABAN14 = DASSJAWABAN14
            st.session_state.DASSJAWABAN15 = DASSJAWABAN15
            st.session_state.DASSJAWABAN16 = DASSJAWABAN16
            st.session_state.DASSJAWABAN17 = DASSJAWABAN17
            st.session_state.DASSJAWABAN18 = DASSJAWABAN18
            st.session_state.DASSJAWABAN19 = DASSJAWABAN19
            st.session_state.DASSJAWABAN20 = DASSJAWABAN20
            st.session_state.DASSJAWABAN21 = DASSJAWABAN21

            SKORDEPRESI = DASSJAWABAN3 + DASSJAWABAN5 + DASSJAWABAN10 + DASSJAWABAN13 + DASSJAWABAN16 + DASSJAWABAN17 + DASSJAWABAN21
            SKORANXIETY = DASSJAWABAN3 + DASSJAWABAN2 + DASSJAWABAN4 + DASSJAWABAN7 + DASSJAWABAN9 + DASSJAWABAN15 + DASSJAWABAN19 + DASSJAWABAN20
            SKORSTRESS = DASSJAWABAN3 + DASSJAWABAN1 + DASSJAWABAN6 + DASSJAWABAN8 + DASSJAWABAN11 + DASSJAWABAN12 + DASSJAWABAN14 + DASSJAWABAN18

            st.session_state.SKORDEPRESI = SKORDEPRESI
            st.session_state.SKORANXIETY = SKORANXIETY
            st.session_state.SKORSTRESS = SKORSTRESS

            log(f"SOAL1={DASSSOAL1}")
            log(f"DASSJAWABAN1={DASSJAWABAN1}")
            log(f"SOAL2={DASSSOAL2}")
            log(f"DASSJAWABAN2={DASSJAWABAN2}")
            log(f"SOAL3={DASSSOAL3}")
            log(f"DASSJAWABAN3={DASSJAWABAN3}")
            log(f"SOAL4={DASSSOAL4}")
            log(f"DASSJAWABAN4={DASSJAWABAN4}")
            log(f"SOAL5={DASSSOAL5}")
            log(f"DASSJAWABAN5={DASSJAWABAN5}")
            log(f"SOAL6={DASSSOAL6}")
            log(f"DASSJAWABAN6={DASSJAWABAN6}")
            log(f"SOAL7={DASSSOAL7}")
            log(f"DASSJAWABAN7={DASSJAWABAN7}")
            log(f"SOAL8={DASSSOAL8}")
            log(f"DASSJAWABAN8={DASSJAWABAN8}")
            log(f"SOAL9={DASSSOAL9}")
            log(f"DASSJAWABAN9={DASSJAWABAN9}")
            log(f"SOAL10={DASSSOAL10}")
            log(f"DASSJAWABAN10={DASSJAWABAN10}")
            log(f"SOAL11={DASSSOAL11}")
            log(f"DASSJAWABAN11={DASSJAWABAN11}")
            log(f"SOAL12={DASSSOAL12}")
            log(f"DASSJAWABAN12={DASSJAWABAN12}")
            log(f"SOAL13={DASSSOAL13}")
            log(f"DASSJAWABAN13={DASSJAWABAN13}")
            log(f"SOAL14={DASSSOAL14}")
            log(f"DASSJAWABAN14={DASSJAWABAN14}")
            log(f"SOAL15={DASSSOAL15}")
            log(f"DASSJAWABAN15={DASSJAWABAN15}")
            log(f"SOAL16={DASSSOAL16}")
            log(f"DASSJAWABAN16={DASSJAWABAN16}")
            log(f"SOAL17={DASSSOAL17}")
            log(f"DASSJAWABAN17={DASSJAWABAN17}")
            log(f"SOAL18={DASSSOAL18}")
            log(f"DASSJAWABAN18={DASSJAWABAN18}")
            log(f"SOAL19={DASSSOAL19}")
            log(f"DASSJAWABAN19={DASSJAWABAN19}")
            log(f"SOAL20={DASSSOAL20}")
            log(f"DASSJAWABAN20={DASSJAWABAN20}")
            log(f"SOAL21={DASSSOAL21}")
            log(f"DASSJAWABAN21={DASSJAWABAN21}")
            log(f"SKORDEPRESI={SKORDEPRESI}")
            log(f"SKORANXIETY={SKORANXIETY}")
            log(f"SKORSTRESS={SKORSTRESS}")

            INTRO = f'''Hallo ChatGPT, nama saya {st.session_state.NAMA}. dan saya saat ini berada di {st.session_state.KELAS}. e-mail saya di {st.session_state.EMAIL} . saya sudah mengisi kuisioner DASS21 dengan detail pertanyaan dan jawaban :- {DASSSOAL1} dan saya menjawab {DASSJAWABAN1} - {DASSSOAL2} dan saya menjawab {DASSJAWABAN2} - {DASSSOAL3} dan saya menjawab {DASSJAWABAN3} - {DASSSOAL4} dan saya menjawab {DASSJAWABAN4} - {DASSSOAL5} dan saya menjawab {DASSJAWABAN5} - {DASSSOAL6} dan saya menjawab {DASSJAWABAN6} - {DASSSOAL7} dan saya menjawab {DASSJAWABAN7} - {DASSSOAL8} dan saya menjawab {DASSJAWABAN8} - {DASSSOAL9} dan saya menjawab {DASSJAWABAN9} - {DASSSOAL10} dan saya menjawab {DASSJAWABAN10} - {DASSSOAL11} dan saya menjawab {DASSJAWABAN11} - {DASSSOAL12} dan saya menjawab {DASSJAWABAN12} - {DASSSOAL13} dan saya menjawab {DASSJAWABAN13} - {DASSSOAL14} dan saya menjawab {DASSJAWABAN14} - {DASSSOAL15} dan saya menjawab {DASSJAWABAN15} - {DASSSOAL16} dan saya menjawab {DASSJAWABAN16} - {DASSSOAL17} dan saya menjawab {DASSJAWABAN17} - {DASSSOAL18} dan saya menjawab {DASSJAWABAN18} - {DASSSOAL19} dan saya menjawab {DASSJAWABAN19} - {DASSSOAL20} dan saya menjawab {DASSJAWABAN20}- {DASSSOAL21} dan saya menjawab {DASSJAWABAN21}. Untuk jawaban tidak pernah nilainya 0, kadang nilainya 1, cukup sering nilainya 2, sangat sering nilainya 3. Dari situ skor depresi saya adalah {SKORDEPRESI}. skor kecemasan atau anxiety saya adalah {SKORANXIETY}. skor stress saya adalah {SKORSTRESS}. Saya tidak tahu apa artinya itu. anda bisa menjelaskannya sekilas.Lakukan tanya jawab sebagai follow up dari keterangan diatas untuk menggali lebih lanjut permasalahan yang sedang dirasakan saat ini. Lakukan satu pertanyaan saja di setiap response. Maksimal 5 pertanyaan lalu tanya mau lanjut atau berhenti. Jika berhenti, tampilkan ringkasan analisa: Identitas Siswa, Jenis Temuan, Skor Risiko, Rekomendasi Tindakan.'''

            st.session_state.INTRO = INTRO
            log(f'INTRO="{INTRO}"')

            st.session_state.MESSAGES.append({"role": "user", "content": INTRO})
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.MESSAGES
            )
            jawaban_awal = response.choices[0].message.content
            st.session_state.MESSAGES.append({"role": "assistant", "content": jawaban_awal})
            st.session_state.CHATGPT.append(jawaban_awal)
            log(f'CHATGPT[1]="{jawaban_awal}"')

            st.session_state.halaman = 3
            st.rerun()

# =========================
# HALAMAN 3 - CHAT
# =========================
elif st.session_state.halaman == 3:
    st.title("Chatbot")

    for i in range(len(st.session_state.CHATGPT)):
        st.write("LabsBuddies:", st.session_state.CHATGPT[i])
        if i < len(st.session_state.USERRESPONSE):
            st.write("User:", st.session_state.USERRESPONSE[i])

    jawaban_user = st.text_area("Jawaban user")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Kirim"):
            if jawaban_user != "":
                nomor = len(st.session_state.USERRESPONSE) + 1
                st.session_state.USERRESPONSE.append(jawaban_user)
                st.session_state.MESSAGES.append({"role": "user", "content": jawaban_user})
                log(f'USERRESPONSE[{nomor}]="{jawaban_user}"')

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=st.session_state.MESSAGES
                )
                jawaban_bot = response.choices[0].message.content
                st.session_state.MESSAGES.append({"role": "assistant", "content": jawaban_bot})
                st.session_state.CHATGPT.append(jawaban_bot)
                log(f'CHATGPT[{len(st.session_state.CHATGPT)}]="{jawaban_bot}"')
                st.rerun()

    with col2:
        if st.button("Berhenti"):
            st.session_state.MESSAGES.append({
                "role": "user",
                "content": "Saya ingin berhenti. Tolong tampilkan ringkasan analisa akhir dengan format: Identitas Siswa, Jenis Temuan, Skor Risiko, Rekomendasi Tindakan."
            })
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.MESSAGES
            )
            ringkasan = response.choices[0].message.content
            st.session_state.RINGKASAN = ringkasan
            log(f'RINGKASAN="{ringkasan}"')
            st.session_state.halaman = 4
            st.rerun()

# =========================
# HALAMAN 4 - RINGKASAN
# =========================
elif st.session_state.halaman == 4:
    st.title("Ringkasan")
    st.write(st.session_state.RINGKASAN)

    if st.button("Mulai Lagi"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
