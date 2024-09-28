import mysql.connector
import json
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from datetime import datetime
import hashlib
from chatbot_rozmowa import predict_class, get_response, intents, append_to_report

# Konfiguracja połączenia z bazą danych
db_config = {
    'user': 'administrator',
    'password': 'haslo',
    'host': '127.0.0.1',
    'database': 'crimedb',
    'raise_on_warnings': True
}

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Połączenie z bazą danych
try:
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    print("Połączono z bazą danych.")

    # # Wczytanie pliku report.json
    # with open('report.json', 'r', encoding='utf-8') as file:
    #     report_data = json.load(file)

    # # Wyświetlenie danych z pliku JSON
    # print("Dane z pliku report.json:")
    # print(json.dumps(report_data, indent=4, ensure_ascii=False))

    # # Wstawienie danych do tabeli witnesses
    # witness_insert = ("INSERT INTO witnesses (info_contact) VALUES (%s)")
    # cursor.execute(witness_insert, (report_data['info_contact'],))
    # witness_id = cursor.lastrowid

    # # Wstawienie danych do tabeli perpetrators
    # perpetrator_insert = ("INSERT INTO perpetrators (appearance) VALUES (%s)")
    # cursor.execute(perpetrator_insert, (report_data['appearance'],))
    # perp_id = cursor.lastrowid

    # # Wstawienie danych do tabeli event_features
    # event_features_insert = (
    #     "INSERT INTO event_features (event_desc, address, event_time, witness_id, perp_id) "
    #     "VALUES (%s, %s, %s, %s, %s)"
    # )
    # cursor.execute(event_features_insert, (
    #     report_data['event_desc'],
    #     report_data['address'],
    #     report_data['event_time'],
    #     witness_id,
    #     perp_id
    # ))
    # event_feature_id = cursor.lastrowid

    # # Wstawienie danych do tabeli reports
    # report_insert = ("INSERT INTO reports (title, event_feature_id) VALUES (%s, %s)")
    # cursor.execute(report_insert, (
    #     report_data['title'],
    #     event_feature_id
    # ))

    # # Zatwierdzenie transakcji
    # cnx.commit()
    # print("Dane zostały pomyślnie wstawione do bazy danych.")

except mysql.connector.Error as err:
    print(f"Błąd: {err}")
    cnx.rollback()
finally:
        print("Połączenie z bazą danych zostało zamknięte.")

# Funkcja do wstawiania raportu do bazy danych
def insert_report_into_db():
    try:
        with open('report.json', 'r', encoding='utf-8') as file:
            report_data = json.load(file)

        # Połączenie z bazą danych
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Wstawienie danych do tabeli reports
        report_insert = "INSERT INTO reports (title) VALUES (%s)"
        cursor.execute(report_insert, (report_data['title'],))

        report_id = cursor.lastrowid

        # Wstawienie danych do tabeli event_features
        event_features_insert = (
            "INSERT INTO event_features (report_id, event_description, address, event_time) "
            "VALUES (%s, %s, %s, %s)"
        )
        cursor.execute(event_features_insert, (
            report_id,
            report_data['event_desc'],
            report_data['address'],
            report_data['event_time'],
        ))
        event_feature_id = cursor.lastrowid

        # Wstawienie danych do tabeli witnesses
        witness_insert = "INSERT INTO witnesses (event_feature_id, info_contact) VALUES (%s, %s)"
        cursor.execute(witness_insert, (event_feature_id, report_data['info_contact'],))

        # Wstawienie danych do tabeli perpetrators
        perpetrator_insert = "INSERT INTO perpetrators (event_feature_id, appearance) VALUES (%s, %s)"
        cursor.execute(perpetrator_insert, (event_feature_id, report_data['appearance'],))

        # Zatwierdzenie transakcji
        cnx.commit()
        print("Dane zostały pomyślnie wstawione do bazy danych.")
    except mysql.connector.Error as err:
        print(f"Błąd: {err}")
        cnx.rollback()
    finally:
        cursor.close()
        cnx.close()

