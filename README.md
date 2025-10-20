# PDF Context ChatBot
The project uses **LangChain**, **Pinecone VectorStore**, and **OpenAI API** to create a functional chatbot which can understand and respond using context from the PDFs uploaded by the users.

---

## Setup
- Create a `.env` file in the project root and add `OPENAI_API_KEY` and `PINECONE_API_KEY` as
```plaintext
OPENAI_API_KEY="your-api-key"
PINECONE_API_KEY="your-api-key"
```

- Update `index_name` and `upload_folder` in `config.json`.

- `upload_folder` is a path where the PDFs are temporarily saved before being saved in the Vector Store. 

## Features
- Context-aware chatbot from uploaded PDFs
- Clean, user-friendly interface
- Secure vector storage using Pinecone

## Tech Stack
- Python 3.12
- Langchain
- OpenAI API
- Pinecone
- Flask
- HTML, CSS, JS

## Installation
```bash
# Clone the repo
git clone https://github.com/VanshChoyal/pdf-context-chatbot.git
cd pdf-context-chatbot

# Install dependencies
pip install -r requirements.txt
```

## Run the App
```bash
python app.py
```
Then open your browser and visit:
👉 http://localhost:5000


### Author
Made by Vansh Choyal
Python Developer | Web Dev