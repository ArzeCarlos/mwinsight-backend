# role.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Roles,db
from app.schemas.schemas import role_schema_all, roles_schema_all
from app.utils import utilities as res

role_bp = Blueprint('role', __name__)

@role_bp.post("/")
def create_role():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = ["name", "tipo", "read_only"]
        allowed_fields = mandatory_fields
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        new_role = Roles(
            name=data['name'],
            tipo=data['tipo'],
            read_only=data['read_only']
        )
        db.session.add(new_role)
        db.session.commit()
        result = role_schema_all.dump(new_role) 
        response =   res.generate_response_create_200(result,"role")
        return jsonify(result), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@role_bp.post("/<id>") # invalid route
def invalid_role(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@role_bp.get("/")
def get_roles():
    try:
        stmt = db.session.query(Roles) # There is a new notation
        resultsquery = stmt.all()
        if resultsquery:
            total_count = db.session.query(func.count(Roles.id)).scalar()
            roles_data = roles_schema_all.dump(resultsquery)
            response = res.generate_response_all(roles_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Roles")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@role_bp.get("/<int:id>")
def get_role(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        
        stmt = db.session.query(Roles).where(Roles.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            role_data= role_schema_all.dump(resultquery)
            response = res.generate_response(role_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Role")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@role_bp.put("/<int:id>")
def update_role(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        role = db.session.query(Roles).where(Roles.id == id).scalar()

        if not role:
            response = res.generate_failed_msg_not_found_404("Role")
            return jsonify(response), 404
        
        allowed_fields = ['name', 'tipo', 'read_only']
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        role.name = data["name"]
        role.tipo = data["tipo"]
        role.read_only = data["read_only"]
        db.session.commit()
        result =role_schema_all.dump(role)
        response = res.generate_response_update_200(result,'Role')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@role_bp.delete("/<int:id>")
def delete_role(id):
    try:
        role = db.session.get(Roles, id)
        if not role:
            response = res.generate_failed_msg_not_found_404("role")
            return jsonify(response), 404

        try:
            db.session.delete(role)
            db.session.commit()
            response = res.generate_response_delete_200(role.name)
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
