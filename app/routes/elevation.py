# elevation.py
# from datetime import datetime
from typing import Dict,List
from flask import Blueprint, request, jsonify, send_file
import numpy as np
from app.utils import utilities as res
from app.services.DEM import ElevationProfile
import io
from rasterio import open as rs_open
from rasterio.windows import from_bounds
# from app.services.propagation_models.fspl import FSPLModel
elevation_bp= Blueprint('elevation', __name__)
@elevation_bp.post("/")
def post_elevations():
    ## METHOD NOT_IMPLEMENTED
    response= res.generate_failed_url_not_found()
    return jsonify(response), 405

# Only elevations, not profile
@elevation_bp.get("/")
def get_elevations():
    ## TODO! VALIDACIONES REQUEST PARAMS
    lot_begin = request.args.get('lotBegin')
    lat_begin = request.args.get('latBegin')
    lot_end = request.args.get('lotEnd')
    lat_end = request.args.get('latEnd')
    coords: Dict = {
        "beginP": {
            "latitude": lat_begin,
            "longitude": lot_begin
        },
        "endP": {
            "latitude": lat_end,
            "longitude": lot_end
        }
    }
    data: Dict = ElevationProfile.get_elevation_profile(coords)
    elevationsfp32: List[float] = data['elevations']
    elevations: List[float] = ElevationProfile.conv_float_32_to_float_64(elevationsfp32)
    response= res.generate_response_all(
        {
            "elevations": elevations,
            "distances_elevations": data["distances"]
        }
        ,len(data['elevations']))
    return jsonify(response),200
@elevation_bp.post("/profile")
def get_profile():
    # [frequency, heightA, heightB,[beginP[latitude,longitude],endP[latitude,longitude]]]
    try:
        data = request.get_json()
        frequency_ghz = data['frequency']/ 1000
        elevationA = ElevationProfile.get_single_elevation(data['beginP'])
        elevationB = ElevationProfile.get_single_elevation(data['endP'])
        heightA = data['heightA']
        heightB = data['heightB']
        beginP = data['beginP']
        endP = data['endP']
        coords = {
            'beginP': beginP,
            'endP': endP,
        }
        dataElevation: Dict = ElevationProfile.get_elevation_profile(coords)
        y1 = heightA + elevationA
        y2 = heightB + elevationB
        
        d1 = np.array(dataElevation['distances'])
        d2 = dataElevation['total_distance'] - d1
        straightfp32 = y1 + (y2 - y1) * (d1 / dataElevation['total_distance'])

        waln = 3e8 / (frequency_ghz* 1e9)
        fresnel_radius = np.sqrt((waln * d1 * d2) / dataElevation['total_distance'])
        fresnel_overfp32 = straightfp32 + fresnel_radius
        fresnel_underfp32 = straightfp32 - fresnel_radius
        elevationsfp32 = dataElevation['elevations']
        straight: List[float] = ElevationProfile.conv_float_32_to_float_64(straightfp32)
        elevations: List[float] = ElevationProfile.conv_float_32_to_float_64(elevationsfp32)
        fresnel_over: List[float] = ElevationProfile.conv_float_32_to_float_64(fresnel_overfp32)
        fresnel_under: List[float] = ElevationProfile.conv_float_32_to_float_64(fresnel_underfp32)
        # Verificación de línea de vista (LOS)
        los_clear = np.all(np.array(elevations) <= np.array(straight))
        response= res.generate_response_all(
        {
            'distances_elevations': dataElevation['distances'],
            'distances_graphs': dataElevation['distances'],
            'elevations': elevations,
            'fresnel_under_line': fresnel_under,
            'fresnel_over_line': fresnel_over, 
            'straight_line': straight,
            'line_of_sight': bool(los_clear)
        }
        ,len(elevations))
        return jsonify(response), 200
    except Exception as e:  # noqa: F841
        print(e)
        response = res.generate_failed_message_exception()
        return jsonify(response), 500
@elevation_bp.post("/window")
def get_elevation_image():
    import matplotlib
    matplotlib.use('Agg')  # Backend sin GUI
    import matplotlib.pyplot as plt
    from matplotlib import cm

    try:
        data = request.get_json()
        beginP = data.get("beginP")
        endP = data.get("endP")
        range_value = data.get("range", 5000)

        if not beginP or not endP:
            return jsonify({"error": "Parámetros beginP y endP son requeridos"}), 400

        dem_path = "./app/services/cocha.tiff"
        with rs_open(dem_path) as src:
            min_lon = min(beginP["longitude"], endP["longitude"]) - range_value / 111320
            max_lon = max(beginP["longitude"], endP["longitude"]) + range_value / 111320
            min_lat = min(beginP["latitude"], endP["latitude"]) - range_value / 110540
            max_lat = max(beginP["latitude"], endP["latitude"]) + range_value / 110540

            window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform=src.transform)
            dem_array = src.read(1, window=window)

        # Crear imagen de colormap
        fig, ax = plt.subplots(figsize=(6, 6))
        cax = ax.imshow(dem_array, cmap=cm.terrain, origin='upper')
        ax.axis("off")
        fig.colorbar(cax, ax=ax, orientation='vertical', label='Elevación (m)')

        # Agregar marcadores de inicio y fin
        # Convertir coordenadas a índice de matriz (aproximación simple)
        nrows, ncols = dem_array.shape
        lon_ratio_start = (beginP["longitude"] - min_lon) / (max_lon - min_lon)
        lat_ratio_start = (max_lat - beginP["latitude"]) / (max_lat - min_lat)
        lon_ratio_end = (endP["longitude"] - min_lon) / (max_lon - min_lon)
        lat_ratio_end = (max_lat - endP["latitude"]) / (max_lat - min_lat)

        col_start = int(lon_ratio_start * ncols)
        row_start = int(lat_ratio_start * nrows)
        col_end = int(lon_ratio_end * ncols)
        row_end = int(lat_ratio_end * nrows)

        ax.scatter([col_start], [row_start], color='red', marker='o', s=100, label='Inicio')
        ax.scatter([col_end], [row_end], color='red', marker='x', s=100, label='Fin')
        ax.legend(loc='upper right')

        # Guardar imagen en memoria
        img_bytes = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        img_bytes.seek(0)

        return send_file(
            img_bytes,
            mimetype='image/png',
            as_attachment=False,
            download_name='dem_colormap.png'
        )

    except Exception as e:
        print(e)
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@elevation_bp.get("/<id>")
def get_elevation():
    ## METHOD NOT_IMPLEMENTED
    response= res.generate_failed_url_not_found()
    return jsonify(response), 405
@elevation_bp.put("/<id>")
def put_elevation():
    ## METHOD NOT_IMPLEMENTED
    response= res.generate_failed_url_not_found()
    return jsonify(response), 405
@elevation_bp.delete("/<id>")
def delete_elevation():
    ## METHOD NOT_IMPLEMENTED
    response= res.generate_failed_url_not_found()
    return jsonify(response), 405