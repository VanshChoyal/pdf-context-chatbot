from flask import Flask, render_template, redirect, request, jsonify
import os
import json
from chat import upload_pdf_to_pinecone, get_response
from werkzeug.utils import secure_filename
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings



with open('config.json', 'r') as file:
    config = json.load(file)

UPLOAD_FOLDER = config.get('upload_folder')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__)

@app.route('/')
def home():
    return redirect('/chat')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    question = data.get("question") if data else None

    if not question:
        return jsonify({"success": False, "error": "No question provided"}), 400

    answer = get_response(question)
    return jsonify({"success": True, "question": question, "response": answer})

def list_files_in_index(index_name: str, k: int = 1000):
    """
    Returns a list of unique file names stored in the Pinecone index.

    Args:
        index_name (str): Name of your Pinecone index.
        k (int): Number of vectors to fetch for metadata (default 1000).

    Returns:
        List[str]: Unique file names.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
    
    results = vectorstore.similarity_search(query="", k=k)
    
    file_names = set()
    for doc in results:
        if "file_name" in doc.metadata:
            file_names.add(doc.metadata["file_name"])
    
    return list(file_names)

@app.route('/api/get/file_names', methods=['GET'])
def api_get_file_names():
    files = list_files_in_index(index_name=config.get('index_name'))
    return files if files else []

@app.route("/api/delete/file", methods=["POST"])
def api_delete_file():
    data = request.get_json()
    file_name = data.get("file_name")
    
    if not file_name:
        return jsonify({"error": "No file name provided"}), 400
    
    try:
        # Delete from Pinecone
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = PineconeVectorStore.from_existing_index(index_name=config.get('index_name'), embedding=embeddings)
        
        # Delete all vectors with matching file_name metadata
        index = vectorstore._index
        index.delete(filter={"file_name": file_name})
        
        # Delete the physical file if it exists
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({"success": True, "message": f"File {file_name} deleted successfully"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload/pdf", methods=["POST"])
def api_upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    file_name_clean = secure_filename(file.filename).replace(" ", "_")
    save_path = os.path.join(UPLOAD_FOLDER, file_name_clean)
    file.save(save_path)

    upload_pdf_to_pinecone(save_path)

    # Remove file
    os.remove(save_path)

    return jsonify({"message": "File uploaded", "path": save_path})

if __name__ == '__main__':
    app.run(debug=True)