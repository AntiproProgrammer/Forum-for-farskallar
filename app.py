from flask import Flask, session, redirect, url_for, request
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'supersecretkey'


def get_db():
    """Öppnar en ny anslutning till databasen."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='users'
    )


def query(sql, params=(), fetchone=False, commit=False):
    """Liten hjälpfunktion: kör en fråga och returnerar rader som dict:ar."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        if fetchone:
            return cur.fetchone()
        return cur.fetchall()
    finally:
        conn.close()


@app.route('/')
def index():
    username = session.get('username')

    if username:
        user = query(
            'SELECT id, username, description FROM users WHERE username = %s',
            (username,),
            fetchone=True
        )

        if user is None:
            session.clear()
            return redirect(url_for('index'))

        return f'''
            <h1>Välkommen, {user['username']}!</h1>
            <p>Beskrivning: {user['description']}</p>
            <p>Ditt id i databasen: {user['id']}</p>
            <ul>
                <li><a href="/new_post">Skriv nytt inlägg</a></li>
                <li><a href="/profile">Min profil</a></li>
                <li><a href="/logout">Logga ut</a></li>
            </ul>
        '''
    else:
        return '''
            <h1>Inte inloggad</h1>
            <p>Du måste logga in för att se mer.</p>
            <a href="/login">Logga in</a>
        '''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = query(
            'SELECT id, username, password FROM users WHERE username = %s',
            (username,),
            fetchone=True
        )

        if user and user['password'] == password:
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return 'Fel användarnamn eller lösenord. <a href="/login">Försök igen</a>'

    return '''
        <h1>Logga in</h1>
        <form method="post">
            Användarnamn: <input type="text" name="username"><br>
            Lösenord:     <input type="password" name="password"><br>
            <input type="submit" value="Logga in">
        </form>
        <p><i>Testa: alice/katt123, bob/hund456, carol/fisk789</i></p>
    '''


@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            user = query(
                'SELECT id FROM users WHERE username = %s',
                (session['username'],),
                fetchone=True
            )
            if user:
                query(
                    'INSERT INTO posts (user_id, content) VALUES (%s, %s)',
                    (user['id'], content),
                    commit=True
                )
                return redirect(url_for('index'))
        return 'Inlägget får inte vara tomt. <a href="/new_post">Försök igen</a>'

    return '''
        <h1>Skriv nytt inlägg</h1>
        <form method="post">
            <textarea name="content" rows="5" cols="50" placeholder="Skriv ditt inlägg här..."></textarea><br><br>
            <input type="submit" value="Publicera">
        </form>
        <p><a href="/">Tillbaka</a></p>
    '''


@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = query(
        'SELECT id, username, description FROM users WHERE username = %s',
        (session['username'],),
        fetchone=True
    )

    return f'''
        <h1>Profil för {user['username']}</h1>
        <p>Id: {user['id']}</p>
        <p>Beskrivning: {user['description']}</p>
        <p><a href="/">Tillbaka</a></p>
    '''


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')