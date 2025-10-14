# antenna.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Antennas,db
from app.utils import utilities as res
from app.schemas.schemas import antenna_schema_all, antennas_schema_all

antenna_bp = Blueprint('antenna', __name__)

@antenna_bp.post("/")
def post_antenna():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        mandatory_fields = ["name", "manufacturer", "frequency_band", "gain", "diameter", "projectid"]
        optional_fields = ["radome_losses", "comments"]
        allowed_fields = mandatory_fields + optional_fields

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        antenna_data = {
            "name": data['name'],
            "manufacturer": data['manufacturer'],
            "frequency_band": data['frequency_band'],
            "gain": data['gain'],
            "diameter": data['diameter'],
            "projectid": data['projectid']
        }
        if "radome_losses" in data:
            antenna_data["radome_losses"] = data["radome_losses"]
        if "comments" in data:
            antenna_data["comments"] = data["comments"]

        new_antenna = Antennas(**antenna_data)
        db.session.add(new_antenna)
        db.session.commit()
        result = antenna_schema_all.dump(new_antenna)
        response = res.generate_response_create_200(result, "antenna")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@antenna_bp.post("/<id>") # invalid route
def invalid_antenna(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@antenna_bp.get("/")
def get_antennas():
    try:
        project_id = request.args.get("projectId")
        stmt = db.session.query(Antennas)
        if project_id:
            stmt = stmt.filter(Antennas.projectid == project_id)
        resultsquery = stmt.all()
        if resultsquery:
            total_count = stmt.count()
            # total_count = db.session.query(func.count(Antennas.id)).scalar()
            antennas_data = antennas_schema_all.dump(resultsquery)
            response = res.generate_response_all(antennas_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Antennas")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@antenna_bp.get("/<id>")
def get_antenna(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        stmt = db.session.query(Antennas).where(Antennas.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            antenna_data = antenna_schema_all.dump(resultquery)
            response = res.generate_response(antenna_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Antenna")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_msg_not_found_200("antenna")
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@antenna_bp.put("/<id>")
def update_antenna(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        antenna = db.session.query(Antennas).where(Antennas.id == id).scalar()

        if not antenna:
            response = res.generate_failed_msg_not_found_404("Antenna")
            return jsonify(response), 404

        allowed_fields = ["name", "manufacturer", "frequency_band", "gain", "diameter", "radome_losses", "comments"]

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                    setattr(antenna, field, data[field])

        db.session.commit()
        result = antenna_schema_all.dump(antenna)
        response = res.generate_response_update_200(result, 'Antenna')
        return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@antenna_bp.delete("/<id>")
def delete_antenna(id):
    try:
        antenna = db.session.get(Antennas, id)
        if not antenna:
            response = res.generate_failed_msg_not_found_404("Antenna")
            return jsonify(response), 404

        try:
            db.session.delete(antenna)
            db.session.commit()
            response = res.generate_response_delete_200(antenna.name)
            return jsonify(response), 200

        except DatabaseError as db_error:  # noqa: F841
            db.session.rollback()
            response = res.generate_failed_message_dberror()
            return jsonify(response), 503

        except Exception as e:  # noqa: F841
            db.session.rollback()
            response = res.generate_response_delete_500(id)
            return jsonify(response), 500

    except Exception as e:  # noqa: F841

        response = res.generate_failed_message_exception()
        return jsonify(response), 500


