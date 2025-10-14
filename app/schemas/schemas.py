from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import (Roles, SNMPFailures, Users, Hostgroups, Hosts, Items, Meterings,ReachbilityHistory,
                        EventTriggers, Diagrams, Shapes, Links_D, RFProjects, Sites, Antennas, Radios, Cables, Connectors, Links)

''' Para casos cuando se quiere hacer mas que deserializar 
class BaseSchema(SQLAlchemyAutoSchema):
    class Meta:
        load_instance = True '''
        
class RoleSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Roles
        
class UserSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        include_fk = True

class ItemsSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Items    

class HostSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Hosts

class HostgroupSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Hostgroups

class EventTriggerSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = EventTriggers

class MeteringSchema(SQLAlchemyAutoSchema):
    id = fields.Int()
    tiempo = fields.DateTime()
    value = fields.Str()

class DiagramSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Diagrams

class DiagramSchemaI(SQLAlchemyAutoSchema):
    class Meta:
        model = Diagrams
        exclude = ("description",)
    url = fields.Method("get_url")
    def get_url(self, obj):
        return f"api/v1/diagrams/{obj.id}"

class Link_DSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Links_D
    diagram = fields.Nested(DiagramSchemaI)

class ShapeSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Shapes
    diagram = fields.Nested(DiagramSchemaI)

class SNMPFailureSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = SNMPFailures

class RFProjectSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = RFProjects

class SiteSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Sites
        include_fk = True 

class AntennaSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Antennas
        include_fk = True 
class RadioSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Radios
        include_fk = True 

class CableSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Cables
        include_fk = True 

class ConnectorSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Connectors
        include_fk = True 

class LinkSchemaAll(SQLAlchemyAutoSchema):
    class Meta:
        model = Links
        include_fk = True 

class RoleSchemaNTRO(SQLAlchemyAutoSchema):
    class Meta:
        model = Roles
        exclude = ("name","tipo","read_only",)

class UserRoleSchemaNTRO(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        exclude = ("passwd",)
    role = fields.Nested(RoleSchemaNTRO)

class RoleSchemaTRO(SQLAlchemyAutoSchema):
    class Meta:
        model = Roles
        exclude = ("read_only",)
    url = fields.Method("get_url")
    def get_url(self, obj):
        return f"api/v1/roles/{obj.id}"

class UserRoleSchemaTRO(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        exclude = ("passwd",)
    role = fields.Nested(RoleSchemaTRO)

class ItemsSchemaNSKSL(SQLAlchemyAutoSchema):
    id = fields.Int()
    name = fields.Str()
    snmp_oid = fields.Str()
    tipo = fields.Str()
    status_code = fields.Int()
    latest_data = fields.Str()
    url = fields.Method("get_url")
    def get_url(self, obj):
        return f"api/v1/items/{obj.id}"

class MeteringItemSchemaNSKSL(SQLAlchemyAutoSchema):
    class Meta:
        model = Meterings
    item = fields.Nested(ItemsSchemaNSKSL)

class EventTriggerItemSchemaNSKSL(SQLAlchemyAutoSchema):
    class Meta:
        model = EventTriggers
    item = fields.Nested(ItemsSchemaNSKSL)

class ReachbilityHistoryAll(SQLAlchemyAutoSchema):
    class meta:
        model = ReachbilityHistory

role_schema_all = RoleSchemaAll()
roles_schema_all = RoleSchemaAll(many=True)
user_schema_all = UserSchemaAll()
users_schema_all = UserSchemaAll(many=True)
hostgroup_schema_all = HostgroupSchemaAll()
hostgroups_schema_all = HostgroupSchemaAll(many=True)
host_schema_all=HostSchemaAll()
item_schema_all = ItemsSchemaAll()
items_schema_all = ItemsSchemaAll(many=True)
event_trigger_schema_all = EventTriggerSchemaAll()
event_triggers_schema_all = EventTriggerSchemaAll(many=True)
metering_schema_all = MeteringSchema()
meterings_schema_all = MeteringSchema(many=True)
diagram_schema_all = DiagramSchemaAll()
shape_schema_all = ShapeSchemaAll()
shapes_schema_all = ShapeSchemaAll(many=True)
linkd_schema_all = Link_DSchemaAll()
linkds_schema_all = Link_DSchemaAll(many=True)
userroleTRO_schema = UserRoleSchemaTRO()
userroleNTRO_schema = UserRoleSchemaNTRO()
meteringitemschemansksl_schema = MeteringItemSchemaNSKSL()
eventtriggeritemschemansksl_schema= EventTriggerItemSchemaNSKSL()
snmpfailureschema_schema= SNMPFailureSchemaAll()
reachbilityhistory_schema_all = ReachbilityHistoryAll(many=True)
#eventtriggeritemschemansksls_schema= EventTriggerItemSchemaNSKSL(many=True)
### planning
rfproject_schema_all = RFProjectSchemaAll()
rfprojects_schema_all = RFProjectSchemaAll(many=True)
site_schema_all = SiteSchemaAll()
sites_schema_all = SiteSchemaAll(many=True)
antenna_schema_all = AntennaSchemaAll()
antennas_schema_all = AntennaSchemaAll(many=True)
radio_schema_all = RadioSchemaAll()
radios_schema_all = RadioSchemaAll(many=True)
cable_schema_all = CableSchemaAll()
cables_schema_all = CableSchemaAll(many=True)
connector_schema_all = ConnectorSchemaAll()
connectors_schema_all = ConnectorSchemaAll(many=True)
link_schema_all = LinkSchemaAll()