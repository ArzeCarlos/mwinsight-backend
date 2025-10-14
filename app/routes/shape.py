# shape.py
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Shapes, db
from app.utils import utilities as res
from app.schemas.schemas import shape_schema_all, shapes_schema_all
shape_bp = Blueprint('shape', __name__)

@shape_bp.post("/")
def create_shape():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields= ["identifier", "name", "posX", "posY", "ip", "diagramid"]
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in mandatory_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        new_shape = Shapes(
            identifier=data['identifier'],
            name=data['name'],
            posX=data['posX'],
            posY=data['posY'],
            ip=data['ip'],
            diagramid= data['diagramid']
        )
        db.session.add(new_shape)
        db.session.commit()
        result = shape_schema_all.dump(new_shape) 
        response =   res.generate_response_create_200(result,"shape")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@shape_bp.get("/")
def get_shapes():
    try:
        stmt = db.session.query(Shapes)
        resultsquery = stmt.all()
        if resultsquery:
            shape_data = shapes_schema_all.dump(resultsquery)
            total_count = db.session.query(func.count(Shapes.id)).scalar()
            response = res.generate_response_all(shape_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Shapes")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@shape_bp.get("/<int:id>")
def get_shape(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        
        stmt = db.session.query(Shapes).where(Shapes.id == id)
        resultquery = stmt.scalar()

        if resultquery:
            shape_data= shape_schema_all.dump(resultquery)
            response = res.generate_response(shape_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Shape")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@shape_bp.put("/<int:id>")
def update_shape(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        shape = db.session.query(Shapes).where(Shapes.id == id).scalar()

        if not shape:
            response = res.generate_failed_msg_not_found_404("Shape")
            return jsonify(response), 404
        
        allowed_fields = ['identifier', 'name', "posX", "posY", "ip", "diagramid"]
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        shape.identifier = data["identifier"]
        shape.name = data["name"]
        shape.posX = data["posX"]
        shape.posY = data["posY"]
        shape.ip = data["ip"]
        shape.diagramid = data["diagramid"]
        db.session.commit()
        result =shape_schema_all.dump(shape)
        response = res.generate_response_update_200(result,'Shape')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@shape_bp.delete("/<int:id>")
def delete_shape(id):
    try:
        shape = db.session.get(Shapes, id)
        if not shape:
            response = res.generate_failed_msg_not_found_404("shape")
            return jsonify(response), 404

        try:
            db.session.delete(shape)
            db.session.commit()
            response = res.generate_response_delete_200(shape.name)
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



