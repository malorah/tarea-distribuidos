import redis
import json
import time
import numpy as np
import os
from typing import Dict, Any, Optional, List
from pymongo import MongoClient

class TrafficCache:
    def __init__(self):
        # Configuración de Redis
        self.redis = redis.StrictRedis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=False  # Para manejar datos binarios
        )
        
        # Configuración de MongoDB (para persistencia a largo plazo)
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:user@almacenamiento:27017/")
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client[os.getenv("MONGO_DB", "db")]
        self.events_col = self.db["traffic_events"]
        self.cache_metrics_col = self.db["cache_metrics"]
        
        # Parámetros configurables
        self.max_cache_size = int(os.getenv('MAX_CACHE_SIZE', 1000))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
        self.cache_ttl = int(os.getenv('CACHE_TTL', 3600))  # 1 hora en segundos
        self.min_repetitions = int(os.getenv('MIN_REPETITIONS', 2))
        self.persist_threshold = int(os.getenv('PERSIST_THRESHOLD', 5))  # Veces que se repite antes de persistir en MongoDB

    # --------------------------
    # Métodos principales
    # --------------------------

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un evento de tráfico:
        1. Intenta encontrar en caché
        2. Si no está, busca eventos similares
        3. Almacena en caché si es repetitivo
        4. Persiste en MongoDB si supera el umbral
        """
        event_key = self._generate_event_key(event)
        event_data = json.dumps(event).encode('utf-8')
        
        # Paso 1: Verificar si el evento exacto está en caché
        cached = self.redis.get(event_key)
        if cached:
            self._increment_cache_hit(event_key)
            return json.loads(cached)

        # Paso 2: Buscar eventos similares
        similar_event_key = self._find_similar_event(event)
        if similar_event_key:
            self._increment_cache_hit(similar_event_key)
            return json.loads(self.redis.get(similar_event_key))

        # Paso 3: Nuevo evento - agregar al caché
        self._add_to_cache(event_key, event_data)
        
        # Paso 4: Persistir en MongoDB si es relevante
        if self._should_persist(event):
            self._persist_to_mongo(event)
        
        return event

    # --------------------------
    # Métodos auxiliares
    # --------------------------

    def _generate_event_key(self, event: Dict[str, Any]) -> str:
        """Genera clave única basada en características principales"""
        core_features = {
            'type': event.get('type'),
            'lat': round(event.get('location', {}).get('lat', 0), 4),
            'lon': round(event.get('location', {}).get('lon', 0), 4),
            'radius': round(event.get('radius', 0), 1) if 'radius' in event else 0
        }
        return f"event:{json.dumps(core_features, sort_keys=True)}"

    def _find_similar_event(self, event: Dict[str, Any]) -> Optional[str]:
        """Busca eventos similares en el caché"""
        for key in self.redis.scan_iter(match="event:*"):
            cached_event = json.loads(self.redis.get(key))
            if self._calculate_similarity(event, cached_event) >= self.similarity_threshold:
                return key
        return None

    def _calculate_similarity(self, event1: Dict, event2: Dict) -> float:
        """Calcula similitud entre eventos (0-1)"""
        vec1 = []
        vec2 = []
        
        # Comparar características numéricas
        for key in ['lat', 'lon', 'radius', 'intensity']:
            val1 = event1.get(key, 0)
            val2 = event2.get(key, 0)
            vec1.append(float(val1))
            vec2.append(float(val2))
        
        # Comparar tipo de evento
        vec1.append(hash(event1.get('type', '')))
        vec2.append(hash(event2.get('type', '')))
        
        # Calcular similitud coseno
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot / (norm1 * norm2) if (norm1 * norm2) != 0 else 0.0

    def _add_to_cache(self, key: str, data: bytes):
        """Agrega un nuevo evento al caché"""
        if self.redis.dbsize() >= self.max_cache_size:
            self._evict_oldest()
        
        self.redis.set(key, data, ex=self.cache_ttl)
        self.redis.zadd('cache_access', {key: time.time()})

    def _increment_cache_hit(self, key: str):
        """Registra un acceso al caché"""
        self.redis.zadd('cache_access', {key: time.time()})
        
        # Incrementar contador para persistencia
        count_key = f"count:{key}"
        new_count = self.redis.incr(count_key)
        
        if new_count >= self.persist_threshold:
            event = json.loads(self.redis.get(key))
            self._persist_to_mongo(event)

    def _should_persist(self, event: Dict) -> bool:
        """Determina si un evento debe persistirse en MongoDB"""
        event_key = self._generate_event_key(event)
        count = self.redis.get(f"count:{event_key}")
        return int(count or 0) >= self.persist_threshold

    def _persist_to_mongo(self, event: Dict):
        """Almacena el evento en MongoDB"""
        event['first_seen'] = time.time()
        event['last_seen'] = time.time()
        event['cache_hits'] = self.redis.get(f"count:{self._generate_event_key(event)}") or 0
        
        self.events_col.update_one(
            {'_id': event.get('id')},
            {'$set': event, '$inc': {'occurrences': 1}},
            upsert=True
        )

    def _evict_oldest(self):
        """Elimina los eventos menos accedidos"""
        oldest = self.redis.zrange('cache_access', 0, int(self.max_cache_size * 0.1))  # 10% más antiguos
        for key in oldest:
            self.redis.delete(key)
            self.redis.zrem('cache_access', key)

    def get_cache_stats(self) -> Dict:
        """Obtiene estadísticas del caché"""
        return {
            'size': self.redis.dbsize(),
            'hits': int(self.redis.get('total_hits') or 0),
            'misses': int(self.redis.get('total_misses') or 0),
            'memory_usage': self.redis.info('memory')['used_memory_human']
        }

    def clear_cache(self):
        """Limpia completamente el caché"""
        self.redis.flushdb()