import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key or api_key == "sua_chave_do_google_aqui":
    print("ERRO: GOOGLE_API_KEY não configurada no arquivo .env")
else:
    try:
        genai.configure(api_key=api_key)
        print("--- Modelos Disponíveis ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Nome: {m.name}")
        print("---------------------------")
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")
