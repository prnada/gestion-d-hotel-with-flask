from flask import Flask, render_template, request, redirect, url_for,session
import joblib
import mysql.connector
from flask_mysqldb import MySQL
import hashlib
from googletrans import Translator
import json
def translate(text, target_language):
    translator = Translator()
    translation = translator.translate(text, dest=target_language)
    return translation.text
 
app = Flask(__name__)

# Configuration de la base de données MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_hotel'
app.config['MYSQL_CHARSET'] = 'utf8mb4'
mysql = MySQL(app)
# Configuration de Flask-Login
app.config['SECRET_KEY'] = 'secret_key'

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect('/')


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/reserver',methods=['GET', 'POST'])
def reservation():
    chambre_id=request.args['chambre_id']
    return render_template('reservation.html',chambre_id=chambre_id)

@app.route('/chambres')
def chambres():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM chambres')
    chambres = cur.fetchall()    
    cur.close()
    return render_template('chambres.html',chambres=chambres)

# Enregistrer une réservation
@app.route('/enregistrer', methods=['GET', 'POST'])
def enregistrer():
    chambre_id=request.args['chambre_id']
    if request.method == 'POST':
        # Récupérer les données du formulaire
        id=session['id']
        arrivee = request.form['arrivee']
        depart = request.form['depart']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO reservations (user_id, arrivee, depart, chambre_id) VALUES (%s,%s, %s, %s)', (id, arrivee, depart, chambre_id))
        mysql.connection.commit()
        cur.close()
        cur = mysql.connection.cursor()
        cur.execute('UPDATE chambres SET disponible = 0 WHERE id = %s', (chambre_id,))
        mysql.connection.commit()
        cur.close()
        message="Votre reservation est complète !"
        return redirect(url_for('reservations',message=message))
    else:
        return render_template('reservation.html',chambre_id=chambre_id)

# Liste des réservations en cours (accessible uniquement par l'admin)
@app.route('/reservation', methods=['GET', 'POST'])
def reservations():
    id = session['id']
    cur = mysql.connection.cursor()
    cur.execute('SELECT reservations.arrivee, reservations.depart, utilisateurs.nom, chambres.type FROM reservations, utilisateurs, chambres WHERE reservations.user_id = utilisateurs.id AND reservations.chambre_id = chambres.id AND reservations.user_id = %s', (id,))
    reservations = cur.fetchall()
    cur.close()
    if request.method == 'GET':
        message = request.args.get('message')
        return render_template('liste_reservations.html', reservations=reservations, message=message)
    else:
        return render_template('liste_reservations.html', reservations=reservations)

# Page des commentaires (accessible uniquement par l'admin)
@app.route('/commentaires')
def commentaires():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM commentaires')
    commentaires = cur.fetchall()
    cur.close()
    return render_template('commentaires.html', commentaires=commentaires)
    
#Page des commentaires (accessible uniquement par l'admin)
@app.route('/commentaires_admin')
def afficher_commentaires():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM commentaires')
    commentaires = cur.fetchall()
    cur.close()
    return render_template('commentaires.html', commentaires=commentaires)

@app.route('/avis')
def avis():
    return render_template('avis.html')
@app.route('/ajouter_avis',methods=['GET', 'POST'])
def prediction():
    cur = mysql.connection.cursor()
    id=session['id']
    nb_commentaires_positifs = 0
    nb_commentaires_negatifs = 0
    cur.execute('SELECT COUNT(*) FROM commentaires WHERE user_id = %s AND predire = %s', (id, 'Positive'))
    nb_commentaires_positifs = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM commentaires WHERE user_id = %s AND predire = %s', (id, 'Negative'))
    nb_commentaires_negatifs = cur.fetchone()[0]
    if request.method == 'POST':
        text = request.form['avis']
        langue_cible = "en"
        resultat_traduction = translate(text, langue_cible)
    # Charger les fichiers de modèle et de vecteur
        vectorizer = joblib.load("my_vectorizer_RL.pkl")
        model = joblib.load("RegressionL_model.pkl")
        # Utiliser le modèle pour prédire le sentiment du commentaire
        new_text_vec = vectorizer.transform([resultat_traduction])
        prediction = model.predict(new_text_vec)
        if prediction == 1:
            result='Positive'
            nb_commentaires_positifs += 1
        elif prediction == 0:
            result='Negative'
            nb_commentaires_negatifs += 1
        else:
            result='Neutral'
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO commentaires (user_id, commentaire, predire) VALUES (%s, %s, %s)', (id, text, result))
        mysql.connection.commit()
        cur.close()
        return redirect('/accueil')
#créer un compte
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['nom']
        email = request.form['email']
        password = request.form['password']
        new_pas = hashlib.sha256(str(password).encode("utf-8")).hexdigest()
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO utilisateurs (nom, email, password) VALUES (%s, %s, %s)', (username, email,new_pas))
        mysql.connection.commit()
        cur.close()

        message = "Votre compte a été créé avec succès !"
        return render_template('register.html', message=message)
    else:
        return render_template('register.html')

@app.route('/accueil')
def accueil():
    return render_template('index.html')  


# Authentification d'un utilisateur
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(str(password).encode("utf-8")).hexdigest()
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM utilisateurs WHERE email = %s AND password = %s', (email, hashed_password))
        row = cur.fetchall()
        if row:
            for row in row:
                session['fullname']=row[1]
                session['id'] = row[0]
            return redirect('/accueil')
        else:
            error = 'Email ou mot de passe invalide. Veuillez réessayer.'
            return error
    else:
        return render_template('login.html')
    

@app.route('/rechercher', methods=['GET', 'POST'])
def rechercher():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        arrivee = request.args.get('arrivee')
        depart = request.args.get('depart')
        budget = request.args.get('budget')

        # Effectuer la recherche dans la base de données
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM chambres 
                       WHERE disponible = 1 
                       AND prix BETWEEN %s AND %s''', get_prix_range(budget))
        chambres = cur.fetchall()
        cur.close()
        # Renvoyer la liste des chambres disponibles
        return render_template('chambres.html', chambres=chambres)

def get_prix_range(budget):
    if budget == '0-50':
        return (0, 50)
    elif budget == '50-100':
        return (50, 100)
    elif budget == '100-200':
        return (100, 200)
    elif budget == '200+':
        return (200, 99999)
    else:
        return (0, 99999)

 
 
 
if __name__ == '__main__':
    app.run(debug=True)
 