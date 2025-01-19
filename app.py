# Importeert de benodigde modules uit Flask
from flask import Flask, render_template, request, redirect, url_for
# Importeert Flask-Login voor gebruikersbeheer en authenticatie
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# Importeert SQLAlchemy voor databasebeheer in Flask
from flask_sqlalchemy import SQLAlchemy

# Initialisatie van de Flask-app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Geheime sleutel voor sessies en beveiliging
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database configuratie
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Vermijden van waarschuwingen over wijzigingen in de database

# Initialiseer SQLAlchemy en Flask-Login
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Account-klasse voor de database 
# Deze klasse is de accountinformatie van een gebruiker in de database
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Uniek ID voor elke gebruiker
    username = db.Column(db.String(150), unique=True, nullable=False)  # Gebruikersnaam, moet uniek zijn
    password = db.Column(db.String(150), nullable=False)  # Wachtwoord

# User-klasse voor Flask-Login 
# Flask-Login vereist een User-klasse voor gebruikersbeheer
class User(UserMixin):
    def __init__(self, id):
        self.id = id  # ID van de gebruiker

#  Gebruiker laden uit de database 
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)  # Retourneer de User data op basis van de  userID

#  Zorgt ervoor dat de tabellen worden aangemaak
# Creëer de tabellen in de database bij de start van de applicatie
with app.app_context():
    db.create_all()

#  Routes voor de website 
@app.route('/')
def home():
    # Laad de home-pagina
    return render_template('home.html')

@app.route('/vragen', methods=['GET', 'POST'])
def vragen():
    # Verwerk het formulier van de vraagpagina
    if request.method == 'POST':
        # Haal gebruikersantwoorden op
        weight = request.form['weight']
        length = request.form['length']
        width = request.form['width']
        height = request.form['height']
        on_pallet = request.form['on_pallet']
        delivery_type = request.form['delivery_type']
        track_trace = request.form['track_trace']

        # Redirect naar de resultatenpagina met de ingevulde gegevens
        return redirect(url_for('result',
                                weight=weight,
                                length=length,
                                width=width,
                                height=height,
                                on_pallet=on_pallet,
                                delivery_type=delivery_type,
                                track_trace=track_trace))

    # Laad de vraagpagina voor GET-verzoeken
    return render_template('vragen.html')

@app.route('/result')
def result():
    # Haal de parameters op voor de resultaten
    weight = request.args.get('weight', '')
    length = request.args.get('length', '')
    width = request.args.get('width', '')
    height = request.args.get('height', '')
    on_pallet = request.args.get('on_pallet', '')
    delivery_type = request.args.get('delivery_type', '')
    track_trace = request.args.get('track_trace', '')

    # Render de resultatenpagina met de verkregen gegevens
    return render_template('result.html',
                           weight=weight,
                           length=length,
                           width=width,
                           height=height,
                           on_pallet=on_pallet,
                           delivery_type=delivery_type,
                           track_trace=track_trace)

