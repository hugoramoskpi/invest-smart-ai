import sys
import json

def main():
    # Lê a entrada do Gemini CLI via stdin
    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            return
        input_data = json.loads(input_raw)
    except Exception as e:
        # Em caso de erro, permite para não travar o CLI, mas reporta no stderr
        print(f"Erro no Hook: {e}", file=sys.stderr)
        print(json.dumps({"decision": "allow"}))
        return

    tool_input = input_data.get("tool_input", {})
    # Pega o conteúdo dependendo da ferramenta usada (write_file ou replace)
    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    
    # Auditoria de segurança: Proibir segredos e chaves expostas
    forbidden_patterns = ["API_KEY =", "SECRET_KEY =", "PASSWORD =", "DEBUG=True"]
    found = [p for p in forbidden_patterns if p in content]

    if found:
        response = {
            "decision": "deny",
            "reason": f"BLOQUEIO DE SEGURANÇA: Foi detectado o uso de termos proibidos (segredos expostos): {', '.join(found)}. Use variáveis de ambiente (.env).",
            "systemMessage": "🚨 Operação bloqueada. Por favor, remova segredos do código e use .env."
        }
    else:
        response = {
            "decision": "allow",
            "systemMessage": "🛡️  Código auditado pela Skill de Investimentos. Segurança OK."
        }

    # Retorna o JSON (Apenas o JSON deve ir para o stdout)
    print(json.dumps(response))

if __name__ == "__main__":
    main()
