import os
from flask import Flask, jsonify
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_cors import CORS 
from sqlalchemy import text
from flask_migrate import Migrate
from dotenv import load_dotenv
from urllib.parse import quote_plus  # ✅ Para codificar rutas en la URI

migrate = Migrate()
load_dotenv()

ma = Marshmallow()
bcrypt = Bcrypt()

def run_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)

    # CORS
    # CORS(
    #     app,
    #     resources={
    #         r"/api/*": {"origins": "*"},
    #         r"/login": {"origins": "*"},  
    #         r"/checkpwd": {"origins": "*"},  
    #         r"/diagram": {"origins": "*"}  
    #     }
    # )    

    # ✅ Obtener la ruta al certificado SSL
    ssl_ca_path = os.getenv("DB_SSL_CA")
    if ssl_ca_path:
        ssl_ca_path = quote_plus(os.path.join(os.getcwd(), ssl_ca_path))  # Codifica y usa ruta absoluta

    # ✅ Configurar la URI de conexión con el certificado
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        f"?ssl_ca={ssl_ca_path}"
    )

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY_FLASK')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('DB_TRACK', 'False').lower() == 'true'  

    from app.models import db

    # Inicializar extensiones
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    # Registrar blueprints
    from app.routes.role import role_bp
    from app.routes.user import user_bp
    from app.routes.hostgroup import hostgroup_bp
    from app.routes.host import host_bp
    from app.routes.item import item_bp
    from app.routes.common import common_bp
    from app.routes.metering import metering_bp
    from app.routes.diagram import diagram_bp
    from app.routes.link_d import link_d_bp
    from app.routes.shape import shape_bp
    from app.routes.elevation import elevation_bp
    from app.routes.site import site_bp
    from app.routes.antenna import antenna_bp
    from app.routes.radio import radio_bp
    from app.routes.cable import cable_bp
    from app.routes.connector import connector_bp
    from app.routes.link import link_bp
    from app.routes.simulation import simulation_bp

    app.register_blueprint(role_bp, url_prefix='/api/v1/roles', name='role_blueprint')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users', name='user_blueprint')
    app.register_blueprint(hostgroup_bp, url_prefix='/api/v1/hostgroups', name='hostgroup_blueprint')
    app.register_blueprint(host_bp, url_prefix='/api/v1/hosts', name='host_blueprint')
    app.register_blueprint(item_bp, url_prefix='/api/v1/items', name='item_blueprint')
    app.register_blueprint(metering_bp, url_prefix='/api/v1/meterings', name='metering_blueprint')
    app.register_blueprint(diagram_bp, url_prefix="/api/v1/diagrams", name='diagram_blueprint')
    app.register_blueprint(link_d_bp, url_prefix="/api/v1/linkds", name='linkd_blueprint')
    app.register_blueprint(shape_bp, url_prefix="/api/v1/shapes", name='shape_blueprint')
    app.register_blueprint(elevation_bp, url_prefix="/api/v1/elevations", name='elevation_blueprint')
    app.register_blueprint(site_bp, url_prefix="/api/v1/sites", name='site_blueprint')
    app.register_blueprint(antenna_bp, url_prefix="/api/v1/antennas", name='antenna_blueprint')
    app.register_blueprint(radio_bp, url_prefix="/api/v1/radios", name='radio_blueprint')
    app.register_blueprint(cable_bp, url_prefix="/api/v1/cables", name='cable_blueprint')
    app.register_blueprint(connector_bp, url_prefix="/api/v1/connectors", name='connector_blueprint')
    app.register_blueprint(link_bp, url_prefix="/api/v1/links", name='link_blueprint')
    app.register_blueprint(simulation_bp, url_prefix="/api/v1/simulations", name='simulation_blueprint')
    app.register_blueprint(common_bp, url_prefix="/", name='common_blueprint')

    @app.errorhandler(404)
    def not_found(error):
        from app.utils.utilities import generate_failed_url_not_found
        response = generate_failed_url_not_found()
        return jsonify(response), 404

    return app