@app.route('/')
def main():
    return redirect(url_for('przekierowanieZgloszenie'))

@app.route('/index.html')
def przekierowanieZgloszenie():
    komunikat = session.pop('komunikat', None)
    try:
        if session['role']=='funkcjonariusz':
            return render_template('przegladanie.html', zalogowany=session.get('zalogowany'), name=session.get('name'))
        if session['role'] == 'cywil':
            return render_template('index.html', zalogowany=session.get('zalogowany'), name=session.get('name'))
    except:
        return render_template('index.html', komunikat=komunikat)
    
# Endpoint to handle form submission and save data to report.json
@app.route('/submit', methods=['POST'])
def submit_form():
    # Pobieranie danych z formularza
    description = request.form.get('opis')
    title = description[:30] + '...' if description else ''
    event_desc = description

    address = f"{request.form.get('location-input', '')} {request.form.get('numer_lokalu', '')} {request.form.get('locality-input', '')} {request.form.get('administrative_area_level_1-input', '')} {request.form.get('postal_code-input', '')}"

    event_time = f"{request.form.get('data', '')} {request.form.get('godzina', '')}"

    # Pobranie liczby sprawców
    liczba_sprawcow = int(request.form.get('liczba', '0'))

    # Pobieranie opisu każdego sprawcy
    sprawcy_opisy = []
    for i in range(1, liczba_sprawcow + 1):
        sprawca_opis = request.form.get(f'sprawca{i}', '')
        if sprawca_opis:
            sprawcy_opisy.append(sprawca_opis)

    # Tworzenie opisu sprawców
    appearance = f"{liczba_sprawcow} - {', '.join(sprawcy_opisy)}"

    # Tworzenie obiektu JSON
    report_data = {
        "title": title,
        "event_desc": event_desc,
        "address": address.strip(),
        "event_time": event_time.strip(),
        "appearance": appearance,
        "info_contact": "anonimowy"
    }

    # Zapis do pliku report.json
    with open('report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)

    insert_report_into_db()

    # Ustawienie komunikatu
    session['komunikat'] = "Zgłoszenie zostało zapisane pomyślnie!"

    # Przekierowanie na stronę główną po zapisaniu danych
    return redirect(url_for('main'))

    
@app.route('/rejestracja.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Pobranie danych z formularza
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        login = request.form['login']
        password = request.form['password']
        role = 'cywil'

        password = password.encode('utf-8')
        password = hashlib.sha256(password).hexdigest()
        
        # Sprawdzenie, czy login już istnieje w bazie danych
        if login_istnieje(login):
            session['error_message'] = 'Podany login już istnieje'
            return redirect(url_for('register'))
        
        # Dodanie danych do tabeli użytkownicy
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        insert_query = "INSERT INTO `users` (`login`, `password`, `role`, `email`, `name`, `surname`) VALUES (%s, %s, %s, %s, %s, %s)"
        insert_values = (login, password, role, email, name, surname)
        cursor.execute(insert_query, insert_values)
        cnx.commit()
        return redirect(url_for('logowanie'))
    

    # Renderowanie szablonu formularza rejestracji
    return render_template('rejestracja.html')

def login_istnieje(login):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT COUNT(*) FROM `users` WHERE `login` = %s"
    cursor.execute(query, (login,))
    result = cursor.fetchone()[0]
    cnx.close()
    return result > 0

@app.route('/logowanie.html', methods=['GET', 'POST'])
def logowanie():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        password = password.encode('utf-8')
        password = hashlib.sha256(password).hexdigest()
        
        # Sprawdzenie danych logowania w bazie danych
        if sprawdz_dane_logowania(login, password):
            # Pobranie user_id z bazy danych
            user_id = pobierz_user_id(login)
            role = pobierz_role_uzytkownika(login)
            imie = pobierz_imie_uzytkownika(login)
            
            # Dodanie informacji do sesji
            session['user_id'] = user_id
            session['zalogowany'] = True
            session['role'] = role
            session['name'] = imie  # Używamy imienia użytkownika
            
            if role == 'cywil':
                return redirect(url_for('przekierowanieZgloszenie'))
            else:
                return redirect(url_for('przegladanie'))
        else:
            session['komunikat'] = 'Nieprawidłowy login lub hasło'
            return redirect(url_for('logowanie'))

    komunikat = session.pop('komunikat', None)
    return render_template('logowanie.html', komunikat=komunikat)

# Funkcja pomocnicza do pobierania user_id z bazy danych na podstawie loginu
def pobierz_user_id(login):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT user_id FROM `users` WHERE `login` = %s"
    cursor.execute(query, (login,))
    result = cursor.fetchone()
    cnx.close()
    if result:
        return result[0]
    else:
        return None

def pobierz_imie_uzytkownika(login):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT name FROM `users` WHERE `login` = %s"
    cursor.execute(query, (login,))
    result = cursor.fetchone()
    cnx.close()
    if result:
        return result[0]
    else:
        return ""

# Funkcja pomocnicza do pobierania roli użytkownika na podstawie loginu
def pobierz_role_uzytkownika(login):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT role FROM `users` WHERE `login` = %s"
    cursor.execute(query, (login,))
    result = cursor.fetchone()
    cnx.close()
    if result:
        return result[0]
    else:
        return None

# Funkcja sprawdzająca dane logowania w bazie danych
def sprawdz_dane_logowania(login, password):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    query = "SELECT COUNT(*) FROM `users` WHERE `login` = %s AND `password` = %s"
    values = (login, password)

    cursor.execute(query, values)
    result = cursor.fetchone()

    cnx.commit()

    return result and result[0] > 0

@app.route('/wyloguj')
def wyloguj():
    session.clear()  # Czyści wszystkie dane w sesji
    return redirect(url_for('main'))  # Przekierowanie do strony logowania

@app.route('/moje_zgloszenia', methods=['GET'])
def moje_zgloszenia():
    if 'zalogowany' not in session or not session['zalogowany']:
        return redirect(url_for('logowanie'))

    user_id = session.get('user_id')

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT zg.report_id, zg.event_time, zg.event_description, zg.address, z.status " \
        "FROM event_features zg " \
        "INNER JOIN reports z ON zg.report_id = z.report_id " \
        "WHERE z.user_id = %s " \
        "ORDER BY zg.event_time DESC"
    cursor.execute(query, (user_id,))
    zgloszenia = cursor.fetchall()

    return render_template('moje_zgloszenia.html', zgloszenia=zgloszenia, zalogowany=session.get('zalogowany'), imie=session.get('imie'))


@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None

    # Debugowanie sesji - w przypadku korzystania z sesji czasami pojawiają się błędy z ciasteczkami - wyczyszczenie ciasteczek pomaga
    print(f"Session data (before request): {session}")

    if 'first_message' not in session:
        session['first_message'] = True

    first_message = session['first_message']
    print(f"first_message (before request): {first_message}")

    if request.method == 'POST':
        user_input = request.form['user_input']
        intent_tag = predict_class(user_input)
        response = get_response(intents, intent_tag)

        # Pobieramy poprzednią wiadomość, jeśli istnieje
        previous_message = session.get('previous_message', None)

        # Dodajemy odpowiedź do raportu z użyciem previous_message jako response
        if session['first_message']:
            append_to_report("title", user_input, previous_message)
            session['first_message'] = False
        else:
            append_to_report(intent_tag, user_input, previous_message)
        
        # Nadpisujemy poprzednią wiadomość nową odpowiedzią
        session['previous_message'] = response

        if intent_tag == "witnesses":
            insert_report_into_db()
            session.pop('first_message', None)
            return "Dziękujemy za zgłoszenie. Dane zostały zapisane w bazie."

    print(f"Session data (after request): {session}")
    return render_template('chatbot.html', response=response)


if __name__ == '__main__':
    app.run()