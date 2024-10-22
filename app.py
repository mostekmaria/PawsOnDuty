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

        # Wstawienie danych do tabeli event_features (bez zdjęć na razie)
        event_features_insert = """
            INSERT INTO event_features (report_id, event_description, address, event_time, photos) 
            VALUES (%s, %s, %s, %s, %s)
        """

        # Obsługa zdjęć (photos)
        uploaded_files = request.files.getlist("photos")
        photos_data = []

        for file in uploaded_files:
            if file and file.filename != '':
                file_content = file.read()  # Odczytanie pliku jako binarny BLOB
                photos_data.append(file_content)

        # Konwertowanie listy binariów do jednego BLOB (opcjonalnie można zapisać każde zdjęcie osobno)
        if photos_data:
            photos_blob = b''.join(photos_data)  # Łączenie plików w jeden strumień binarny
        else:
            photos_blob = None

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
    try:
        with open('report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)
        logger.debug("Dane zgłoszenia zapisane do report.json.")
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania do pliku report.json: {e}")

    insert_report_into_db()  # Funkcja do wstawiania do bazy danych

    session['komunikat'] = "Zgłoszenie zostało zapisane pomyślnie!"  # Ustawienie komunikatu

    # Pobieramy adres e-mail od użytkownika z formularza
    email = request.form.get('email', '').strip()
    
    # Tworzymy wiadomość e-mail
    message = SendGridMail(
        from_email='pawsondutywebapp@gmail.com',  # Twój e-mail nadawcy
        to_emails='paulina.krok@onet.pl',  # Adres e-mail odbiorcy (użytkownika)
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
        logger.info(f"Wysłano wiadomość e-mail: {response.status_code}")
        
        flash('Twój e-mail został pomyślnie wysłany! Sprawdź swoją skrzynkę pocztową.', 'success')  # Sukces
        return redirect(url_for('main'))  # Przekierowanie na stronę wynikową

    except Exception as e:
        logger.error(f"Wystąpił błąd podczas wysyłania e-maila: {e}")
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
    print(f"Session data (before request): {session}")
    if 'first_message' not in session:
        session['first_message'] = True

    first_message = session['first_message']
    print(f"first_message (before request): {first_message}")

    if request.method == 'POST':
        print(f"Received form data: {request.form}")
        print(f"Received files: {request.files}")

        if 'photos' in request.files and request.files['photos']:
            # Obsługa przesyłania zdjęć
            uploaded_files = request.files.getlist("photos")
            print(f"Uploaded files: {[file.filename for file in uploaded_files]}")

            # Wstawiamy dane do bazy danych
            insert_report_into_db()  # Wstawiamy dane do bazy danych

            session.pop('first_message', None)
            return redirect(url_for('main'))

        user_input = request.form.get('user_input')
        if not user_input:
            print("User input is missing.")
            return "User input is required.", 400  # Wczesne zakończenie z błędem

        intent_tag = predict_class(user_input)
        response = get_response(intents, intent_tag)

        previous_message = session.get('previous_message', None)

        if session['first_message']:
            append_to_report("title", user_input, previous_message)
            session['first_message'] = False
        else:
            append_to_report(intent_tag, user_input, previous_message)

        session['previous_message'] = response

        if intent_tag == "witnesses":
            return render_template('chatbot.html', response=response, witness_step=True)

    print(f"Session data (after request): {session}")
    return render_template('chatbot.html', response=response, zalogowany=session.get('zalogowany'), name=session.get('name'))

@app.route('/chatbot_clear')
def chatbot_clear():
    if 'first_message' in session:
        session.pop('first_message', None)
    if 'previous_message' in session:
        session.pop('previous_message', None)
    return redirect(url_for('chatbot'))

if __name__ == '__main__':
    app.run()