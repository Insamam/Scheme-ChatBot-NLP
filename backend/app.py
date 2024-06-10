import os
import pandas as pd
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from sentence_transformers import SentenceTransformer
import faiss
import re
import random
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download NLTK data
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('words')

# Load stopwords
stop_words = set(stopwords.words('english'))

def simulate_typing(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.001)  # Adjust the delay to control typing speed
    print()

file_path = '/home/ins/Code/CHATBOT/backend/finaldataset.xlsx'

try:
    df = pd.read_excel(file_path)
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit()

df['combined_text'] = df.apply(
    lambda row: ' '.join(row[['Scheme Name', 'Sector', 'Description', 'Objectives',
                             'Eligibility Criteria', 'Benefits', 'Implementation Agency',
                             'Application Process', 'Documents Required']].astype(str)),
    axis=1
)

texts = df['combined_text'].tolist()

scheme_names = df['Scheme Name'].tolist()

model_name = "paraphrase-MiniLM-L6-v2"
embedding_model = SentenceTransformer(model_name)

embeddings = embedding_model.encode(texts)

tokenizer_name = "gpt2-medium"
tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_name)
model = GPT2LMHeadModel.from_pretrained(tokenizer_name)

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

def generate_response(user_input, similar_docs, num_schemes):
    response = ""
    intro_phrases = [
        "Sure! Let's talk about",
        "Here's some information on",
        "Check out this scheme:",
        "Take a look at",
        "Here's a scheme for you:"
    ]
    schemes_shown = 0
    for doc in similar_docs[:min(num_schemes, 10)]:
        scheme_info = df.iloc[doc]
        response += f"{random.choice(intro_phrases)} {scheme_info['Scheme Name']}<br>" \
                    f"<b>Sector:</b> {scheme_info['Sector']}<br>" \
                    f"<b>Overview:</b> {scheme_info['Description']}<br>" \
                    f"<b>Objectives:</b> {scheme_info['Objectives']}<br>" \
                    f"<b>Eligibility:</b> {scheme_info['Eligibility Criteria']}<br>" \
                    f"<b>Benefits:</b> {scheme_info['Benefits']}<br>" \
                    f"<b>Implementation Agency:</b> {scheme_info['Implementation Agency']}<br>" \
                    f"<b>Application Process:</b> {scheme_info['Application Process']}<br>" \
                    f"<b>Documents Required:</b> {scheme_info['Documents Required']}<br>" \
                    f"{'-'*40}<br>"
        schemes_shown += 1

    if schemes_shown == 0:
        response = handle_unknown_question()
    elif schemes_shown < num_schemes:
        response += "<br>I can only provide information on up to 10 schemes at a time. " \
                    "Would you like to narrow down your search?"

    return response.strip()

def preprocess_query(user_input):
    user_input = user_input.lower()
    user_input = ''.join(char for char in user_input if char not in set(string.punctuation))
    alphanumeric_regex = r'\w+'
    words = re.findall(alphanumeric_regex, user_input)
    if words:
        return ' '.join(words)
    else:
        return ""

def detect_num_schemes(user_input):
    match = re.search(r'(?:list|explain|describe)\s+(\d+)?\s*(?:\w+\s+)?schemes?', user_input)
    if match:
        return int(match.group(1))
    return 1

def handle_unknown_question():
    unknown_responses = [
        "I'm sorry, I couldn't find any relevant schemes for your query.",
        "Unfortunately, I don't have information related to that. Could you please ask something else?",
        "I apologize, but your query doesn't seem to match any of the schemes in my database. Could you rephrase your question or ask about a different topic?"
    ]
    return random.choice(unknown_responses)

def handle_greetings_and_sentiments(user_input):
    greetings = ["hi", "hello", "good morning", "good afternoon", "good evening", "hey", "gud morning", "greetings", "howdy", "hola", "bonjour", "ciao", "namaste", "salaam", "aloha", "shalom", "konnichiwa", "yo", "what's up", "wassup", "sup", "ahoy", "g'day", "hiya", "well hello there", "greetings and salutations", "howdy partner", "hey there", "hi there"]
    sentiments = ["how are you", "what's up", "whats up" "how's it going", "how are you doing", "how you doing", "how's everything", "how r u", "how r you", "how ru", "how ru doing", "how are things", "how goes it", "how's life", "how's your day"]
    
    user_input = user_input.lower()

    for greeting in greetings:
        if greeting in user_input:
            return random.choice(["Hello! How can I assist you today?", "Hi there! What would you like to know about?", "Hey! How can I help you?", "Greetings! How may I be of service?", "Howdy! What can I help you with?", "Yo! What's up? How can I help?", "G'day! What can I do for you?", "Well hello there! How can I assist you today?"])

    for sentiment in sentiments:
        if sentiment in user_input:
            return random.choice(["I'm just a bot, but I'm here to help you!", "I'm here to assist you. How can I help?", "I'm here to provide information on schemes. How can I assist you?", "I'm an AI assistant, but I'll do my best to help you!", "I'm doing well, thanks for asking! How can I assist you today?"])

    return None

def is_valid_query(user_input):
    # Tokenize the input into words
    tokens = word_tokenize(user_input)
    
    # Remove stop words and punctuation
    filtered_tokens = [word.lower() for word in tokens if word.lower() not in stop_words and word.isalnum()]
    
    # Check if there are any remaining meaningful words using a word dictionary
    english_words = set(nltk.corpus.words.words())
    meaningful_words = [word for word in filtered_tokens if word in english_words]
    
    # Consider the query valid if it contains at least one meaningful word
    return len(meaningful_words) > 0

app = Flask(__name__)
CORS(app)

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get("user_input")
    if not user_input:
        return jsonify({"response": "Please provide an input."})

    if not is_valid_query(user_input):
        return jsonify({"response": "I couldn't understand your input. Please rephrase your question or ask something else."})

    preprocessed_input = preprocess_query(user_input)
    if not preprocessed_input:
        return jsonify({"response": "I couldn't understand your input. Please rephrase your question or ask something else."})

    num_schemes = detect_num_schemes(user_input)
    greeting_response = handle_greetings_and_sentiments(preprocessed_input)
    if greeting_response:
        return jsonify({"response": greeting_response})

    user_embedding = embedding_model.encode([preprocessed_input])
    k = max(num_schemes, 3)
    _, indices = index.search(user_embedding, k)
    similar_doc_indices = indices[0]

    if len(similar_doc_indices) > 0 and similar_doc_indices[0] < len(df):
        response = generate_response(preprocessed_input, similar_doc_indices, num_schemes)
    else:
        response = handle_unknown_question()

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)