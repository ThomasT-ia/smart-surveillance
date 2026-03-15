#!/usr/bin/env python3
"""
Script per Criptare Credenziali con AES-256 GCM
===============================================

Questo script ti aiuta a criptare le tue credenziali (password, token, ecc.)
in modo sicuro usando AES-256 GCM.

UTILIZZO:
1. Esegui: python3 encrypt_credentials.py
2. Segui le istruzioni a schermo
3. Copia i valori criptati nel file .env

IMPORTANTE:
- Conserva la MASTER_KEY in un posto sicuro!
- Se perdi la master key, non potrai più decriptare le credenziali
"""

import os
import sys
from base64 import b64encode, b64decode
from Crypto.Cipher import AES

def generate_master_key():
    """Genera una nuova chiave master AES-256 (32 byte)"""
    key = os.urandom(32)  # 32 byte = 256 bit
    return b64encode(key).decode()

def encrypt_secret(plaintext, master_key_b64):
    """
    Cripta un segreto usando AES-256 GCM
    
    Args:
        plaintext (str): testo in chiaro da criptare
        master_key_b64 (str): chiave master in base64
    
    Returns:
        str: formato "nonce.tag.ciphertext" (tutto in base64)
    """
    # Decodifica la master key da base64
    master_key = b64decode(master_key_b64)
    
    # Crea un nonce casuale (12 byte standard per GCM)
    nonce = os.urandom(12)
    
    # Crea il cipher AES in modalità GCM
    cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
    
    # Cripta il testo
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    
    # Codifica tutto in base64 e unisci con punti
    nonce_b64 = b64encode(nonce).decode()
    tag_b64 = b64encode(tag).decode()
    cipher_b64 = b64encode(ciphertext).decode()
    
    return f"{nonce_b64}.{tag_b64}.{cipher_b64}"

def main():
    print("=" * 70)
    print("SCRIPT DI CRIPTAZIONE CREDENZIALI - AES-256 GCM")
    print("=" * 70)
    print()
    
    # Chiedi se vuoi generare una nuova master key o usarne una esistente
    print("Hai già una MASTER_KEY?")
    print("1. No, generane una nuova")
    print("2. Sì, la inserisco io")
    choice = input("\nScegli (1/2): ").strip()
    
    if choice == "1":
        master_key = generate_master_key()
        print("\n" + "=" * 70)
        print("🔑 MASTER KEY GENERATA (conservala in un posto sicuro!):")
        print("=" * 70)
        print(master_key)
        print("=" * 70)
        print("\n⚠️  IMPORTANTE: Inserisci questa chiave nel file .env come:")
        print(f"MASTER_KEY_256={master_key}")
        print()
    else:
        master_key = input("\nInserisci la tua MASTER_KEY (base64): ").strip()
    
    # Verifica che la master key sia valida
    try:
        key_bytes = b64decode(master_key)
        if len(key_bytes) != 32:
            print("❌ ERRORE: La master key deve essere di 32 byte (256 bit)")
            sys.exit(1)
    except:
        print("❌ ERRORE: Master key non valida (deve essere in base64)")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("CRIPTAZIONE CREDENZIALI")
    print("=" * 70)
    
    results = {}
    
    # Telegram Token
    print("\n1️⃣  TELEGRAM BOT TOKEN")
    print("   (Ottienilo da @BotFather su Telegram)")
    token = input("   Inserisci il token: ").strip()
    if token:
        results['TELEGRAM_TOKEN_ENC_256'] = encrypt_secret(token, master_key)
    
    # Password Web
    print("\n2️⃣  PASSWORD INTERFACCIA WEB")
    password = input("   Inserisci la password: ").strip()
    if password:
        results['WEB_PASSWORD_ENC_256'] = encrypt_secret(password, master_key)
    
    # Flask Secret Key
    print("\n3️⃣  FLASK SECRET KEY")
    print("   (Lascia vuoto per generarla automaticamente)")
    flask_key = input("   Inserisci la chiave (o premi INVIO): ").strip()
    if not flask_key:
        import secrets
        flask_key = secrets.token_hex(32)
        print(f"   ✅ Generata automaticamente: {flask_key[:20]}...")
    results['FLASK_SECRET_KEY_ENC_256'] = encrypt_secret(flask_key, master_key)
    
    # Mostra risultati
    print("\n" + "=" * 70)
    print("✅ CREDENZIALI CRIPTATE CON SUCCESSO!")
    print("=" * 70)
    print("\nCopia queste righe nel tuo file .env:\n")
    print("-" * 70)
    
    if choice == "1":
        print(f"MASTER_KEY_256={master_key}")
    
    for key, value in results.items():
        print(f"{key}={value}")
    
    print("-" * 70)
    print("\n⚠️  IMPORTANTE:")
    print("1. NON committare MAI il file .env su GitHub!")
    print("2. Conserva la MASTER_KEY in un posto sicuro")
    print("3. Se perdi la master key, dovrai rigenerare tutto")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operazione annullata dall'utente")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)
