import os
import base64

def main():
    token_dir = os.path.expanduser("~/.garminconnect")
    token_file = os.path.join(token_dir, "garmin_tokens.json")
    
    if not os.path.exists(token_file):
        print(f"Erro: O arquivo de tokens nao foi encontrado em: {token_file}")
        print("Certifique-se de que voce autenticou o Garmin localmente primeiro usando o comando:")
        print("  garmin-mcp-auth")
        return
        
    try:
        with open(token_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Codifica o conteudo em base64
        b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        print("\n" + "="*80)
        print("SUCESSO: Seu token Garmin foi codificado com sucesso!")
        print("Copie TODO o texto abaixo (incluindo todas as linhas) e guarde-o.")
        print("Voce usara esse texto como a variavel de ambiente GARMIN_TOKENS_BASE64 na nuvem.")
        print("="*80 + "\n")
        print(b64_content)
        print("\n" + "="*80)
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo: {e}")

if __name__ == "__main__":
    main()
