import cv2, threading, time, datetime, os, asyncio, psutil, queue
from base64 import b64decode
from Crypto.Cipher import AES
from flask import Flask, render_template, Response, session, redirect, url_for, request, jsonify
from functools import wraps
from datetime import timedelta
from ultralytics import YOLO
from gpiozero import MotionSensor, LED
from telegram import Bot
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# --- FUNZIONE DI DECRIPTAZIONE AES-256 GCM 
def decrypt_secret(enc_variable_name):
    """Decripta una variabile d'ambiente criptata con AES-256 GCM"""
    try:
        master_key = b64decode(os.getenv("MASTER_KEY_256"))
        raw_data = os.getenv(enc_variable_name)
        if not raw_data:
            return None
        # Split dei tre pezzi: nonce.tag.ciphertext
        nonce_b64, tag_b64, cipher_b64 = raw_data.split(".")
        # Decodifica
        nonce = b64decode(nonce_b64)
        tag = b64decode(tag_b64)
        ciphertext = b64decode(cipher_b64)
        # oggetto
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        # Converte
        return decrypted_data.decode()
    except Exception as e:
        print(f"❌ Errore decrittazione {enc_variable_name}: {e}")
        return None

# --- CARICAMENTO SICURO DELLE CREDENZIALI 
# 1. Recuperiamo i dati non sensibili (in chiaro)
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ADMIN_USER = os.getenv('WEB_USER')

# 2. Decriptiamo i dati sensibili (Token, Password e Secret Key di Flask)
TOKEN = decrypt_secret('TELEGRAM_TOKEN_ENC_256')
ADMIN_PASS = decrypt_secret('WEB_PASSWORD_ENC_256')
FLASK_KEY = decrypt_secret('FLASK_SECRET_KEY_ENC_256')

# 3. Controllo sicurezza: se qualcosa fallisce, fermiamo tutto
if not TOKEN or not ADMIN_PASS or not FLASK_KEY:
    print("ERRORE CRITICO: Impossibile decriptare le password. Verifica il file .env!")
    exit()

# 4. Inizializzazione UNICA di Flask
app = Flask(__name__)
app.secret_key = FLASK_KEY # Utilizzo la chiave decriptata correttamente
app.permanent_session_lifetime = timedelta(minutes=30)

# Risoluzione e FPS
W_HD, H_HD = 1280, 720
W_REC, H_REC = 1280, 720
FPS_TARGET = 25

system_enabled = True
is_recording = False
last_seen_timestamp = 0 # Tiene traccia dell'ultima volta che una persona è stata vista

# Coda per i frame in RAM
video_queue = queue.Queue(maxsize=1000)

