import time
import numpy as np
from typing import List, Dict
from math import radians, cos, sin, sqrt, atan2
from rasterio import open 
from rasterio.windows import Window

class ElevationProfile(object):
    def __init__(self, path: str):
        self.ds = open(path)
        self.meta = self.ds.meta

    def get_info(self)->Dict:
        return {
            "width": self.ds.width,
            "height": self.ds.height,
            "borde-izq": self.ds.bounds.left,
            "borde-der": self.ds.bounds.right,
            "borde-arr": self.ds.bounds.top,
            "borde-abj": self.ds.bounds.bottom,
            "centro": self.ds.lnglat(),
            "metadata": self.meta
        }

    @staticmethod
    def _haversine(lon_a: float, lat_a: float, lon_b: float, lat_b: float) -> float:
        """
        Calcula la distancia (en metros) entre dos puntos geográficos usando la fórmula de Haversine.
        """
        radius = 6371000  # Radio de la Tierra en metros
        phi1, phi2 = radians(lat_a), radians(lat_b)
        dphi = radians(lat_b - lat_a)
        dlambda = radians(lon_b - lon_a)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return radius * c

    @staticmethod
    def _bresenham_line(x0:int, y0:int, x1:int, y1:int):
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        if dx > dy:
            err = dx // 2
            while x != x1:
                points.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy // 2
            while y != y1:
                points.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        points.append((x1, y1))
        return points

    @staticmethod
    def get_elevation_profile(coords: Dict) -> Dict[str, List[float] | float]:
        """
        Devuelve el perfil de elevación entre dos puntos.
        Args:
            coords: Diccionario con 'beginP' y 'endP', cada uno con 'latitude' y 'longitude'.
        """
        start = time.monotonic()
        # Friendly name
        lat1 =  float(coords['beginP']['latitude'])
        lon1 =  float(coords['beginP']['longitude'])
        lat2 =  float(coords['endP']['latitude'])
        lon2 =  float(coords['endP']['longitude'])
        # Read file
        # ds = open(r"C:\Users\Admin\Documents\Bolivia_1.tif")
        ds =open(r"./app/services/cocha_2.tif")
        # Ubicar puntos
        p1 = ds.index(lon1, lat1)
        p2 = ds.index(lon2, lat2)
        # Generar linea
        line_points = ElevationProfile._bresenham_line(p1[1], p1[0], p2[1], p2[0])
        cols = [pt[0] for pt in line_points]
        rows = [pt[1] for pt in line_points]
        # Definir ventana que cubre la línea
        row_min, row_max = min(rows), max(rows)
        col_min, col_max = min(cols), max(cols)
        window = Window(col_off=col_min, row_off=row_min,
                        width=col_max - col_min + 1,
                        height=row_max - row_min + 1)
        # Leer ventana del raster
        data_window = ds.read(1, window=window)
        rr_adj = [r - row_min for r in rows]
        cc_adj = [c - col_min for c in cols]
        elevations = [data_window[r, c] for r, c in zip(rr_adj, cc_adj)]
        # Calcular distancia total y generar eje x con separación uniforme
        total_distance_m = ElevationProfile._haversine(lon1, lat1, lon2, lat2)
        x_distances = [i * total_distance_m / (len(elevations) - 1) for i in range(len(elevations))]
        stop =  time.monotonic()
        print("Elapsed_time:",stop-start)
        return {
            "elevations": elevations,
            "distances": x_distances,
            "total_distance": total_distance_m
        }
    @staticmethod
    def get_single_elevation(coords: Dict) -> float:
        with open("./app/services/cocha_2.tif") as ds:
        # with open(r"C:\Users\Admin\Documents\Bolivia_1.tif") as ds:
            # Ubicar puntos
            row, col = ds.index(float(coords['longitude']), float(coords['latitude']))
            
            # Crear una ventana pequeña de 1x1 para obtener el valor de elevación
            window = Window(col_off=col, row_off=row, width=1, height=1)
            
            # Leer solo el valor del píxel en la ventana
            value = ds.read(1, window=window)[0, 0]
        return value
    @staticmethod
    def conv_float_32_to_float_64(params: List[np.float32]) -> List[np.float64]:
        """
        Convierte una lista de float32 a float64.
        """
        return [np.float64(x) for x in params]
