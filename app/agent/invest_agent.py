import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class InvestAgent:
    def __init__(self):
        # Tenta carregar a chave, se não houver, o agente falhará graciosamente
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.llm = None
        else:
            self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

    def ask(self, question: str, portfolio_data: str):
        if not self.llm:
            return "⚠️ Erro: Chave de API da OpenAI não encontrada no arquivo .env."

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
