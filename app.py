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
    'database': 'baza_zgloszen',
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

@app.route('/')
def main():
    return redirect(url_for('przekierowanieZgloszenie'))

@app.route('/index.html')
def przekierowanieZgloszenie():
    try:
        if session['rola']=='funkcjonariusz':
            return render_template('przegladanie.html', zalogowany=session.get('zalogowany'), imie=session.get('imie'))
        else:
            return render_template('index.html', zalogowany=session.get('zalogowany'), imie=session.get('imie'))
    except:
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

def login_istnieje(login):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT COUNT(*) FROM `Users` WHERE `login` = %s"
    cursor.execute(query, (login,))
    result = cursor.fetchone()[0]
    cnx.close()
    return result > 0

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

# Funkcja pomocnicza do pobierania user_id z bazy danych na podstawie loginu
def pobierz_user_id(login):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    query = "SELECT user_id FROM `Users` WHERE `login` = %s"
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
    query = "SELECT imię FROM `Users` WHERE `login` = %s"
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
    query = "SELECT rola FROM `Users` WHERE `login` = %s"
    cursor.execute(query, (login,))
    result = cursor.fetchone()
    cnx.close()
    if result:
        return result[0]
    else:
        return None


# Funkcja sprawdzająca dane logowania w bazie danych
def sprawdz_dane_logowania(login, haslo):
    # Połączenie z bazą danych (tu można dodać odpowiednie dane dostępowe)

    # Przykładowe zapytanie do bazy danych w celu sprawdzenia danych logowania
    # Należy dostosować zapytanie do struktury swojej bazy danych


    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    query = "SELECT COUNT(*) FROM `Users` WHERE `login` = %s AND `password` = %s"
    values = (login, haslo)

    cursor.execute(query, values)
    result = cursor.fetchone()

    cnx.commit()

    # Jeśli zapytanie zwraca wartość większą niż 0, to dane logowania są poprawne
    if result and result[0] > 0:
        return True
    else:
        return False

    
@app.route('/wyloguj', methods=['GET'])
def wyloguj():
    # Usunięcie flagi zalogowania z sesji
    session.pop('zalogowany', None)
    session.pop('user_id', None)  # Usunięcie również user_id z sesji
    session.pop('role', None) #usunięcie roli z sesji
    return redirect(url_for('logowanie'))

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




def insert_report_into_db():
    try:
        with open('report.json', 'r', encoding='utf-8') as file:
            report_data = json.load(file)

        # Połączenie z bazą danych
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Wstawienie danych do tabeli witnesses
        witness_insert = ("INSERT INTO witnesses (info_contact) VALUES (%s)")
        cursor.execute(witness_insert, (report_data['info_contact'],))
        witness_id = cursor.lastrowid

        # Wstawienie danych do tabeli perpetrators
        perpetrator_insert = ("INSERT INTO perpetrators (appearance) VALUES (%s)")
        cursor.execute(perpetrator_insert, (report_data['appearance'],))
        perp_id = cursor.lastrowid

        # Wstawienie danych do tabeli event_features
        event_features_insert = (
            "INSERT INTO event_features (event_desc, address, event_time, witness_id, perp_id) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cursor.execute(event_features_insert, (
            report_data['event_desc'],
            report_data['address'],
            report_data['event_time'],
            witness_id,
            perp_id
        ))
        event_feature_id = cursor.lastrowid

        # Wstawienie danych do tabeli reports
        report_insert = ("INSERT INTO reports (title, event_feature_id) VALUES (%s, %s)")
        cursor.execute(report_insert, (
            report_data['title'],
            event_feature_id
        ))

        # Zatwierdzenie transakcji
        cnx.commit()
        print("Dane zostały pomyślnie wstawione do bazy danych.")
    except mysql.connector.Error as err:
        print(f"Błąd: {err}")
        cnx.rollback()
    finally:
        cursor.close()
        cnx.close()



if __name__ == '__main__':
    app.run()