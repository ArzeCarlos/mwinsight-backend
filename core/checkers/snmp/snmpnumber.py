#!/usr/bin/env python
# Copyright (c) 2014, Paessler AG <support@paessler.com>
# All rights reserved.
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
# and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse
# or promote products derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
import asyncio
import time
from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.proto.rfc1902 import (
    Integer, OctetString, ObjectIdentifier, IpAddress,
    Counter32, Counter64, Gauge32, TimeTicks, Unsigned32, Null
)

class SNMPCustomNumber:
    @staticmethod
    def get_sensordef():
        """
        Definición del item y los datos a mostrar.
        """
        
        sensordefinition = {
            "name": "SNMP Custom Numerical",
            "description": "Monitors a numerical value returned by a specific OID using SNMP",
            "help": "Monitors a numerical value returned by a specific OID using SNMP",
            "tag": "snmpcustomnumerical",
            "groups": [
                {
                    "name": "OID values",
                    "caption": "OID values",
                    "fields": [
                        {
                            "type": "edit",
                            "name": "oid",
                            "caption": "OID Value",
                            "required": "1",
                            "help": "Please enter the OID value."
                        },
                        {
                            "type": "edit",
                            "name": "unit",
                            "caption": "Unit String",
                            "default": "#",
                            "help": "Enter a 'unit' string, e.g. 'ms', 'Kbyte' (for display purposes only)."
                        },
                        {
                            "type": "radio",
                            "name": "value_type",
                            "caption": "Value Type",
                            "required": "1",
                            "help": ("Select 'Gauge' if you want to see absolute values (e.g. for temperature value) "
                                     "or 'Delta' for counter differences divided by time period "
                                     "(e.g. for bandwidth values)"),
                            "options": {
                                "1": "Gauge",
                                "2": "Delta"
                            },
                            "default": 1
                        },
                        {
                            "type": "integer",
                            "name": "multiplication",
                            "caption": "Multiplication",
                            "required": "1",
                            "default": 1,
                            "help": "Provide a value the raw SNMP value is to be multiplied by."
                        },
                        {
                            "type": "integer",
                            "name": "division",
                            "caption": "Division",
                            "required": "1",
                            "default": 1,
                            "help": "Provide a value the raw SNMP value is divided by."
                        },
                        {
                            "type": "radio",
                            "name": "snmp_version",
                            "caption": "SNMP Version",
                            "required": "1",
                            "help": "Choose your SNMP Version",
                            "options": {
                                "1": "V1",
                                "2": "V2c",
                                "3": "V3"
                            },
                            "default": 2
                        },
                        {
                            "type": "edit",
                            "name": "community",
                            "caption": "Community String",
                            "required": "1",
                            "help": "Please enter the community string."
                        },
                        {
                            "type": "integer",
                            "name": "port",
                            "caption": "Port",
                            "required": "1",
                            "default": 161,
                            "help": "Provide the SNMP port"
                        }
                    ]
                }
            ]
        }
        return sensordefinition

    async def snmp_get(self, oid: str, target: str, snmp_type: str, community: str,
                       port: int, unit: str, multiplication: int = 1, division: int = 1) -> dict:
        """
        Realiza una consulta SNMP de manera asíncrona, y retorna la respuesta procesada.
        """
        snmpEngine = SnmpEngine()
        try:
            # transport_target = await UdpTransportTarget.create((target, port))
            transport_target = await UdpTransportTarget.create((target, port), timeout=1.5, retries=1)
            iterator = get_cmd(
                snmpEngine,
                CommunityData(community, mpModel=1),
                transport_target,
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            
            error_indication, error_status, error_index, var_binds = await iterator

            if error_indication:
                return {
                "name": "Value",
                "mode": "string",
                "kind": "custom",
                "customunit": str(unit),
                "value": None,
                "error": f"SNMP error indication: {error_indication}"
                }
            if error_status:
                return {
                "name": "Value",
                "mode": "string",
                "kind": "custom",
                "customunit": str(unit),
                "value": None,
                "error": f"SNMP error status: {error_status.prettyPrint()} at {error_index}"
                }

            raw_value = var_binds[0][1]

            processed_value = None

            try:
                numeric_value = float(raw_value)
                processed_value = (numeric_value * multiplication) / division
            except (ValueError, TypeError):
                if isinstance(raw_value, (Integer, Unsigned32, Counter32, Counter64, Gauge32, TimeTicks)):
                    try:
                        numeric_value = int(raw_value)
                        processed_value = (numeric_value * multiplication) / division
                    except Exception:
                        processed_value = int(raw_value)
                elif isinstance(raw_value, OctetString):
                    try:
                        processed_value = raw_value.prettyPrint()
                    except Exception:
                        processed_value = str(raw_value)
                elif isinstance(raw_value, ObjectIdentifier):
                    processed_value = raw_value.prettyPrint()
                elif isinstance(raw_value, IpAddress):
                    processed_value = str(raw_value)
                elif isinstance(raw_value, Null):
                    processed_value = None
                else:
                    try:
                        processed_value = raw_value.prettyPrint()
                    except Exception:
                        processed_value = str(raw_value)

            if snmp_type == "1":
                channel = {
                    "name": "Value",
                    "mode": "integer" if isinstance(processed_value, (int, float)) else "string",
                    "kind": "custom",
                    "customunit": str(unit),
                    "value": processed_value
                }
            else:
                channel = {
                    "name": "Value",
                    "mode": "counter" if isinstance(processed_value, (int, float)) else "string",
                    "kind": "custom",
                    "customunit": str(unit),
                    "value": processed_value
                }

            return channel
        except Exception as e:
            print(e)
        finally:
            snmpEngine.close_dispatcher()

    async def get_data_async(self, data: dict) -> dict:
        """
        Versión asíncrona que recopila y retorna lo1s datos SNMP junto con el tiempo de respuesta.
        """
        try:
            # resolution
            start_time =  time.perf_counter()
            # standard
            # start_time = time.monotonic()
            channel_data = await self.snmp_get(
                oid=str(data['oid']),
                target=data['host'],
                snmp_type=data['value_type'],
                community=data['community'],
                port=int(data['port']),
                unit=data['unit'],
                multiplication=int(data['multiplication']),
                division=int(data['division'])
            )
            # standard
            # end_time = time.monotonic()
            # resolution
            end_time =  time.perf_counter()
            response_time = (end_time - start_time) * 1000 #ms
            response_channel = {
                "name": "Response Time",
                "mode": "float",
                "kind": "TimeResponse",
                "value": response_time
            }

            result = {
                "itemid": int(data['itemid']),
                "message": "OK",
                # "type": int(data['type']),
                "type":1,
                "channel": [channel_data, response_channel]
            }
        except Exception as e:
            end_time =  time.perf_counter() #If fails
            logging.error(f"Something went wrong with item {data['itemid']}. Error: {e}")
            result = {
                "itemid": int(data['itemid']),
                "error": "Exception",
                "code": 1,
                "type":1,
                "message": "SNMP Request failed. See log for details"
            }
        return result

    # def get_data(data: dict, out_queue) -> int:
    def get_data(data: dict) -> int:
        """
        Función sincrónica que actúa como envoltorio para la versión asíncrona.
        Ejecuta get_data_async y envía el resultado a out_queue.
        """
        try:
            result = asyncio.run(SNMPCustomNumber().get_data_async(data))
        except Exception as run_error:
            logging.error("Error running asyncio loop: %s", run_error)
            result = {
                "itemid": int(data.get('itemid', -1)),
                "error": "Exception",
                "code": 1,
                "message": "Failed to run the async SNMP request."
            }
        # out_queue.put(result)
        return result
