import requests
import pprint

api_key = "1986d494aa064214a6e195755260101"

link_api = "http://api.weatherapi.com/v1/current.json"

parametros = {
    "key": api_key,
    "q": "São Mateus,Espirito Santo",
    "lang": "pt"
}


resposta =requests.get(link_api, params=parametros) # params é usado para enviar os parâmetros na URL da requisição.

#statu da requisição para saber a razão do erro e o conteúdo da resposta.
#print(resposta.status_code)
#print(resposta.reason)
#print(resposta.content)

if resposta.status_code == 200:
    dados = resposta.json() # Converte o conteúdo da resposta em um dicionário Python.
    pprint.pprint(dados)
    temp = dados["current"]["temp_c"]
    descricao = dados["current"]["condition"]["text"]
    print(f"A temperatura atual em São Mateus-ES é de {temp}°C com {descricao}.")
    
    