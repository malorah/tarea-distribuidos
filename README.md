# Sistema Distribuido de Gestión de Tráfico

Sistema completo para procesamiento de eventos de tráfico con:
- Scraper de datos reales
- Generador de eventos sintéticos
- Caché de alto rendimiento
- Almacenamiento persistente

## 🚀 Instalación Rápida

```bash
git clone https://github.com/malorah/tarea-distribuidos.git
cd tarea-distribuidos
docker-compose up -d --build
```

Puede modificar los enviroments del archivo docker-compose:
# Scrapper
SCRAP_INTERVAL=60
SCRAP_REGION="santiago"

# Generador
POISSON_LAMBDA=5
NORMAL_MEAN=100
EVENT_TYPES="ACCIDENT,JAM,HAZARD"

# Caché
CACHE_TTL=7200
MAX_CACHE_SIZE=5000

1. Scrapper
```bash
docker-compose up -d --build scraper
```
2. Generador de trafico
```bash
docker-compose up -d --build traffic-generator
```

3. Sistema de cache
```bash
docker-compose up -d redis cache-service
```

4.Almacenamiento con mongoDB
```bash
docker-compose up -d almacenamiento
```
📊 Monitorización
# Ver logs en tiempo real
```bash
docker-compose logs -f
```
# Acceder a Redis CLI
```bash
docker exec -it redis_cache redis-cli
```

# Conectar a MongoDB
```bash
docker exec -it mongo_almacenamiento mongosh -u admin -p user
```
#Para finalizar los servicios docker
```bash
docker-compose down
```

# Extra
#Opcionalmente se pueden crear y levantar todos los servicios al mismo tiempo con el comando
```bash
docker-compose up -d --build
```