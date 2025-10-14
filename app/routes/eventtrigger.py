# eventtrigger.py
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Items, EventTriggers, db
from app.schemas.schemas import (event_trigger_schema_all,event_triggers_schema_all,
                                  eventtriggeritemschemansksl_schema)
from app.utils import utilities as res

event_trigger_bp = Blueprint('eventtrigger', __name__)


@event_trigger_bp.post("/")
def create_event_trigger():
    try:
        data = request.get_json()
        print("Datos recibidos:", data)
        if not data:
            response = res.generate_failed_params()
            return jsonify(response),400
        mandatory_fields = ["name", "itemid", "data_type", "enabled"]
        optional_fields = ["description", "expression", "max_evento", "min_evento", "counter"]
        allowed_fields = mandatory_fields + optional_fields

        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400
        unknown_fields = [field for field in data.keys() if field not in allowed_fields]

        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400

        event_trigger_data = {
            "name": data['name'],
            "itemid": data['itemid'],
            "data_type": data['data_type'],
            "enabled": data['enabled'],
        }
        if "description" in data:
            event_trigger_data["description"] = data["description"]
        if "expression" in data:
            event_trigger_data["expression"] = data["expression"]
        if "max_evento" in data:
            event_trigger_data["max_evento"] = data["max_evento"]
        if "min_evento" in data:
            event_trigger_data["min_evento"] = data["min_evento"]
        if "counter" in data:
            event_trigger_data["counter"] = data["counter"]

        new_event_trigger = EventTriggers(**event_trigger_data)
        db.session.add(new_event_trigger)
        db.session.commit()
        result = event_trigger_schema_all.dump(new_event_trigger)
        response = res.generate_response_create_200(result, "Event_Trigger")
        return jsonify(response), 201

    except DatabaseError as db_error:
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@event_trigger_bp.post("/<id>")
def invalid_host(id):
    response = res.generate_failed_invalid_post()
    return jsonify(response), 500


@event_trigger_bp.get("/")
def get_event_triggers():
    try:
        valid_params = {'sort_by', 'order', 'itemid'}
        query_params = request.args
        unknown_params = [param for param in query_params if param not in valid_params]
        if unknown_params:
            response = res.generate_failed_message_unknown("Event_Triggers", unknown_params)
            return jsonify(response), 400

        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        itemid = request.args.get('itemid')
        # Validación de columna para el ordenamiento.
        valid_columns = {'id', 'createdAt', 'updatedAt'}
        if sort_by not in valid_columns:
            return jsonify(res.generate_failed_message_unknown("Event_Triggers", [sort_by])), 400

        stmt = db.session.query(EventTriggers, Items).join(Items, EventTriggers.itemid == Items.id)

        if itemid:
            try:
                itemid_int = int(itemid)
            except ValueError:
                return jsonify(res.generate_failed_message("El parámetro itemid debe ser un entero.")), 400

            stmt = stmt.filter(Items.id == itemid_int)

        sort_column = getattr(EventTriggers, sort_by, None)
        if order.lower() == 'desc':
            sort_column = sort_column.desc()
        stmt = stmt.order_by(sort_column)

        resultsquery = stmt.all()

        if resultsquery:
            event_trigger_data_list = []
            for event_trigger, item in resultsquery:
                event_trigger_data = eventtriggeritemschemansksl_schema.dump({"item": item, **event_trigger.__dict__})
                event_trigger_data_list.append(event_trigger_data)

            response = res.generate_response(event_trigger_data_list)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_200("Event_Triggers")
            return jsonify(response), 200

    except DatabaseError as db_error:
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@event_trigger_bp.get("/<id>")
def get_event_trigger(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400
        resultquery = db.session.query(EventTriggers, Items).join(Items, EventTriggers.itemid == Items.id).where(EventTriggers.id == id).first()
        if resultquery:
            event_trigger, item = resultquery
            event_trigger_data = eventtriggeritemschemansksl_schema.dump({"item": item, **event_trigger.__dict__})
            response = res.generate_response(event_trigger_data)
            return jsonify(response), 200
        else:
            response = res.generate_failed_msg_not_found_404("Event_Trigger")
            return jsonify(response), 404

    except DatabaseError as db_error:
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@event_trigger_bp.put("/<int:id>")
def update_event_trigger(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400

        event_trigger = db.session.get(EventTriggers, id)
        if not event_trigger:
            response = res.generate_failed_msg_not_found_404("Event_Trigger")
            return jsonify(response), 404

        allowed_fields = ['name', 'itemid', 'data_type', 'expression', 'max_evento', 'min_evento', 'counter', 'description', 'enabled']

        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        for field in allowed_fields:
            if field in data:
                setattr(event_trigger, field, data[field])

        db.session.commit()
        result = event_trigger_schema_all.dump(event_trigger)
        response = res.generate_response_update_200(result, 'Event_Trigger')
        return jsonify(response), 200

    except DatabaseError as db_error:
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500


@event_trigger_bp.delete("/<int:id>")
def delete_event_trigger(id):
    try:
        event_trigger = db.session.get(EventTriggers, id)
        if not event_trigger:
            response = res.generate_failed_msg_not_found_404("Event_Trigger")
            return jsonify(response), 404

        try:
            db.session.delete(event_trigger)
            db.session.commit()
            response = res.generate_response_delete_200(event_trigger.value)
            return jsonify(response), 200

        except DatabaseError as db_error:
            db.session.rollback()
            response = res.generate_failed_message_dberror()
            return jsonify(response), 503

        except Exception as e:
            db.session.rollback()
            response = res.generate_response_delete_500(id)
            return jsonify(response), 500

    except Exception as e:

        response = res.generate_failed_message_exception()
        return jsonify(response), 500
