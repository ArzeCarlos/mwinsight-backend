# radio.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Radios,db
from app.utils import utilities as res
from app.schemas.schemas import radio_schema_all, radios_schema_all

radio_bp = Blueprint('radio', __name__)

@radio_bp.post("/")
def post_radio():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        mandatory_fields = ["name", "manufacturer", "frequency_band", "modulation", "transmission_power", "receiver_threshold","projectid"]
        optional_fields = ["comments"]
        allowed_fields = mandatory_fields + optional_fields

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        radio_data = {
            "name": data['name'],
            "manufacturer": data['manufacturer'],
            "frequency_band": data['frequency_band'],
            "modulation": data['modulation'],
            "transmission_power": data['transmission_power'],
            "receiver_threshold": data['receiver_threshold'],
            "projectid": data['projectid'],
        }
        if "comments" in data:
            radio_data["comments"] = data["comments"]

        new_radio = Radios(**radio_data)
        db.session.add(new_radio)
        db.session.commit()
        result = radio_schema_all.dump(new_radio)
        response = res.generate_response_create_200(result, "radio")
        return jsonify(response), 201

    except DatabaseError as db_error:
        print(db_error)
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@radio_bp.post("/<id>") # invalid route
def invalid_radio(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@radio_bp.get("/")
def get_radios():
    try:
        project_id = request.args.get("projectId")
        stmt = db.session.query(Radios)
        if project_id:
            stmt = stmt.filter(Radios.projectid == project_id)
        resultsquery = stmt.all()
        if resultsquery:
            total_count = stmt.count()
            # total_count = db.session.query(func.count(Radios.id)).scalar()
            radios_data = radios_schema_all.dump(resultsquery)
            response = res.generate_response_all(radios_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Radios")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@radio_bp.get("/<id>")
def get_radio(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        stmt = db.session.query(Radios).where(Radios.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            radio_data = radio_schema_all.dump(resultquery)
            response = res.generate_response(radio_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Radio")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_msg_not_found_200("radio")
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@radio_bp.put("/<id>")
def update_radio(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        radio = db.session.query(Radios).where(Radios.id == id).scalar()

        if not radio:
            response = res.generate_failed_msg_not_found_404("Radio")
            return jsonify(response), 404

        allowed_fields = ["name", "manufacturer", "frequency_band", "modulation", "transmission_power", "receiver_threshold", "comments"]

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                    setattr(radio, field, data[field])

        db.session.commit()
        result = radio_schema_all.dump(radio)
        response = res.generate_response_update_200(result, 'Radio')
        return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@radio_bp.delete("/<id>")
def delete_radio(id):
    try:
        radio = db.session.get(Radios, id)
        if not radio:
            response = res.generate_failed_msg_not_found_404("Radio")
            return jsonify(response), 404

        try:
            db.session.delete(radio)
            db.session.commit()
            response = res.generate_response_delete_200(radio.name)
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


