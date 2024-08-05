import mysql.connector
import json

# Konfiguracja połączenia z bazą danych
db_config = {
    'user': 'administrator',
    'password': 'haslo',
    'host': '127.0.0.1',
    'database': 'baza_zgloszen',
    'raise_on_warnings': True
}

# Połączenie z bazą danych
try:
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    print("Połączono z bazą danych.")

    # Wczytanie pliku report.json
    with open('report.json', 'r', encoding='utf-8') as file:
        report_data = json.load(file)

    # Wyświetlenie danych z pliku JSON
    print("Dane z pliku report.json:")
    print(json.dumps(report_data, indent=4, ensure_ascii=False))

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
    if cnx.is_connected():
        cursor.close()
        cnx.close()
        print("Połączenie z bazą danych zostało zamknięte.")
