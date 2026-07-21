# 🚀 GUIA DE IMPLANTAÇÃO GRATUITA NO KOYEB 24/7 (PEDRO & LAURA)

Tudo já foi configurado e testado no seu computador! O servidor duplo aceita as duas contas simultaneamente e decodifica os tokens com 100% de sucesso em 1 segundo.

---

## 📋 PASSO 1: Subir a pasta no GitHub

1. Acesse seu **GitHub** (github.com).
2. Crie um repositório chamado `garmin-mcp-nuvem`.
3. Suba o conteúdo desta pasta para o repositório (`Dockerfile`, `requirements.txt`, `garmin_mcp_server`).

---

## 🛠️ PASSO 2: Criar o App no Koyeb (100% Grátis)

1. Acesse **[koyeb.com](https://www.koyeb.com)** e faça login com sua conta do GitHub.
2. Clique em **Create Web Service**.
3. Selecione a opção **GitHub** e escolha o repositório `garmin-mcp-nuvem`.
4. Em **Builder**, selecione **Dockerfile**.

---

## 🔑 PASSO 3: Adicionar Variáveis de Ambiente no Koyeb

Na tela de configuração do Koyeb, abra a seção **Environment Variables** e adicione as seguintes variáveis:

1. `PEDRO_TOKENS_BASE64`:  
   *(Abra o arquivo `PEDRO_B64.txt` na pasta do seu computador e cole todo o texto aqui)*

2. `LAURA_TOKENS_BASE64`:  
   *(Abra o arquivo `LAURA_B64.txt` na pasta do seu computador e cole todo o texto aqui)*

3. `PEDRO_EMAIL`: `pedrocastrodias@gmail.com`
4. `LAURA_EMAIL`: `laurasisdelli@gmail.com`

---

## 🎯 PASSO 4: Cole as URLs no Claude Mobile!

Após clicar em **Deploy**, o Koyeb gerará um endereço fixo (Exemplo: `https://garmin-mcp-pedro-laura.koyeb.app`).

### Suas URLs para o Claude:

* **URL do Pedro:**  
  `https://SEU-APP.koyeb.app/pedrogarminsolucao123/sse`

* **URL da Laura:**  
  `https://SEU-APP.koyeb.app/lauragarminsolucao123/sse`

---
✨ **Pronto! Fica 100% online 24/7 na nuvem sem precisar do computador ligado!**
