# models.py
import uuid
from datetime import datetime, time
from sqlalchemy import Integer, String, Float, Boolean, DateTime, Time, UniqueConstraint, ForeignKey, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

## Monitoring

class Roles(db.Model):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipo: Mapped[int] = mapped_column(Integer, nullable=False) #1->Admin(Role/Usuarios),#2->Ingeniero(Todo),#3->Tecnico(Lectura)
    read_only: Mapped[bool] = mapped_column(Boolean, default=False)
    users: Mapped[list] = relationship('Users', backref='roles', cascade="all, delete-orphan")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Role {self.name}>"

class Users(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    firstname: Mapped[str] = mapped_column(String(40), nullable=False)
    lastname: Mapped[str] = mapped_column(String(60))
    passwd: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    autologout: Mapped[time] = mapped_column(Time, default=time(0, 30, 0))
    refresh: Mapped[time] = mapped_column(Time, default=time(0, 0, 30))
    roleid: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id', ondelete="CASCADE"), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<User {self.username}>"

class Hostgroups(db.Model):
    __tablename__ = 'hostgroups'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(120), nullable=False)
    hosts: Mapped[list] = relationship('Hosts', backref='hostgroups', cascade="all, delete-orphan")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Group {self.name}-{self.model}>"

class Hosts(db.Model):
    __tablename__ = 'hosts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    groupid: Mapped[int] = mapped_column(Integer, ForeignKey('hostgroups.id', ondelete="CASCADE"), nullable=False)
    ip: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    snmpenabled: Mapped[bool] = mapped_column(Boolean, default=False)
    community: Mapped[str] = mapped_column(String(120), default='')
    description: Mapped[str] = mapped_column(String(120))  # Se asume que puede ser nulo, sino agregar nullable=False
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tag: Mapped[str] = mapped_column(String(20), nullable=False)
    items: Mapped[list] = relationship('Items', backref='host', cascade="all, delete-orphan")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Host {self.hostname}>"

class Items(db.Model):
    __tablename__ = 'items'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[int] = mapped_column(Integer, default=1)  # 1->snmp, 2->others, 3->Trap(No UI)
    hostid: Mapped[int] = mapped_column(Integer, ForeignKey('hosts.id', ondelete="CASCADE"), nullable=False)
    snmp_oid: Mapped[str] = mapped_column(String(100))  # Tiene ser único por host (se puede agregar constraint a nivel de tabla)
    acronimo: Mapped[str] = mapped_column(String(100))       # Tiene ser único por host #Cambiar Nombre
    units: Mapped[str] = mapped_column(String(10))
    status_codes: Mapped[int] = mapped_column(Integer, default=200)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    updateinterval: Mapped[time] = mapped_column(Time, default=time(0, 0, 30))
    timeout: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    latest_data: Mapped[str] = mapped_column(String(100), default='')
    factor_multiplicacion: Mapped[float] = mapped_column(Float, default=1.0, nullable=True)
    factor_division: Mapped[float] = mapped_column(Float, default=1.0, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('hostid', 'snmp_oid', name='uq_hostid_snmp_oid'),
        UniqueConstraint('hostid', 'acronimo', name='uq_hostid_acronimo'),
    )

    def __repr__(self):
        return f"<Item {self.id}>"

class Meterings(db.Model):
    __tablename__ = 'meterings'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    itemid: Mapped[int] = mapped_column(Integer, ForeignKey('items.id', ondelete="CASCADE"), nullable=False)
    tiempo: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, index=True)
    valor: Mapped[str] = mapped_column(String(60), nullable=False) #cambiado
    latencia: Mapped[float] = mapped_column(Float, nullable=True) #nuevo
    def __repr__(self):
        return f"<Metering {self.id}>"

class ReachbilityHistory(db.Model):
    __tablename__ = 'reachbilityhistory'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_ip: Mapped[str] = mapped_column(String(120), nullable=False)
    tiempo: Mapped[datetime] = mapped_column(DateTime(timezone=True), default = datetime.now, index=True)
    alcanzable: Mapped[bool] = mapped_column(Boolean, default=True)
    ping_min: Mapped[float] = mapped_column(Float, nullable=True)
    ping_max: Mapped[float] = mapped_column(Float, nullable=True)
    ping_avg: Mapped[float] = mapped_column(Float, nullable=True)
    packet_loss: Mapped[int] = mapped_column(Integer, nullable=True)
    nota: Mapped[str] = mapped_column(String(20), nullable=True)

class SNMPFailures(db.Model):
    __tablename__ = 'snmpfailures'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    itemid: Mapped[int] = mapped_column(Integer, ForeignKey('items.id', ondelete="CASCADE"), nullable=False)
    host_ip: Mapped[str] = mapped_column(String(120), nullable=False)
    oid: Mapped[str] = mapped_column(String(120), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(255), nullable=True)  # Guarda "SNMP error indication: Timeout"
    valor: Mapped[str] = mapped_column(String(30), nullable=True)   # Guarda el valor si llegó algo pero fue None
    tiempo: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, index=True)

    def __repr__(self):
        return f"<SNMPFailure item={self.itemid} host={self.host_ip} at={self.timestamp}>"


