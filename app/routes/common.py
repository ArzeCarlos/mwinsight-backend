import os
import json
import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint,request,jsonify
from sqlalchemy.exc import DatabaseError
from app.utils import utilities as res
from app import bcrypt
from app.models import Roles, Users,db
from app.schemas.schemas import user_schema_all
common_bp = Blueprint('common', __name__)

@common_bp.post('/signup')
def register():
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
@common_bp.post('/login')
def login():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        resultquery = db.session.query(Users).where(Users.username == data["username"]).first()
        resultquery2 = db.session.query(Roles).where(Roles.id == resultquery.roleid).first()
        if not resultquery or not bcrypt.check_password_hash(resultquery.passwd, data["passwd"]):
            return jsonify({'status':'error','message': 'Invalid username or password'}), 200
        token = jwt.encode({'public_id': resultquery.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
                           "1adnoqkweedweef2", algorithm="HS256")
        return jsonify({
            'status': "ok",
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': resultquery.id,
                'username': resultquery.username,
                'tipo': resultquery2.tipo
            }
        }), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@common_bp.post('/diagram')
def saveDiagram():
    try:
        data = request.get_json()
        
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        print("Datos recibidos:", data)

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(BASE_DIR, "..", "diagrams")
        os.makedirs(save_path, exist_ok=True)

        # diagram_name = data.get("name", "diagrama_sin_nombre")
        # safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in diagram_name)
        filename = "probe.json"

        file_path = os.path.join(save_path, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return jsonify({"message": "Diagrama guardado correctamente."}), 200

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@common_bp.get('/diagram')
def getDiagram():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "..", "diagrams", "probe.json")

        if not os.path.exists(file_path):
            return jsonify({"error": "El diagrama no existe"}), 404

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data), 200
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@common_bp.post('/checkpwd')
def check_password_chg():
    try:
        data= request.get_json()
        resultquery = db.session.query(Users).where(Users.username==data["username"]).first()
        if not resultquery:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 200

        if bcrypt.check_password_hash(resultquery.passwd, data["passwd"]):
            print("ok")
            return jsonify({'status': 'ok', 'message': 'Password correct'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 200
        
    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500
    
