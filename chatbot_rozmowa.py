import random
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

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

# Inicjalizacja struktury do przechowywania danych
report_data = {
    "title": "",
    "event_desc": "",
    "address": "",
    "event_time": "",
    "appearance": "",
    "info_contact": ""
}

# Test działania
first_message = True
last_tag = None
while True:
    message = input("Ty: ")
    
    # Przypisanie tytułu na podstawie pierwszej wiadomości
    if first_message:
        report_data['title'] = message
        first_message = False
    
    intent_tag = predict_class(message)
    response = get_response(intents, intent_tag)
    print(f"Chatbot: {response}")
    
    # Zbieranie danych w zależności od tagu odpowiedzi
    if intent_tag == "address":
        report_data['address'] = message
    elif intent_tag == "date":
        report_data['event_time'] = message
    elif intent_tag == "number_of_perpetrators":
        report_data['appearance'] = message + ", "  # Dodanie przecinka na późniejsze połączenie
    elif intent_tag == "perpetrators_apperance":
        report_data['appearance'] += message  # Dodanie opisu wyglądu sprawców
    elif intent_tag == "witnesses":
        report_data['info_contact'] = message
        print("Kończymy rozmowę, ponieważ otrzymano tag 'witness'.")
        break  # Przerwanie pętli, gdy chatbot odpowie na pytanie o świadków
    else:
        if last_tag != None:
        # Dodanie kolejnych pytań i odpowiedzi do event_desc
            report_data['event_desc'] += f"{last_tag}: {message}; "
        last_tag = response

# Zapis do pliku JSON
with open('report.json', 'w', encoding='utf-8') as json_file:
    json.dump(report_data, json_file, ensure_ascii=False, indent=4)

print("Raport zapisany do report.json")