@app.route('/comparison')
def comparison():
    # Haal de ingevoerde gegevens op via de queryparameters
    weight = request.args.get('weight', '')
    length = request.args.get('length', '')
    width = request.args.get('width', '')
    height = request.args.get('height', '')
    on_pallet = request.args.get('on_pallet', '')
    delivery_type = request.args.get('delivery_type', '')
    track_trace = request.args.get('track_trace', '')

    # Puntenlogica voor vervoerders
    carriers = {
        "DHL": 0, "POSTNL": 0, "DPD": 0, "GLS": 0,
        "UPS": 0, "FEDEX": 0, "SCHENKER": 0, "KUEHNE+NAGEL": 0,
        "RHENUS": 0, "Bakker Groep": 0
    }

    #  Vraag 1: Gewicht 
    # Vergelijk het gewicht en wijs punten toe aan de vervoerders
    if weight == "0-5":
        for carrier in ["POSTNL", "FEDEX", "UPS"]:
            carriers[carrier] += 1
    elif weight == "5-10":
        for carrier in ["DHL", "DPD", "KUEHNE+NAGEL"]:
            carriers[carrier] += 1
    elif weight == "10+":
        for carrier in ["GLS", "RHENUS", "Bakker Groep"]:
            carriers[carrier] += 1

    #  Vraag 2: Dimensies 
    # Vergelijk de afmetingen en wijs punten toe aan de vervoerders
    for dimension in [length, width, height]:
        if dimension == "0-5":
            for carrier in ["DHL", "UPS", "FEDEX"]:
                carriers[carrier] += 1
        elif dimension == "5-10":
            for carrier in ["GLS", "SCHENKER", "KUEHNE+NAGEL"]:
                carriers[carrier] += 1
        elif dimension == "10+":
            for carrier in ["POSTNL", "DPD", "RHENUS", "Bakker Groep"]:
                carriers[carrier] += 1

    #  Vraag 3: Pallet 
    # Vergelijk of het op een pallet moet en wijs punten toe aan de vervoerders
    if on_pallet == "ja":
        for carrier in ["DPD", "GLS", "UPS", "RHENUS", "Bakker Groep"]:
            carriers[carrier] += 1
    elif on_pallet == "nee":
        for carrier in ["DHL", "POSTNL", "FEDEX", "SCHENKER", "KUEHNE+NAGEL"]:
            carriers[carrier] += 1

    #  Vraag 4: Bestemming 
    # Vergelijk het bestemmingstype en wijs punten toe aan de vervoerders
    if delivery_type == "nationaal":
        for carrier in ["POSTNL", "RHENUS", "Bakker Groep"]:
            carriers[carrier] += 1
    elif delivery_type == "internationaal_europa":
        for carrier in ["DPD", "GLS", "FEDEX", "SCHENKER"]:
            carriers[carrier] += 1
    elif delivery_type == "internationaal_buiten_europa":
        for carrier in ["DHL", "UPS", "KUEHNE+NAGEL"]:
            carriers[carrier] += 1

    #  Vraag 5: Track & Trace 
    # Vergelijk of een track & trace gewenst is en wijs punten toe aan de vervoerders
    if track_trace == "ja":
        for carrier in ["DHL", "POSTNL", "GLS", "RHENUS", "Bakker Groep"]:
            carriers[carrier] += 1
    elif track_trace == "nee":
        for carrier in ["DPD", "UPS", "FEDEX", "SCHENKER", "KUEHNE+NAGEL"]:
            carriers[carrier] += 1

    # Bepaal de hoogste score
    max_score = max(carriers.values())  # Zoekt de hoogste score
    best_carriers = [carrier for carrier, score in carriers.items() if score == max_score]  # Vind de vervoerders met de hoogste score

    # Laad de vergelijking-pagina met de beste vervoerders
    return render_template('comparison.html', best_carriers=best_carriers)

@app.route('/inloggen', methods=['GET', 'POST'])
def inloggen():
    # Verwerkt het inlogformulier
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Account.query.filter_by(username=username).first()  # Zoekt de gebruiker in de database
        
        # Vergelijk wachtwoord en user idee en als het goed is inloggen
        if user and user.password == password:
            login_user(User(user.id))
            return redirect(url_for('home'))
    # Laad het inlogformulier voor GET-verzoeken
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Verwerkt het aanmeldformulier
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Controleerd of de gebruikersnaam al bestaat
        if Account.query.filter_by(username=username).first():
            return "Gebruikersnaam bestaat al", 400  # Return error als gebruikersnaam al bestaat
        
        # Maakt een nieuwe gebruiker aan en voeg deze toe aan de database (users.db)
        new_user = Account(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # gaat naar de login-pagina
        return redirect(url_for('inloggen'))
    return render_template('signup.html')

@app.route('/overview')
def overview():
    # Overzicht van de vervoerders
    carriers = ["DHL", "POSTNL", "DPD", "GLS", "UPS", "FEDEX", "SCHENKER", "KUEHNE+NAGEL", "RHENUS", "Bakker Groep"]
    return render_template('overview.html', carriers=carriers)

@app.route('/about')
def about():
    # Toont de over-pagina
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # Dit verwerkt het formulier van de contactpagina
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        print(f"Bericht van {name} ({email}): {message}")  # Print het bericht naar de console

        # Bevestigd dat het bericht is ontvangen
        return render_template('contact.html', message=True)

    # Laad het contactformulier voor GET-verzoeken
    return render_template('contact.html')

# Start de Flask-app
if __name__ == '__main__':
    app.run(debug=True)

