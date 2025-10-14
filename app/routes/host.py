# host.py
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import DatabaseError
from sqlalchemy import func
from app.models import Hosts,Items,Hostgroups,db
from app.schemas.schemas import  host_schema_all
from app.utils.utilities import generate_failed_invalid_post 
from app.utils import utilities as res

host_bp = Blueprint('host', __name__)

@host_bp.post("/")
def create_host():
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
        mandatory_fields = ["hostname", "groupid", "ip", "snmpenabled", "description", "enabled", "tag"]
        optional_fields = ["community"]
        allowed_fields = mandatory_fields + optional_fields

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400
        unknown_fields = [field for field in data.keys() if field not in allowed_fields]

        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        host_data = {
            "hostname": data['hostname'],
            "groupid": data['groupid'],
            "ip": data['ip'],
            "snmpenabled": data['snmpenabled'],
            "description": data['description'],
            "enabled": data['enabled'],
            "tag": data['tag'],
        }
        if "community" in data:
            host_data["community"] = data["community"]

        new_host = Hosts(**host_data)
        db.session.add(new_host)
        db.session.commit()
        result = host_schema_all.dump(new_host)
        response = res.generate_response_create_200(result,"Host")
        return jsonify(response), 201
    
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@host_bp.post("/<id>")
def invalid_host(id):
    response = generate_failed_invalid_post()
    return jsonify(response), 500

