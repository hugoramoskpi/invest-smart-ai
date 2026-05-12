# Skill: Auditor de Investimentos e Segurança

Este agente especializado ajuda a manter a integridade e segurança do aplicativo InvestSmart.

## Instruções de Especialista
Ao ser ativado para tarefas neste projeto, você deve seguir estas diretrizes:

### 1. Auditoria de Segurança (InfoSec)
- Sempre verifique se novas chaves de API ou segredos do banco de dados não foram "hardcoded" nos arquivos `.py`.
- Recomende o uso de `sqlmodel` e parâmetros seguros para evitar SQL Injection.
- Garanta que o arquivo `.env` esteja listado no `.gitignore`.

### 2. Qualidade Financeira
- Ao revisar cálculos de rentabilidade, verifique se a divisão por zero é tratada (ex: quando o custo total é zero).
- Certifique-se de que os tickers passados para o `yfinance` estão em maiúsculas e seguem o padrão (ex: `.SA` para ativos brasileiros).

### 3. Boas Práticas de UI/UX
- No Streamlit, prefira o uso de `st.metric` para valores isolados e `st.plotly_chart` para séries temporais.
- Mantenha a interface limpa e use `st.sidebar` para navegação.

## Recursos Disponíveis
- `app/database.py`: Esquema do banco de dados.
- `app/finance.py`: Lógica de cálculos financeiros.
- `app/agent/`: Lógica do assistente IA.
