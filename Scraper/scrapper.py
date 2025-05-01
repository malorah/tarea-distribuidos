import time
import requests
import pymongo

#Cosas a borrar
keys_to_remove = [
    "comments",
    "reportDescription",
    "nThumbsUp",
    "reportBy",
    "reportByMunicipalityUser",
    "reportRating",
    "reportMood",
    "fromNodeId",
    "toNodeId",
    "magvar",
    "additionalInfo",
    "wazeData",
    "endTimeMillis",
    "startTimeMillis",
    "startTime",
    "endTime"
]

def remove_keys_from_dict(data, keys_to_remove):
    """Función recursiva para eliminar claves específicas de un diccionario."""
    if isinstance(data, list):
        for item in data:
            remove_keys_from_dict(item, keys_to_remove)
    elif isinstance(data, dict):
        for key in keys_to_remove:
            if key in data:
                del data[key]

        for key in data:
            if isinstance(data[key], (dict, list)):
                remove_keys_from_dict(data[key], keys_to_remove)

def scrape_traffic_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si la respuesta contiene un estado HTTP de error
        data = response.json()

        # Eliminar los atributos innecesarios
        remove_keys_from_dict(data, keys_to_remove=keys_to_remove)

        return data

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a {url}: {e}")
        return {}

def update_all_json(data,key,value): 
    #Agrega un elemento y un valor a un diccionario
    for elem in data:
        elem.update({key:value})

def unicos(datos1,datos2):
    #Esta funcion filtra los datos obtenidos en base a su id para solo obtener datos unicos
    indice = set({}) #Set para buscar mas rapido (es la idea)
    for dato in datos1:
        indice.add(dato["id"])

    for dato in datos2:
        #Si no se encuentra el indice en los datos anteriores, agrega la entrada
        if(dato["id"] not in indice):
            indice.add(dato["id"])
            datos1.append(dato)
    return datos1

def scrap_waze(N:int,intentos:bool,datos_unicos:bool = True):
    """
    @param N : Numero.
    @param intentos : si True, N es numero de intentos exitosos de scraping, sino, N es cantidad de datos scrapeados.
    @param datos_unicos : Si se obtienen solo entradas unicas de datos (diferente id).
    """
    # Establecer la URL predeterminada
    url = "https://www.waze.com/live-map/api/georss?top=-33.37380423388275&bottom=-33.418863153828454&left=-70.73255538940431&right=-70.54201126098634&env=row&types=alerts,traffic"
    
    retorno = {}
    print(f"Scrapeando datos de la URL: {url}")
    c = 0 # c es numero de intento exitoso
    print("Se terminara de scrapear cuando",end=" ")
    if(intentos):print("se realicen",N,"intentos exitosos de scraping.")
    else:print("se obtengan",N,"entradas de datos diferentes.")

    while ((len(retorno)<N and not intentos) or (c<N and intentos)):
        if(intentos):print("Intento numero",c+1)
        try:
            print("Extrayendo datos de tráfico...")
            traffic_data=scrape_traffic_data(url)


            # Separar los datos en dos partes: alerts y jams
            #print("Separando alertas y congestiones")
            alerts_data = traffic_data.get("alerts", [])
            jams_data = traffic_data.get("jams", [])

            #print("Hay",len(alerts_data),"alertas y",len(jams_data),"congestiones")
            
            #Se agrega el campo isAlert para identificar si se trata de una alerta o no (un jam)
            update_all_json(alerts_data,"isAlert",True)
            update_all_json(jams_data,"isAlert",False)
            
            #Se filta solo por datos cuyo id sea unico (no hay duplicados)
            if(datos_unicos):
                if(len(retorno) == 0): retorno = alerts_data
                else:retorno = unicos(retorno,alerts_data)
                retorno = unicos(retorno,jams_data)
            else:
                if(len(retorno) == 0): retorno = alerts_data
                else:retorno = retorno + alerts_data
                retorno = retorno + jams_data
            
            print("Se encontraron",len(alerts_data)+len(jams_data),"entradas.")
            print("Hay un total de",len(retorno),"entradas diferentes.")
            print("Faltan",end=" ")
            if(intentos):print(N-c,"intentos exitosos.")
            else:print(N-len(retorno),"datos.")
            c += 1
            time.sleep(10)
        except Exception as e:
            print(f"Error en el scraper: {e}")
            time.sleep(2)

    return retorno 

if __name__ == "__main__":
    total = 0 #Datos totales insertados en la db
    maximo = 10000 #Datos maximos a insertar en la db
    N = 10 #Tanda de datos a insertar simultaneamente o intentos a realizar
    intentos = False #Si true, intentos a realizar, si no, cantidad de datos a insertar
    datos_unicos = True # si true solo insertar datos con ids diferentes
    print("Iniciando conexion a almacenamiento")
    client = pymongo.MongoClient()
    client.server_info()
    db = client.db
    collection = db["waze"]
    print("Conexion exitosa.")
    while total<maximo:
        data=scrap_waze(N,intentos,datos_unicos)
        total+=len(data)
        print("Enviando",len(data),"entradas a la base de datos.")
        collection.insert_many(data)

