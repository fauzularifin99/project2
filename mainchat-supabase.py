import streamlit as st
from openai import OpenAI
from datetime import datetime, date
import time
import uuid
import yagmail
from twilio.rest import Client
import html
from supabase import create_client


# isi api key langsung di sini
account_sid = st.secrets['TWILIO_ACCOUNT_SID']
auth_token = st.secrets['TWILIO_AUTH_TOKEN']
twilio_number = st.secrets['TWILIO_PHONE_NUMBER']
hpbk = st.secrets['HPBK']
gmail_key =  st.secrets['GMAIL_KEY']
gmail_from =  st.secrets['GMAIL_FROM']
gmail_bkto = st.secrets['GMAIL_BKTO']
API_KEY = st.secrets['OPENAI_KEY']
SUPABASE_URL = st.secrets['SUPABASE_URL']
SUPABASE_KEY = st.secrets['SUPABASE_KEY']

client = OpenAI(api_key=API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MODEL_PATH = "best (1).pt"
CONF_THRESHOLD = 0.50
ALERT_HOLD_FRAMES = 10

DANGEROUS_CLASSES = ["pisau", "gunting", "cutter"]
SAFE_CLASS = "safe"

@st.cache_resource
def load_model():
   from ultralytics import YOLO
   return YOLO(MODEL_PATH)

class DangerDetector:
    def __init__(self):
        self.alert_counter = 0
        self.model = load_model()

    def recv(self, frame):
        import av
        import cv2

        img = frame.to_ndarray(format="bgr24")

        results = self.model(img, conf=CONF_THRESHOLD, imgsz=640, verbose=False)[0]

        danger_detected = False

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]

            if label in DANGEROUS_CLASSES:
                danger_detected = True
                break

        if danger_detected:
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

st.set_page_config(page_title="DASS-21 Simple", layout="wide")


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
            "content": "Anda adalah LabsBuddies, sistem kecerdasan buatan pendamping siswa. Gunakan pendekatan empati remaja, santai tapi sopan, suportif, dan hanya boleh bertanya satu pertanyaan di setiap response."
        }
    ]

if "RINGKASAN" not in st.session_state:
    st.session_state.RINGKASAN = ""

# logger sederhana
log_file = open("logger.txt", "a", encoding="utf-8")

def log(text):
    waktu = datetime.now().strftime("%d-%b-%Y-%H:%M:%S")
    text = str(text).replace("\n", " --- ")
    log_file.write(f"{waktu}|{st.session_state.SESSION_ID}|{text}\n")
    log_file.flush()

def ambil_konteks_aktif():
    result = supabase.table("sumber_belajar").select("judul,isi").eq("status", "AKTIF").order("id", desc=True).execute()

    konteks = ""
    nomor = 1

    for row in result.data:
        judul = row["judul"]
        isi = row["isi"]
        konteks += f"\n\nSUMBER {nomor}: {judul}\n{isi[:5000]}"
        nomor += 1

    return konteks

def fungsi_darurat():
    yag = yagmail.SMTP(
        gmail_from,
        gmail_key
    )

    subject_darurat = f"PERINGATAN DARURAT - {st.session_state.NAMA} - {st.session_state.KELAS}"

    isi_email_darurat = f"""
Terdeteksi indikasi bahaya dari percakapan siswa.

Nama: {st.session_state.NAMA}
Kelas: {st.session_state.KELAS}
HP: {st.session_state.HP}
Email: {st.session_state.EMAIL}
Session ID: {st.session_state.SESSION_ID}

Mohon segera dilakukan pendampingan.
"""

    yag.send(
        to=gmail_bkto,
        subject=subject_darurat,
        contents=isi_email_darurat
    )

    time.sleep(5)

    twilio_client = Client(account_sid, auth_token)

    sms_darurat = f"DARURAT: Terdeteksi indikasi bahaya pada siswa {st.session_state.NAMA} kelas {st.session_state.KELAS} dengan HP {st.session_state.HP}. Mohon segera cek dan dampingi."

    twilio_client.messages.create(
        body=sms_darurat,
        from_=twilio_number,
        to=hpbk
    )

    time.sleep(5)

    twilio_client.calls.create(
        twiml=f'<Response><Say language="id-ID">{html.escape(sms_darurat)}</Say></Response>',
        from_=twilio_number,
        to=hpbk
    )

    log(f"FUNGSI_DARURAT_DIPANGGIL LEWAT SMS DAN EMAIL:{sms_darurat}")

