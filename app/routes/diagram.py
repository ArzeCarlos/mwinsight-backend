# diagram.py
from typing import Dict
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from app.models import Diagrams, Shapes, Links_D, ReachbilityHistory, db
from app.utils import utilities as res
from app.schemas.schemas import diagram_schema_all, reachbilityhistory_schema_all
from core.checkers.asynping import AsyPing
diagram_bp = Blueprint('diagram', __name__)

@diagram_bp.post("/")
def create_diagram():
    try:
        data= request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        mandatory_fields= ["name", "description"]
        missing_fields = [field for field in mandatory_fields if field not in data]
        if missing_fields:
            response = res.generate_failed_post_missparams(missing_fields)
            return jsonify(response), 400

        unknown_fields = [field for field in data.keys() if field not in mandatory_fields]
        if unknown_fields:
            response = res.generate_failed_invalid_params()
            return jsonify(response), 400
        new_diagram = Diagrams(
            name=data['name'],
            description=data['description'],
        )
        db.session.add(new_diagram)
        db.session.commit()
        result = diagram_schema_all.dump(new_diagram) 
        response =   res.generate_response_create_200(result,"diagram")
        return jsonify(response), 201

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@diagram_bp.get("/")
def get_diagrams():
    try:
        stmt = (
            db.session.query(Diagrams, Shapes, Links_D)
            .join(Shapes, Diagrams.id == Shapes.diagramid)
            .join(Links_D, Diagrams.id == Links_D.diagramid)
        )
        results = stmt.all()

        if not results:
            response = res.generate_failed_msg_not_found_200("Diagrams")
            return jsonify(response), 200

        diagrams_dict = defaultdict(lambda: {"shapes": [], "links": []})

        for diagram, shape, link in results:
            d_id = diagram.id
            if "name" not in diagrams_dict[d_id]:
                diagrams_dict[d_id]["name"] = diagram.name
                diagrams_dict[d_id]["description"] = diagram.description
                diagrams_dict[d_id]["id"] = diagram.id
            # Shapes
            shape_data = {
                "id": shape.identifier,
                "x": shape.posX,
                "y": shape.posY,
                "name": shape.name,
                "ip": shape.ip
            }
            if shape_data not in diagrams_dict[d_id]["shapes"]:
                diagrams_dict[d_id]["shapes"].append(shape_data)

            # Links
            link_data = {
                "idSource": link.identifierBeg,
                "idTarget": link.identifierEnd
            }
            if link_data not in diagrams_dict[d_id]["links"]:
                diagrams_dict[d_id]["links"].append(link_data)

        result = list(diagrams_dict.values())
        total_count = db.session.query(func.count(Diagrams.id)).scalar()

        response = res.generate_response_all(result, total_count)
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception as e:  # noqa: F841
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@diagram_bp.get("/<int:id>")
def get_diagram(id):
    try:
        try:
            id = int(id)
            if id <= 0:
                response = res.generate_failed_message_error_id()
                return jsonify(response), 400
        except ValueError:
            response = res.generate_failed_message_error_id()
            return jsonify(response), 400

        stmt = (
            db.session.query(Diagrams, Shapes, Links_D)
            .join(Shapes, Diagrams.id == Shapes.diagramid)
            .join(Links_D, Diagrams.id == Links_D.diagramid)
            .filter(Diagrams.id == id)
        )
        results = stmt.all()

        if not results:
            response = res.generate_failed_msg_not_found_404("Diagram")
            return jsonify(response), 404

        diagram_data = {"shapes": [], "links": []}

        for diagram, shape, link in results:
            if "name" not in diagram_data:
                diagram_data["name"] = diagram.name
                diagram_data["description"] = diagram.description
                diagram_data["id"] =  diagram.id
            # Shapes
            shape_data = {
                "id": shape.identifier,
                "x": shape.posX,
                "y": shape.posY,
                "name": shape.name,
                "ip": shape.ip
            }
            if shape_data not in diagram_data["shapes"]:
                diagram_data["shapes"].append(shape_data)

            # Links
            link_data = {
                "idSource": link.identifierBeg,
                "idTarget": link.identifierEnd
            }
            if link_data not in diagram_data["links"]:
                diagram_data["links"].append(link_data)

        response = res.generate_response(diagram_data)
        return jsonify(response), 200

    except DatabaseError:
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503

    except Exception:
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@diagram_bp.put("/<int:id>")
def update_diagram(id):
    try:
        data = request.get_json()
        if not data:
            response = res.generate_failed_params()
            return jsonify(response), 400
        diagram = db.session.query(Diagrams).where(Diagrams.id == id).scalar()

        if not diagram:
            response = res.generate_failed_msg_not_found_404("Diagram")
            return jsonify(response), 404
        
        allowed_fields = ['name', 'description']
        if not any(field in data for field in allowed_fields):
            response = res.generate_failed_invalid_fields()
            return jsonify(response), 400

        diagram.name = data["name"]
        diagram.description = data["description"]
        db.session.commit()
        result =diagram_schema_all.dump(diagram)
        response = res.generate_response_update_200(result,'Diagram')
        return jsonify(response), 200

    except DatabaseError as db_error:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_dberror()
        return jsonify(response), 503
    except Exception as e:  # noqa: F841
        db.session.rollback()
        response = res.generate_failed_message_exception()
        return jsonify(response), 500

