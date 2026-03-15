# Configurazione File .env

## 📋 Guida Completa alla Configurazione

Questo progetto usa un file `.env` per memorizzare credenziali e configurazioni sensibili in modo sicuro.

## 🔐 Sicurezza

**IMPORTANTE:** 
- ❌ **NON committare MAI** il file `.env` su GitHub
- ✅ Solo il file `.env.example` va committato (è sicuro, contiene solo esempi)
- ✅ Il file `.gitignore` previene automaticamente il commit del `.env`

## 🚀 Setup Rapido (3 Passi)

### 1️⃣ Crea il File .env

```bash
# Copia il template
cp .env.example .env
```

### 2️⃣ Genera le Credenziali Criptate

```bash
# Esegui lo script di criptazione
python3 encrypt_credentials.py
```

Lo script ti guiderà passo-passo:
- Genererà una **MASTER_KEY** sicura
- Ti chiederà il **Token Telegram**
- Ti chiederà la **Password Web**
- Genererà automaticamente la **Flask Secret Key**
- Ti darà tutte le stringhe criptate da copiare nel `.env`

### 3️⃣ Completa il File .env

Apri il file `.env` e incolla i valori generati:

```bash
# Esempio di come dovrebbe apparire il tuo .env finale
MASTER_KEY_256=Jx4kL2mN9pQ...  # (la tua chiave generata)
TELEGRAM_TOKEN_ENC_256=abc123.def456.ghi789...
TELEGRAM_CHAT_ID=123456789
WEB_USER=admin
WEB_PASSWORD_ENC_256=xyz111.uvw222.rst333...
FLASK_SECRET_KEY_ENC_256=klm444.jkl555.hij666...
```

## 📝 Dettagli delle Variabili

### MASTER_KEY_256
- **Cosa è:** Chiave master per decriptare tutte le altre credenziali
- **Formato:** Stringa Base64 di 32 byte (256 bit)
- **Come ottenerla:** Generata dallo script `encrypt_credentials.py`
- **Esempio:** `Jx4kL2mN9pQ1rS5tU7vW8xY0zA2bC4dE6fG8hI0jK2lM4nO6pQ==`

### TELEGRAM_TOKEN_ENC_256
- **Cosa è:** Token del bot Telegram (criptato)
- **Come ottenerlo:** 
  1. Apri Telegram
  2. Cerca `@BotFather`
  3. Invia `/newbot` e segui le istruzioni
  4. Copia il token che ti dà (es: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
  5. Incollalo nello script di criptazione
- **Formato nel .env:** `nonce.tag.ciphertext` (tutto Base64)

### TELEGRAM_CHAT_ID
- **Cosa è:** ID della chat dove ricevere notifiche
- **Come ottenerlo:**
  1. Apri Telegram
  2. Cerca `@userinfobot`
  3. Invia `/start`
  4. Il bot ti risponderà con il tuo ID (es: `123456789`)
- **Formato:** Numero intero (NON criptato)
- **Esempio:** `123456789`

### WEB_USER
- **Cosa è:** Username per accedere all'interfaccia web
- **Formato:** Stringa (NON criptata, non sensibile)
- **Esempio:** `admin` o `pi` o il tuo nome

### WEB_PASSWORD_ENC_256
- **Cosa è:** Password per l'interfaccia web (criptata)
- **Come impostarla:** Inseriscila nello script di criptazione
- **Formato nel .env:** `nonce.tag.ciphertext` (tutto Base64)

### FLASK_SECRET_KEY_ENC_256
- **Cosa è:** Chiave usata da Flask per firmare le sessioni/cookie
- **Come ottenerla:** Generata automaticamente dallo script
- **Formato nel .env:** `nonce.tag.ciphertext` (tutto Base64)

## 🛠️ Metodo Manuale (Avanzato)

Se preferisci fare tutto manualmente:

### Genera Master Key
```python
python3 -c "from base64 import b64encode; import os; print(b64encode(os.urandom(32)).decode())"
```

### Genera Flask Secret Key
```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Cripta le Credenziali
Usa lo script `encrypt_credentials.py` fornito.

## ❓ FAQ

### Come faccio se perdo la MASTER_KEY?
❌ Dovrai rigenerare TUTTO:
1. Genera nuova MASTER_KEY
2. Ricripta tutte le credenziali
3. Aggiorna il file `.env`

### Posso usare password semplici?
⚠️ No! Usa password complesse:
- Almeno 12 caratteri
- Maiuscole, minuscole, numeri, simboli
- Non usare password ovvie

### Il file .env è sicuro?
✅ Sì, SE:
- NON lo committi su GitHub
- Il Raspberry è protetto (login, firewall)
- Le credenziali sono criptate

❌ No, SE:
- Lo condividi pubblicamente
- Usi password deboli
- Non proteggi il Raspberry

### Devo ricriptare se cambio password?
✅ Sì! Ogni volta che cambi una credenziale:
1. Esegui `encrypt_credentials.py`
2. Inserisci la stessa MASTER_KEY
3. Inserisci la nuova password
4. Aggiorna il `.env`

## 🔧 Troubleshooting

### Errore: "Impossibile decriptare le password"
**Cause possibili:**
- MASTER_KEY sbagliata
- Credenziali criptate con una chiave diversa
- File .env corrotto

**Soluzione:**
1. Verifica che la MASTER_KEY sia corretta
2. Ri-cripta le credenziali con la stessa chiave
3. Controlla che non ci siano spazi extra nel .env

### Errore: "File .env non trovato"
**Soluzione:**
```bash
# Verifica che sia nella directory corretta
ls -la .env

# Se non esiste, crealo da template
cp .env.example .env
```

### Telegram non invia notifiche
**Controlla:**
1. Token del bot corretto (prova su https://api.telegram.org/bot<TOKEN>/getMe)
2. CHAT_ID corretto
3. Bot avviato (invia `/start` al bot)
4. Credenziali criptate correttamente

## 📚 Riferimenti

- [AES-256 GCM Encryption](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Python dotenv](https://pypi.org/project/python-dotenv/)

## 🔒 Best Practices

1. ✅ **Usa password complesse** (almeno 12 caratteri)
2. ✅ **Backup della MASTER_KEY** (conservala offline, sicura)
3. ✅ **Cambia password regolarmente** (ogni 3-6 mesi)
4. ✅ **Non condividere credenziali** (neanche con amici fidati)
5. ✅ **Revoca token compromessi** (genera nuovo bot se necessario)
6. ❌ **Mai committare .env** (verifica sempre con `git status`)
7. ❌ **Mai credenziali in chiaro** (sempre criptate nel .env)

## 📞 Supporto

Problemi con la configurazione? 
- Controlla prima il [Troubleshooting](#troubleshooting)
- Verifica che tutte le librerie siano installate (`pip install -r requirements.txt`)
- Controlla i log dell'applicazione per errori specifici
