from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

system_prompt="Você é um modelo para resolver problemas de lógica. Problemas de lógica quase sempre envolvem pegadinhas que exigem que você investigue um outro tipo de relação entre os objetos do problema, como quantidade de letras, relações matemáticas, hierárquicas, etc."

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=input('Insira o problema: '),
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            top_p=0.95
        )
    )
    print(response.text)

except Exception as e:
    print('Erro ao consumir a API:', e)