# =========================
# HALAMAN 1 - IDENTITAS
# =========================
if st.session_state.halaman == 1:
    st.title("Form Identitas")

    if "input_nama" not in st.session_state:
        st.session_state.input_nama = ""

    if "input_ttl" not in st.session_state:
        st.session_state.input_ttl = None

    if "NISN_CHECK" not in st.session_state:
        st.session_state.NISN_CHECK = ""

    if "KELAS_CHECK" not in st.session_state:
        st.session_state.KELAS_CHECK = ""

    if "HP_CHECK" not in st.session_state:
        st.session_state.HP_CHECK = ""

    if "EMAIL_CHECK" not in st.session_state:
        st.session_state.EMAIL_CHECK = ""

    if "DATA_SISWA_DITEMUKAN" not in st.session_state:
        st.session_state.DATA_SISWA_DITEMUKAN = False

    def nama_uppercase():
        st.session_state.input_nama = st.session_state.input_nama.upper()

    NAMA = st.text_input("Input NAMA", key="input_nama", on_change=nama_uppercase)
    NAMA = NAMA.upper()

    TTL = st.date_input(
        "Input TANGGAL LAHIR",
        value=date(2010, 1, 1),
        min_value=date(1950, 1, 1),
        max_value=date.today()
    )
    if st.button("CHECK"):
        if NAMA == "" or TTL is None:
            st.error("Nama dan tanggal lahir harus diisi")
        else:
            TTL_TEXT = TTL.strftime("%Y-%m-%d")

            result = supabase.table("SISWA").select("NISN,KELAS,HP,EMAIL").ilike("NAMA", NAMA).eq("TTL", TTL_TEXT).execute()
            row = result.data[0] if len(result.data) > 0 else None

            if row:
                st.session_state.NISN_CHECK = row["NISN"]
                st.session_state.KELAS_CHECK = row["KELAS"]
                st.session_state.HP_CHECK = row["HP"]
                st.session_state.EMAIL_CHECK = row["EMAIL"]
                st.session_state.DATA_SISWA_DITEMUKAN = True
                st.rerun()
            else:
                st.session_state.NISN_CHECK = ""
                st.session_state.KELAS_CHECK = ""
                st.session_state.HP_CHECK = ""
                st.session_state.EMAIL_CHECK = ""
                st.session_state.DATA_SISWA_DITEMUKAN = False
                st.error("Data siswa tidak ditemukan")

    NISN = st.text_input("NISN", value=st.session_state.NISN_CHECK, disabled=True)
    KELAS = st.text_input("KELAS", value=st.session_state.KELAS_CHECK, disabled=True)
    HP = st.text_input("Input Nomor HP", value=st.session_state.HP_CHECK, disabled=True)
    EMAIL = st.text_input("Input E-mail", value=st.session_state.EMAIL_CHECK, disabled=True)

    if st.session_state.DATA_SISWA_DITEMUKAN == True:
        st.success("Data siswa ditemukan. Silakan klik Submit Identitas jika data sudah sesuai.")

    if st.button("Submit Identitas"):
        if st.session_state.DATA_SISWA_DITEMUKAN == False:
            st.error("Klik CHECK terlebih dahulu sampai data siswa ditemukan")
        elif NAMA == "" or KELAS == "" or HP == "" or EMAIL == "":
            st.error("Semua data harus diisi")
        elif not HP.startswith("+62"):
            st.error("Nomor HP harus dimulai dengan +62")
        elif "@" not in EMAIL:
            st.error("E-mail harus ada @")
        else:
            st.session_state.NAMA = NAMA
            st.session_state.TTL = TTL.strftime("%Y-%m-%d")
            st.session_state.NISN = NISN
            st.session_state.KELAS = KELAS
            st.session_state.HP = HP
            st.session_state.EMAIL = EMAIL

            log(f"Nama={NAMA}")
            log(f"TTL={st.session_state.TTL}")
            log(f"NISN={NISN}")
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
    st.text("Mohon isi kuisioner ini terlebih dahulu.")
    pilihan = ["Tidak Pernah", "Kadang-kadang", "Cukup Sering", "Sangat Sering"]

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

    if st.button("Submit Jawaban Kuisoner DASS-21"):
        if None in [j1,j2,j3,j4,j5,j6,j7,j8,j9,j10,j11,j12,j13,j14,j15,j16,j17,j18,j19,j20,j21]:
            st.error("Semua pertanyaan harus dijawab")
        else:
            if j1 == "Tidak Pernah": DASSJAWABAN1 = 0
            elif j1 == "Kadang-kadang": DASSJAWABAN1 = 1
            elif j1 == "Cukup Sering": DASSJAWABAN1 = 2
            else: DASSJAWABAN1 = 3

            if j2 == "Tidak Pernah": DASSJAWABAN2 = 0
            elif j2 == "Kadang-kadang": DASSJAWABAN2 = 1
            elif j2 == "Cukup Sering": DASSJAWABAN2 = 2
            else: DASSJAWABAN2 = 3

            if j3 == "Tidak Pernah": DASSJAWABAN3 = 0
            elif j3 == "Kadang-kadang": DASSJAWABAN3 = 1
            elif j3 == "Cukup Sering": DASSJAWABAN3 = 2
            else: DASSJAWABAN3 = 3

            if j4 == "Tidak Pernah": DASSJAWABAN4 = 0
            elif j4 == "Kadang-kadang": DASSJAWABAN4 = 1
            elif j4 == "Cukup Sering": DASSJAWABAN4 = 2
            else: DASSJAWABAN4 = 3

            if j5 == "Tidak Pernah": DASSJAWABAN5 = 0
            elif j5 == "Kadang-kadang": DASSJAWABAN5 = 1
            elif j5 == "Cukup Sering": DASSJAWABAN5 = 2
            else: DASSJAWABAN5 = 3

            if j6 == "Tidak Pernah": DASSJAWABAN6 = 0
            elif j6 == "Kadang-kadang": DASSJAWABAN6 = 1
            elif j6 == "Cukup Sering": DASSJAWABAN6 = 2
            else: DASSJAWABAN6 = 3

            if j7 == "Tidak Pernah": DASSJAWABAN7 = 0
            elif j7 == "Kadang-kadang": DASSJAWABAN7 = 1
            elif j7 == "Cukup Sering": DASSJAWABAN7 = 2
            else: DASSJAWABAN7 = 3

            if j8 == "Tidak Pernah": DASSJAWABAN8 = 0
            elif j8 == "Kadang-kadang": DASSJAWABAN8 = 1
            elif j8 == "Cukup Sering": DASSJAWABAN8 = 2
            else: DASSJAWABAN8 = 3

            if j9 == "Tidak Pernah": DASSJAWABAN9 = 0
            elif j9 == "Kadang-kadang": DASSJAWABAN9 = 1
            elif j9 == "Cukup Sering": DASSJAWABAN9 = 2
            else: DASSJAWABAN9 = 3

            if j10 == "Tidak Pernah": DASSJAWABAN10 = 0
            elif j10 == "Kadang-kadang": DASSJAWABAN10 = 1
            elif j10 == "Cukup Sering": DASSJAWABAN10 = 2
            else: DASSJAWABAN10 = 3

            if j11 == "Tidak Pernah": DASSJAWABAN11 = 0
            elif j11 == "Kadang-kadang": DASSJAWABAN11 = 1
            elif j11 == "Cukup Sering": DASSJAWABAN11 = 2
            else: DASSJAWABAN11 = 3

            if j12 == "Tidak Pernah": DASSJAWABAN12 = 0
            elif j12 == "Kadang-kadang": DASSJAWABAN12 = 1
            elif j12 == "Cukup Sering": DASSJAWABAN12 = 2
            else: DASSJAWABAN12 = 3

            if j13 == "Tidak Pernah": DASSJAWABAN13 = 0
            elif j13 == "Kadang-kadang": DASSJAWABAN13 = 1
            elif j13 == "Cukup Sering": DASSJAWABAN13 = 2
            else: DASSJAWABAN13 = 3

            if j14 == "Tidak Pernah": DASSJAWABAN14 = 0
            elif j14 == "Kadang-kadang": DASSJAWABAN14 = 1
            elif j14 == "Cukup Sering": DASSJAWABAN14 = 2
            else: DASSJAWABAN14 = 3

            if j15 == "Tidak Pernah": DASSJAWABAN15 = 0
            elif j15 == "Kadang-kadang": DASSJAWABAN15 = 1
            elif j15 == "Cukup Sering": DASSJAWABAN15 = 2
            else: DASSJAWABAN15 = 3

            if j16 == "Tidak Pernah": DASSJAWABAN16 = 0
            elif j16 == "Kadang-kadang": DASSJAWABAN16 = 1
            elif j16 == "Cukup Sering": DASSJAWABAN16 = 2
            else: DASSJAWABAN16 = 3

            if j17 == "Tidak Pernah": DASSJAWABAN17 = 0
            elif j17 == "Kadang-kadang": DASSJAWABAN17 = 1
            elif j17 == "Cukup Sering": DASSJAWABAN17 = 2
            else: DASSJAWABAN17 = 3

            if j18 == "Tidak Pernah": DASSJAWABAN18 = 0
            elif j18 == "Kadang-kadang": DASSJAWABAN18 = 1
            elif j18 == "Cukup Sering": DASSJAWABAN18 = 2
            else: DASSJAWABAN18 = 3

            if j19 == "Tidak Pernah": DASSJAWABAN19 = 0
            elif j19 == "Kadang-kadang": DASSJAWABAN19 = 1
            elif j19 == "Cukup Sering": DASSJAWABAN19 = 2
            else: DASSJAWABAN19 = 3

            if j20 == "Tidak Pernah": DASSJAWABAN20 = 0
            elif j20 == "Kadang-kadang": DASSJAWABAN20 = 1
            elif j20 == "Cukup Sering": DASSJAWABAN20 = 2
            else: DASSJAWABAN20 = 3

            if j21 == "Tidak Pernah": DASSJAWABAN21 = 0
            elif j21 == "Kadang-kadang": DASSJAWABAN21 = 1
            elif j21 == "Cukup Sering": DASSJAWABAN21 = 2
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

            INTRO = f'''Hallo ChatGPT, nama saya {st.session_state.NAMA}. dan saya saat ini saya seorang siswa yang duduk di kelas {st.session_state.KELAS} dan saya lahir pada {st.session_state.TTL}. e-mail saya di {st.session_state.EMAIL} . saya sudah mengisi kuisioner DASS21 dengan detail pertanyaan dan jawaban :- {DASSSOAL1} dan saya menjawab {DASSJAWABAN1} - {DASSSOAL2} dan saya menjawab {DASSJAWABAN2} - {DASSSOAL3} dan saya menjawab {DASSJAWABAN3} - {DASSSOAL4} dan saya menjawab {DASSJAWABAN4} - {DASSSOAL5} dan saya menjawab {DASSJAWABAN5} - {DASSSOAL6} dan saya menjawab {DASSJAWABAN6} - {DASSSOAL7} dan saya menjawab {DASSJAWABAN7} - {DASSSOAL8} dan saya menjawab {DASSJAWABAN8} - {DASSSOAL9} dan saya menjawab {DASSJAWABAN9} - {DASSSOAL10} dan saya menjawab {DASSJAWABAN10} - {DASSSOAL11} dan saya menjawab {DASSJAWABAN11} - {DASSSOAL12} dan saya menjawab {DASSJAWABAN12} - {DASSSOAL13} dan saya menjawab {DASSJAWABAN13} - {DASSSOAL14} dan saya menjawab {DASSJAWABAN14} - {DASSSOAL15} dan saya menjawab {DASSJAWABAN15} - {DASSSOAL16} dan saya menjawab {DASSJAWABAN16} - {DASSSOAL17} dan saya menjawab {DASSJAWABAN17} - {DASSSOAL18} dan saya menjawab {DASSJAWABAN18} - {DASSSOAL19} dan saya menjawab {DASSJAWABAN19} - {DASSSOAL20} dan saya menjawab {DASSJAWABAN20}- {DASSSOAL21} dan saya menjawab {DASSJAWABAN21}. Untuk jawaban Tidak Pernah nilainya 0, kadang nilainya 1, Cukup Sering nilainya 2, Sangat Sering nilainya 3. Dari situ skor depresi saya adalah {SKORDEPRESI}. skor kecemasan atau anxiety saya adalah {SKORANXIETY}. skor stress saya adalah {SKORSTRESS}. Saya tidak tahu apa artinya itu. Tolong jelaskan dengan singkat sekitar 3-4 kalimat dari hasil skor DASS-21. Lalu lakukan tanya jawab sebagai follow up dari keterangan diatas untuk menggali lebih lanjut permasalahan yang sedang dirasakan saat ini. Lakukan satu pertanyaan saja di setiap response. lakukan anamnesis secara terperinci dan detail dengan bahasa yang mengalir seperti layaknya psikolog dan jangan berhenti kecuali diminta user. dan saat membalas, fontnya biasa saja (tidak usah ukurannya beda-beda, tidak usah pakai emoji, format teks biasa, rapi, tanpa markdown, tanpa tanda ###, tanpa **, dan tanpa bullet aneh, dan sejenisnya). Jika ChatGPT mendeteksi adanya kata kata atau kalimat yang menjurus ke Tindakan membahayakan seperti percobaan bunuh diri atau menyakiti diri sendiri pada input user, maka tuliskan kata berikut diakhir respon yang ChatGPT berikan = STATUS:BAHAYA!'''

            st.session_state.INTRO = INTRO

            KONTEKS_BELAJAR = ambil_konteks_aktif()

            PROMPT_FINAL = f"""
            Gunakan referensi berikut sebagai sumber utama jawaban.

            REFERENSI:
            {KONTEKS_BELAJAR}

            PERTANYAAN / KONTEKS USER:
            {INTRO}
            """
            log(f'INTRO="{PROMPT_FINAL}"')
            st.session_state.MESSAGES.append({"role": "user", "content": PROMPT_FINAL})
            response = client.responses.create(
                model="gpt-5.4-nano",
                input=st.session_state.MESSAGES
            )
            jawaban_awal = response.output_text
            st.session_state.MESSAGES.append({"role": "assistant", "content": jawaban_awal})
            st.session_state.CHATGPT.append(jawaban_awal)
            log(f'CHATGPT[1]="{jawaban_awal}"')

            st.session_state.halaman = 3
            st.rerun()

