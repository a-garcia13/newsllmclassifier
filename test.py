import json

# JSON string
json_str = '[{"_id": {"$oid": "643d05a58561915558a07392"}, "FechaHora_Extraccion": {"$date": "2021-10-14T12:50:05Z"}, "Fecha_Noticia": {"$date": "2021-10-14T12:50:05Z"}, "Cod_Url": "https://www.valoraanalitik.com/web-stories/dia-sin-iva/", "Nombre_Medio": "Valora Analitik", "Desc_Noticia": "", "Desc_Noticia_Limpia": "D\u00eda sin IVA", "Similarity_Mean": 0.002970129760730674, "Similarity_SD": 0.020154584882931915, "Max_similarity": 0.6461247199222353, "character_count": 11}]'

# Parse the JSON string
json_data = json.loads(json_str)

print(type(json_data[0]))

# Print the decoded JSON data
print(json_data)
