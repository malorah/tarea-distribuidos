import pandas as pd
import os

def guardado(datos,datos_unicos = True):
    output = "db.xlsx"
    
    if os.path.exists(output):
        #se guardan las entradas antiguas y las entradas con id nuevo
        print("Se encontraron datos previos.")
        df = pd.read_excel(output)
        datos2 = df.to_dict('records')
        if(datos_unicos):datos1 = unicos(datos,datos2)
        else:datos1 = datos + datos2
        df = pd.DataFrame(datos1)
        print("Se agregaron",len(datos1)-len(datos),"datos nuevos.")
        df.to_excel(output)
    else:
        print("No se encontraron datos previos.")
        print("Guardando datos actuales.")
        df = pd.DataFrame(datos)
        df.to_excel(output,index=False)


def unicos(datos1,datos2):
    indice = set({}) #Set para buscar mas rapido (es la idea)
    for dato in datos1:
        indice.add(dato["id"])

    for dato in datos2:
        if(dato["id"] not in indice):
            indice.add(dato["id"])
            datos1.append(dato)
    return datos1