import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__) # Crea l'istanza dell'applicazione
app.config.from_object(__name__) # Carica la config da questo file (flaskr.py)

# Carichiamo una config di default
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'demo.db'),
    SECRET_KEY='development key',   # Serve per mantenere le sessioni client-side sicure
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('DEMO_SETTINGS', silent=True) #Carica il file config puntato dalla variabile DEMO_SETTINGS, solo se presente
#Il flag silent=True indica all'app di non creare problemi nel caso la variabile DEMO_SETTINGS non sia presente
#L'oggetto config si comporta come un dizionario, quindi sarà possibile aggiornarlo successivamente con nuovi valori

# La funzione connect permette di accedere rapidamente al database, e di utilizzare l'oggetto sqlite3.Row
# per rappresentare le righe del db. Questo permette di trattare le righe come dizionari, e non come tuple
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

# La funzione ed il comando seguenti inizializzano il database
def init_db(): 
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f: # open_resource() apre la risorsa fornita dall'applicazione (in questo caso schema.sql)
        db.cursor().executescript(f.read())
    db.commit()

# Il decoratore app.cli.command fa in modo che Flask crei automaticamente il contesto dell'applicazione 
# quando il comando viene eseguito. Quando lo script termina, verrà effettuato il teardown del context
# e i
@app.cli.command('initdb')
def initdb_command():
    """Inizializza il database"""
    init_db()
    print('Initialized the database.')


# Apre una nuova connessione al database, se non ne è presente già una
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
# dove g è una variabile utilizzata per salvare le informazioni sul db

# Chiude il database alla fine della richiesta, grazie al decoratore teardown_appcontext il codice viene
# eseguito ogni volta che il contesto dell'applicazione viene "teared down" (abbattuto)
# Un teardown puo' avvenire per due motivi: per una richiesta andata a buon fine (per la quale il parametro errore sarà settato a None)
# o nel caso di un'eccezione, dove il codice derrore verrà passato come argomento della fuzione teardown.
@app.teardown_appcontext 
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()




@app.route('/')
def show_entries(): # La funzione ci permette di esaminare le entries salvate sul database
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries) # Le entry verranno passate al template show_entries.html
# E verranno ritornate dopo essere state renderizzate

# La seguente funzione permette agli utenti (se loggati) di aggiungere nuove entries
@app.route('/add', methods=['POST'])    # Risponde solo a richieste HTTP POST 
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)', # E' importante inserire '?' negli statement SQL per evitare vulnerabilità nei confronti di SQL injections
                 [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted') # Il messaggio indica che tutto è andato a buon fine
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']: # Controlla se lo username è lo stesso salvato nel DB
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']: #Controlla se la password è corretta
            error = 'Invalid password'
        else:
            session['logged_in'] = True # Tutto è andato a buon fine -> la chiave logged_in viene impostata a True
            flash('You were logged in')
            return redirect(url_for('show_entries')) # L'utente loggato viene reinderizzato alla pagina show_entries
    return render_template('login.html', error=error) # Restituisce l'errore e chiede di nuov password e username


@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Reimposta la chiave logged_in a False per la sessione corrente
    flash('You were logged out')
    return redirect(url_for('show_entries')) # Reindirizza l'utente a show_entries

# NB: Le password non vanno MAI salvate come plain text in un'applicazione reale, come invece
# viene fatto qui, per amor di brevità. Consultare la documentazione di Flask per maggiori informazioni.
