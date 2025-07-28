# resumo_ia.py
import os
from google import genai

# Usa chave da variável de ambiente: GEMINI_API_KEY
client = genai.Client()


def gerar_resumo(codigo_processo, movimento_atual, houve_novidade, tipo=None):
    caminho = os.path.join("moves", f"{codigo_processo}.txt")

    if not os.path.exists(caminho):
        return "❌ Histórico não encontrado."

    with open(caminho, "r", encoding="utf-8") as f:
        historico = f.read().strip()

    # Cabeçalho condicional do resumo
    if houve_novidade:
        cabecalho = "Uma novidade processual foi registrada."
    else:
        cabecalho = "Sem novidades."

    prompt = f"""
            Você é um assistente jurídico. Abaixo estão os movimentos de um processo judicial:
            
            {historico}
        
            Situação atual: "{movimento_atual}"
            
            Observação: 
            - Se o {tipo} for "Interdito Proibitório" ou "Agravo de Instrumento", considere que somos a parte ré. 
            - Se o {tipo} for "Reintegração de Posse", considere que somos a parte autora.
            Com base nesse histórico, escreva um parágrafo curto (máximo 2 frases) que resuma o estado do processo. 
            Comece o resumo com a frase:
        
            "{cabecalho}"
        
            E explique de forma objetiva e formal o contexto processual atual.
            
            Exemplo esperado:
        
            "Sem novidades. 
            O processo segue em curso, aguardando cumprimento de mandado expedido ao oficial de justiça."
            Evite repetir literalmente o conteúdo dos movimentos. Use linguagem clara e jurídica. 
            A resposta deve estar completamente em português formal.
            
            Movimentos que falem apenas de petições protocoladas, ou ciência, não deve ser interpretada com 
            ré ou autor, quaisquer partes podem ter protocolado.
        
            Agora gere o resumo, em apenas um parágrafo:
            """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"❌ Erro ao gerar resumo IA: {e}"
