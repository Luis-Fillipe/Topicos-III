import streamlit as st
import requests
import os
from dotenv import load_dotenv
import arxiv
from PyPDF2 import PdfReader

# Carregar variáveis de ambiente do arquivo .env
base_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_path, '.env'))

# Obter a chave da API
grok_key = os.getenv("GROK_KEY")

if not grok_key:
    raise ValueError("API key not found. Please add it to the .env file following the format GROK_KEY=\"your_key_here\".")

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

# Buscar e processar artigos
fetch_arxiv_articles("Large Language Models", max_results=5)

# Processar os PDFs baixados
documents = []
for file in os.listdir("arxiv_pdfs"):
    path = os.path.join("arxiv_pdfs", file)
    text = extract_text_from_pdf(path)
    documents.append(text)

print("Artigos baixados, processados e indexados com sucesso!")

# Função para responder perguntas usando o modelo Gemini
def answer_question(context, question):
    prompt = f"Responda à pergunta descrita após a tag **Pergunta:** com base no texto dentro da tag **Contexto:**\n\n**Contexto:** {context}\n\n**Pergunta:** {question}\n\n**Resposta:**"
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {grok_key}"
        },
        json={
            "model": "llama3-8b-8192",
            "messages": [{
                "role": "system",
                "content": "Assistente conversacional para responder perguntas baseadas em um contexto. É necessário que ao finalizar uma pergunte, se disponha a responder mais alguma pergunta sobre algum novo PDF ou sobre o pdf que foi feito o upload."
            },
            {
                "role": "user",
                "content": prompt
            }]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

st.title("Assistente Conversacional PDFbot")
st.write("""
Bem-vindo ao PDFbot! Este assistente conversacional responde perguntas com base no contexto fornecido por um arquivo PDF. 
Em nossa base de dados, temos 5 artigos em PDF sobre Modelos de Linguagem de Grande Escala (LLMs). 
Você pode fazer upload de um arquivo PDF para fornecer um contexto ou fazer perguntas diretamente sobre os artigos disponíveis.
""")
st.write("""
Os artigos disponíveis são:
1. Lost in Translation: Large Language Models in Non-English Content Analysis
2. Cedille: A large autoregressive French language model
3. How Good are Commercial Large Language Models on African Languages?
4. Goldfish: Monolingual Language Models for 350 Languages
5. Modelling Language
""")

question = st.text_input("Possui alguma pergunta em mente?")

uploaded_file = st.file_uploader("Escolha um arquivo PDF para servir de contexto para a LLM. Tenha em mente que arquivos muito extensos não serão aceitos.", type="pdf")

if uploaded_file is not None:
    with st.spinner("Por favor, aguarde enquanto o texto é extraído..."):
        try:
            uploaded_text = extract_text_from_pdf(uploaded_file)
            if not uploaded_text:
                st.error("Falha ao extrair texto do PDF.")
                return
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {e}")
            return

    # Concatenar textos dos PDFs baixados e do PDF enviado pelo usuário
    context = "\n".join(documents) + "\n" + uploaded_text

    if st.button("Enviar"):
        with st.spinner("Por favor, aguarde enquanto a resposta é gerada..."):
            try:
                answer = answer_question(context, question)
                st.write(answer)
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
