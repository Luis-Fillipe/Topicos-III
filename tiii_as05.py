import streamlit as st
import requests
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# Carregar variáveis de ambiente do arquivo .env
base_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_path, '.env'))

# Obter a chave da API
grok_key = os.getenv("GROK_KEY")

if not grok_key:
    raise ValueError("API key not found. Please add it to the .env file following the format GROK_KEY=\"your_key_here\".")

# Função que recebe o file_path e realiza a leitura do arquivo PDF
def read_pdf_from_directory(file_path):
    # Verifica se o arquivo existe no diretório fornecido
    if os.path.exists(file_path):
        return extract_text_from_pdf(file_path)
    else:
        st.error(f"O arquivo {file_path} não foi encontrado.")
        st.stop()

# Função para extrair texto de PDFs
def extract_text_from_pdf(file):
    text = ""
    try:
        # Se o arquivo for um UploadedFile do Streamlit, deve-se salvá-lo primeiro
        if isinstance(file, bytes):  # Caso o arquivo seja em formato bytes (upload via Streamlit)
            with open("temp.pdf", "wb") as f2:
                f2.write(file)
            file_path = "temp.pdf"
        else:
            file_path = file  # Caso seja um arquivo já no diretório

        # Ler o arquivo PDF
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text()
    except Exception as e:
        st.error(f"Erro ao processar o arquivo PDF: {e}")
    return text

documents = []

file_path = 'artigo1.pdf'
documents.append(read_pdf_from_directory(file_path))

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
Em nossa base de dados, temos um artigo em PDF sobre Modelos de Linguagem de Grande Escala (LLMs). 
Você pode fazer upload de um arquivo PDF para fornecer um contexto ou fazer perguntas diretamente sobre os artigos disponíveis.
""")
st.write("""
Os artigos disponíveis são:
1. Diversidade Linguística e Inclusão Digital: Desafios para uma IA brasileira
""")

st.write("""
Caso deseje fazer perguntas sobre o artigo disponível, basta clicar no botão "Enviar" sem fazer upload de um arquivo PDF.
""")

question = st.text_input("Possui alguma pergunta em mente?")

uploaded_files = st.file_uploader("Escolha arquivos PDF para servir de contexto para a LLM. Tenha em mente que arquivos muito extensos não serão aceitos.", type="pdf", accept_multiple_files=True)

# Processar arquivos enviados e gerar contexto
uploaded_texts = []
if uploaded_files is not None:
    with st.spinner("Por favor, aguarde enquanto o texto é extraído..."):
        try:
            for uploaded_file in uploaded_files:
                uploaded_text = extract_text_from_pdf(uploaded_file)
                if uploaded_text:
                    uploaded_texts.append(uploaded_text)
                else:
                    st.error(f"Falha ao extrair texto do PDF: {uploaded_file.name}")
                    st.stop()
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {e}")
            st.stop()

# Definir o contexto com os documentos existentes e os arquivos enviados
context = "\n".join(documents)
if uploaded_texts:
    context += "\n" + "\n".join(uploaded_texts)

if question:
    if st.button("Enviar"):
        with st.spinner("Por favor, aguarde enquanto a resposta é gerada..."):
            try:
                answer = answer_question(context, question)
                st.write(answer)
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
