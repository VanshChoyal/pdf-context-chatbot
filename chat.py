from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import json
from dotenv import load_dotenv
import pinecone

load_dotenv()

    # Initialize Pinecone
pinecone.Pinecone(api_key=os.environ['PINECONE_API_KEY'])

with open('config.json', 'r') as file:
    config = json.load(file)

embeddings = OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
index_name = config.get('index_name')

# Upload PDF to Pinecone
def upload_pdf_to_pinecone(path):
    file_name = os.path.basename(path).replace(" ", "_")

    loader = PyPDFLoader(path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(pages)

    for d in docs:
        d.metadata['file_name'] = file_name

    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    existing_docs = vectorstore.similarity_search(
        query="dummy",
        filter={"file_name": file_name},
        k=1
    )

    if existing_docs:
        print(f"{file_name} already exists in Pinecone. Skipping upload.")
        return

    PineconeVectorStore.from_documents(docs, embedding=embeddings, index_name=index_name)
    print(f"{file_name} uploaded successfully!")

# Create retriever
vectorstore = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, input_key="question")

def clear_memory():
    """Clear the conversation memory"""
    global memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, input_key="question")


prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant. Use the chat history and retrieved document context to answer accurately.
    Always maintain awareness of our previous conversation and refer back to previous topics when relevant.
    If the user refers to something mentioned earlier, acknowledge it and build upon that context.
    Consider both the immediate question and the broader context of our ongoing conversation."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "Question: {question}\n\nRelevant context:\n{context}\n\nAnswer:")
])

# Model + Chain
llm = ChatOpenAI(model="gpt-4", temperature=0)
qa_chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

def get_response(query: str):
    """Retrieve context, update memory, and get AI response."""
    # Retrieve context from vectorstore
    docs = retriever.get_relevant_documents(query)
    context = "\n".join([d.page_content for d in docs]) if docs else "No relevant context found."
    
    # Load current memory state
    memory_vars = memory.load_memory_variables({})
    chat_history = memory_vars.get("chat_history", [])
    
    # Create system context with previous conversations
    history_context = "\n".join([
        f"{'Human' if msg.type == 'human' else 'Assistant'}: {msg.content}"
        for msg in chat_history
    ])
    
    # Add history context to the query context
    full_context = f"Previous conversation:\n{history_context}\n\nCurrent context:\n{context}"
    
    # Generate response
    response = qa_chain.run(question=query, context=full_context)
    
    return response