class EventTriggers(db.Model):
    __tablename__ = 'eventtriggers'
    id: Mapped[int]= mapped_column(Integer, primary_key=True)
    itemid: Mapped[int]= mapped_column(Integer,ForeignKey('items.id',ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(String(120),nullable=True)
    data_type: Mapped[str]= mapped_column(String(30), nullable=False)
    expression: Mapped[str]= mapped_column(String(30), nullable=True)
    max_evento: Mapped[float]= mapped_column(Float, nullable=True)
    min_evento: Mapped[float]= mapped_column(Float, nullable=True)
    counter: Mapped[int]= mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Eventtrigger {self.id}>"

class Diagrams(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(40), nullable=False)

    shapes = relationship("Shapes", backref="diagram", cascade="all, delete")
    links_d = relationship("Links_D", backref="diagram", cascade="all, delete")
    
class Shapes(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    posX: Mapped[int] = mapped_column(Integer, nullable=False)
    posY: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str] = mapped_column(String(120), nullable=False)
    diagramid: Mapped[int] = mapped_column(Integer, ForeignKey('diagrams.id', ondelete="CASCADE"), nullable=False)

class Links_D(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifierBeg: Mapped[str] = mapped_column(String(60), nullable=False)
    identifierEnd: Mapped[str] = mapped_column(String(60), nullable=False)
    diagramid: Mapped[int] = mapped_column(Integer, ForeignKey('diagrams.id', ondelete="CASCADE"), nullable=False)


## Planning
class RFProjects(db.Model):
    __tablename__ = 'rfprojects'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False, unique= True)
    description: Mapped[str] = mapped_column(String(120), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

class Sites(db.Model):
    __tablename__ = 'sites'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[DECIMAL(9,6)] = mapped_column(DECIMAL(9,6), nullable=False) # type: ignore
    longitude: Mapped[DECIMAL(9,6)] = mapped_column(DECIMAL(9,6), nullable=False) # type: ignore
    description: Mapped[str] = mapped_column(String(120), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    projectid: Mapped[int] = mapped_column(Integer, ForeignKey('rfprojects.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Site {self.id}>"

class Antennas(db.Model):
    __tablename__ =  'antennas'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(60), nullable=False)
    frequency_band: Mapped[str] = mapped_column(String(60), nullable=False)
    gain: Mapped[float] = mapped_column(Float, nullable=False)
    diameter: Mapped[float] = mapped_column(Float, nullable=False)
    radome_losses: Mapped[float] = mapped_column(Float, nullable=True, default=0)
    comments: Mapped[str] = mapped_column(String(120), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    projectid: Mapped[int] = mapped_column(Integer, ForeignKey('rfprojects.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Antenna {self.id}>"

class Radios(db.Model):
    __tablename__ = 'radios'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(60), nullable=False)
    frequency_band: Mapped[str] = mapped_column(String(60), nullable=False)
    modulation: Mapped[str] = mapped_column(String(60), nullable=False)
    transmission_power: Mapped[float] = mapped_column(Float, nullable=False)
    receiver_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    comments: Mapped[str] = mapped_column(String(120), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    projectid: Mapped[int] = mapped_column(Integer, ForeignKey('rfprojects.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Radio {self.id}>"

class Cables(db.Model):
    __tablename__ = 'cables'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    loss_per_meter: Mapped[float] = mapped_column(Float, nullable=False)
    comments: Mapped[str] = mapped_column(String(120), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    projectid: Mapped[int] = mapped_column(Integer, ForeignKey('rfprojects.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Cable {self.id}>"

class Connectors(db.Model):
    __tablename__ = 'connectors'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    insertion_loss: Mapped[float] = mapped_column(Float, nullable=False)
    comments: Mapped[str] = mapped_column(String(120), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    projectid: Mapped[int] = mapped_column(Integer, ForeignKey('rfprojects.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Connector {self.id} >"

class Links(db.Model):
    __tablename__ = 'links'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    site_a_id: Mapped[int] = mapped_column(Integer, ForeignKey('sites.id', ondelete="CASCADE"), nullable=False)
    site_b_id: Mapped[int] = mapped_column(Integer, ForeignKey('sites.id', ondelete="CASCADE"), nullable=False)
    # --- Site A ---
    antenna_a_id: Mapped[int] = mapped_column(Integer, ForeignKey("antennas.id", ondelete="CASCADE"), nullable=False)
    radio_a_id:   Mapped[int] = mapped_column(Integer, ForeignKey("radios.id",   ondelete="CASCADE"), nullable=False)
    cable_a_id:   Mapped[int] = mapped_column(Integer, ForeignKey("cables.id",   ondelete="CASCADE"), nullable=False)
    # --- Site B ---
    antenna_b_id: Mapped[int] = mapped_column(Integer, ForeignKey("antennas.id", ondelete="CASCADE"), nullable=False)
    radio_b_id:   Mapped[int] = mapped_column(Integer, ForeignKey("radios.id",   ondelete="CASCADE"), nullable=False)
    cable_b_id:   Mapped[int] = mapped_column(Integer, ForeignKey("cables.id",   ondelete="CASCADE"), nullable=False)
    # Connector
    connector_id: Mapped[int] = mapped_column(Integer, ForeignKey("connectors.id", ondelete="CASCADE"), nullable=False)
    # Height, distance
    antenna_height_a: Mapped[float] = mapped_column(Float, nullable=False)
    antenna_height_b: Mapped[float] = mapped_column(Float, nullable=False)
    distance:         Mapped[float] = mapped_column(Float, default=0)
    # Metadata
    description: Mapped[str]       = mapped_column(String(120))
    createdAt:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=datetime.now)
    updatedAt:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    projectid: Mapped[int] = mapped_column(Integer, ForeignKey('rfprojects.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        return f"<Links {self.id}>"
