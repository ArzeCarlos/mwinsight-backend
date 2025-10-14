from math import log10, pi, atan2, sin, cos, sqrt, acos
from typing import Dict,List
import matplotlib.pyplot as plt
import numpy as np
import time
from app.services.DEM import ElevationProfile

class FSPLModel:
    @staticmethod
    def link_budget_atenuattion(params:Dict)->float:
        """ frequency -> [MHz], distance[Km]"""
        distance=float(params["distance_km"])
        frequency=float(params["frequency_mhz"])
        num= (4 * pi * 10**9)
        den= (3 * 10**8)
        attenuation= 20 * log10(num/den) + 20 * log10(frequency) + 20 * log10(distance)# eq (9-20a)-> Tomasi or ITU-R P.525
        return attenuation
    @staticmethod
    def link_budget(params:Dict)->float:
        #In some cases radome attenuation
        #Loss_per_meter maybe is not the best name, more simple user insert total loss in cable.
        cables_attenuation = 2 * params["loss_per_meter"] #Must be fixed, only simetrical y htx=htx
        connector_atenuattion = 2 * params["insertion_loss"] #Must be fixed, different insertion_loss
        gain_antenna_a = params["gain_a"]
        gain_antenna_b= params["gain_b"]
        fspl_attenuation= params["fspl_attenuation"]
        rsl= params["ptx"] - cables_attenuation - connector_atenuattion + gain_antenna_a + gain_antenna_b - fspl_attenuation
        return rsl
    @staticmethod
    def pire(params:Dict)->float:
        return params["ptx"]+params["gain"]-params["loss_per_meter"]-params["insertion_loss"]
    ## Fade margin use to calculate SNR
    @staticmethod
    def _to_radians(angle:float)->float:
        return angle * pi / 180
    @staticmethod
    def azimuth(initial_point:Dict, end_point:Dict)->float:
        """ Great circle navigaiton azimuth formula """
        lat_begin = FSPLModel._to_radians(initial_point["latitude"])
        lon_begin = FSPLModel._to_radians(initial_point["longitude"])
        lat_end = FSPLModel._to_radians(end_point["latitude"])
        lon_end = FSPLModel._to_radians(end_point["longitude"])
        delta_lon = lon_end - lon_begin
        y = sin(delta_lon)*cos(lat_end)
        x = cos(lat_begin)*sin(lat_end)-sin(lat_begin)*cos(lat_end)*cos(delta_lon)
        azimuth = atan2(y,x)
        return azimuth
    @staticmethod
    def visibility_distance(height_tx:float, height_rx:float, refraction_index:float=4/3)->float:
        return 3.57 * (sqrt(refraction_index*height_tx)+sqrt(refraction_index*height_rx))# eq(3.7.4)
    @staticmethod
    # def reflection_model(total_length:float, visibility_distance:float, height_tx:float, height_rx:float, refraction_index:float)->Dict:
    #     """Used when (total_length< visibility_distance), plain terrain"""
    #     if total_length> visibility_distance:
    #         return {}
    #     else:
    #         p= 2/sqrt(3) * sqrt((6.37*refraction_index*(height_rx+height_tx)+(d/2))**2)# eq(3.7.9)
    #         if height_tx >= height_rx:
    #             phi = acos((12.74 * refraction_index * (height_tx-height_rx)*d) / p**3)# eq(3.7.10)(a)
    #             d1 = total_length / 2 + p * cos(pi / phi / 3)  # eq(3.7.8)
    #             d2= d-d1
    #         else:
    #             phi = acos((12.74 * refraction_index * (height_rx - height_tx) * d) / p ** 3)# eq(3.7.10)(b)
    #             d2= total_length / 2 + p * cos(pi / phi / 3)  # eq(3.7.8)
    #             d1 = d - d2
    #         return {
    #             "d1": d1,
    #             "d2": d2,
    #         }
    @staticmethod
    def frequency_to_wavelength(frequency:float)->float:
        light_speed = 3*(10**8)
        return light_speed / (frequency * 1e6)
    @staticmethod
    def radius_fresnel(n:int,wavelength:float,d1: float, d2: float)->float:
        return sqrt((n*wavelength*d1*d2)/(d1+d2))
    @staticmethod
    def radius_zone_n_fresnel(frequency: float, n:int, d1: float, d2:float)->float:
        """ frequency: [MHz]"""
        wavelength= FSPLModel.frequency_to_wavelength(frequency)
        radius_fresnel_values=[]
        limit= range(1,n+1)
        for i in limit:
            radius_fresnel_values.append(FSPLModel.radius_fresnel(i,wavelength,d1,d2))
        return radius_fresnel_values
    @staticmethod
    def _ghz_to_mhz(frequency:float)->float:
        return frequency*1000
    @staticmethod
    def _mhz_to_ghz(frequency:float)->float:
        return frequency/1000
    @staticmethod
    def fade_margin_barnett_vigants(distance: float, frequency:float, rugosity_factor:float, convertion_factor:float,
                                    reliability_factor: float)->float:
        """note: frequency in [GHz]
        Rugosity factor:
        4 for water or very smooth terrain
        1 for average terrain
        0.25 for very rough and mountainous terrain
        Conversion factor:
        1 to convert annual availability to the worst month base
        0.5 for warm or humid areas
        0.25 for average continental areas
        0.125 for very dry or mountainous areas
        reliability -> decimal format"""
        fade_margin = 30 * log10(distance) + 10 * log10(6 * rugosity_factor * convertion_factor * frequency) - 10 * log10(1 - reliability_factor) - 70
        return fade_margin

    @staticmethod
    def fade_margin_variant_bv(distance: float, frequency: float, rugosity_factor: float, conversion_factor: float,
                               reliability_factor: float) -> float:
        """
            frequency in [MHz]
        """
        fade_margin = (-30 * log10(distance)) + \
                      (-10 * log10(6 * rugosity_factor * conversion_factor * frequency / 1000)) + \
                      (10 * log10(1 - (reliability_factor / 100))) + 70
        return fade_margin

    ## PoC_Section
    @staticmethod
    def first_fresnel_curve(waln: float,distance_m: float,data: Dict, n_samples:int) -> Dict:
        """ This method was modified to make line_straight_calcs-> v1
            This method was modified to make rotation fresnel_graph-> v2
        """
        curves={}
        t0 = time.perf_counter()
        # Muestras uniformes a lo largo del enlace
        d1 = np.linspace(0.0, distance_m, n_samples)
        d2 = distance_m - d1

        # Recta entre antenas
        y1 = data["origin_height"] + data["origin_antenna_height"]
        y2 = data["end_height"] + data["end_antenna_height"]
        straight = y1 + (y2 - y1) * (d1 / distance_m)

        # Primer radio de Fresnel (positivo y negativo)
        fresnel_radius = np.sqrt((waln * d1 * d2) / distance_m)
        fresnel_over = straight + fresnel_radius
        fresnel_under = straight - fresnel_radius

        curves["x_axis"]= d1
        curves["straight_line"]=straight
        curves["fresnel_over_line"]=fresnel_over
        curves["fresnel_under_line"]=fresnel_under

        elapsed = (time.perf_counter() - t0) * 1e3  # ms
        print(f"Delay cálculo puntos linea y fresnel:{elapsed:.4f} ms")
        ##Debugging
        # plt.figure(figsize=(10, 6))
        # plt.plot(curves["x_axis"], curves["under_line"], label=f'Curva superior ',color="yellow")
        # plt.plot(curves["x_axis"], curves["below_line"], label=f'Curva inferior ',color="blue")
        # plt.title(f'Zonas de Fresnel para {waln}')
        # plt.xlabel('Distancia')
        # plt.ylabel('Radio de la zona de Fresnel')
        # plt.grid(True)
        # plt.legend()
        # plt.show()
        return curves
    @staticmethod
    def criterion_fresnel_microwave(compress_factor:float,curves:Dict)->Dict:
        # under_line and below_line lengths must be equals
        return {
            "x_axis" : curves["x_axis"],
            "under_line": compress_factor*curves["under_line"],
            "below_line": compress_factor*curves["below_line"]
        }
    ##Plotting for testing proposes
    @staticmethod
    def plot_fresnel_and_elevation():
        coords: Dict = {
            "beginP": {
                "latitude": -16.501141,
                "longitude": -68.142043
            },
            "endP": {
                "latitude": -17.967905,
                "longitude": -67.074510
            }
        }
        data: Dict= ElevationProfile.get_elevation_profile(coords)
        print(data)
        elevationsfp32: List[float]= data['elevations']
        elevations: List[float]= ElevationProfile.conv_float_32_to_float_64(elevationsfp32)
        frequency = 2000
        wavelength = FSPLModel.frequency_to_wavelength(frequency)
        params = {
            "origin_height": elevations[0],
            "origin_antenna_height": 60,
            "end_height": elevations[-1],
            "end_antenna_height": 40
        }
        print(len(elevations))
        data_curves=FSPLModel.first_fresnel_curve(wavelength,data["total_length"],params ,1000)
        print(len(3*data_curves["x_axis"])+len(data["distances"]))
        # debugging
        plt.figure(figsize=(10, 6))
        plt.plot(data['distances'], elevations,color="blue")
        plt.plot(data_curves['x_axis'], data_curves["fresnel_over_line"], color="red")
        plt.plot(data_curves['x_axis'], data_curves["straight_line"], color="green")
        plt.plot(data_curves['x_axis'], data_curves["fresnel_under_line"], color="red")
        plt.title('Elevaciones')
        plt.xlabel('Distancia')
        plt.ylabel('Altura')
        plt.grid(True)
        plt.show()
