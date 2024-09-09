from flask import Flask, render_template, request
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Konfiguracja połączenia z bazą danych
db_config = {
    'user': 'administrator',
    'password': 'haslo',
    'host': 'localhost',
    'database': 'crimedb',
    'raise_on_warnings': True
}

app = Flask(__name__)
app.secret_key = 'super_secret_key'

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None
    if request.method == 'POST':
        user_input = request.form['user_input']
        intent_tag = predict_class(user_input)
        response = get_response(intents, intent_tag)
    return render_template('chatbot.html', response=response)

@app.route('/', methods=['GET', 'POST'])
def zgloszenie():
    if request.method == 'POST':
        # Pobieranie danych z formularza
        location = request.form['location-input']
        numer_lokalu = request.form.get('numer_lokalu')  # Opcjonalne pole
        city = request.form['locality-input']
        wojewodztwo = request.form['administrative_area_level_1-input']
        postal_code = request.form['postal_code-input']
        data = request.form['data']
        godzina = request.form['godzina']
        opis = request.form['opis']
        liczba_sprawcow = request.form['liczba']

        # Pobranie aktualnej daty i godziny zgłoszenia
        data_zgloszenia = datetime.now().date()
        godzina_zgloszenia = datetime.now().time()

        # Utworzenie połączenia z bazą danych
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        try:
            # Wstawienie danych do tabeli reports
            insert_query = "INSERT INTO reports (title, user_id, report_time, status) " \
                           "VALUES (%s, %s, %s, 'przyjęte')"
            cursor.execute(insert_query, ('Zgłoszenie', None, godzina_zgloszenia))
            cnx.commit()

            # Pobranie ostatnio wstawionego identyfikatora zgłoszenia
            report_id = cursor.lastrowid

            # Wstawienie danych do tabeli event_features
            insert_query = "INSERT INTO event_features (report_id, event_description, address, event_time) " \
                           "VALUES (%s, %s, %s, %s)"
            address = f"{location}, {numer_lokalu}, {city}, {wojewodztwo}, {postal_code}"
            event_time = f"{data} {godzina}"
            cursor.execute(insert_query, (report_id, opis, address, event_time))
            cnx.commit()

            # Wstawienie danych do tabeli perpetrators (sprawcy)
            insert_query = "INSERT INTO perpetrators (event_feature_id, appearance) " \
                           "VALUES (%s, %s)"
            event_feature_id = cursor.lastrowid
            cursor.execute(insert_query, (event_feature_id, 'Opis sprawcy'))
            cnx.commit()

            return 'Zgłoszenie dodane do bazy danych.'

        except mysql.connector.Error as error:
            cnx.rollback()
            return 'Błąd podczas dodawania zgłoszenia do bazy danych: {}'.format(error)

        finally:
            cursor.close()
            cnx.close()

    return render_template('index.html')


@app.route('/rejestracja.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Pobranie danych z formularza
        imie = request.form['imie']
        nazwisko = request.form['nazwisko']
        email = request.form['email']
        login = request.form['login']
        haslo = request.form['hasło']
        rola = 'cywil'

        haslo = haslo.encode('utf-8')
        haslo = hashlib.sha256(haslo).hexdigest()
        
        # Sprawdzenie, czy login już istnieje w bazie danych
        if login_istnieje(login):
            session['error_message'] = 'Podany login już istnieje'
            return redirect(url_for('register'))
        
        # Dodanie danych do tabeli użytkownicy
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        insert_query = "INSERT INTO `Users` (`login`, `password`, `role`, `email`, `name`, `surname`) VALUES (%s, %s, %s, %s, %s, %s)"
        insert_values = (login, haslo, rola, email, imie, nazwisko)
        cursor.execute(insert_query, insert_values)
        cnx.commit()
        return redirect(url_for('logowanie'))
    

    # Renderowanie szablonu formularza rejestracji
    return render_template('rejestracja.html')




@app.route('/logowanie.html', methods=['GET', 'POST'])
def logowanie():
    if request.method == 'POST':
        login = request.form['login']
        haslo = request.form['hasło']

        haslo = haslo.encode('utf-8')
        haslo = hashlib.sha256(haslo).hexdigest()
        # Szyfrowanie hasła

        # Sprawdzenie danych logowania w bazie danych
        if sprawdz_dane_logowania(login, haslo):
        # Pobranie user_id z bazy danych
            user_id = pobierz_user_id(login)
            rola = pobierz_role_uzytkownika(login)
        # Dodanie user_id do sesji
            session['user_id'] = user_id
            session['zalogowany'] = True
            session['role'] = rola
            session['name'] = pobierz_imie_uzytkownika(login)  # Funkcja pobierz_imie_uzytkownika() powinna zwrócić imię użytkownika na podstawie loginu
            if rola == 'cywil':
                return redirect(url_for('zgloszenie'))
            else:
                return redirect(url_for('przegladanie'))
        else:
            session['komunikat'] = 'Nieprawidłowy login lub hasło'
            return redirect(url_for('logowanie'))
    komunikat = session.pop('komunikat', None)
    return render_template('logowanie.html', komunikat=komunikat)

if __name__ == '__main__':
    app.run()
