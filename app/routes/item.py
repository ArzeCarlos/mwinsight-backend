# item.py
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import func,text, or_
from sqlalchemy.exc import DatabaseError
from app.models import Items,Hosts,Meterings,db
from app.schemas.schemas import item_schema_all
from app.utils import utilities as res

item_bp = Blueprint('item', __name__)

def convert_to_time(time_str):
    try:
        return datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        raise ValueError("El formato de updateinterval debe ser HH:MM:SS.")

@item_bp.post("/")
def create_item():
    try:
        data = request.get_json()
        print(data)
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        
        mandatory_fields = ["name", "tipo", "hostid", "snmp_oid", "acronimo", "units",
                            "factor_multiplicacion", "factor_division", "updateinterval", "description", "enabled"]
        optional_fields = ["timeout"]
        allowed_fields = mandatory_fields + optional_fields
        
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        try:
            updateinterval_obj = convert_to_time(data['updateinterval'])
        except ValueError as ve:
            response = {"error": str(ve)}
            return jsonify(response), 400

        DEFAULT_TIMEOUT = 30  
        timeout = data.get("timeout", DEFAULT_TIMEOUT)

        new_item = Items(
            name=data['name'],
            tipo=data['tipo'],
            hostid=data['hostid'],
            snmp_oid=data['snmp_oid'],
            acronimo=data['acronimo'],
            units=data['units'],
            updateinterval=updateinterval_obj,
            description=data['description'],
            enabled=data['enabled'],
            timeout=timeout,
            factor_multiplicacion=data['factor_multiplicacion'],
            factor_division= data['factor_division']
        )

        db.session.add(new_item)
        db.session.commit()

        result = item_schema_all.dump(new_item)
        response = res.generate_response_create_200(result, "Item")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        print(db_error)
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        print(e)
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@item_bp.post("/<id>")
def invalid_item(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405    

#Backup, core functionality.
@item_bp.get('/core')
def get_items_core():
    try:
        valid_params = {'nextcheck', 'itemstocheck'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("Items", unknown_params)
            return jsonify(response), 400
        nextcheck = request.args.get('nextcheck')
        itemstocheck = request.args.get('itemstocheck')
        if itemstocheck:
            creation_threshold: timedelta = timedelta(microseconds=20)
            threshold_us = creation_threshold.microseconds
            cond_interval_expired = (
                func.addtime(Items.updatedAt, Items.updateinterval) <= func.current_timestamp()
            )
            diff_microseconds = func.timestampdiff(
                text("MICROSECOND"),
                Items.createdAt,
                Items.updatedAt
            )
            cond_recently_created = func.abs(diff_microseconds) <= threshold_us
            stmt = (
                db.session.query(
                    Items.id,
                    Items.enabled,
                    Items.snmp_oid,
                    Hosts.ip,
                    Hosts.community,
                    Items.tipo
                )
                .join(Hosts, Items.hostid == Hosts.id)
                .filter(
                    or_(
                        cond_interval_expired,
                        cond_recently_created
                    )
                )
            )
            query_result = stmt.all()
            items_serialized = []
            if query_result:
                for data in query_result:
                    if data.id not in items_serialized:
                        items_serialized.append(({
                            "id": data.id,
                            "enabled": data.enabled,
                            "oid": data.snmp_oid,
                            "ip": data.ip,
                            "community": data.community,
                            "tipo": data.tipo
                        }))
            return jsonify(items_serialized), 200
        if (nextcheck):
            min_interval = (
                db.session.query(func.min(Items.updateinterval))
                .filter(
                func.addtime(Items.updatedAt, Items.updateinterval) <= func.current_timestamp(),
                Items.enabled.is_(True)
            )
            .scalar()        
            )
            if min_interval:
                return jsonify({'min_interval': min_interval.isoformat()}), 200

    except Exception as e:
        print(f'Ocurrió un error en la obtención de datos {e}')    

@item_bp.get('/monitoring')
def get_to_monitoring():
    stmtcore = (
        db.session.query(Items.id,Items.name,Items.tipo,Items.snmp_oid, Items.enabled, Items.factor_multiplicacion,
                        Items.factor_division,
                        Items.updateinterval,Items.updatedAt,
                         Items.createdAt,
                         Hosts.hostname,Hosts.ip,Hosts.community,).join(Hosts, Items.hostid == Hosts.id)
    )
    resultquery = stmtcore.all()
    items_serialized = []
    for data in resultquery:
        items_serialized.append({
            'id': data.id,
            'name': data.name,
            'tipo': data.tipo,
            'snmp_oid': data.snmp_oid,
            'enabled': data.enabled,
            'factor_multiplicacion': data.factor_multiplicacion,
            'factor_division': data.factor_division,
            'updateinterval': data.updateinterval.isoformat(),
            'updatedAt': data.updatedAt.isoformat(),
            'createdAt': data.createdAt.isoformat(),
            "host" : {
                "hostname": data.hostname,
                "ip": data.ip,
                'community': data.community
            }
        })
    return jsonify(items_serialized), 200
                      

@item_bp.get("/")
def get_items():
    try:
        valid_params = {'groupId','hostid', 'sort_by', 'order', 'enabled', 'enabledGraph', 'core'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("Items", unknown_params)
            return jsonify(response), 400
        hostid = request.args.get('hostid')
        groupid = request.args.get('groupId')
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        enabled = request.args.get('enabled')
        enabled_graph = request.args.get('enabledGraph')
        valid_columns = {'id', 'hostname', 'uuid', 'name', 'acronimo', 'createdAt', 'updatedAt'}

        if sort_by not in valid_columns:
            return jsonify(res.generate_failed_message_unknown("Items", [sort_by])), 400

        if enabled:
            count_true = db.session.query(func.count()).filter(Items.enabled).scalar()
            count_false = db.session.query(func.count()).filter(not Items.enabled).scalar()
            statusresponse = {
                "enabledItem":count_true,
                "disabledItem":count_false
            }
            return jsonify(statusresponse), 200

        if enabled_graph and groupid:
            count_true = (
                db.session.query(func.count(Items.id))
                .join(Hosts, Items.hostid == Hosts.id)
                .filter(Items.enabled, Hosts.groupid == groupid)
                .scalar()
            )
            count_false = (
                db.session.query(func.count(Items.id))
                .join(Hosts, Items.hostid == Hosts.id)
                .filter(not Items.enabled, Hosts.groupid == groupid)
                .scalar()
            )
            
            statusresponse = {
                "enabledItem": count_true,
                "disabledItem": count_false
            }
            return jsonify(statusresponse), 200
        
        stmt = (
            db.session.query(Items, Hosts)
            .join(Hosts, Items.hostid == Hosts.id)
        )

        if hostid:
            stmt = stmt.filter(Items.hostid == hostid)

        if groupid:
            stmt = stmt.filter(Hosts.groupid == groupid)

        sort_column = getattr(Items, sort_by, None)
        if order.lower() == 'desc':
            sort_column = sort_column.desc()
        stmt = stmt.order_by(sort_column)

        resultsquery = stmt.all()
        if resultsquery:
            items_serialized = {}

            for item, host in resultsquery:
                if item.id not in items_serialized:
                    items_serialized[item.id] = {
                        "id": item.id,
                        "name": item.name,
                        "tipo": item.tipo,
                        "snmp_oid": item.snmp_oid,
                        "acronimo": item.acronimo,
                        "units": item.units,
                        "status_codes": item.status_codes,
                        "uuid": item.uuid,
                        "updateinterval": item.updateinterval.isoformat() if item.updateinterval else None,
                        "timeout": item.timeout,
                        "description": item.description,
                        "enabled": item.enabled,
                        "factor_multiplicacion": item.factor_multiplicacion,
                        "factor_division": item.factor_division,
                        "latest_data": item.latest_data,
                        "createdAt": item.createdAt.isoformat() if item.createdAt else None,
                        "updatedAt": item.updatedAt.isoformat() if item.updatedAt else None,
                        "host": {
                            "id": host.id,
                            "hostname": host.hostname,
                            "community": host.community,
                            "enabled": host.enabled,
                            "ip": host.ip,
                            "url": f"api/v1/host/{host.id}",
                            "createdAt": host.createdAt.isoformat() if host.createdAt else None,
                            "updatedAt": host.updatedAt.isoformat() if host.updatedAt else None
                        },
                    }
            items_data = list(items_serialized.values())
            total_count = db.session.query(func.count(Items.id)).scalar()
            response = res.generate_response_all(items_data, total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Item")
            return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@item_bp.get("/<int:id>")
def get_item(id):
    try:
        result = (
            db.session.query(Items, Hosts, Meterings)
            .join(Hosts, Items.hostid == Hosts.id)
            .outerjoin(Meterings, Meterings.itemid == Items.id)
            .filter(Items.id == id)
            .all()
        )

        if not result:
            response = res.generate_failed_msg_not_found_200("Item")
            return jsonify(response), 200

        item, host, _ = result[0]

        item_data = {
            "id": item.id,
            "name": item.name,
            "tipo": item.tipo,
            "snmp_oid": item.snmp_oid,
            "acronimo": item.acronimo,
            "units": item.units,
            "status_codes": item.status_codes,
            "uuid": item.uuid,
            "updateinterval": item.updateinterval.isoformat() if item.updateinterval else None,
            "timeout": item.timeout,
            "description": item.description,
            "enabled": item.enabled,
            "factor_multiplicacion": item.factor_multiplicacion,
            "factor_division": item.factor_division,
            "latest_data": item.latest_data,
            "createdAt": item.createdAt.isoformat() if item.createdAt else None,
            "updatedAt": item.updatedAt.isoformat() if item.updatedAt else None,
            "host": {
                "id": host.id,
                "hostname": host.hostname,
                "community": host.community,
                "enabled": host.enabled,
                "ip": host.ip,
                "url": f"api/v1/host/{host.id}",
                "createdAt": host.createdAt.isoformat() if host.createdAt else None,
                "updatedAt": host.updatedAt.isoformat() if host.updatedAt else None
            },
            "meterings": {
                "values": [],
                "tiempos": []
            }
        }

        for _, _, metering in result:
            if metering is not None:
                item_data["meterings"]["values"].append(metering.valor)
                item_data["meterings"]["tiempos"].append(
                    metering.tiempo.isoformat() if metering.tiempo else None
                )

        response = res.generate_response(item_data)
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500
    
@item_bp.post("/<int:id>/filtering")
def get_graph(id):
    try:
        data = request.get_json()
        # Obtener fechas
        init_date_str = data.get('initDate')
        end_date_str = data.get('endDate')
        
        print("Valores")
        print(init_date_str,end_date_str)
        # Meterings tiempo
        try:
            init_date = datetime.fromisoformat(init_date_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return jsonify({"error": "Fechas inválidas"}), 400
        # Consulta con filtro de rango de fechas
        result = (
            db.session.query(Items, Hosts, Meterings)
            .join(Hosts, Items.hostid == Hosts.id)
            .outerjoin(Meterings, Meterings.itemid == Items.id)
            .filter(Items.id == id)
            .filter(Meterings.tiempo >= init_date, Meterings.tiempo <= end_date)
            .all()
        )
        if not result:
            response = res.generate_failed_msg_not_found_200("Item")
            return jsonify(response), 200
        item, host, _ = result[0]
        item_data = {
            "id": item.id,
            "name": item.name,
            "tipo": item.tipo,
            "snmp_oid": item.snmp_oid,
            "acronimo": item.acronimo,
            "units": item.units,
            "status_codes": item.status_codes,
            "uuid": item.uuid,
            "updateinterval": item.updateinterval.isoformat() if item.updateinterval else None,
            "timeout": item.timeout,
            "description": item.description,
            "enabled": item.enabled,
            "factor_multiplicacion": item.factor_multiplicacion,
            "factor_division": item.factor_division,
            "latest_data": item.latest_data,
            "createdAt": item.createdAt.isoformat() if item.createdAt else None,
            "updatedAt": item.updatedAt.isoformat() if item.updatedAt else None,
            "host": {
                "id": host.id,
                "hostname": host.hostname,
                "community": host.community,
                "enabled": host.enabled,
                "ip": host.ip,
                "url": f"api/v1/host/{host.id}",
                "createdAt": host.createdAt.isoformat() if host.createdAt else None,
                "updatedAt": host.updatedAt.isoformat() if host.updatedAt else None
            },
            "meterings": {
                "values": [],
                "tiempos": []
            }
        }

        for _, _, metering in result:
            if metering is not None:
                item_data["meterings"]["values"].append(metering.valor)
                item_data["meterings"]["tiempos"].append(
                    metering.tiempo.isoformat() if metering.tiempo else None
                )

        response = res.generate_response(item_data)
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@item_bp.put("/<int:id>")
def update_item(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400

        item = db.session.get(Items, id)
        if not item:
            response = res.generate_failed_msg_not_found_404("Item")
            return jsonify(response), 404

        allowed_fields = ['name', 'tipo', 'hostid', 'snmp_oid', 'acronimo', 'units', 'updateinterval', 'timeout',
                          'factor_multiplicacion', 'factor_division' , 'description', 'enabled','status_codes', 'latest_data']

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        if "name" in data:
            item.name = data["name"]

        if "tipo" in data:
            item.tipo = data["tipo"]

        if "hostid" in data:
            item.hostid = data["hostid"]

        if "snmp_oid" in data:
            item.snmp_oid = data["snmp_oid"]

        if "acronimo" in data:
            item.acronimo = data["acronimo"]

        if "units" in data:
            item.units = data["units"]
        
        if "status_codes" in data:
            item.status_codes = data["status_codes"]

        if "updateinterval" in data:
            try:
                item.updateinterval = convert_to_time(data["updateinterval"])
            except ValueError as ve:
                response = {"error": str(ve)}
                return jsonify(response), 400

        if "timeout" in data:
            item.timeout = data["timeout"]

        if "description" in data:
            item.description = data["description"]

        if "enabled" in data:
            item.enabled = data["enabled"]

        if "latest_data" in data:
            item.latest_data= data["latest_data"]

        if "factor_multiplicacion" in data:
            item.factor_multiplicacion = data["factor_multiplicacion"]

        if "factor_division" in data:
            item.factor_division= data["factor_division"]

        item.updatedAt = datetime.now() #Only for test (OK!)
        db.session.commit()

        result = item_schema_all.dump(item)
        response = res.generate_response_update_200(result, 'Item')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500
    
@item_bp.delete("/<int:id>")
def delete_item(id):
    try:
        item = db.session.get(Items, id)
        if not item:
            response = res.generate_failed_msg_not_found_404("Item")
            return jsonify(response), 404

        try:
            db.session.delete(item)
            db.session.commit()
            response = res.generate_response_delete_200(item.name)
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
