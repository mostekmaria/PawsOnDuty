import random
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Wczytaj plik intents.json
with open('intents.json', encoding='utf-8') as file:
    intents = json.load(file)

# Przygotowanie listy tagów (klas)
classes = [intent['tag'] for intent in intents['intents']]
num_labels = len(classes)

# Załaduj tokenizer i model lokalnie
tokenizer = AutoTokenizer.from_pretrained("./local_model_2")
model = AutoModelForSequenceClassification.from_pretrained("./local_model_2", num_labels=num_labels)

tag2idx = {tag: idx for idx, tag in enumerate(classes)}
idx2tag = {idx: tag for tag, idx in tag2idx.items()}

def tokenize_input(text, tokenizer, max_length=128):
    return tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=max_length,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
        truncation=True
    )

def predict_class(text):
    tokens = tokenize_input(text, tokenizer)
    input_ids = tokens['input_ids']
    attention_mask = tokens['attention_mask']

    model.eval()
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    predicted_class_idx = torch.argmax(logits, dim=1).item()
    return idx2tag[predicted_class_idx]

def get_response(intents, intent_tag):
    for intent in intents['intents']:
        if intent['tag'] == intent_tag:
            return random.choice(intent['responses'])
        
def initialize_report_file():
    if os.path.exists('report.json'):
        with open('report.json', 'w', encoding='utf-8') as json_file:
            json.dump({
                "title": "",
                "event_desc": "",
                "address": "",
                "event_time": "",
                "appearance": "",
                "info_contact": ""
            }, json_file, ensure_ascii=False, indent=4)

def append_to_report(intent_tag, message, response=None):
    with open('report.json', 'r+', encoding='utf-8') as json_file:
        try:
            report_data = json.load(json_file)
        except json.JSONDecodeError:
            report_data = {
                "title": "",
                "event_desc": "",
                "address": "",
                "event_time": "",
                "appearance": "",
                "info_contact": ""
            }

        # Przypisywanie wiadomości do odpowiednich tagów
        if intent_tag == "title":
            report_data['title'] = message
        elif intent_tag == "address":
            report_data['address'] = message
        elif intent_tag == "date":
            report_data['event_time'] = message
        elif intent_tag == "number_of_perpetrators":
            if report_data['appearance']:
                report_data['appearance'] += f"{message}, "
            else:
                report_data['appearance'] = f"{message}, "
        elif intent_tag == "perpetrators_apperance":
            if report_data['appearance']:
                report_data['appearance'] += message
            else:
                report_data['appearance'] = message
        elif intent_tag == "witnesses":
            report_data['info_contact'] = message
        else:
            # Przypisywanie wiadomości do event_desc, jeśli nie pasują do innych tagów
            if intent_tag not in ["address", "date", "number_of_perpetrators", "perpetrators_apperance", "witnesses", "title"]:
                if report_data['event_desc']:
                    report_data['event_desc'] += f"{response}: {message}, "
                else:
                    report_data['event_desc'] = f"{response}: {message}, "

        json_file.seek(0)
        json.dump(report_data, json_file, ensure_ascii=False, indent=4)
        json_file.truncate()



initialize_report_file()
# Funkcja do interaktywnego testowania w terminalu (tylko do uruchomienia lokalnie)
def interactive_chat():
    first_message = True
    last_tag = None

    while True:
        message = input("Ty: ")

        if first_message:
            append_to_report("title", message)
            first_message = False
            continue

        intent_tag = predict_class(message)
        response = get_response(intents, intent_tag)
        print(f"Chatbot: {response}")

        if intent_tag == "address":
            append_to_report(intent_tag, message)
            print("Kończymy rozmowę, ponieważ otrzymano tag 'address'.")
            break
        elif intent_tag == "date":
            append_to_report(intent_tag, message)
        elif intent_tag == "number_of_perpetrators":
            append_to_report(intent_tag, message)
        elif intent_tag == "perpetrators_apperance":
            append_to_report(intent_tag, message)
        elif intent_tag == "witnesses":
            append_to_report(intent_tag, message)
            print("Kończymy rozmowę, ponieważ otrzymano tag 'witness'.")
            break
        else:
            if last_tag is not None:
                append_to_report("event_desc", message, last_tag)
            last_tag = response

    print("Raport zapisany do report.json")
