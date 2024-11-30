# Instalar dependências necessárias
!pip install arxiv PyPDF2 sentence-transformers faiss-cpu
!pip install -q -U google-generativeai



# Importar bibliotecas
import arxiv
import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import requests
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display, Markdown
from google.colab import userdata



# Diretório para armazenar os artigos
os.makedirs("arxiv_pdfs", exist_ok=True)

# Função para buscar e baixar artigos no arXiv
def fetch_arxiv_articles(query, max_results=5):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    for result in search.results():
        title = result.title.replace(" ", "_").replace("/", "_")
        pdf_path = os.path.join("arxiv_pdfs", f"{title}.pdf")
        print(f"Baixando: {result.title}")
        response = requests.get(result.pdf_url)
        with open(pdf_path, "wb") as f:
            f.write(response.content)

# Função para extrair texto de PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text()
    except Exception as e:
        print(f"Erro ao processar {pdf_path}: {e}")
    return text

# Função para indexar os textos
def index_texts(texts):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts, show_progress_bar=True)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index, embeddings

# Buscar e processar artigos
fetch_arxiv_articles("Large Language Models", max_results=5)

# Processar os PDFs baixados
documents = []
for file in os.listdir("arxiv_pdfs"):
    path = os.path.join("arxiv_pdfs", file)
    text = extract_text_from_pdf(path)
    documents.append(text)

# Indexar os documentos
index, embeddings = index_texts(documents)

print("Artigos baixados, processados e indexados com sucesso!")

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# Used to securely store your API key
# Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
GOOGLE_API_KEY=userdata.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def search_articles(query, index, embeddings, documents, top_k=5):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    return [documents[i] for i in indices[0]]

# Função para responder perguntas usando o modelo Gemini
def answer_question(question):
    relevant_articles = search_articles(question, index, embeddings, documents)
    context = "\n\n".join(relevant_articles)
    response = model.generate_content('context: ' + context + ' QUESTION: ' + question)
    return response

perguntas = [
    "Qual é a principal aplicação dos LLMs no contexto de conteúdo não-inglês?",
    "Como os LLMs lidam com idiomas que possuem menos dados de treinamento?",
    "Como o modelo Cedille se diferencia de outros LLMs?",
    "Quais são os principais benefícios de treinar modelos monolíngues para um grande número de idiomas?",
]

for pergunta in perguntas:
    print(f"Pergunta: {pergunta}")
    resposta = answer_question(pergunta)
    resposta = to_markdown(resposta.text)
    display(resposta)