# =========================
# HALAMAN 3 - CHAT
# =========================
elif st.session_state.halaman == 3:
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1500px;
    }
    .app-header {
        background: #ffffff;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 22px;
        font-weight: 700;
        color: #111827;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
    }
    .section-label {
        color: #6b7280;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .bubble-row-left {
        display: flex;
        justify-content: flex-start;
        margin: 8px 0;
    }
    .bubble-row-right {
        display: flex;
        justify-content: flex-end;
        margin: 8px 0;
    }
    .bubble-bot {
        background-color: #f1f1f1;
        color: #111827;
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 88%;
        font-size: 15px;
        line-height: 1.45;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
    }
    .bubble-user {
        background-color: #d8f7c6;
        color: #111827;
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 88%;
        font-size: 15px;
        line-height: 1.45;
        text-align: right;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
    }
    div[data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 10px 12px;
        margin-top: 12px;
    }
    div[data-testid="stForm"] button {
        border-radius: 24px;
        font-weight: 700;
        min-height: 40px;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 24px;
        min-height: 40px;
    }
    iframe {
        max-height: 520px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="app-header">‹ &nbsp; Asisten Video AI</div>', unsafe_allow_html=True)

    kolom_video, kolom_chat = st.columns([1.05, 1.75], gap="small")

    with kolom_video:
        from streamlit_webrtc import webrtc_streamer

        st.markdown('<div class="section-label">VIDEO AI DETECTION</div>', unsafe_allow_html=True)
        webrtc_streamer(
            key="danger-detection",
            video_processor_factory=DangerDetector,
            media_stream_constraints={"video": True, "audio": False},
        )

    with kolom_chat:
        st.markdown('<div class="section-label">RIWAYAT CHAT</div>', unsafe_allow_html=True)
        chat_box = st.container(height=610, border=True, autoscroll=True)

        with chat_box:
            for i in range(len(st.session_state.CHATGPT)):

                # BOT (kiri)
                st.markdown(
                    f'<div class="bubble-row-left"><div class="bubble-bot">AI: {html.escape(st.session_state.CHATGPT[i])}</div></div>',
                    unsafe_allow_html=True
                )

                # USER (kanan)
                if i < len(st.session_state.USERRESPONSE):
                    st.markdown(
                        f'<div class="bubble-row-right"><div class="bubble-user">{html.escape(st.session_state.USERRESPONSE[i])}</div></div>',
                        unsafe_allow_html=True
                    )

    with st.form("form_chat", clear_on_submit=True, enter_to_submit=False):
        col_stop, col_input, col_send = st.columns([1.1, 7, 1.2])

        with col_send:
            kirim = st.form_submit_button("KIRIM ➤")

        with col_stop:
            berhenti = st.form_submit_button("BERHENTI")

        with col_input:
            jawaban_user = st.text_input("Jawaban user", placeholder="Ketik pesan Anda di sini...", label_visibility="collapsed")


    if kirim:
        if jawaban_user != "":
            nomor = len(st.session_state.USERRESPONSE) + 1
            st.session_state.USERRESPONSE.append(jawaban_user)

            st.session_state.MESSAGES.append({"role": "user", "content": jawaban_user})

            log(f'USERRESPONSE[{nomor}]="{jawaban_user}"')

            response = client.responses.create(
                model="gpt-5.4-nano",
                input=st.session_state.MESSAGES
            )
            jawaban_bot = response.output_text
            st.session_state.MESSAGES.append({"role": "assistant", "content": jawaban_bot})
            st.session_state.CHATGPT.append(jawaban_bot)
            log(f'CHATGPT[{len(st.session_state.CHATGPT)}]="{jawaban_bot}"')
            if "STATUS:BAHAYA!" in jawaban_bot:
                fungsi_darurat()
            st.rerun()

    if berhenti:

        st.session_state.MESSAGES.append({
            "role": "user",
            "content": "Saya ingin berhenti tanya jawab. Tolong tampilkan ringkasan analisa akhir dalam format teks biasa, rapi, tanpa markdown, tanpa tanda ###, tanpa **, dan tanpa bullet aneh. Format: Identitas Siswa, Jenis Temuan, Skor Risiko, Rekomendasi Tindakan."
        })

        response = client.responses.create(
            model="gpt-5.4-nano",
            input=st.session_state.MESSAGES
        )
        ringkasan = response.output_text
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
    
    if "email_sudah_dikirim" not in st.session_state:
        st.session_state.email_sudah_dikirim = False

    if st.session_state.email_sudah_dikirim == False:
        yag = yagmail.SMTP(
            gmail_from,
            gmail_key
        )

        subject = f"Ringkasan Pemeriksaan {st.session_state.NAMA} dan kelas {st.session_state.KELAS}"

        yag.send(
            to=st.session_state.EMAIL,
            subject=subject,
            contents=st.session_state.RINGKASAN
        )

        yag.send(
            to=gmail_bkto,
            subject=subject,
            contents=st.session_state.RINGKASAN
        )

        log(f'EMAIL="{subject}"')
        st.session_state.email_sudah_dikirim = True
        st.success("Email berhasil dikirim")
    
    if "sms_sudah_dikirim" not in st.session_state:
        st.session_state.sms_sudah_dikirim = False

    if st.session_state.sms_sudah_dikirim == False:
        twilio_client = Client(account_sid, auth_token)

        sms_isi = f"Halo {st.session_state.NAMA}, ringkasan pemeriksaan DASS-21 Anda sudah dikirim ke e-mail {st.session_state.EMAIL}"
        time.sleep(5)
        twilio_client.messages.create(
            body=sms_isi,
            from_=twilio_number,
            to=st.session_state.HP
        )

        log(f'SMS="{sms_isi}"')
        st.session_state.sms_sudah_dikirim = True
        st.success("SMS berhasil dikirim")

    if st.button("Mulai Lagi"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