@host_bp.get("/stats")
def stats_hosts():
    try:
        groupid = request.args.get('groupId')
        stmt = (
            db.session.query(
                Hosts.hostname,
                func.count(Items.id)
            )
            .outerjoin(Items, Hosts.id == Items.hostid)
            .filter(Hosts.groupid == groupid)
            .group_by(Hosts.id, Hosts.hostname)
        )
        resultquery= stmt.all()
        data = [{"name": hostname, "y": total} for hostname, total in resultquery]
        return jsonify(data),200
    
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@host_bp.get("/")
def get_hosts():
    try:
        valid_params = {'groupId', 'sort_by', 'order', 'enabled','enabledGraph', 'names'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("Hosts", unknown_params)
            return jsonify(response), 400
        groupid = request.args.get('groupId')
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        enabled = request.args.get('enabled')
        names = request.args.get('names')
        enabled_graph = request.args.get('enabledGraph')

        valid_columns = {'id', 'hostname', 'tag', 'community', 'enabled', 'createdAt', 'updatedAt'}
        if sort_by not in valid_columns:
            return jsonify(res.generate_failed_message_unknown("Users", [sort_by])), 400

        stmt = (
            db.session.query(Hosts, Hostgroups, Items)
            .join(Hostgroups, Hosts.groupid == Hostgroups.id)
            .outerjoin(Items, Items.hostid == Hosts.id)
        )

        filters = []
        if names:
            stmtNames = db.session.query(Hosts.hostname).all()
            responseNames = [x[0] for x in stmtNames]
            return jsonify({"names": responseNames}), 200

        if enabled:
            count_true = db.session.query(func.count()).filter(Hosts.enabled).scalar()
            count_false = db.session.query(func.count()).filter(not Hosts.enabled).scalar()
            statusresponse = {
                "enabledHost": count_true,
                "disabledHost": count_false
            }
            return jsonify(statusresponse), 200

        print(groupid)
        if enabled_graph and groupid:
            count_true = (
                db.session.query(func.count(Hosts.id))
                .filter(Hosts.enabled == 1, Hosts.groupid == groupid)
                .scalar()
            )

            count_false = (
                db.session.query(func.count(Hosts.id))
                .filter(Hosts.enabled == 0, Hosts.groupid == groupid)
                .scalar()
            )

            statusresponse = {
                "enabledHost": count_true,
                "disabledHost": count_false
            }
            return jsonify(statusresponse), 200

        if groupid:
            filters.append(Hosts.groupid == groupid)
        if filters:
            stmt = stmt.filter(*filters)

        sort_column = getattr(Hosts, sort_by, None)
        if order.lower() == 'desc':
            sort_column = sort_column.desc()
        stmt = stmt.order_by(sort_column)

        resultsquery = stmt.all()
        if resultsquery:
            hosts_serialized = {}

            for host, hostgroup, item in resultsquery:
                if host.id not in hosts_serialized:
                    hosts_serialized[host.id] = {
                        "id": host.id,
                        "hostname": host.hostname,
                        "ip": host.ip,
                        "community": host.community,
                        "enabled": host.enabled,
                        "snmpenabled": host.snmpenabled,
                        "tag": host.tag,
                        "createdAt": host.createdAt.isoformat() if host.createdAt else None,
                        "updatedAt": host.updatedAt.isoformat() if host.updatedAt else None,
                        "hostgroup": {
                            "id": hostgroup.id,
                            "name": hostgroup.name,
                            "url": f"api/v1/hostgroups/{hostgroup.id}",
                            "createdAt": hostgroup.createdAt.isoformat() if hostgroup.createdAt else None,
                            "updatedAt": hostgroup.updatedAt.isoformat() if hostgroup.updatedAt else None
                        },
                        "items": []
                    }

                if item is not None:
                    existing_items = hosts_serialized[host.id]["items"]
                    # Evitar ítems duplicados por joins múltiples
                    if not any(i["id"] == item.id for i in existing_items):
                        existing_items.append({
                            "id": item.id,
                            # "key": item.key,
                            # "name": item.name,
                            "url": f"api/v1/items/{item.id}",
                            # "createdAt": item.createdAt.isoformat() if item.createdAt else None,
                            # "updatedAt": item.updatedAt.isoformat() if item.updatedAt else None
                        })

            hosts_data = list(hosts_serialized.values())
            total_count = db.session.query(func.count(Hosts.id)).scalar()
            response = res.generate_response_all(hosts_data, total_count)
            return jsonify(response), 200

        else:
            response = res.generate_failed_msg_not_found_200("Host")
            return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@host_bp.get("/<id>")
def get_host(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        resultquery = (
            db.session.query(Hosts, Hostgroups, Items)
            .join(Hostgroups, Hosts.groupid == Hostgroups.id)
            .outerjoin(Items, Items.hostid == Hosts.id)
            .filter(Hosts.id == id)
        ).all()

        if resultquery:
            host_data = None
            items_list = []

            for host, hostgroup, item in resultquery:
                if host_data is None:
                    host_data = {
                        "id": host.id,
                        "hostname": host.hostname,
                        "ip": host.ip,
                        "community": host.community,
                        "enabled": host.enabled,
                        "snmpenabled": host.snmpenabled,
                        "tag": host.tag,
                        "hostgroup": {
                            "id": hostgroup.id,
                            "name": hostgroup.name,
                            "url": f"api/v1/hostgroups/{hostgroup.id}"
                        },
                        "items": []
                    }

                if item is not None and not any(i["id"] == item.id for i in items_list):
                    items_list.append({
                        "id": item.id,
                        "acronimo": item.acronimo,
                        "name": item.name,
                        "enabled": item.enabled,
                        "url": f"api/v1/items/{item.id}",
                        "createdAt": item.createdAt.isoformat() if item.createdAt else None,
                        "updatedAt": item.updatedAt.isoformat() if item.updatedAt else None
                    })

            host_data["items"] = items_list

            valid_fields = {"hostname", "ip", "snmpenabled", "community", "description", "enabled", "tag"}
            parameters = request.args.get("fields")
            if parameters:
                parameters_list = [p.strip() for p in parameters.split(",") if p.strip()]
                invalid_fields = [p for p in parameters_list if p not in valid_fields]
                if invalid_fields:
                    response = res.generate_failed_invalid_fields("Host", invalid_fields)
                    return jsonify(response), 400

                filtered_data = {
                    "id": host_data["id"],
                    "hostgroup": host_data["hostgroup"],
                    "items": host_data["items"]
                }
                for field in parameters_list:
                    if field in host_data:
                        filtered_data[field] = host_data[field]
                host_data = filtered_data

            response = res.generate_response(host_data)
            return jsonify(response), 200

        else:
            response = res.generate_failed_msg_not_found_404("Host")
            return jsonify(response), 404

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@host_bp.put("/<int:id>")
def update_host(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400

        host = db.session.get(Hosts, id)
        if not host:
            response = res.generate_failed_msg_not_found_404("User")
            return jsonify(response), 404
    

        allowed_fields = ['community','hostname', 'groupid', 'ip', 'snmpenabled', 'description', 'tag','enabled']

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                setattr(host, field, data[field])

        db.session.commit()
        result = host_schema_all.dump(host)
        response = res.generate_response_update_200(result,'Host')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@host_bp.delete("/<int:id>")
def delete_host(id):
    try:
        host = db.session.get(Hosts, id)
        if not host:
            response = res.generate_failed_msg_not_found_404("Host")
            return jsonify(response), 404

        try:
            db.session.delete(host)
            db.session.commit()
            response = res.generate_response_delete_200(host.hostname)
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
