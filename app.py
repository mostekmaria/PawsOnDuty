import mysql.connector
import json
import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from datetime import datetime
import hashlib
from chatbot_rozmowa import predict_class, get_response, intents, append_to_report
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendGridMail
import logging
import socket
import base64


# Konfiguracja połączenia z bazą danych
db_config = {
    'user': 'administrator',
    'password': os.environ.get('DB_PASS'),
    'host': '127.0.0.1',
    'database': 'crimedb', #tu sobie ja musze zmieniać na 2
    'raise_on_warnings': True
}

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Konfiguracja loggera
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Połączenie z bazą danych
try:
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    print("Połączono z bazą danych.")

except mysql.connector.Error as err:
    print(f"Błąd: {err}")
    cnx.rollback()
finally:
        print("Połączenie z bazą danych zostało zamknięte.")


def insert_report_into_db():
    try:
        # Połączenie z bazą danych
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Pobranie danych z formularza JSON oraz daty i czasu
        report_data = json.load(open('report.json', 'r', encoding='utf-8'))
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Wstawienie danych do tabeli reports
        report_insert = """
            INSERT INTO reports (title, report_time, user_id, status) 
            VALUES (%s, %s, %s, %s)
        """
        user_id = session.get('user_id', None)
        status = report_data.get('status', 'Zgłoszono')  # Domyślnie "Zgłoszono"
        
        cursor.execute(report_insert, (
            report_data['title'], 
            report_time, 
            user_id, 
            status
        ))
        report_id = cursor.lastrowid

        # Wstawienie danych do tabeli event_features (obsługa zdjęć)
        event_features_insert = """
            INSERT INTO event_features (report_id, event_description, address, event_time, photos) 
            VALUES (%s, %s, %s, %s, %s)
        """

        # Obsługa zdjęć (photos)
        uploaded_files = request.files.getlist("photo")
        photos_data = []

        for file in uploaded_files:
            if file and file.filename != '':
                file_content = file.read()  # Read file as binary BLOB
                photos_data.append(file_content)

        # If no photos were uploaded
        if not photos_data:
            photos_blob = None  # Set to None if no files were uploaded
        else:
            photos_blob = b''.join(photos_data)  # Combine files into a single binary stream

        cursor.execute(event_features_insert, (
            report_id,
            report_data['event_desc'],
            report_data['address'],
            report_data['event_time'],
            photos_blob
        ))
        event_feature_id = cursor.lastrowid

        # Wstawienie danych do innych tabel (np. witnesses, perpetrators)
        witness_insert = "INSERT INTO witnesses (event_feature_id, info_contact) VALUES (%s, %s)"
        cursor.execute(witness_insert, (event_feature_id, report_data['info_contact'],))

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
def insert_suspect_into_db(event_feature_id, name, surname, address, birthdate, photo_blob):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Zapytanie SQL
        suspect_insert = """
            INSERT INTO suspects (event_feature_id, name, surname, address, birthdate, photo) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Wstawienie danych do tabeli suspects
        cursor.execute(suspect_insert, (
            event_feature_id,
            name,
            surname,
            address,
            birthdate,
            photo_blob
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


def send_confirmation():
    # Pobieramy adres e-mail od użytkownika z formularza
    if session.get('zalogowany'):
        # Pobierz id użytkownika z sesji
        user_id = session.get('user_id')
        
        # Pobierz e-mail użytkownika z bazy danych na podstawie id
        email = get_user_email_by_id(user_id)
    else:
        # Użytkownik niezalogowany, pobieramy e-mail z formularza
        email = request.form.get('email', '').strip() or None
    
    # Jeśli email jest pusty, pomiń wysyłanie wiadomości i zakończ funkcję
    if not email:
        logger.info("Adres e-mail nie podany. Zgłoszenie zapisane bez wysyłania potwierdzenia.")
        flash("Zgłoszenie zostało dodane")
        return
    
    # Tworzymy wiadomość e-mail
    message = SendGridMail(
        from_email='pawsondutywebapp@gmail.com',  # Twój e-mail nadawcy
        to_emails=email,  # Adres e-mail odbiorcy (użytkownika)
        subject='Potwierdzenie zgłoszenia',  # Temat wiadomości
        html_content='<p>Zgłoszenie zostało przesłane.</p><br><p>Dziękujemy za przesłanie zgłoszenia i dbanie o bezpieczeństwo naszego społeczeństwa! Zachęcamy do założenia konta w naszej aplikacji i śledzenia postępu w śledztwie!</p>'  # Treść wiadomości w HTML
    )

    # Sprawdzenie dostępności portów
    try:
        logger.debug("Sprawdzanie dostępności portu 587.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect(("smtp.sendgrid.net", 587))
            logger.debug("Port 587 jest dostępny.")
    except socket.error as e:
        logger.error(f"Błąd połączenia z portem 587: {e}")
        flash('Port 587 nie jest dostępny. Proszę sprawdzić ustawienia sieciowe.', 'danger')
        return redirect(url_for('main'))

    try:
        # Inicjalizacja klienta SendGrid za pomocą klucza API
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

        # Wysłanie wiadomości
        response = sg.send(message)
        logger.info(f"Wysłano wiadomość e-mail: {response.status_code} na adres {email}")
        
        flash('Twój e-mail został pomyślnie wysłany! Sprawdź swoją skrzynkę pocztową.', 'success')  # Sukces

    except Exception as e:
        logger.error(f"Wystąpił błąd podczas wysyłania e-maila: {e}")
        flash('Wystąpił błąd podczas wysyłania e-maila. Prosimy spróbować ponownie.', 'danger')  # Błąd

def get_user_email_by_id(user_id):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        # Wykonanie zapytania SQL do pobrania e-maila na podstawie user_id
        query = "SELECT email FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        # Pobranie wyniku zapytania
        result = cursor.fetchone()

        # Zamknięcie kursora i połączenia
        cnx.close()

        if result:
            return result[0]  # Zwraca e-mail
        else:
            return None

    except mysql.connector.Error as err:
        print(f"Błąd: {err}")
        return None
    
    
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
    logger.debug("Rozpoczynam obsługę zgłoszenia formularza.")

    # Pobieranie danych z formularza
    description = request.form.get('opis', '')
    title = description[:30] + '...' if description else ''
    event_desc = description

    address = f"{request.form.get('location-input', '')} {request.form.get('numer_lokalu', '')} {request.form.get('locality-input', '')} {request.form.get('administrative_area_level_1-input', '')} {request.form.get('postal_code-input', '')}"
    event_time = f"{request.form.get('data', '')} {request.form.get('godzina', '')}"

    # Pobranie liczby sprawców
    liczba_sprawcow = int(request.form.get('liczba', '0'))
    logger.debug(f"Liczba sprawców: {liczba_sprawcow}")

    # Pobieranie opisu każdego sprawcy
    sprawcy_opisy = [request.form.get(f'sprawca{i}', '') for i in range(1, liczba_sprawcow + 1)]
    sprawcy_opisy = [sprawca for sprawca in sprawcy_opisy if sprawca]

    # Tworzenie opisu sprawców
    appearance = f"{len(sprawcy_opisy)} - {', '.join(sprawcy_opisy)}"

        # Pobieranie liczby świadków
    liczba_swiadkow = int(request.form.get('liczba-swiadkow', '0'))
    logger.debug(f"Liczba świadków: {liczba_swiadkow}")
    # Pobieranie danych kontaktowych świadków
    swiadkowie_info = [request.form.get(f'świadek{i}', '') for i in range(1, liczba_swiadkow + 1)]
    swiadkowie_info = [info for info in swiadkowie_info if info]  # Filtrujemy puste dane
    # Sprawdzamy, czy dane świadków zostały poprawnie pobrane
    logger.debug(f"Dane świadków: {swiadkowie_info}")
    # Przekonwertowanie listy świadków na jeden ciąg tekstowy
    info_contact = ', '.join(swiadkowie_info) if swiadkowie_info else "Brak danych kontaktowych"

    # Tworzenie obiektu JSON
    report_data = {
        "title": title,
        "event_desc": event_desc,
        "address": address.strip(),
        "event_time": event_time.strip(),
        "appearance": appearance,
        "info_contact": info_contact,  # Zmieniamy listę na string
        "info_contact": "anonimowy",
        "status": "Zgłoszono"
    }

    # Zapis do pliku report.json
    try:
        with open('report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)
        logger.debug("Dane zgłoszenia zapisane do report.json.")
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania do pliku report.json: {e}")

    insert_report_into_db()  # Funkcja do wstawiania do bazy danych

    session['komunikat'] = "Zgłoszenie zostało zapisane pomyślnie!"  # Ustawienie komunikatu

    send_confirmation()
    return redirect(url_for('main'))


@app.route('/przegladanie.html')
def przegladanie():
    return render_template('przegladanie.html', zalogowany=session.get('zalogowany'), imie=session.get('name'))


@app.route('/rejestracja.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Pobranie danych z formularza
        name = request.form['suspect_name']
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
    query = "SELECT r.report_id, r.title, ef.event_description, ef.address, ef.event_time, p.appearance,\
        w.info_contact,r.status FROM reports r JOIN event_features ef ON r.report_id = ef.report_id JOIN\
        perpetrators p ON ef.event_feature_id = p.event_feature_id JOIN witnesses w ON ef.event_feature_id = w.event_feature_id " \
        "WHERE r.user_id = %s " \
        "ORDER BY ef.event_time DESC"
    cursor.execute(query, (user_id,))
    zgloszenia = cursor.fetchall()

    return render_template('moje_zgloszenia.html', zgloszenia=zgloszenia, zalogowany=session.get('zalogowany'), imie=session.get('name'))

@app.route('/zgloszenia.html', methods=['GET'])
def zgloszenia():
    selected_date = request.args.get('data')
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        if selected_date:
            query = """
                SELECT r.report_id, r.title, ef.event_description, ef.address, ef.event_time, p.appearance, w.info_contact, r.status 
                FROM reports r 
                JOIN event_features ef ON r.report_id = ef.report_id 
                JOIN perpetrators p ON ef.event_feature_id = p.event_feature_id 
                JOIN witnesses w ON ef.event_feature_id = w.event_feature_id
                WHERE DATE(r.report_time) = %s
            """
            cursor.execute(query, (selected_date,))
        else:
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

        return render_template(
            'zgloszenia.html', 
            zgloszenia=zgloszenia,
            selected_date=selected_date,
            name=session.get('name')
        )

    except mysql.connector.Error as err:
        print(f"Błąd podczas pobierania zgłoszeń: {err}")
        return render_template(
            'zgloszenia.html', 
            zgloszenia=[],
            komunikat="Wystąpił błąd podczas pobierania zgłoszeń.",
            name=session.get('name')
        )
    finally:
        cursor.close()
        cnx.close()

@app.route('/suspects.html', methods=['GET', 'POST'])
def handle_suspects():
    report_id = request.args.get('report_id')  # Ustawienie report_id z zapytania GET
    if request.method == 'POST':
        # Pobieranie danych z formularza
        name = request.form.get('suspect_name')
        surname = request.form.get('surname')
        address = request.form.get('address')
        birthdate = request.form.get('birthdate')
        report_id = request.form.get('report_id')  # Upewnij się, że jest tutaj

        # Walidacja danych
        if not name or not surname or not report_id:
            return "Brak wymaganych danych", 400

        # Pobieranie pliku zdjęcia
        if 'photo' not in request.files:
            return "Brak pliku zdjęcia", 400
        photo = request.files['photo']

        # Sprawdzanie, czy plik jest poprawny
        if photo and allowed_file(photo.filename):
            photo_blob = photo.read()
        else:
            photo_blob = None

            #return "Nieprawidłowy plik. Dozwolone formaty to JPG i PNG", 400


        # Pobranie event_feature_id na podstawie report_id
        event_feature_id = get_event_feature_id(report_id)
        if event_feature_id is None:
            return "Nie znaleziono event_feature_id dla podanego report_id", 400

        # Wstawienie podejrzanego do bazy danych, razem z plikiem BLOB
        try:
            insert_suspect_into_db(event_feature_id, name, surname, address, birthdate, photo_blob)
            print("Dane zostały pomyślnie wstawione do bazy danych.")  # Debugging
        except Exception as e:
            print(f"Wystąpił błąd: {e}")  # Logowanie błędu

        # Przekierowanie lub renderowanie odpowiedzi
        return redirect(url_for('report', report_id=report_id))

    return render_template('suspects.html', report_id=report_id)



def get_event_feature_id(report_id):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        # Zapytanie SQL
        query = "SELECT event_feature_id FROM event_features WHERE report_id = %s"
        cursor.execute(query, (report_id,))
        
        result = cursor.fetchone()  # Pobierz pierwszy wiersz wyniku
        if result:
            return result[0]  # Zwróć event_feature_id
        else:
            return None
    except mysql.connector.Error as err:
        print(f"Błąd podczas pobierania event_feature_id: {err}")
        return None
    finally:
        cursor.close()
        cnx.close()



@app.route('/update_status', methods=['POST'])
def update_status():
    zgloszenie_id = request.json['zgloszenieId']
    new_status = request.json['newStatus']

    print(f"Zgłoszenie ID: {zgloszenie_id}, Nowy status: {new_status}")  # Debugging

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    try:
        # Verify the existence of the report
        cursor.execute("SELECT * FROM reports WHERE report_id = %s", (zgloszenie_id,))
        if cursor.fetchone() is None:
            print(f"Report with ID {zgloszenie_id} not found.")
            return 'Nie znaleziono zgłoszenia', 404

        # Update the status
        update_query = "UPDATE reports SET status = %s WHERE report_id = %s"
        cursor.execute(update_query, (new_status, zgloszenie_id))
        
        # Check how many rows were affected (logging for debugging)
        print(f"Rows affected: {cursor.rowcount}")

        cnx.commit()
        return 'OK', 200
    except Exception as e:
        print('Error updating status:', str(e))
        cnx.rollback()
        return 'Błąd podczas aktualizacji statusu', 500
    finally:
        cursor.close()
        cnx.close()


@app.route('/report/<int:report_id>', methods=['GET'])
def report(report_id):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Pobranie danych zgłoszenia z bazy
        query_report = """
            SELECT 
                r.report_id,
                r.title, 
                r.report_time, 
                r.status
            FROM reports r 
            WHERE r.report_id = %s
        """
        cursor.execute(query_report, (report_id,))
        report_data = cursor.fetchone()

        if report_data is None:
            return render_template(
                'report.html',
                komunikat="Nie znaleziono zgłoszenia o podanym ID.",
                name=session.get('name'),
                role=session.get('role')
            )

        # Zmienna report_id, która będzie używana w późniejszych zapytaniach
        report_id = report_data[0]

        # Pobranie event_feature_id dla danego report_id
        query_event_features = """
            SELECT 
                ef.event_feature_id, 
                ef.event_description, 
                ef.address, 
                ef.event_time, 
                ef.photos
            FROM event_features ef
            WHERE ef.report_id = %s
        """
        cursor.execute(query_event_features, (report_id,))
        event_features = cursor.fetchall()

        # Przygotowanie listy na dane event_features
        event_feature_list = []

        for event_feature in event_features:
            event_feature_id, event_description, address, event_time, photos = event_feature
            photo_base64 = base64.b64encode(photos).decode('utf-8') if photos else None

            query_suspects = """
                SELECT suspect_id, name, surname, address, birthdate, photo
                FROM suspects
                WHERE event_feature_id = %s
            """
            cursor.execute(query_suspects, (event_feature_id,))
            suspects = cursor.fetchall()

            suspect_list = []
            for suspect in suspects:
                suspect_id, name, surname, address, birthdate, photo = suspect
                photo_base64_sus = base64.b64encode(photo).decode('utf-8') if photo else None
                suspect_list.append({
                    "suspect_id": suspect_id,
                    "name": name,
                    "surname": surname,
                    "address": address,
                    "birthdate": birthdate,
                    "photo": photo_base64_sus
                })


                        # Pobranie świadków
            query_witnesses = """
                SELECT witness_id, info_contact
                FROM witnesses
                WHERE event_feature_id = %s
            """
            cursor.execute(query_witnesses, (event_feature_id,))
            witnesses = cursor.fetchall()
            witness_list = [
                {"witness_id": witness_id, "info_contact": info_contact}
                for witness_id, info_contact in witnesses
            ]
            # Pobranie sprawców
            query_perpetrators = """
                SELECT perpetrator_id, appearance
                FROM perpetrators
                WHERE event_feature_id = %s
            """
            cursor.execute(query_perpetrators, (event_feature_id,))
            perpetrators = cursor.fetchall()
            perpetrator_list = [
                {"perpetrator_id": perpetrator_id, "appearance": appearance}
                for perpetrator_id, appearance in perpetrators
            ]
            event_feature_list.append({
                "event_feature_id": event_feature_id,
                "event_description": event_description,
                "address": address,
                "event_time": event_time,
                "photos": photo_base64,
                "suspects": suspect_list,
                "witnesses": witness_list,
                "perpetrators": perpetrator_list
            })

        return render_template(
            'report.html',
            report_data=report_data,
            event_features=event_feature_list,
            name=session.get('name'),
            role=session.get('role')
        )

    except mysql.connector.Error as err:
        print(f"Błąd bazy danych: {err}")
        return render_template(
            'report.html',
            komunikat="Wystąpił błąd podczas pobierania danych zgłoszenia.",
            name=session.get('name'),
            role=session.get('role')
        )

    finally:
        cursor.close()
        cnx.close()



@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None
    print(f"Session data (before request): {session}")
    
    if 'conversation' not in session:
        session['conversation'] = []
    else:
        # Kopiujemy rozmowę, aby zapobiec nadpisaniu
        conversation_copy = list(session['conversation'])

    if 'first_message' not in session:
        session['first_message'] = True

    first_message = session['first_message']
    print(f"first_message (before request): {first_message}")

    if request.method == 'POST':
        print(f"Received form data: {request.form}")
        print(f"Received files: {request.files}")
        
        email = request.form.get('email', '').strip() or None

        if 'photo' in request.files:
            # Obsługa przesyłania zdjęć
            uploaded_files = request.files.getlist("photo")
            print(f"Uploaded files: {[file.filename for file in uploaded_files]}")
            if email:
                session['user_email'] = email  # Przechowujemy e-mail w sesji do późniejszego użycia

            # Wstawiamy dane do bazy danych
            insert_report_into_db()  # Wstawiamy dane do bazy danych

            session.pop('first_message', None)

            send_confirmation()
            return redirect(url_for('main'))

        user_input = request.form.get('user_input')
        if not user_input:
            print("User input is missing.")
            return "User input is required.", 400  # Wczesne zakończenie z błędem

        # Przewidzenie intencji i uzyskanie odpowiedzi od chatbota
        intent_tag = predict_class(user_input)
        response = get_response(intents, intent_tag)

        # Dodajemy wiadomość użytkownika do kopii konwersacji
        conversation_copy.append({'sender': 'user', 'message': user_input})

        # Pobierz ostatnią wiadomość chatbota, jeśli istnieje
        last_bot_message = next(
            (msg['message'] for msg in reversed(conversation_copy) if msg['sender'] == 'bot'), None
        )

        # Generujemy odpowiedź i dodajemy ją do kopii konwersacji
        conversation_copy.append({'sender': 'bot', 'message': response})

        # Przypisujemy uaktualnioną kopię do sesji
        session['conversation'] = conversation_copy

        # Zapisywanie do raportu z użyciem poprzedniej wiadomości bot
        if session['first_message']:
            append_to_report("title", user_input, last_bot_message)
            session['first_message'] = False
        else:
            append_to_report(intent_tag, user_input, last_bot_message)

        # Jeżeli chatbot pyta o zdjęcia, przechodzimy do następnego kroku
        if intent_tag == "witnesses":
            return render_template('chatbot.html', conversation=session['conversation'], witness_step=True)

    print(f"Session data (after request): {session}")
    print(f"Full conversation in session: {session['conversation']}")
    return render_template('chatbot.html', conversation=session['conversation'], zalogowany=session.get('zalogowany'), name=session.get('name'))


@app.route('/chatbot_clear')
def chatbot_clear():
    # Czyszczenie danych tylko dla konwersacji chatbota
    if 'conversation' in session:
        session.pop('conversation')  # Usuwa historię konwersacji
    if 'first_message' in session:
        session.pop('first_message')  # Resetuje flagę pierwszej wiadomości
    if 'previous_message' in session:
        session.pop('previous_message')  # Usuwa poprzednią wiadomość (jeśli istnieje)
    
    # Opcjonalne: Zresetowanie struktury w pliku report.json, jeśli jest częścią konwersacji
    initial_data = {
        "title": "",
        "event_desc": "",
        "address": "",
        "event_time": "",
        "appearance": "",
        "info_contact": "",
        "status": "Zgłoszono"
    }
    
    with open('report.json', 'w', encoding='utf-8') as report_file:
        json.dump(initial_data, report_file, ensure_ascii=False, indent=4)
    
    # Przekierowanie do chatbota, aby załadować początkowy widok
    return redirect(url_for('chatbot'))


if __name__ == '__main__':
    app.run()