Youtube video: https://youtu.be/N7Cis1Tb22Q

1. Introduzione
Nel panorama attuale della Internet of Things (IoT), la sicurezza domestica ha subito un’evoluzione significativa, passando da semplici sistemi di allarme "passivi" a soluzioni connesse e intelligenti. Il presente progetto riguarda lo sviluppo di un sistema di videosorveglianza avanzato basato su Raspberry Pi 5, progettato per superare i limiti dei sensori di movimento tradizionali e per garantire un elevato livello di privacy sui dati.
1.1 Definizione del Problema
I sistemi di sicurezza convenzionali basati esclusivamente su sensori PIR (Passive Infrared) o di riconoscimento delle figure soffrono spesso di un alto tasso di falsi allarmi. Questi sono causati da variazioni termiche, animali domestici o movimenti di oggetti inanimati (come tende o rami). Questo genera "rumore" nelle notifiche e riduce l'affidabilità percepita dall'utente. A questa alternativa si può ricorrere a sistemi con analisi di dati tramite cloud, più affidabili ma con un rischio concreto per la nostra privacy.
1.2 La Soluzione Proposta
La soluzione proposta integra la rilevazione fisica del movimento con l'Intelligenza Artificiale (Computer Vision). Il sistema utilizza un sensore PIR per attivare il monitoraggio, ma delega a un modello di Deep Learning (YOLO) il compito di confermare l'effettiva presenza di una figura umana prima di generare un'allerta.
1.3 Obiettivi del Progetto
Il sistema è stato sviluppato per soddisfare i tre pilastri fondamentali dell'IoT:
1.	Edge Computing: Elaborazione locale dei dati video su piattaforma Raspberry Pi 5 per garantire privacy e velocità di risposta.
2.	Integrazione Sensori/Attuatori: Utilizzo di input fisici (PIR) e feedback visivi (LED e Camera) per l'interazione con l'ambiente e l’utente.
3.	Accesso Remoto Multicanale: Monitoraggio e controllo tramite una dashboard web e notifiche istantanee via Bot Telegram, garantendo all'utente il pieno controllo del dispositivo da qualsiasi posizione.
2. Architettura del Sistema
L'architettura del sistema segue un modello Edge-first, dove l'elaborazione pesante avviene localmente sull'unità centrale (Edge) e i risultati vengono inviati a servizi remoti (Cloud) per la fruizione dell'utente.
2.1 Infrastruttura Hardware
Il sistema è composto dai seguenti componenti fisici:
•	Unità Centrale: Raspberry Pi 5 (8GB RAM). Scelta per la versatilità e le elevate prestazioni della CPU e il supporto hardware per il multitasking.
•	Sensore di Input: Modulo PIR HC-SR501, collegato al pin GPIO 4. Rileva variazioni di radiazione infrarossa nel raggio di 7 metri.
•	Sensore Video: Camera USB Logitech C920 ad alta definizione (1920x1080p) per l'acquisizione dei frame.
•	Attuatore Locale: LED collegato al pin GPIO 17, utilizzato per fornire un feedback visivo immediato sullo stato di rilevamento dell'AI.

2.2 Cablaggio e Realizzazione Fisica
L'integrazione tra l'unità centrale e le periferiche è stata realizzata su una breadboard sperimentale, utilizzando cavi jumper per garantire la modularità del prototipo. Il circuito segue uno schema preciso per proteggere i componenti e garantire la stabilità del segnale:
•	Circuito LED (Output): Il LED di stato non è collegato direttamente al pin GPIO, ma è posto in serie a un resistore di limitazione di corrente. Questo accorgimento è fondamentale per evitare il sovraccarico della porta GPIO del Raspberry Pi e prevenire il burn-out del diodo luminoso.
•	Circuito PIR (Input): Il sensore HC-SR501 è alimentato tramite i pin a 5V del Raspberry Pi. Il pin di segnale del sensore è collegato direttamente al GPIO 4, configurato via software per rilevare i segnali generati dal rilevamento di movimento.
•	Gestione dell'alimentazione: Il cablaggio è stato ottimizzato per minimizzare le interferenze, separando fisicamente le linee di alimentazione dai cavi di segnale dati, garantendo che l'input inviato all'algoritmo di IA sia privo di rumore elettrico.

 

