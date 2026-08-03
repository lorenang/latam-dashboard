import requests
import pandas as pd
from io import BytesIO

url = "https://api-cepalstat.cepal.org/cepalstat/api/v1/thematic-tree"
params = {"format": "excel", "lang": "es"}

response = requests.get(url, params=params, timeout=30)
excel_data = BytesIO(response.content)  # lo tratamos como un archivo en memoria

catalogo = pd.read_excel(excel_data)
print(catalogo.columns.tolist())
print(catalogo.head())
print(f"\nTotal de filas: {len(catalogo)}")

# Nos quedamos solo con filas que son indicadores (no categorías)
indicadores = catalogo[catalogo["type"] == "indicator"]

# Buscamos por palabras clave en el nombre
def buscar(palabra):
    resultados = indicadores[indicadores["name"].str.contains(palabra, case=False, na=False)]
    return resultados[["id", "name"]]

print("=== PIB / Crecimiento ===")
print(buscar("Producto Interno Bruto").head(15))

print("\n=== Inflación ===")
print(buscar("inflaci").head(15))

print("\n=== Déficit / Balance fiscal ===")
print(buscar("fiscal").head(15))

print("\n=== Tipo de cambio ===")
print(buscar("cambio").head(15))