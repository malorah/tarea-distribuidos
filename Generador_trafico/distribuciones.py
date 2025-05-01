import numpy as np
from typing import Optional, Union

class Distributions:
    @staticmethod
    def poisson(lam: float = 1.0, size: Optional[int] = None) -> Union[int, np.ndarray]:
        """Genera valores con distribución Poisson.
        
        Args:
            lam: Parámetro lambda (media y varianza)
            size: Número de muestras a generar
            
        Returns:
            Entero o array de enteros con los valores generados
            
        Raises:
            ValueError: Si lam <= 0
        """
        if lam <= 0:
            raise ValueError("lambda debe ser mayor que 0")
        return np.random.poisson(lam, size)
    
    @staticmethod
    def normal(mean: float = 0.0, std_dev: float = 1.0, 
               min_val: Optional[float] = None, max_val: Optional[float] = None,
               size: Optional[int] = None) -> Union[float, np.ndarray]:
        """Genera valores con distribución Normal truncada.
        
        Args:
            mean: Media de la distribución
            std_dev: Desviación estándar
            min_val: Valor mínimo permitido (opcional)
            max_val: Valor máximo permitido (opcional)
            size: Número de muestras a generar
            
        Returns:
            Float o array de floats con los valores generados
            
        Raises:
            ValueError: Si std_dev <= 0
        """
        if std_dev <= 0:
            raise ValueError("std_dev debe ser mayor que 0")
            
        val = np.random.normal(mean, std_dev, size)
        
        if min_val is not None:
            val = np.maximum(min_val, val)
        if max_val is not None:
            val = np.minimum(max_val, val)
            
        return val
    
    @staticmethod
    def exponential(scale: float = 1.0, size: Optional[int] = None) -> Union[float, np.ndarray]:
        """Genera valores con distribución Exponencial.
        
        Args:
            scale: Parámetro de escala (beta = 1/lambda)
            size: Número de muestras a generar
            
        Returns:
            Float o array de floats con los valores generados
            
        Raises:
            ValueError: Si scale <= 0
        """
        if scale <= 0:
            raise ValueError("scale debe ser mayor que 0")
        return np.random.exponential(scale, size)