# link.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.exc import DatabaseError
from app.models import Links, db, Antennas, Radios, Cables, Connectors, Sites
from app.utils import utilities as res
from app.schemas.schemas import link_schema_all

link_bp = Blueprint('link', __name__)

@link_bp.post("/")
def post_link():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        mandatory_fields = ["name","site_a_id", "site_b_id", "antenna_a_id", "antenna_b_id", "radio_a_id", "radio_b_id", "cable_a_id",
        "cable_b_id", "connector_id", "antenna_height_a",
                            "antenna_height_b","projectid"]
        optional_fields = ["description", "distance"]
        allowed_fields = mandatory_fields + optional_fields
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in allowed_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        ## Debo validar que ambas sitios no sean el mismo
        link_data = {
            "name": data['name'],
            "site_a_id": data['site_a_id'],
            "site_b_id": data['site_b_id'],
            "antenna_a_id": data['antenna_a_id'],
            "antenna_b_id": data['antenna_b_id'],
            "radio_a_id": data['radio_a_id'],
            "radio_b_id": data['radio_b_id'],
            "cable_a_id": data['cable_a_id'],
            "cable_b_id": data['cable_b_id'],
            "connector_id": data['connector_id'],
            "antenna_height_a": data['antenna_height_a'],
            "antenna_height_b": data['antenna_height_b'],
            "projectid": data['projectid'],
        }
        if "distance" in data:
            link_data["distance"] = data["distance"]
        if "description" in data:
            link_data["description"] = data["description"]

        new_link = Links(**link_data)
        db.session.add(new_link)
        db.session.commit()
        result = link_schema_all.dump(new_link)
        response = res.generate_response_create_200(result, "link")
        return jsonify(response), 201

    except DatabaseError as db_error:
        print(db_error)
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:
        print(e)
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_bp.post("/<id>") # invalid route
def invalid_link(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 405

@link_bp.get("/")
def get_links():
    try:
        project_id = request.args.get("projectId")
        site_a      = aliased(Sites)
        site_b      = aliased(Sites)

        antenna_a   = aliased(Antennas)
        antenna_b   = aliased(Antennas)

        radio_a     = aliased(Radios)
        radio_b     = aliased(Radios)

        cable_a     = aliased(Cables)
        cable_b     = aliased(Cables)

        stmt = (
            db.session.query(
                Links,                 
                site_a, site_b,        
                antenna_a, antenna_b,  
                radio_a, radio_b,      
                cable_a, cable_b,      
                Connectors             
            )
            .join(site_a,    Links.site_a_id      == site_a.id)
            .join(site_b,    Links.site_b_id      == site_b.id)

            .join(antenna_a, Links.antenna_a_id   == antenna_a.id)
            .join(antenna_b, Links.antenna_b_id   == antenna_b.id)

            .join(radio_a,   Links.radio_a_id     == radio_a.id)
            .join(radio_b,   Links.radio_b_id     == radio_b.id)

            .join(cable_a,   Links.cable_a_id     == cable_a.id)
            .join(cable_b,   Links.cable_b_id     == cable_b.id)

            .join(Connectors, Links.connector_id     == Connectors.id)
        )
        if project_id:
            stmt = stmt.filter(Links.projectid == project_id)
        resultsquery = stmt.all()
        if resultsquery:
            links_serialized = {}
            for link, sa, sb, anta, antb, rada, radb, caba, cabb, conn in resultsquery:
                if link.id not in links_serialized:
                    links_serialized[link.id] = {
                        "id": link.id,
                        "antenna_height_a": link.antenna_height_a,
                        "antenna_height_b": link.antenna_height_b,
                        "distance": link.distance,
                        "description": link.description,
                        "createdAt": link.createdAt.isoformat() if link.createdAt else None,
                        "updatedAt": link.updatedAt.isoformat() if link.updatedAt else None,
                        "name": link.name,
                        "projectid": link.projectid,
                        "site_a": {
                            "id": sa.id,
                            "name": sa.name,
                            "latitude": float(sa.latitude),
                            "longitude": float(sa.longitude),
                            "description": sa.description,
                            "createdAt": sa.createdAt.isoformat() if sa.createdAt else None,
                            "updatedAt": sa.updatedAt.isoformat() if sa.updatedAt else None,
                        },
                        "site_b": {
                            "id": sb.id,
                            "name": sb.name,
                            "latitude": float(sb.latitude),
                            "longitude": float(sb.longitude),
                            "description": sb.description,
                            "createdAt": sb.createdAt.isoformat() if sb.createdAt else None,
                            "updatedAt": sb.updatedAt.isoformat() if sb.updatedAt else None,
                        },
                        "antenna_a": {
                            "id": anta.id,
                            "name": anta.name,
                            "gain": anta.gain,
                            "diameter": anta.diameter,
                            "createdAt": anta.createdAt.isoformat() if anta.createdAt else None,
                            "updatedAt": anta.updatedAt.isoformat() if anta.updatedAt else None,
                        },
                        "antenna_b": {
                            "id": antb.id,
                            "name": antb.name,
                            "gain": antb.gain,
                            "diameter": antb.diameter,
                            "createdAt": antb.createdAt.isoformat() if antb.createdAt else None,
                            "updatedAt": antb.updatedAt.isoformat() if antb.updatedAt else None,
                        },
                        "radio_a": {
                            "id": rada.id,
                            "name": rada.name,
                            "frequency_band": rada.frequency_band,
                            "transmission_power": rada.transmission_power,
                            "receiver_threshold": rada.receiver_threshold,
                            "createdAt": rada.createdAt.isoformat() if rada.createdAt else None,
                            "updatedAt": rada.updatedAt.isoformat() if rada.updatedAt else None,
                        },
                        "radio_b": {
                            "id": radb.id,
                            "name": radb.name,
                            "frequency_band": radb.frequency_band,
                            "transmission_power": radb.transmission_power,
                            "receiver_threshold": radb.receiver_threshold,
                            "createdAt": radb.createdAt.isoformat() if radb.createdAt else None,
                            "updatedAt": radb.updatedAt.isoformat() if radb.updatedAt else None,
                        },
                        "cable_a": {
                            "id": caba.id,
                            "name": caba.name,
                            "loss_per_meter": caba.loss_per_meter,
                            "comments": caba.comments,
                            "createdAt": caba.createdAt.isoformat() if caba.createdAt else None,
                            "updatedAt": caba.updatedAt.isoformat() if caba.updatedAt else None,
                        },
                        "cable_b": {
                            "id": cabb.id,
                            "name": cabb.name,
                            "loss_per_meter": cabb.loss_per_meter,
                            "comments": cabb.comments,
                            "createdAt": cabb.createdAt.isoformat() if cabb.createdAt else None,
                            "updatedAt": cabb.updatedAt.isoformat() if cabb.updatedAt else None,
                        },
                        "connector": {
                            "id": conn.id,
                            "name": conn.name,
                            "insertion_loss": conn.insertion_loss,
                            "comments": conn.comments,
                            "createdAt": conn.createdAt.isoformat() if conn.createdAt else None,
                            "updatedAt": conn.updatedAt.isoformat() if conn.updatedAt else None,
                        },
                    }
            links_data = list(links_serialized.values())
            total_count = stmt.count()
            # total_count = db.session.query(func.count(Links.id)).scalar()
            response = res.generate_response_all(links_data,total_count)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Links")
            return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_bp.get("/<id>")
def get_link(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        site_a      = aliased(Sites)
        site_b      = aliased(Sites)

        antenna_a   = aliased(Antennas)
        antenna_b   = aliased(Antennas)

        radio_a     = aliased(Radios)
        radio_b     = aliased(Radios)

        cable_a     = aliased(Cables)
        cable_b     = aliased(Cables)

        stmt = (
            db.session.query(
                Links,                 
                site_a, site_b,        
                antenna_a, antenna_b,  
                radio_a, radio_b,      
                cable_a, cable_b,      
                Connectors             
            )
            .join(site_a,    Links.site_a_id      == site_a.id)
            .join(site_b,    Links.site_b_id      == site_b.id)

            .join(antenna_a, Links.antenna_a_id   == antenna_a.id)
            .join(antenna_b, Links.antenna_b_id   == antenna_b.id)

            .join(radio_a,   Links.radio_a_id     == radio_a.id)
            .join(radio_b,   Links.radio_b_id     == radio_b.id)

            .join(cable_a,   Links.cable_a_id     == cable_a.id)
            .join(cable_b,   Links.cable_b_id     == cable_b.id)

            .join(Connectors, Links.connector_id     == Connectors.id)
            .filter(Links.id == id)
        )
        row = stmt.first()
        if not row:
            response = res.generate_failed_msg_not_found_404("Link")
            return jsonify(response), 404

        link, sa, sb, anta, antb, rada, radb, caba, cabb, conn = row
        link_data = {
            "id": link.id,
            "projectid": link.projectid,
            "antenna_height_a": link.antenna_height_a,
            "antenna_height_b": link.antenna_height_b,
            "distance": link.distance,
            "description": link.description,
            "createdAt": link.createdAt.isoformat() if link.createdAt else None,
            "updatedAt": link.updatedAt.isoformat() if link.updatedAt else None,
            "name": link.name,
            "site_a": {
                "id": sa.id,
                "name": sa.name,
                "latitude": float(sa.latitude),
                "longitude": float(sa.longitude),
                "description": sa.description,
                "createdAt": sa.createdAt.isoformat() if sa.createdAt else None,
                "updatedAt": sa.updatedAt.isoformat() if sa.updatedAt else None,
            },
            "site_b": {
                "id": sb.id,
                "name": sb.name,
                "latitude": float(sb.latitude),
                "longitude": float(sb.longitude),
                "description": sb.description,
                "createdAt": sb.createdAt.isoformat() if sb.createdAt else None,
                "updatedAt": sb.updatedAt.isoformat() if sb.updatedAt else None,
            },
            "antenna_a": {
                "id": anta.id,
                "name": anta.name,
                "gain": anta.gain,
                "diameter": anta.diameter,
                "createdAt": anta.createdAt.isoformat() if anta.createdAt else None,
                "updatedAt": anta.updatedAt.isoformat() if anta.updatedAt else None,
            },
            "antenna_b": {
                "id": antb.id,
                "name": antb.name,
                "gain": antb.gain,
                "diameter": antb.diameter,
                "createdAt": antb.createdAt.isoformat() if antb.createdAt else None,
                "updatedAt": antb.updatedAt.isoformat() if antb.updatedAt else None,
            },
            "radio_a": {
                "id": rada.id,
                "name": rada.name,
                "frequency_band": rada.frequency_band,
                "transmission_power": rada.transmission_power,
                "receiver_threshold": rada.receiver_threshold,
                "createdAt": rada.createdAt.isoformat() if rada.createdAt else None,
                "updatedAt": rada.updatedAt.isoformat() if rada.updatedAt else None,
            },
            "radio_b": {
                "id": radb.id,
                "name": radb.name,
                "frequency_band": radb.frequency_band,
                "transmission_power": radb.transmission_power,
                "receiver_threshold": radb.receiver_threshold,
                "createdAt": radb.createdAt.isoformat() if radb.createdAt else None,
                "updatedAt": radb.updatedAt.isoformat() if radb.updatedAt else None,
            },
            "cable_a": {
                "id": caba.id,
                "name": caba.name,
                "loss_per_meter": caba.loss_per_meter,
                "comments": caba.comments,
                "createdAt": caba.createdAt.isoformat() if caba.createdAt else None,
                "updatedAt": caba.updatedAt.isoformat() if caba.updatedAt else None,
            },
            "cable_b": {
                "id": cabb.id,
                "name": cabb.name,
                "loss_per_meter": cabb.loss_per_meter,
                "comments": cabb.comments,
                "createdAt": cabb.createdAt.isoformat() if cabb.createdAt else None,
                "updatedAt": cabb.updatedAt.isoformat() if cabb.updatedAt else None,
            },
            "connector": {
                "id": conn.id,
                "name": conn.name,
                "insertion_loss": conn.insertion_loss,
                "comments": conn.comments,
                "createdAt": conn.createdAt.isoformat() if conn.createdAt else None,
                "updatedAt": conn.updatedAt.isoformat() if conn.updatedAt else None,
            },
        }

        response = res.generate_response(link_data)
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@link_bp.put("/<id>")
def update_link(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        link = db.session.query(Links).where(Links.id == id).scalar()

        if not link:
            response = res.generate_failed_msg_not_found_404("Link")
            return jsonify(response), 404

        allowed_fields = ["name","site_a_id", "site_b_id", "antenna_a_id", "antenna_b_id", "radio_a_id", "radio_b_id", 
                          "cable_a_id", "cable_b_id", "connector_id", "antenna_height_a",
                            "antenna_height_b", "description", "distance"]
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                setattr(link, field, data[field])

        db.session.commit()
        result = link_schema_all.dump(link)
        response = res.generate_response_update_200(result, 'Link')
        return jsonify(response), 200
    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@link_bp.delete("/<id>")
def delete_link(id):
    try:
        link = db.session.get(Links, id)
        if not link:
            response = res.generate_failed_msg_not_found_404("link")
            return jsonify(response), 404

        try:
            db.session.delete(link)
            db.session.commit()
            response = res.generate_response_delete_200(link.name)
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