2.3 Stack Software e Tecnologie
La logica di controllo è interamente sviluppata in Python 3, sfruttando le seguenti librerie:
•	OpenCV: Per la manipolazione dei flussi video e la codifica dei file .webm.
•	Ultralytics (YOLO): Modello di rete neurale convoluzionale per il riconoscimento di oggetti in tempo reale.
•	Flask: Framework web per la creazione della dashboard di controllo e delle API di stato.
•	Telegram bot (Telegram API): Per l'invio asincrono di notifiche e file multimediali.
•	Pycryptodome: per poter utilizzare la crittografia AES 256
2.4 Logica di Funzionamento (Workflow)
Per garantire fluidità e reattività, il software adotta un'architettura Multithreading con una gestione a code (Queue):
1.	Thread di Acquisizione: Legge costantemente i frame dalla camera e li rende disponibili in RAM.
2.	Thread di Elaborazione (IA): Viene attivato dal segnale del sensore PIR. Analizza i frame tramite YOLO. Se viene rilevata una "person", attiva la registrazione.
3.	Thread di Scrittura (Buffer Queue): Riceve i frame dall'AI e li scrive su disco in modo asincrono, evitando che la lentezza della MicroSD rallenti il sistema.
4.	Thread Web Server: Gestisce l'interfaccia utente e le richieste remote in parallelo a tutte le altre attività.
2.4.1 Gestione dello Storage e Pulizia Automatica
Considerata la natura continua del sistema di videosorveglianza e le limitate capacità di archiviazione dell’unità Edge, è stato implementato un meccanismo automatico di gestione dello spazio su disco.
Il sistema esegue giornalmente una procedura di auto-cleaning che elimina in modo automatico i file video e le immagini di allerta più vecchi di 30 giorni. La procedura viene avviata tramite un task che si attiva ogni 24 ore e opera esclusivamente sui file di registrazione.
Questo approccio consente di mantenere costante l’utilizzo dello storage nel tempo, prevenendo la saturazione della memoria e garantendo la continuità operativa del dispositivo senza richiedere interventi manuali da parte dell’utente.
2.4.2 Sicurezza dei Dati e Crittografia AES-256
La strategia di sicurezza adottata non si ferma alla mera protezione del canale di trasmissione, estendendosi alla salvaguardia delle credenziali critiche residenti sul dispositivo. Considerando la natura Edge del Raspberry, che lo rende fisicamente accessibile, la memorizzazione di chiavi sensibili in chiaro costituirebbe un vettore di rischio considerevole.
Per mitigare tale vulnerabilità, è stato implementato un modulo crittografico basato sullo standard AES-256 (Advanced Encryption Standard a 256 bit). Questa tecnologia viene applicata a due livelli critici:
•	Password di Accesso alla Dashboard: Le credenziali per il login web non sono memorizzate in chiaro, ma cifrate. Ciò rende inefficace qualsiasi tentativo di accesso non autorizzato all'interfaccia di controllo, anche nel caso di analisi diretta del codice sorgente.
•	Token API Telegram: Il token univoco, necessario per l'autenticazione del Bot con i server Telegram, è anch'esso sottoposto a cifratura AES-256. Questa misura impedisce che, in caso di furto fisico della MicroSD o compromissione del file system, un attaccante possa esfiltrare il token per assumere il controllo del Bot o intercettare le notifiche di sorveglianza.
Questa protezione dei dati viene completata dalla messa in sicurezza del canale di trasmissione, analizzata nel paragrafo successivo.
2.5 Connettività e Accesso Remoto
Per soddisfare il requisito di accessibilità remota senza compromettere la sicurezza della rete locale, è stato implementato un Tunnel Cloudflare. Questo permette di:
•	Esporre il web server locale su un dominio pubblico sicuro (HTTPS).
•	Evitare l'apertura manuale di porte sul router (Port Forwarding), proteggendo il sistema da attacchi esterni.
3. Descrizione del Funzionamento e Risultati
In questo capitolo viene analizzato il comportamento del sistema durante il ciclo operativo, evidenziando le soluzioni tecniche adottate per garantire la fluidità del video e l'accuratezza delle segnalazioni.
3.1 Algoritmo di Rilevamento a Doppia Verifica
Il sistema opera secondo una logica gerarchica per ottimizzare le risorse del Raspberry Pi 5:
1.	Fase di Standby: Il modello YOLO è caricato in memoria ma "dormiente". Il sistema monitora solo il segnale digitale dal sensore PIR (basso consumo CPU).
2.	Attivazione (Trigger): Quando il PIR rileva movimento, il sistema attiva il controllo dei frame con YOLO.
3.	Validazione IA: YOLO analizza i frame alla ricerca della classe "person" con una confidenza superiore al 75%.
4.	Registrazione Dinamica: Se viene confermata una presenza, inizia la registrazione. La registrazione non si interrompe finché l'IA vede il soggetto, garantendo la continuità del video anche se il sensore PIR smette temporaneamente di rilevare il movimento (fase di stasi del soggetto).
3.2 Ottimizzazione del Flusso Video (Risultati Tecnici)
Uno dei principali risultati raggiunti riguarda la stabilità del framerate a risoluzioni HD ready.
•	Risoluzione: 1280x720p (HD).
•	Framerate: 25 FPS.
•	Soluzione al collo di bottiglia: Per evitare la perdita di fotogrammi dovuta alla latenza di scrittura sulla MicroSD, è stata implementata una Frame Buffer Queue in RAM. I frame vengono catturati a 25 FPS reali e "parcheggiati" in una coda FIFO (First-In-First-Out). Un thread secondario (Writer) preleva i frame dalla coda e li codifica in formato WebM asincronamente.
Questo approccio ha permesso di ottenere video fluidi e della durata corretta, eliminando l'effetto "accelerato" tipico dei sistemi che processano e scrivono i dati in modo sincrono su hardware limitati. Purtroppo questo metodo però ha uno svantaggio, nel caso il video dovesse durare più di un minuto potremmo incontrare 2 problemi:
1.	Latenza in fase di scrittura: questo potrebbe causare problemi nel caso ci fosse un ulteriore evento poco dopo la fine di quello precedente.
2.	Protezione da saturazione RAM: per sicurezza è stato impostato un numero massimo di frame che possono essere allocati temporaneamente nella RAM (1000), questo, per non saturare la memoria.
3.3 Interfaccia e Notifiche Remote
I test hanno confermato l'efficacia della comunicazione remota:
•	Telegram Bot: Il sistema invia una notifica push con la foto dell'evento entro 2-3 secondi  dal rilevamento. Questo tempo di latenza ridotto è essenziale per un sistema di sicurezza.
•	Web Dashboard: Tramite la dashboard, l'utente può visualizzare in tempo reale la temperatura della CPU (mantenuta fra i 40-50°C  grazie all'ottimizzazione del codice e della ventola) e lo stato di occupazione della memoria, oltre a poter attivare/disattivare il monitoraggio con un click.
3.4 Analisi dei Risultati
L'integrazione di YOLO ha ridotto i falsi positivi del 90%  rispetto all'uso del solo sensore PIR. Il sistema si è dimostrato capace di ignorare movimenti di oggetti inanimati e variazioni di luce, attivando i protocolli di allerta solo in presenza di intrusioni umane reali.
4. Conclusioni e Sviluppi Futuri
Il progetto ha dimostrato con successo come l'integrazione di tecniche di Edge AI in un ecosistema IoT possa trasformare un semplice sensore di movimento in uno strumento di monitoraggio intelligente, affidabile e accessibile.
4.1 Considerazioni Finali
Il sistema realizzato soddisfa pienamente i requisiti prefissati:
•	Affidabilità: L'uso della "doppia verifica" (PIR + YOLO) ha eliminato quasi totalmente i falsi allarmi , un problema critico nei sistemi di sorveglianza entry-level.
•	Performance: L'adozione di un'architettura multithreading e di una gestione asincrona della memoria ha permesso di superare i limiti fisici di scrittura del Raspberry Pi 5, garantendo flussi video HD a 25 FPS.
•	Usabilità: L'integrazione con Telegram e la dashboard rende il dispositivo estremamente facile da gestire per l'utente finale, indipendentemente dalla sua posizione geografica.
4.2 Sviluppi Futuri
Nonostante l'attuale stabilità, il sistema è stato progettato con un'architettura modulare che permette future espansioni:
1.	Riconoscimento Facciale: Implementazione di librerie di face recognition per distinguere tra membri della famiglia ed estranei, personalizzando le notifiche.
2.	Archiviazione Cloud Alternativa: Integrazione con API di Google Drive o AWS per il backup automatico dei video, proteggendo i dati anche in caso di furto fisico del dispositivo.
3.	Integrazione Domotica (Smart Home): Possibilità di interfacciare il sistema con protocolli come MQTT o Home Assistant per attivare automaticamente luci o sirene in caso di intrusione confermata.
4.	Edge LLM: Sperimentazione con modelli di linguaggio locali per generare descrizioni testuali degli eventi (es. "Rilevata una persona con maglia rossa alle 14:30") inviate direttamente su Telegram.
5.	Protezione Brute-Force: Introduzione di un limite massimo di tentativi di login falliti per proteggere la dashboard web. Il sistema potrebbe inibire l'accesso a specifici indirizzi IP o bloccare temporaneamente l'account dopo un numero prefissato di errori, neutralizzando tentativi di intrusione automatizzati.

