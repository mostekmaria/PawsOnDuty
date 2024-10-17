import mysql.connector
import json
import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from datetime import datetime
import hashlib
from chatbot_rozmowa import predict_class, get_response, intents, append_to_report
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# Konfiguracja połączenia z bazą danych
db_config = {
    'user': 'administrator',
    'password': 'haslo',
    'host': '127.0.0.1',
    'database': 'crimedb', #tu sobie ja musze zmieniać na 2
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

        # Pobranie aktualnej daty i czasu z systemu
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Wstawienie danych do tabeli reports (dodanie kolumny status)
        report_insert = """
            INSERT INTO reports (title, report_time, user_id, status) 
            VALUES (%s, %s, %s, %s)
        """
        
        # Pobieramy user_id z sesji; jeśli użytkownik nie jest zalogowany, ustawiamy None
        user_id = session.get('user_id', None)
        status = report_data.get('status', 'Zgłoszono')  # Domyślnie "Zgłoszono"
        
        cursor.execute(report_insert, (
            report_data['title'], 
            report_time, 
            user_id, 
            status
        ))

        report_id = cursor.lastrowid

        # Wstawienie danych do tabeli event_features
        event_features_insert = """
            INSERT INTO event_features (report_id, event_description, address, event_time) 
            VALUES (%s, %s, %s, %s)
        """
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

# Funkcja do wstawiania podejrzanych do tabeli suspects w bazie danych
def insert_suspect_into_db(report_id, name, surname, address, birthdate, photo_blob):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Zapytanie SQL
        suspect_insert = """
            INSERT INTO suspects (report_id, name, surname, address, birthdate, photo) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Wstawienie danych do tabeli suspects
        cursor.execute(suspect_insert, (
            report_id,  # Upewnij się, że to jest report_id
            name,
            surname,
            address,
            birthdate,
            photo_blob  # Upewnij się, że photo_blob jest przekazywane
        ))

        # Zatwierdzenie transakcji
        cnx.commit()
        print("Dane podejrzanego zostały pomyślnie wstawione do bazy danych.")
    except mysql.connector.Error as err:
        print(f"Błąd podczas wstawiania danych podejrzanego: {err}")
        cnx.rollback()
    finally:
        cursor.close()
        cnx.close()
        with open('report.json', 'w', encoding='utf-8') as f:
            f.write('')  # Zapisywanie pustego pliku


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    """Sprawdzenie, czy plik ma dozwolone rozszerzenie."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        "info_contact": "anonimowy",
        "status": "Zgłoszono"
    }

    # Zapis do pliku report.json
    with open('report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)

    insert_report_into_db()

    report_data=None

    # Ustawienie komunikatu
    session['komunikat'] = "Zgłoszenie zostało zapisane pomyślnie!"

    # Pobieramy adres e-mail od użytkownika z formularza
    email = request.form['email']
    
    # Tworzymy wiadomość e-mail
    message = Mail(
        from_email='pawsondutywebapp@gmail.com',  # Twój e-mail nadawcy
        to_emails=email,  # Adres e-mail odbiorcy (użytkownika)
        subject='Potwierdzenie zgłoszenia',  # Temat wiadomości
        html_content='<p>Zgłoszenie zostało przesłane.</p><br><p>Dziękujemy za przesłanie zgłoszenia i dbanie o bezpieczeństwo naszego społeczeństwa! Zachęcamy do założenia konta w naszej aplikacji i śledzenia postępu w śledztwie!</p>'  # Treść wiadomości w HTML
    )

    try:
        # Inicjalizacja klienta SendGrid za pomocą klucza API (używamy zmiennej środowiskowej)
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

        # Wysłanie wiadomości
        response = sg.send(message)
        flash('Twój e-mail został pomyślnie wysłany! Sprawdź swoją skrzynkę pocztową.', 'success')  # Sukces
        return redirect(url_for('main'))  # Przekierowanie na stronę wynikową

    except Exception as e:
        print(e)
        flash('Wystąpił błąd podczas wysyłania e-maila. Prosimy spróbować ponownie.', 'danger')  # Błąd
        return redirect(url_for('main'))  # Przekierowanie na stronę wynikową





@app.route('/przegladanie.html')
def przegladanie():
    return render_template('przegladanie.html', zalogowany=session.get('zalogowany'), imie=session.get('name'))



    
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
    query = "SELECT r.title, ef.event_description, ef.address, ef.event_time, p.appearance, w.info_contact, r.status FROM reports r JOIN event_features ef ON r.report_id = ef.report_id JOIN perpetrators p ON ef.event_feature_id = p.event_feature_id JOIN witnesses w ON ef.event_feature_id = w.event_feature_id " \
        "WHERE r.user_id = %s " \
        "ORDER BY ef.event_time DESC"
    cursor.execute(query, (user_id,))
    zgloszenia = cursor.fetchall()

    return render_template('moje_zgloszenia.html', zgloszenia=zgloszenia, zalogowany=session.get('zalogowany'), imie=session.get('name'))

@app.route('/zgloszenia.html', methods=['GET'])
def zgloszenia():
    selected_date = request.args.get('data')  # Pobranie parametru 'data' z zapytania GET
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        if selected_date:
            # Zakładam, że format daty w report_time to 'YYYY-MM-DD HH:MM:SS'
            # Używamy funkcji DATE() aby wyekstrahować część daty
            query = """
                SELECT 
                    r.report_id, 
                    r.title, 
                    ef.event_description, 
                    ef.address, 
                    ef.event_time, 
                    p.appearance, 
                    w.info_contact, 
                    r.status 
                FROM reports r 
                JOIN event_features ef ON r.report_id = ef.report_id 
                JOIN perpetrators p ON ef.event_feature_id = p.event_feature_id 
                JOIN witnesses w ON ef.event_feature_id = w.event_feature_id
                WHERE DATE(r.report_time) = %s
            """
            cursor.execute(query, (selected_date,))
        else:
            # Jeśli nie podano daty, pobieramy wszystkie zgłoszenia
            query = """
                SELECT 
                    r.report_id, 
                    r.title, 
                    ef.event_description, 
                    ef.address, 
                    ef.event_time, 
                    p.appearance, 
                    w.info_contact, 
                    r.status 
                FROM reports r 
                JOIN event_features ef ON r.report_id = ef.report_id 
                JOIN perpetrators p ON ef.event_feature_id = p.event_feature_id 
                JOIN witnesses w ON ef.event_feature_id = w.event_feature_id
            """
            cursor.execute(query)
        
        zgloszenia = cursor.fetchall()
        
        # Opcjonalnie: Przekazanie wybranej daty do szablonu, aby ją wyświetlić
        return render_template(
            'zgloszenia.html', 
            zgloszenia=zgloszenia, 
            komunikat=None, 
            zalogowany=session.get('zalogowany'), 
            name=session.get('name'),
            selected_date=selected_date
        )
        
    except mysql.connector.Error as err:
        print(f"Błąd podczas pobierania zgłoszeń: {err}")
        zgloszenia = []
        return render_template(
            'zgloszenia.html', 
            zgloszenia=zgloszenia, 
            komunikat="Wystąpił błąd podczas pobierania zgłoszeń.", 
            zalogowany=session.get('zalogowany'), 
            name=session.get('name')
        )
    finally:
        cursor.close()
        cnx.close()


@app.route('/suspects.html', methods=['GET', 'POST'])
def handle_suspects():
    if request.method == 'POST':
        # Pobieranie danych z formularza
        name = request.form.get('name') or None
        surname = request.form.get('surname') or None
        address = request.form.get('address') or None
        birthdate = request.form.get('birthdate') or None
        report_id = request.form.get('report_id') or None

        # Pobieranie pliku zdjęcia
        if 'photo' not in request.files:
            return "Brak pliku zdjęcia", 400
        photo = request.files['photo']

        # Sprawdzanie, czy plik jest poprawny
        if photo and allowed_file(photo.filename):
            # Odczyt pliku jako danych binarnych (BLOB)
            photo_blob = photo.read()
        else:
            return "Nieprawidłowy plik. Dozwolone formaty to JPG i PNG", 400

        # Walidacja danych
        if not name or not surname or not report_id:
            return "Brak wymaganych danych", 400

        # Wstawienie podejrzanego do bazy danych, razem z plikiem BLOB
        insert_suspect_into_db(report_id, name, surname, address, birthdate, photo_blob)

        # Przekierowanie lub renderowanie odpowiedzi
        return redirect(url_for('przekierowanieZgloszenie'))

    # Jeśli metoda GET, wyświetlamy formularz suspects.html
    report_id = request.args.get('report_id')  # Pobieramy report_id z URL

    return render_template('suspects.html', report_id=report_id)


@app.route('/update_status', methods=['POST'])
def update_status():
    zgloszenie_id = request.json['zgloszenieId']
    new_status = request.json['newStatus']
    
    print(f"Zgłoszenie ID: {zgloszenie_id}, Nowy status: {new_status}")  # Debugowanie
    
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    
    try:
        update_query = f"UPDATE reports SET status = %s WHERE report_id = %s"
        cursor.execute(update_query, (new_status, zgloszenie_id))
        cnx.commit()
        return 'OK', 200
    except Exception as e:
        print('Błąd podczas aktualizacji statusu:', e)
        cnx.rollback()
        return 'Błąd podczas aktualizacji statusu', 500
    finally:
        cursor.close()
        cnx.close()


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
            return redirect(url_for('main'))

    print(f"Session data (after request): {session}")
    return render_template('chatbot.html', response=response, zalogowany=session.get('zalogowany'), 
            name=session.get('name'),)










if __name__ == '__main__':
    app.run()