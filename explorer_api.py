import requests

# La API del Banco Mundial funciona así:
# /country/{código_país}/indicator/{código_indicador}
# NY.GDP.MKTP.KD.ZG = crecimiento del PIB (% anual)

url = "https://api.worldbank.org/v2/country/ARG/indicator/NY.GDP.MKTP.KD.ZG"
params = {
    "format": "json",
    "date": "2018:2026"
}

response = requests.get(url, params=params)
data = response.json()

# La API devuelve una lista de 2 elementos: [metadata, datos]
print(data[0])  # metadata (info de paginación)
print(data[1][:3])  # primeros 3 registros de datos