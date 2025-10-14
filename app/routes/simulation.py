'''simulation.py'''
from math import fabs, pi
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
import itur.models.itu453 as ITU453
import itur.models.itu530 as ITU530
import itur.models.itu676 as ITU676
import itur.models.itu835 as ITU835
import itur.models.itu836 as ITU836
import itur.models.itu837 as ITU837
import itur.models.itu838 as ITU838
import itur.models.itu1510 as ITU1510
import itur.models.itu1511 as ITU1511
from astropy import units as u
from app.models import db, RFProjects
from app.services.DEM import ElevationProfile
from app.utils import utilities as res
from app.services.propagation_models.fspl import FSPLModel
from app.schemas.schemas import rfproject_schema_all

simulation_bp= Blueprint('simulation', __name__)

@simulation_bp.post("/Project")
def create_rfproject():
    ''' Endpoint project creation '''
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = ["name", "description"]
        allowed_fields = mandatory_fields
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        new_project = RFProjects(
            name=data['name'],
            description=data['description']
        )
        db.session.add(new_project)
        db.session.commit()
        # result = role_schema_all.dump(new_project)
        response =   res.generate_response_create_200("ok","RfProject")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@simulation_bp.get("/Project")
def get_rfprojects():
    ''' Endpoint get rf-projects'''
    try:
        valid_params = {'name'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("RFProject", unknown_params)
            return jsonify(response), 400

        name = request.args.get('name')
        stmt = (
            db.session.query(RFProjects)
        )

        if name:
            stmt_names = db.session.query(RFProjects.name).all()
            response_names = [x[0] for x in stmt_names]
            return jsonify({"names": response_names}), 200

        resultsquery = stmt.all()
        if resultsquery:
            projects_serialized = []
            for project in resultsquery:
                if project.id not in projects_serialized:
                    projects_serialized.append({
                        'id':project.id,
                        'name': project.name,
                        'description': project.description,
                        'createdAt': project.createdAt,
                        'updatedAt': project.updatedAt
                    })
            total_count = db.session.query(func.count(RFProjects.id)).scalar()
            response = res.generate_response_all(projects_serialized, total_count)
            return jsonify(response), 200
        response = res.generate_failed_msg_not_found_200("RFProject")
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@simulation_bp.put("/Project/<int:project_id>")
def update_rfproject(project_id: int):
    ''' End point update RfProject'''
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        rfproject = db.session.query(RFProjects).where(RFProjects.id == project_id).scalar()

        if not rfproject:
            response = res.generate_failed_msg_not_found_404("Role")
            return jsonify(response), 404

        allowed_fields = ['name', 'description']
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields(name="Update_Project")
            return jsonify(response), 400

        rfproject.name = data["name"]
        rfproject.description = data["description"]
        db.session.commit()
        result =rfproject_schema_all.dump(rfproject)
        response = res.generate_response_update_200(result,'RFProject')
        return jsonify(response), 200

    except DatabaseError as db_error:
        print(db_error)
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e: # pylint: disable=broad-exception-caught
        print(e)
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@simulation_bp.delete("/Project/<int:project_id>")
def delete_rfproject(project_id):
    ''' End point delete RfProject'''
    try:
        rf_project = db.session.get(RFProjects, project_id)
        if not rf_project:
            response = res.generate_failed_msg_not_found_404("RfProject")
            return jsonify(response), 404

        try:
            db.session.delete(rf_project)
            db.session.commit()
            response = res.generate_response_delete_200(rf_project.name)
            return jsonify(response), 200

        except DatabaseError as db_error:  # noqa: F841
            db.session.rollback()
            response = res.generate_failed_message_dberror()
            return jsonify(response), 503

        except Exception as e:  # noqa: F841
            db.session.rollback()
            response = res.generate_response_delete_500(id)
            return jsonify(response), 500

    except Exception as e: # pylint: disable=broad-exception-caught
        print(e)
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@simulation_bp.post("/")
def create_simulation():
    '''Endpoint to create a simulation. This is where the calculations are performed.'''
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = [
            "linkName", "latA", "lonA", "latB", "lonB", "heightA", "heightB", "distance",
            "gainA", "gainB", "diameterA", "diameterB", "frequency", "threshold", "powerTx",
            "cableLossA", "cableLossB", "insertionLoss", "itu530Model"
        ]
        allowed_fields = mandatory_fields
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400
        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        mean_lat = (data['latA'] + data['latB']) / 2
        mean_lon = (data['lonB'] + data['lonB']) / 2
        ## Free space loss
        data_fspl = {'frequency_mhz': data['frequency'], 'distance_km': data['distance'] }
        fspl = FSPLModel.link_budget_atenuattion( data_fspl)
        ## Refractive gradient DN65
        dn65 = ITU453.DN65(mean_lat,mean_lon,1)
        ## Factor geoclimatico y rugosidad TODO!
        ## Topographic altitude
        h =  ElevationProfile.get_single_elevation({
            'latitude': mean_lat,
            'longitude': mean_lon,
        })
        # hs = ITU1511.topographic_altitude(mean_lat,mean_lon)
        ## Presión atmosférica estándar
        p = ITU835.standard_pressure(h/1000)
        # p = ITU835.pressure(mean_lat,h/1000)
        ## Temperatura media superficial
        t = ITU835.standard_temperature(h/1000)
        # t = ITU835.temperature(mean_lat,h/1000)
        ## Densidad de vapor de agua superficial
        rho = ITU835.standard_water_vapour_density(h/1000)
        # rho = ITU835.water_vapour_density(mean_lat,h/1000)
        f = (data["frequency"]/1000) * u.GHz # pylint: disable=no-member
        ## Atenuación por gases
        gamma = ITU676.gamma_exact(f, p, rho, t)
        ## Lluvia
        r001 = ITU837.rainfall_rate(mean_lat,mean_lon,0.01)
        rain_specific_attenuation = ITU838.rain_specific_attenuation(r001, f, 0, 90)
        elev_mrad = fabs(data["heightB"]-data["heightA"])/ data["distance"]
        elev_deg = elev_mrad * (180 / pi) * 0.001
        # gamma= ITU676.gaseous_attenuation_terrestrial_path(data["distance"],f,elev_deg,rho,p,t,'approx')
        rain_att = ITU530.rain_attenuation(mean_lat, mean_lon, data["distance"], f, elev_deg,0.8)
        print(dn65,fspl,h,p,t,rho,gamma,r001, rain_att)
        response = {
            'dn65': float(dn65.value),
            'fspl': fspl,
            'gas_attenuation': float(gamma.value) * data["distance"],
            # 'gas_attenuation': float(gamma.value),
            'rainfall_rate': float(r001.value),
            'rain_attenuation': float(rain_specific_attenuation.value),
            'data': data,
        }
        return jsonify(response), 200
    except Exception as e:  # noqa: F841
        print(e)
        response = res.generate_failed_message_exception()
        return jsonify(response), 500