# hostgroup.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Hostgroups,db
from app.schemas.schemas import hostgroup_schema_all, hostgroups_schema_all
from app.utils import utilities as res

hostgroup_bp = Blueprint('hostgroup', __name__)

@hostgroup_bp.post("/")
def create_hostgroup():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = ["name", "model", "description"]
        allowed_fields = mandatory_fields
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        new_hostgroup = Hostgroups(
            name=data['name'], 
            model=data['model'], 
            description=data['description']
        )
        db.session.add(new_hostgroup)
        db.session.commit()
        result = hostgroup_schema_all.dump(new_hostgroup)
        response =   res.generate_response_create_200(result,"hostgroup")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@hostgroup_bp.get("/")
def get_hostgroups():
    try:
        valid_params = {'groupid', 'sort_by', 'order', 'names'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        names = request.args.get('names')
        if unknown_params:
            response = res.generate_failed_message_unknown("Hostgroups", unknown_params)
            return jsonify(response), 400

        stmt = db.session.query(Hostgroups)
        
        if names:
            stmtNames = db.session.query(Hostgroups.name).all()
            responseNames =[x[0] for x in stmtNames]
            return ({"names":responseNames}), 200

        resultsquery = stmt.all()
        if resultsquery:
            result = hostgroups_schema_all.dump(resultsquery)
            total_count = db.session.query(func.count(Hostgroups.id)).scalar()
            response = res.generate_response_all(result,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Hostgroups")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@hostgroup_bp.get("/<int:id>")
def get_hostgroup(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        
        stmt = db.session.query(Hostgroups).where(Hostgroups.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            hostgroup_data = hostgroup_schema_all.dump(resultquery)
            response = res.generate_response(hostgroup_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Hostgroup")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@hostgroup_bp.put("/<int:id>")
def update_hostgroup(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        hostgroup = db.session.query(Hostgroups).where(Hostgroups.id == id).scalar()

        if not hostgroup:
            response = res.generate_failed_msg_not_found_404("Hostgroup")
            return jsonify(response), 404
        
        allowed_fields = ['name', 'model', 'description']
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        hostgroup.name = data["name"]
        hostgroup.model = data["model"]
        hostgroup.description = data["description"]
        db.session.commit()
        result= hostgroup_schema_all.dump(hostgroup)
        response = res.generate_response_update_200(result,'Hostgroup')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@hostgroup_bp.delete("/<int:id>")
def delete_hostgroup(id):
    try:
        hostgroup = db.session.get(Hostgroups, id)
        if not hostgroup:
            response = res.generate_failed_msg_not_found_404("Hostgroup")
            return jsonify(response), 404

        try:
            db.session.delete(hostgroup)
            db.session.commit()
            response = res.generate_response_delete_200(hostgroup.name)
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
