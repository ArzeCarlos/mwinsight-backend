# user.py
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import bcrypt
from app.models import Users,Roles,db
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.schemas.schemas import userroleTRO_schema, userroleNTRO_schema, user_schema_all
from app.utils import utilities as res

user_bp = Blueprint('user', __name__)

@user_bp.post("/")
def create_user():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = ["username", "firstname", "lastname", "passwd", "email", "roleid"]
        optional_fields = ["autologout", "refresh"]
        allowed_fields = mandatory_fields + optional_fields
        
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        hashed_password = bcrypt.generate_password_hash(data['passwd']).decode('utf-8')
        
        user_data = {
            "username": data['username'],
            "firstname": data['firstname'],
            "lastname": data['lastname'],
            "passwd": hashed_password,
            "email": data['email'],
            "roleid": data['roleid'],
        }
        if "autologout" in data:
            user_data["autologout"] = data["autologout"]
        if "refresh" in data:
            user_data["refresh"] = data["refresh"]

        new_user = Users(**user_data)
        db.session.add(new_user)
        db.session.commit()
        result = user_schema_all.dump(new_user)
        response = res.generate_response_create_200(result,"User")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@user_bp.post("/<id>") # invalid route
def invalid_user(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@user_bp.get("/") 
def get_users():
    try:
        valid_params = {'roletype', 'refresh', 'sort_by', 'order'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("Users", unknown_params)
            return jsonify(response), 400

        roletype = request.args.get('roletype')
        refresh = request.args.get('refresh')
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')

        valid_columns = {'id', 'username', 'firstname','lastname', 'createdAt', 'updatedAt'} 
        if sort_by not in valid_columns:
            return jsonify(res.generate_failed_message_unknown("Users", [sort_by])), 400

        stmt = db.session.query(Users, Roles).join(Roles, Users.roleid == Roles.id)
        filters = []
        if roletype:
            filters.append(Roles.tipo == roletype)
        if refresh:
            refresh_time = datetime.strptime(refresh, "%H:%M:%S").time()
            filters.append(Users.refresh == refresh_time)
        if filters:
            stmt = stmt.filter(*filters)

        sort_column = getattr(Users, sort_by, None)
        if order.lower() == 'desc':
            sort_column = sort_column.desc()
        stmt = stmt.order_by(sort_column)
        resultsquery = stmt.all()
        if resultsquery:
            users_data = [(userroleTRO_schema.dump({"role": role, **user.__dict__})) for user, role in resultsquery]
            total_count = db.session.query(func.count(Users.id)).scalar()
            response = res.generate_response_all(users_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Users")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        print(e)
        response = res.generate_failed_message_exception()
        return jsonify(response), 500
    
@user_bp.get("/<id>")
def get_user(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        
        resultquery = db.session.query(Users, Roles)\
            .join(Roles, Users.roleid == Roles.id)\
            .where(Users.id == id).first()

        if resultquery:
            user, role = resultquery
            user_data = userroleNTRO_schema.dump({"role": role, **user.__dict__})
            fields = request.args.get("fields")
            valid_fields = set(user_data.keys())
            if fields:
                requested_fields = set(fields.split(","))
                invalid_fields = requested_fields - valid_fields
                if invalid_fields:
                    response = res.generate_failed_invalid_fields("User",list(invalid_fields))
                    return jsonify(response), 400
                user_data = {k: v for k, v in user_data.items() if k in requested_fields}
            
            response = res.generate_response(user_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("User")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@user_bp.put("/<int:id>") 
def update_user(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400

        user = db.session.get(Users, id)
        if not user:
            response = res.generate_failed_msg_not_found_404("User")
            return jsonify(response), 404

        allowed_fields = ['username', 'firstname', 'lastname', 'passwd', 'email', 'roleid', 'autologout', 'refresh']

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                if field == "passwd":
                    hashed_password = bcrypt.generate_password_hash(data['passwd']).decode('utf-8')
                    setattr(user, field, hashed_password)
                else:
                    setattr(user, field, data[field])

        db.session.commit()
        result = user_schema_all.dump(user)
        response = res.generate_response_update_200(result,'User')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@user_bp.delete("/<int:id>")
def delete_user(id):
    try:
        user = db.session.get(Users, id)
        if not user:
            response = res.generate_failed_msg_not_found_404("User")
            return jsonify(response), 404

        try:
            db.session.delete(user)
            db.session.commit()
            response = res.generate_response_delete_200(user.username)
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
