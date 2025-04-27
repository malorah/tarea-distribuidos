from scrapper import scrap_waze
from almacenamiento import guardado

N = 200 #Al menos 10000 eventos almacenados pide la tarea

datos = scrap_waze(N,False)
guardado(datos)