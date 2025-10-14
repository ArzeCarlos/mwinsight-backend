# metering.py
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Meterings, Items, SNMPFailures,db
from app.schemas.schemas import metering_schema_all, item_schema_all, meteringitemschemansksl_schema, snmpfailureschema_schema
from app.utils import utilities as res
import socket
metering_bp = Blueprint('metering', __name__)

def convert_to_time(time_str):
    try:
        return datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        raise ValueError("El formato de updateinterval debe ser HH:MM:SS.")

@metering_bp.post("/")
def create_metering():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = ["itemid", "valor", "latencia"] #Added latency
        optional_fields= ["tiempo"]
        allowed_fields = mandatory_fields + optional_fields 

        print(data)

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        # try:
        #     timestamp = convert_to_time(data['timestamp'])
        # except ValueError as ve:
        #     response = {"error": str(ve)}
        #     return jsonify(response), 400

        
        metering_data = {
            "itemid":data['itemid'],
            "valor":data['valor'],
            "latencia": data['latencia']
        }

        new_metering = Meterings(**metering_data)
        db.session.add(new_metering)
        db.session.commit()
        result = metering_schema_all.dump(new_metering)
        response = res.generate_response_create_200(result,"Metering")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        print(e)
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@metering_bp.get("/")
def get_meterings():
    try:
        valid_params = {'sort_by', 'order', 'itemid'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("Meterings", unknown_params)
            return jsonify(response), 400

        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        itemid = request.args.get('itemid')  # Puede ser None si no se especifica

        valid_columns = {'id', 'valor', 'createdAt', 'updatedAt'}
        if sort_by not in valid_columns:
            return jsonify(res.generate_failed_message_unknown("Meterings", [sort_by])), 400

        stmt = db.session.query(Meterings, Items).join(Items, Meterings.itemid == Items.id)

        if itemid:
            try:
                itemid_int = int(itemid)
            except ValueError:
                return jsonify(res.generate_failed_message("El parámetro itemid debe ser un entero.")), 400

            stmt = stmt.filter(Items.id == itemid_int)

        sort_column = getattr(Meterings, sort_by, None)
        if order.lower() == 'desc':
            sort_column = sort_column.desc()
        stmt = stmt.order_by(sort_column)

        resultsquery = stmt.all()

        if resultsquery:
            grouped_data = {}

            for metering, item in resultsquery:
                if item.id not in grouped_data:
                    grouped_data[item.id] = {
                        "item": item_schema_all.dump(item),
                        "ids": [],
                        "values": [],
                        "tiempo": []
                    }
                grouped_data[item.id]["ids"].append(metering.id)
                grouped_data[item.id]["values"].append(metering.valor)
                grouped_data[item.id]["tiempo"].append(metering.tiempo)

            meterings_data = list(grouped_data.values())

            total_count = len(meterings_data)

            response = res.generate_response_all(meterings_data, total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Meterings")
            return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@metering_bp.post("/<int:id>/latency")
def get_metering_latency(id):
    try:
        data = request.get_json()
        init_date_str = data.get('initDate')
        end_date_str = data.get('endDate')
        try:
            init_date = datetime.fromisoformat(init_date_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return jsonify({"error": "Fechas inválidas"}), 400
        result = (
            db.session.query(
                func.max(Meterings.latencia),
                func.avg(Meterings.latencia),
                func.min(Meterings.latencia)
            )
            .filter(Meterings.itemid == id)
            .filter(Meterings.tiempo >= init_date, Meterings.tiempo <= end_date)
            .first()  
        )
        return jsonify({
            "maxLat": result[0],
            "avgLat": result[1],
            'minLat': result[2]
        }), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@metering_bp.get("/<int:id>")
def get_metering(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        resultquery = db.session.query(Meterings, Items).join(Items, Meterings.itemid == Items.id).where(Meterings.id == id).first()
        if resultquery:
            metering, item = resultquery
            metering_data = meteringitemschemansksl_schema.dump({"item": item, **metering.__dict__})
            response = res.generate_response(metering_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Metering")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@metering_bp.put("/<int:id>")
def update_metering(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400

        metering = db.session.get(Meterings, id)
        if not metering:
            response = res.generate_failed_msg_not_found_404("Metering")
            return jsonify(response), 404

        allowed_fields = ['itemid', 'valor', 'latencia']

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        metering.itemid = data["itemid"]
        metering.valor = data["valor"]
        metering.latencia = data['latencia'] #added
        db.session.commit()

        result = metering_schema_all.dump(metering)
        response = res.generate_response_update_200(result,'Metering')
        return jsonify(response), 200
    
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@metering_bp.delete("/<int:id>")
def delete_metering(id):
    try:
        metering = db.session.get(Meterings, id)
        if not metering:
            response = res.generate_failed_msg_not_found_404("Metering")
            return jsonify(response), 404

        try:
            db.session.delete(metering)
            db.session.commit()
            response = res.generate_response_delete_200(metering.valor)
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

@metering_bp.post("/falla")
def post_metering_fail():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields = ["itemid", "host_ip", "oid", 'mensaje', 'valor']
        allowed_fields = mandatory_fields 

        print(data)

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        
        snmp_failed_data = {
            "itemid":data['itemid'],
            "valor":data['valor'],
            "oid":data['oid'],
            "mensaje":data['mensaje'],
            "host_ip": data['host_ip']
        }

        new_snmp_failed_data = SNMPFailures(**snmp_failed_data)
        db.session.add(new_snmp_failed_data)
        db.session.commit()
        result = snmpfailureschema_schema.dump(new_snmp_failed_data)
        response = res.generate_response_create_200(result,"SNMP Failed data")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        print(e)
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@metering_bp.get("/falla")
def get_snmp_failed():
    try:
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        print(start_date_str,end_date_str)
        stmt = db.session.query(SNMPFailures)
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M")
                stmt = stmt.filter(SNMPFailures.tiempo.between(start_date, end_date))
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido, usar YYYY-MM-DDTHH:MM:SS"}), 400

        results = stmt.all()
        serialized_results = [
            {
                "id": r.id,
                "itemid": r.itemid,
                "host_ip": r.host_ip,
                "oid": r.oid,
                "mensaje": r.mensaje,
                "valor": r.valor,
                "tiempo": r.tiempo.isoformat() if r.tiempo else None
            }
            for r in results
        ]

        response = res.generate_response_create_200(serialized_results, "reachbility")
        return jsonify(response), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500
@metering_bp.post("/refresh")
def refresh_core():
    try:
        data = request.get_json()
        wake = data["wake"]
        if not wake:
            return jsonify({"error": "No se recibió el valor 'wake'"}), 400

        # --- Equivalente a wake_fetcher.js ---
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", 5050))
                s.sendall(wake.encode())
        except Exception as e:
            return jsonify({"error": f"No se pudo conectar al fetcher: {e}"}), 500

        return jsonify({"status": "WAKE enviado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500