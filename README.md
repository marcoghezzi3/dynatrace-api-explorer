# Dynatrace API Explorer

Un'applicazione web leggera e locale per esplorare e testare le API Dynatrace in tempo reale. Realizzata con backend Flask e frontend vanilla JavaScript.

## Cosa Fa

**Dynatrace API Explorer** fornisce un'interfaccia interattiva per:
- Connettersi ad ambienti Dynatrace SaaS o Managed
- Costruire e inviare richieste API (GET, POST, PUT, DELETE, PATCH)
- Esplorare le API Dynatrace (`/api/v1/*`, `api/v2/*`, `/platform/*`)
- Visualizzare risposte JSON formattate con syntax highlighting
- Gestire parametri di query e body delle richieste
- Navigare la cronologia delle richieste (memorizzata localmente)
- Accesso rapido agli endpoint più comuni

Tutto il traffico viene instradato attraverso il tuo server locale — il token API non tocca mai il browser.

## Caratteristiche

✨ **Sicurezza al Primo Posto**
- Token API memorizzato solo nella sessione lato server
- Token mai restituito al browser, mai registrato, mai negli URL
- Token eliminato dall'input immediatamente dopo l'invio
- Validazione HTTPS sugli URL Dynatrace

🎨 **Interfaccia Moderna**
- Palette brand Dynatrace (teal #00B9CC su navy scuro)
- Tipografia DM Sans per l'UI, IBM Plex Mono per il codice
- Animazioni fluide e micro-interazioni
- Sidebar responsive + builder principale + barra cronologia
- Tema scuro ottimizzato per sessioni lunghe

⚡ **User-Friendly per Sviluppatori**
- Un singolo file HTML — nessun build step richiesto
- JavaScript vanilla (nessun framework)
- Tabella parametri di query dinamica
- Editor JSON body con pulsante format
- Tracciamento del tempo di risposta e avvisi di troncamento (cap 10 MB)
- Cronologia memorizzata in localStorage (max 50 entry)

🔧 **Supporto Ambienti**
| Tipo | Pattern URL |
|---|---|
| SaaS | `https://{env-id}.live.dynatrace.com` |
| Managed | `https://{domain}/e/{env-id}` |

## Prerequisiti

- Python 3.8+
- pip (o venv con dependencies già installate)

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/marcoghezzi3/dynatrace-api-explorer.git
cd dynatrace-api-explorer
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

Oppure se usi il venv incluso:
```bash
source venv/bin/activate  # Su Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Avvio dell'App

```bash
python app.py
```

Quindi apri il browser a **http://127.0.0.1:5000**

> **Nota:** Il server si lega esclusivamente a `127.0.0.1:5000` per sicurezza. Non sarà esposto alla rete.

## Come Funziona

**Backend (`app.py`)**
- Singola applicazione Flask (~150 righe)
- Riceve richieste dal browser
- Valida l'URL Dynatrace (deve essere HTTPS)
- Testa la connettività via `/api/v2/metrics?pageSize=1`
- Memorizza token + base_url nella sessione lato server
- Proxya le richieste API, iniettando `Authorization: Api-Token {token}` lato server
- Limita le risposte a 10 MB; imposta `X-Response-Truncated: true` se superato
- Sopprime i log di accesso per evitare di catturare accidentalmente i token

**Frontend (`static/index.html`)**
- Pannello di connessione: modalità SaaS costruisce automaticamente l'URL; modalità Managed accetta URL completo
- Request builder: selettore metodo, input path, tabella params dinamica, editor JSON
- Pannello risposta: badge status, tempo elapsed, JSON syntax-highlighted
- Barra cronologia: richieste recenti (metodo, path, status, timestamp)
- Accesso rapido: scorciatoie sidebar agli endpoint Dynatrace comuni

## Invarianti di Sicurezza

- `session['token']` è write-only dal punto di vista del browser
- `/api/status` restituisce solo `{connected: bool, base_url: str|null}`
- `app.secret_key` si rigenera ad ogni avvio del server, invalidando tutte le sessioni
- `BLOCKED_HEADERS` rimuove `authorization` dagli header inviati dal browser, poi re-inietta il token lato server
- Input token cancellato immediatamente dopo `POST /api/connect`

## Scorciatoie da Tastiera

| Azione | Binding |
|---|---|
| Invia richiesta | `Enter` (in path input) |
| (Altre in arrivo) | |

## Sviluppo

Per note architetturali dettagliate e workflow git, vedi [CLAUDE.md](./CLAUDE.md).

### Apportare Modifiche

Dopo modifiche significative al codice:
```bash
git add <file>
git commit -m "descrizione breve"
git push origin main
```

Per tornare a una versione precedente:
```bash
git log --oneline
git checkout <hash> -- .
```

## Tecnologie

- **Backend:** Python 3.14, Flask 3.1, Requests
- **Frontend:** JavaScript vanilla, CSS Grid, Google Fonts (DM Sans, IBM Plex Mono)
- **Nessuna dipendenza esterna:** JSON highlighting e parsing delle risposte eseguiti lato client

## Licenza

MIT

## Autore

Marco Ghezzi

---

**Domande?** Apri un issue su GitHub o consulta `CLAUDE.md` per dettagli architetturali.
