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

def simulate_typing(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.001)  # Adjust the delay to control typing speed
    print()
file_path = 'finaldataset.xlsx'
# Load the Excel file


try:
    df = pd.read_excel(file_path)
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit()
    
# Combine relevant text fields into a single column for embedding
df['combined_text'] = df.apply(
    lambda row: ' '.join(row[['Scheme Name', 'Sector', 'Description', 'Objectives',
                             'Eligibility Criteria', 'Benefits', 'Implementation Agency',
                             'Application Process', 'Documents Required']].astype(str)),
    axis=1
)

# Extract combined text and scheme names
texts = df['combined_text'].tolist()
scheme_names = df['Scheme Name'].tolist()

# Initialize a sentence transformer model
model_name = "paraphrase-MiniLM-L6-v2"
embedding_model = SentenceTransformer(model_name)

# Compute embeddings for the texts
embeddings = embedding_model.encode(texts)

# Initialize the GPT-2 tokenizer and model
tokenizer_name = "gpt2-medium"
tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_name)
model = GPT2LMHeadModel.from_pretrained(tokenizer_name)

# Create a FAISS index
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
    for doc in similar_docs[:min(num_schemes, 10)]:  # Limit to maximum 10 schemes
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
    return user_input

def detect_num_schemes(user_input):
    match = re.search(r'(?:list|explain|describe)\s+(\d+)?\s*(?:\w+\s+)?schemes?', user_input)

    if match:
        return int(match.group(1))
    return 1  # Default to 1 scheme if not specified

def handle_unknown_question():
    return "I'm sorry, I don't have information on that topic. Could you please ask something else?"

def handle_greetings_and_sentiments(user_input):
    greetings = ["hi", "hello", "good morning", "good afternoon", "good evening", "hey"]
    sentiments = ["how are you", "what's up", "how's it going"]

    for greeting in greetings:
        if greeting in user_input:
            return random.choice(["Hello! How can I assist you today?", "Hi there! What would you like to know about?", "Hey! How can I help you?"])

    for sentiment in sentiments:
        if sentiment in user_input:
            return random.choice(["I'm just a bot, but I'm here to help you!", "I'm here to assist you. How can I help?", "I'm here to provide information on schemes. How can I assist you?"])

    return None

app = Flask(__name__)
CORS(app)

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get("user_input")
    if not user_input:
        return jsonify({"response": "Please provide an input."})

    preprocessed_input = preprocess_query(user_input)
    num_schemes = detect_num_schemes(user_input)
    greeting_response = handle_greetings_and_sentiments(preprocessed_input)
    if (greeting_response):
        return jsonify({"response": greeting_response})

    user_embedding = embedding_model.encode([preprocessed_input])
    k = max(num_schemes, 3)  # Ensure we have enough results to choose from
    _, indices = index.search(user_embedding, k)
    similar_doc_indices = indices[0]

    if len(similar_doc_indices) > 0 and similar_doc_indices[0] < len(df):
        response = generate_response(preprocessed_input, similar_doc_indices, num_schemes)
    else:
        response = handle_unknown_question()

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
