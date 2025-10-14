# site.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Sites,db
from app.utils import utilities as res
from app.schemas.schemas import site_schema_all, sites_schema_all

site_bp = Blueprint('site', __name__)

@site_bp.post("/")
def post_site():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        mandatory_fields = ["name", "latitude", "longitude", "projectid"]
        optional_fields = ["description"]
        allowed_fields = mandatory_fields + optional_fields

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        site_data = {
            "name": data['name'],
            "latitude": data['latitude'],
            "longitude": data['longitude'],
            "projectid": data['projectid'],
        }
        if "description" in data:
            site_data["description"] = data["description"]

        new_site = Sites(**site_data)
        db.session.add(new_site)
        db.session.commit()
        result = site_schema_all.dump(new_site)
        response = res.generate_response_create_200(result, "site")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@site_bp.post("/<id>") # invalid route
def invalid_site(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405


@site_bp.get("/")
def get_sites():
    try:
        project_id = request.args.get("projectId")

        stmt = db.session.query(Sites)

        if project_id:
            stmt = stmt.filter(Sites.projectid == project_id)

        resultsquery = stmt.all()

        if resultsquery:
            total_count = stmt.count()
            sites_data = sites_schema_all.dump(resultsquery)
            response = res.generate_response_all(sites_data, total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Sites")
            return jsonify(response), 200

    except DatabaseError:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        print(e)
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@site_bp.get("/<id>")
def get_site(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        stmt = db.session.query(Sites).where(Sites.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            site_data = site_schema_all.dump(resultquery)
            response = res.generate_response(site_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Site")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_msg_not_found_200("site")
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@site_bp.put("/<id>")
def update_site(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        site = db.session.query(Sites).where(Sites.id == id).scalar()

        if not site:
            response = res.generate_failed_msg_not_found_404("Site")
            return jsonify(response), 404

        allowed_fields = ['name', 'latitude', 'longitude', 'description']
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                setattr(site, field, data[field])

        db.session.commit()
        result = site_schema_all.dump(site)
        response = res.generate_response_update_200(result, 'Site')
        return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@site_bp.delete("/<id>")
def delete_site(id):
    try:
        site = db.session.get(Sites, id)
        if not site:
            response = res.generate_failed_msg_not_found_404("site")
            return jsonify(response), 404

        try:
            db.session.delete(site)
            db.session.commit()
            response = res.generate_response_delete_200(site.name)
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


