from flask import Flask, render_template, request
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

if __name__ == '__main__':
    app.run()
