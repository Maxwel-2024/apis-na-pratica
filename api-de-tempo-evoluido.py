import customtkinter as ctk
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests.exceptions as req_exc
from PIL import Image
from io import BytesIO

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppClima(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Weather Vision v1.0")
        self.geometry("450x700")
        self.resizable(False, False)

        # Container Principal
        self.frame = ctk.CTkFrame(self, corner_radius=20)
        self.frame.pack(pady=40, padx=40, fill="both", expand=True)

        self.label_titulo = ctk.CTkLabel(self.frame, text="Previsão do Tempo", font=("Roboto", 24, "bold"))
        self.label_titulo.pack(pady=(30, 20))

        self.label_instrucao = ctk.CTkLabel(self.frame, text="Digite cidade e estado separado por vírgula", font=("Roboto", 12), text_color="gray")
        self.label_instrucao.pack(pady=(0, 10))

        self.entrada_cidade = ctk.CTkEntry(self.frame, placeholder_text="Ex: São Mateus, Espírito Santo", width=250, height=40)
        self.entrada_cidade.pack(pady=10)

        self.botao = ctk.CTkButton(self.frame, text="Consultar", command=self.buscar_clima, font=("Roboto", 14, "bold"), height=40)
        self.botao.pack(pady=20)

        # Área de Exibição dos Resultados
        self.icon_label = ctk.CTkLabel(self.frame, text="") # Aqui ficará a imagem
        self.icon_label.pack(pady=10)

        self.res_temp = ctk.CTkLabel(self.frame, text="--°C", font=("Roboto", 50, "bold"))
        self.res_temp.pack()

        self.res_desc = ctk.CTkLabel(self.frame, text="Digite uma cidade acima", font=("Roboto", 16), text_color="gray")
        self.res_desc.pack(pady=(0, 10))

        self.res_umidade = ctk.CTkLabel(self.frame, text="Umidade: --%", font=("Roboto", 14), text_color="gray")
        self.res_umidade.pack(pady=(0, 10))

        self.res_localizacao = ctk.CTkLabel(self.frame, text="", font=("Roboto", 11), text_color="gray")
        self.res_localizacao.pack(pady=(0, 10))

        # Sessão com retry para tolerar falhas transitórias/servidor lento
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _traduzir_mensagem_api(self, msg: str) -> str:
        if not msg:
            return "Erro na API."

        m = msg.strip().lower()

        # Mapeamentos comuns (mensagens da WeatherAPI e similares)
        if "no matching location" in m or "location not found" in m:
            return "Cidade não encontrada."
        if "invalid api key" in m or "api key" in m and "invalid" in m:
            return "Chave de API inválida." 
        if "no api key" in m or "key" in m and "missing" in m:
            return "Chave de API ausente." 
        if "quota" in m or "rate limit" in m or "exceed" in m:
            return "Limite de requisições excedido. Tente novamente mais tarde." 
        if "invalid request" in m or "bad request" in m:
            return "Requisição inválida." 

        # Se a mensagem já estiver em português, retornar capitalizada
        if any(x in m for x in ["cidade", "chave", "limite", "requis" ]):
            return msg.capitalize()

        # Caso não reconheça, fornecer uma tradução genérica mantendo a mensagem original
        return f"Erro: {msg}"

    def buscar_clima(self):
        cidade = self.entrada_cidade.get().strip()

        # Validar entrada: rejeitar se for vazio ou muito curto (ex: nomes inválidos como "é", "mae")
        if not cidade or len(cidade) < 3:
            self.res_desc.configure(text="Digite uma cidade válida (mínimo 3 caracteres).", text_color="orange")
            self.res_temp.configure(text="--°C")
            self.res_umidade.configure(text="Umidade: --%", text_color="gray")
            self.res_localizacao.configure(text="")
            return

        api_key = "1986d494aa064214a6e195755260101"
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={cidade}&lang=pt"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            dados = response.json()

            # API pode devolver um objeto de erro dentro do JSON
            if isinstance(dados, dict) and dados.get("error"):
                api_msg = dados["error"].get("message", "Cidade não encontrada")
                self.res_desc.configure(text=self._traduzir_mensagem_api(api_msg), text_color="red")
                self.res_temp.configure(text="--°C")
                self.res_localizacao.configure(text="")
                return

            # Extração
            temp = dados["current"]["temp_c"]
            condicao = dados["current"]["condition"]["text"]
            umidade = dados["current"].get("humidity", "--")
            icon_url = "http:" + dados["current"]["condition"]["icon"]
            
            # Extração de localização
            localizacao = dados.get("location", {})
            nome_cidade = localizacao.get("name", "")
            estado = localizacao.get("region", "")
            pais = localizacao.get("country", "")
            lat = localizacao.get("lat", "")
            lon = localizacao.get("lon", "")
            
            localizacao_texto = f"{nome_cidade}, {estado}, {pais} (Lat: {lat}, Lon: {lon})"

            # Atualizar Texto
            self.res_temp.configure(text=f"{int(temp)}°C")
            self.res_desc.configure(text=condicao.capitalize(), text_color="white")
            self.res_umidade.configure(text=f"Umidade: {umidade}%", text_color="white")
            self.res_localizacao.configure(text=localizacao_texto, text_color="gray")

            # Carregar e exibir o ícone do clima (com timeout)
            try:
                icon_resp = self.session.get(icon_url, timeout=5)
                icon_resp.raise_for_status()
                img_data = icon_resp.content
                img = Image.open(BytesIO(img_data))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                self.icon_label.configure(image=ctk_img)
            except (req_exc.Timeout, req_exc.ConnectTimeout, req_exc.ReadTimeout):
                # servidor de ícone lento — ignorar ícone
                self.icon_label.configure(text="")
            except Exception:
                self.icon_label.configure(text="")

        except (req_exc.ConnectTimeout, req_exc.ReadTimeout, req_exc.Timeout):
            self.res_desc.configure(text="Tempo esgotado. Servidor lento ou sem resposta.", text_color="orange")
            self.res_temp.configure(text="--°C")
            self.res_umidade.configure(text="Umidade: --%", text_color="gray")
            self.res_localizacao.configure(text="")
        except req_exc.ConnectionError:
            self.res_desc.configure(text="Sem conexão com a internet.", text_color="red")
            self.res_temp.configure(text="--°C")
            self.res_umidade.configure(text="Umidade: --%", text_color="gray")
            self.res_localizacao.configure(text="")
        except requests.HTTPError as e:
            # Tentar extrair mensagem mais útil do corpo JSON retornado pela API
            api_msg = None
            if e.response is not None:
                try:
                    err_json = e.response.json()
                    if isinstance(err_json, dict):
                        if err_json.get("error"):
                            api_msg = err_json["error"].get("message")
                        else:
                            api_msg = err_json.get("message")
                except ValueError:
                    api_msg = None

            if api_msg:
                self.res_desc.configure(text=self._traduzir_mensagem_api(api_msg), text_color="red")
            else:
                code = e.response.status_code if e.response is not None else "?"
                self.res_desc.configure(text=f"Erro no servidor: {code}", text_color="red")

            self.res_temp.configure(text="--°C")
            self.res_umidade.configure(text="Umidade: --%", text_color="gray")
            self.res_localizacao.configure(text="")
        except (ValueError, KeyError, TypeError):
            self.res_desc.configure(text="Cidade não encontrada ou resposta inválida.", text_color="red")
            self.res_temp.configure(text="--°C")
            self.res_umidade.configure(text="Umidade: --%", text_color="gray")
            self.res_localizacao.configure(text="")
        except Exception:
            self.res_desc.configure(text="Erro inesperado. Tente novamente.", text_color="red")
            self.res_temp.configure(text="--°C")
            self.res_umidade.configure(text="Umidade: --%", text_color="gray")
            self.res_localizacao.configure(text="")

if __name__ == "__main__":
    app = AppClima()
    app.mainloop()