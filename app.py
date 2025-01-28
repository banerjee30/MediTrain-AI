from flask import Flask, request, jsonify
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import random
import json

# Load fine-tuned or pre-trained GPT-2 model and tokenizer
model_name = "gpt2"  # Replace with "finetuned_gpt2" if you have a fine-tuned model
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Load the conversations dataset
with open("conversations.json", "r") as file:
    conversation_data = json.load(file)

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to MediTrain AI Patient Persona Generator API!"})

@app.route("/generate_persona", methods=["POST"])
def generate_persona():
    # Parse request data
    data = request.json
    if not data or "condition" not in data:
        return jsonify({"error": "Please provide a medical condition."}), 400

    condition = data["condition"]
    age_range = data.get("age_range", (20, 80))
    gender = data.get("gender", random.choice(["Male", "Female"]))
    additional_context = data.get("additional_context", "")

    # Find relevant conversation data
    condition_data = [
        entry for entry in conversation_data if condition.lower() in entry["condition"].lower()
    ]
    if not condition_data:
        return jsonify({"error": f"No data found for the condition: {condition}"}), 404

    # Randomly select a conversation
    sample = random.choice(condition_data)
    age = random.randint(*age_range)

    # Create input prompt for persona generation
    prompt = (
        f"Create a detailed patient persona based on the following information:\n"
        f"Condition: {condition}\n"
        f"Age: {age}\n"
        f"Gender: {gender}\n"
        f"Conversation: {sample['conversation']}\n"
        f"{additional_context}\n"
    )

    # Generate persona
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=300, temperature=0.7)
    persona = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return jsonify({"condition": condition, "persona": persona})

@app.route("/ask_question", methods=["POST"])
def ask_question():
    # Parse request data
    data = request.json
    if not data or "question" not in data or "persona" not in data:
        return jsonify({"error": "Please provide a question and a persona."}), 400

    question = data["question"]
    persona = data["persona"]

    # Create input prompt for answering the question
    prompt = (
        f"Based on the following patient persona, answer the question:\n"
        f"Persona: {persona}\n"
        f"Question: {question}\n"
        f"Answer:"
    )
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=200, temperature=0.7)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return jsonify({"question": question, "answer": answer})

if __name__ == "__main__":
    app.run(debug=True)
