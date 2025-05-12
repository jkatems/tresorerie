from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'

def init_db():
    if not os.path.exists("tresorerie.db"):
        conn = sqlite3.connect("tresorerie.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE revenus 
                     (id INTEGER PRIMARY KEY, description TEXT, montant REAL, date TEXT)''')
        c.execute('''CREATE TABLE depenses 
                     (id INTEGER PRIMARY KEY, description TEXT, montant REAL, date TEXT, category TEXT)''')
        c.execute('''CREATE TABLE utilisateurs 
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')

        # Ajouter un utilisateur admin par défaut
        hashed_password = generate_password_hash("admin123")
        c.execute("INSERT INTO utilisateurs (username, password) VALUES (?, ?)", 
                 ("admin", hashed_password))

        conn.commit()
        conn.close()

init_db()

@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect("tresorerie.db")
    c = conn.cursor()
    c.execute("SELECT SUM(montant) FROM revenus")
    total_revenus = c.fetchone()[0] or 0
    c.execute("SELECT SUM(montant) FROM depenses")
    total_depenses = c.fetchone()[0] or 0
    solde = total_revenus - total_depenses
    conn.close()
    return render_template("dashboard.html", solde=solde, revenus=total_revenus, depenses=total_depenses)

@app.route('/ajouter_revenu', methods=['GET', 'POST'])
def ajouter_revenu():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        description = request.form['description']
        montant = float(request.form['montant'])
        date = request.form['date']
        conn = sqlite3.connect("tresorerie.db")
        c = conn.cursor()
        c.execute("INSERT INTO revenus (description, montant, date) VALUES (?, ?, ?)", 
                 (description, montant, date))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))  # Changé de 'index' à 'dashboard'
    return render_template("add_income.html")

@app.route('/ajouter_depense', methods=['GET', 'POST'])
def ajouter_depense():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        description = request.form['description']
        montant = float(request.form['montant'])
        date = request.form['date']
        conn = sqlite3.connect("tresorerie.db")
        c = conn.cursor()
        c.execute("INSERT INTO depenses (description, montant, date) VALUES (?, ?, ?)", 
                 (description, montant, date))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))  # Changé de 'index' à 'dashboard'
    return render_template("add_expende.html")

@app.route('/historique')
def historique():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect("tresorerie.db")
    c = conn.cursor()
    c.execute("SELECT description, montant, date FROM revenus")
    revenus = c.fetchall()
    c.execute("SELECT description, montant, date FROM depenses")
    depenses = c.fetchall()
    conn.close()
    return render_template("history.html", revenus=revenus, depenses=depenses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("tresorerie.db")
        c = conn.cursor()
        c.execute("SELECT * FROM utilisateurs WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Nom d'utilisateur ou mot de passe incorrect")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/stats')
def stats():
    conn = sqlite3.connect("tresorerie.db")
    c = conn.cursor()
    revenus = c.execute("SELECT date, montant FROM revenus").fetchall()
    depenses = c.execute("SELECT date, montant FROM depenses").fetchall()
    conn.close()

    return jsonify({
        "revenus": [{"date": r[0], "montant": r[1]} for r in revenus],
        "depenses": [{"date": d[0], "montant": d[1]} for d in depenses]
    })

if __name__ == '__main__':
    app.run(debug=True)