@diagram_bp.delete("/<int:id>")
def delete_diagram(id):
    try:
        diagram = db.session.get(Diagrams, id)
        if not diagram:
            response = res.generate_failed_msg_not_found_404("diagram")
            return jsonify(response), 404

        try:
            db.session.delete(diagram)
            db.session.commit()
            response = res.generate_response_delete_200(diagram.name)
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

@diagram_bp.post("/ping")
def get_availability():
    try:
        data = request.get_json()
        if not data or 'ips' not in data:
            return jsonify({"error": "No IPs provided"}), 400

        ips = data['ips']
        results_availability = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ip = {
                executor.submit(
                    lambda ip_data: asyncio.run(AsyPing.get_data({
                        "host": ip_data.get("host"),
                        "itemid": ip_data.get("itemid", 0),
                        "pingcount": ip_data.get("pingcount", 4),
                        "timeout": ip_data.get("timeout", 1),
                        "packsize": ip_data.get("packsize", 32)
                    })), ip_data
                ): ip_data for ip_data in ips
            }

            for future in as_completed(future_to_ip):
                ip_data = future_to_ip[future]
                try:
                    result = future.result()
                    result["host"] = ip_data.get("host")
                    results_availability.append(result)
                    insertReachbilityHist(result,True)
                except Exception as e:
                    results_availability.append({
                        "itemid": ip_data.get("itemid", 0),
                        "host": ip_data.get("host"),
                        "error": "Exception",
                        "code": 1,
                        "message": str(e),
                        "type": 2
                    })
                    insertReachbilityHist(result,False)


        return jsonify(results_availability), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

def insertReachbilityHist(result:Dict, flagState:bool)->None:
    if flagState:
        resReachHist = {
            "host_ip": result["host"],
            "alcanzable": True,
            "ping_min":result["channel"][0]["value"],
            "ping_avg":result["channel"][1]["value"],
            "ping_max":result["channel"][2]["value"],
            "packet_loss":result["channel"][4]["value"],
            "nota": ""
        }
        new_reachHist= ReachbilityHistory(**resReachHist)
        db.session.add(new_reachHist)
        db.session.commit()
    else:
        resReachHist = {
            "host_ip": result["host"],
            "alcanzable": False,
            "nota": "",
        }
        new_reachHist= ReachbilityHistory(**resReachHist)
        db.session.add(new_reachHist)
        db.session.commit()



@diagram_bp.get("/ping")
def get_pings_data():
    try:
        reachilility_ok = request.args.get('reachbilityOk')
        reachbility_failed = request.args.get('reachbilityFailed')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        print(start_date_str,end_date_str)
        stmt = db.session.query(ReachbilityHistory)
        
        if reachilility_ok and reachilility_ok.lower() == 'true':
            stmt = stmt.filter(ReachbilityHistory.alcanzable.is_(True))
        elif reachbility_failed and reachbility_failed.lower() == 'true':
            stmt = stmt.filter(ReachbilityHistory.alcanzable.is_(False))

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M")
                stmt = stmt.filter(ReachbilityHistory.tiempo.between(start_date, end_date))
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido, usar YYYY-MM-DDTHH:MM:SS"}), 400

        results = stmt.all()

        serialized_results = [
            {
                "id": r.id,
                "host_ip": r.host_ip,
                "tiempo": r.tiempo.isoformat() if r.tiempo else None,
                "alcanzable": r.alcanzable,
                "ping_min": r.ping_min,
                "ping_max": r.ping_max,
                "ping_avg": r.ping_avg,
                "packet_loss": r.packet_loss,
                "nota": r.nota
            } for r in results
        ]

        response = res.generate_response_create_200(serialized_results, "reachbility")
        return jsonify(response), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500
