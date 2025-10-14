# link_d.py
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Links_D, db
from app.utils import utilities as res
from app.schemas.schemas import linkd_schema_all, linkds_schema_all
link_d_bp = Blueprint('link_d', __name__)
@link_d_bp.post("/")
def create_link_d():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields= ["identifierBeg", "identifierEnd", "diagramid"]
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in mandatory_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        new_link_d = Links_D(
            identifierBeg=data['identifierBeg'],
            identifierEnd=data['identifierEnd'],
            diagramid= data['diagramid']
        )
        db.session.add(new_link_d)
        db.session.commit()
        result = linkd_schema_all.dump(new_link_d) 
        response =   res.generate_response_create_200(result,"link_d")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_d_bp.get("/")
def get_links_d():
    try:
        stmt = db.session.query(Links_D)
        resultsquery = stmt.all()
        if resultsquery:
            link_d_data = linkds_schema_all.dump(resultsquery)
            total_count = db.session.query(func.count(Links_D.id)).scalar()
            response = res.generate_response_all(link_d_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Links_D")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_d_bp.get("/<int:id>")
def get_link_d(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        
        stmt = db.session.query(Links_D).where(Links_D.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            link_data= linkd_schema_all.dump(resultquery)
            response = res.generate_response(link_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Link_D")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_d_bp.put("/<int:id>")
def update_link_d(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        link_d = db.session.query(Links_D).where(Links_D.id == id).scalar()

        if not link_d:
            response = res.generate_failed_msg_not_found_404("Link_D")
            return jsonify(response), 404
        
        allowed_fields = ['identifierBeg', 'identifierEnd', "diagramid"]
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        link_d.identifierBeg = data["identifierBeg"]
        link_d.identifierEnd = data["identifierEnd"]
        link_d.diagramid = data["diagramid"]
        db.session.commit()
        result =linkd_schema_all.dump(link_d)
        response = res.generate_response_update_200(result,'Link_D')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_d_bp.delete("/<int:id>")
def delete_link_d(id):
    try:
        link_d = db.session.get(Links_D, id)
        if not link_d:
            response = res.generate_failed_msg_not_found_404("link_d")
            return jsonify(response), 404

        try:
            db.session.delete(link_d)
            db.session.commit()
            response = res.generate_response_delete_200(link_d.id)
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



