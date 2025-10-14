# cable.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Cables,db
from app.utils import utilities as res
from app.schemas.schemas import cable_schema_all, cables_schema_all

cable_bp = Blueprint('cable', __name__)

@cable_bp.post("/")
def post_cable():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        mandatory_fields = ["name", "loss_per_meter","projectid"]
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

        cable_data = {
            "name": data['name'],
            "loss_per_meter": data['loss_per_meter'],
            "projectid": data['projectid'],
        }
        if "comments" in data:
            cable_data["comments"] = data["comments"]

        new_cable = Cables(**cable_data)
        db.session.add(new_cable)
        db.session.commit()
        result = cable_schema_all.dump(new_cable)
        response = res.generate_response_create_200(result, "cable")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@cable_bp.post("/<id>") # invalid route
def invalid_cable(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@cable_bp.get("/")
def get_cables():
    try:
        project_id = request.args.get("projectId")
        stmt = db.session.query(Cables)
        if project_id:
            stmt = stmt.filter(Cables.projectid == project_id)
        resultsquery = stmt.all()
        if resultsquery:
            total_count = stmt.count()
            # total_count = db.session.query(func.count(Cables.id)).scalar()
            cables_data = cables_schema_all.dump(resultsquery)
            response = res.generate_response_all(cables_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Cables")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@cable_bp.get("/<id>")
def get_cable(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        stmt = db.session.query(Cables).where(Cables.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            cable_data = cable_schema_all.dump(resultquery)
            response = res.generate_response(cable_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Cable")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_msg_not_found_200("cable")
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@cable_bp.put("/<id>")
def update_cable(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        cable = db.session.query(Cables).where(Cables.id == id).scalar()

        if not cable:
            response = res.generate_failed_msg_not_found_404("Cable")
            return jsonify(response), 404

        allowed_fields = ["name", "loss_per_meter", "comments"]

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                    setattr(cable, field, data[field])

        db.session.commit()
        result = cable_schema_all.dump(cable)
        response = res.generate_response_update_200(result, 'Cable')
        return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@cable_bp.delete("/<id>")
def delete_cable(id):
    try:
        cable = db.session.get(Cables, id)
        if not cable:
            response = res.generate_failed_msg_not_found_404("Cable")
            return jsonify(response), 404

        try:
            db.session.delete(cable)
            db.session.commit()
            response = res.generate_response_delete_200(cable.name)
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


