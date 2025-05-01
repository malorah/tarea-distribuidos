import os
import time
import random
from datetime import datetime
import numpy as np
from Cache.cache import TrafficCache
from typing import Dict, Any, Optional, List

class TrafficGenerator:
    def __init__(self):
        self.cache = TrafficCache()
        self.poisson_lambda = float(os.getenv('POISSON_LAMBDA', 3))
        self.normal_mean = float(os.getenv('NORMAL_MEAN', 50))
        self.normal_stddev = float(os.getenv('NORMAL_STDDEV', 15))
        self.generation_interval = float(os.getenv('GENERATION_INTERVAL', 5))

    def _generate_event(self) -> Dict[str, Any]:
        """Genera un evento de tráfico simulado"""
        event_types = ['ACCIDENT', 'JAM', 'ROAD_CLOSED', 'HAZARD']
        event_id = f"evt_{int(time.time())}_{random.randint(1000, 9999)}"
        
        return {
            'id': event_id,
            'type': random.choice(event_types),
            'timestamp': datetime.now().isoformat(),
            'intensity': max(0, int(np.random.normal(self.normal_mean, self.normal_stddev))),
            'duration': int(np.random.poisson(self.poisson_lambda)),
            'location': {
                'lat': round(-33.45 + random.uniform(-0.1, 0.1), 6),
                'lon': round(-70.66 + random.uniform(-0.1, 0.1), 6)
            },
            'radius': round(random.uniform(0.1, 1.0), 2)
        }

    def run(self):
        """Ejecuta el generador de tráfico continuamente"""
        try:
            while True:
                num_events = np.random.poisson(self.poisson_lambda)
                
                for _ in range(num_events):
                    event = self._generate_event()
                    processed_event = self.cache.process_event(event)
                    
                    if processed_event.get('from_cache'):
                        print(f"[CACHE] Evento repetido: {processed_event['id']}")
                    else:
                        print(f"[NEW] Evento generado: {processed_event['id']}")
                
                time.sleep(self.generation_interval)
                
        except KeyboardInterrupt:
            print("\nDeteniendo generador...")
            stats = self.cache.get_cache_stats()
            print(f"\nEstadísticas finales del caché:")
            print(f"- Tamaño: {stats['size']} eventos")
            print(f"- Aciertos: {stats['hits']}")
            print(f"- Fallos: {stats['misses']}")
            print(f"- Memoria usada: {stats['memory_usage']}")

if __name__ == "__main__":
    generator = TrafficGenerator()
    generator.run()