# --- DECORATOR PER PROTEGGERE LE ROTTE
def login_required(f):
    """
    Decorator che protegge le rotte richiedendo autenticazione.
    Se l'utente non è loggato, viene rediretto al login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- CLASSE VIDEO Classe che gestisce l'acquisizione video dalla camera in un thread separato.
class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, W_HD)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, H_HD)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        (self.grabbed, self.frame) = self.stream.read()

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        #        Loop infinito che acquisisce frame continuamente. Questa funzione viene eseguita nel thread separato.
        while True:
            (self.grabbed, self.frame) = self.stream.read()
            time.sleep(0.01)

    def read(self):
        return self.frame

# --- INIZIALIZZAZIONE 
vs = VideoStream().start()
model = YOLO('yolo26n.pt')
bot = Bot(token=TOKEN)
pir = MotionSensor(4)
led = LED(17)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REC_DIR = os.path.join(BASE_DIR, 'static/recordings')
os.makedirs(REC_DIR, exist_ok=True)

# --- AUTO-CLEANING (30 GIORNI) 
def daily_cleanup_task():
    """Esegue la pulizia ogni 24 ore in un thread separato"""
    while True:
        print(f" [{datetime.datetime.now()}] Avvio pulizia automatica (30 giorni)...")
        now = time.time()
        retention_time = 30 * 24 * 60 * 60
        count = 0
        try:
            for f in os.listdir(REC_DIR):
                f_path = os.path.join(REC_DIR, f)
                if os.path.isfile(f_path) and os.stat(f_path).st_mtime < (now - retention_time):
                    os.remove(f_path)
                    count += 1
            print(f" Pulizia completata. Eliminati {count} file vecchi.")
        except Exception as e:
            print(f" Errore durante la pulizia: {e}")
        time.sleep(86400)

# --- UTILS recupero informazioni del sistema
def get_sys_info():
    try:
        # Legge temperatura CPU dal file di sistema (Raspberry Pi)
        # /sys/class/thermal/thermal_zone0/temp contiene temp in milligradi
        # 'r' = modalità lettura
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            # Legge tutto il contenuto, converte in int e divide per 1000
            temp = int(f.read()) / 1000
    except:
        temp = 0
    return {
        "cpu_temp": round(temp, 1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

def get_daily_stats():
    daily_data = {}
    # Se la directory non esiste, ritorna dizionario vuoto
    if not os.path.exists(REC_DIR):
        return daily_data
    files = sorted(os.listdir(REC_DIR))
    for f in files:
        if f.startswith("video_") and f.endswith(".webm"):
            try:
                parts = f.split('_')
                date_str = parts[1]
                hour = int(parts[2].split('-')[0])
                if date_str not in daily_data:
                    daily_data[date_str] = [0] * 24
                daily_data[date_str][hour] += 1
            except:
                continue
    return daily_data

# --- ROTTE FLASK
@app.route('/api/system_stats')
def api_stats():
    # jsonify converte un dizionario Python in risposta JSON
    return jsonify({
        "sys": get_sys_info(),
        "stats": get_daily_stats(),
        "enabled": system_enabled
    })

@app.route('/toggle_system', methods=['POST'])
@login_required
def toggle_system():
    global system_enabled
    system_enabled = not system_enabled
    return jsonify({"status": system_enabled})

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', enabled=system_enabled)

@app.route('/stats')
def stats_page():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('stats.html', all_stats=get_daily_stats())

@app.route('/logs')
def logs_page():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    files = sorted([f for f in os.listdir(REC_DIR) if not f.startswith('.')], reverse=True)
    grouped = {}
    for f in files:
        if '_' in f:
            date_str = f.split('_')[1]
            if date_str not in grouped:
                grouped[date_str] = []
            grouped[date_str].append(f)
    return render_template('logs.html', grouped_logs=grouped)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Ora confrontiamo con le variabili prese dal file .env
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

# --- VIDEO_FEED PROTETTO CON AUTENTICAZIONE 
@app.route('/video_feed')
@login_required  # Protegge lo stream video da accessi non autorizzati
def video_feed():
    def gen():
        while True:
            f = vs.read()
            if f is not None:
                _, img = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 60])
                yield(b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + bytearray(img) + b'\r\n')
            time.sleep(0.05)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- WORKER DI SCRITTURA
def writer_worker(vid_path, out):
    #Svuota la coda della RAM sul disco
    while is_recording or not video_queue.empty():
        try:
            f = video_queue.get(timeout=1.0)
            out.write(f)
            video_queue.task_done()
        except:
            continue
    out.release()

# --- Registra un video finché vengono rilevate persone
def record_video(timestamp):
    global is_recording
    is_recording = True

    vid_path = os.path.join(REC_DIR, f"video_{timestamp}.webm")
    fourcc = cv2.VideoWriter_fourcc(*'VP80')
    # Crea l'oggetto VideoWriter di OpenCV con i parametri passati
    out = cv2.VideoWriter(vid_path, fourcc, FPS_TARGET, (W_REC, H_REC))

    threading.Thread(target=writer_worker, args=(vid_path, out), daemon=True).start()

    frame_duration = 1.0 / FPS_TARGET

    while time.time() - last_seen_timestamp < 10:
        start_loop = time.time()
        f = vs.read()
        if f is not None:
            if not video_queue.full():
                video_queue.put(f)
        elapsed = time.time() - start_loop
        time.sleep(max(0, frame_duration - elapsed))

    is_recording = False

#  FUNZIONE DI RILEVAMENTO 
def detect_motion():
    global last_seen_timestamp
    while True:
        # Se stiamo già registrando, controlliamo YOLO SEMPRE (anche se il PIR è False)
        # Se non stiamo registrando, aspettiamo il segnale dal PIR.
        should_check = (system_enabled and pir.motion_detected) or is_recording

        if should_check:
            led.on()
            frame = vs.read()
            if frame is not None:
                results = model(frame, conf=0.75, classes=[0], verbose=False)
                if any(model.names[int(c)] == 'person' for r in results for c in r.boxes.cls):
                    last_seen_timestamp = time.time()
                    if not is_recording:
                        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        img_path = os.path.join(REC_DIR, f"alert_{ts}.jpg")
                        cv2.imwrite(img_path, frame)
                        threading.Thread(target=record_video, args=(ts,), daemon=True).start()
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(bot.send_photo(CHAT_ID, open(img_path, 'rb'), caption=f"🚨 Persona rilevata!\n📅 {ts}"))
                        except:
                            pass
            time.sleep(1) # Check ogni secondo
        else:
            led.off()
            time.sleep(0.1)

if __name__ == '__main__':
     #Avvia il thread di pulizia automatica
    threading.Thread(target=daily_cleanup_task, daemon=True).start()
    threading.Thread(target=detect_motion, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
