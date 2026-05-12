import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class InvestAgent:
    def __init__(self):
        # Prioriza Google Gemini, mas mantém suporte a OpenAI
        google_key = os.getenv("GOOGLE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if google_key and google_key != "sua_chave_do_google_aqui":
            # Usando o alias estável 'gemini-flash-latest' que apareceu no seu diagnóstico
            self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=google_key)
        elif openai_key:
            self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
        else:
            self.llm = None

    def ask(self, question: str, portfolio_data: str):
        if not self.llm:
            return "⚠️ Erro: Nenhuma chave de API (GOOGLE_API_KEY ou OPENAI_API_KEY) encontrada no arquivo .env."

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente financeiro inteligente especializado em investimentos.
            Você tem acesso aos dados da carteira do usuário abaixo.
            Sua tarefa é analisar esses dados e responder perguntas de forma estratégica e clara.
            
            Dados da Carteira:
            {portfolio_data}
            
            Diretrizes:
            - Seja conciso e use um tom profissional.
            - Se o usuário perguntar sobre diversificação, analise os tipos de ativos.
            - Se perguntar sobre performance, foque no P&L e rentabilidade.
            """),
            ("human", "{question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"question": question, "portfolio_data": portfolio_data})
        except Exception as e:
            return f"❌ Erro ao processar a requisição: {e}"
