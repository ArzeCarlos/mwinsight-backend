# connector.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Connectors,db
from app.utils import utilities as res
from app.schemas.schemas import connector_schema_all, connectors_schema_all

connector_bp = Blueprint('connector', __name__)

@connector_bp.post("/")
def post_connector():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        mandatory_fields = ["name", "insertion_loss", "projectid"]
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

        connector_data = {
            "name": data['name'],
            "insertion_loss": data['insertion_loss'],
            "projectid": data['projectid'],
        }
        if "comments" in data:
            connector_data["comments"] = data["comments"]

        new_connector = Connectors(**connector_data)
        db.session.add(new_connector)
        db.session.commit()
        result = connector_schema_all.dump(new_connector)
        response = res.generate_response_create_200(result, "connector")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        print(DatabaseError)
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@connector_bp.post("/<id>") # invalid route
def invalid_connector(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@connector_bp.get("/")
def get_connectors():
    try:
        project_id = request.args.get("projectId")
        stmt = db.session.query(Connectors)
        if project_id:
            stmt = stmt.filter(Connectors.projectid == project_id)
        resultsquery = stmt.all()
        if resultsquery:
            total_count = stmt.count()
            # total_count = db.session.query(func.count(Connectors.id)).scalar()
            connectors_data = connectors_schema_all.dump(resultsquery)
            response = res.generate_response_all(connectors_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Connectors")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@connector_bp.get("/<id>")
def get_connector(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        stmt = db.session.query(Connectors).where(Connectors.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            connector_data = connector_schema_all.dump(resultquery)
            response = res.generate_response(connector_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Connector")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_msg_not_found_200("connector")
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@connector_bp.put("/<id>")
def update_connector(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        connector = db.session.query(Connectors).where(Connectors.id == id).scalar()

        if not connector:
            response = res.generate_failed_msg_not_found_404("Connector")
            return jsonify(response), 404

        allowed_fields = ["name", "insertion_loss", "comments"]

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                    setattr(connector, field, data[field])

        db.session.commit()
        result = connector_schema_all.dump(connector)
        response = res.generate_response_update_200(result, 'Connector')
        return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@connector_bp.delete("/<id>")
def delete_connector(id):
    try:
        connector = db.session.get(Connectors, id)
        if not connector:
            response = res.generate_failed_msg_not_found_404("Connector")
            return jsonify(response), 404

        try:
            db.session.delete(connector)
            db.session.commit()
            response = res.generate_response_delete_200(connector.name)
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


