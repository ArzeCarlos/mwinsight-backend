#!/usr/bin/env python
# Copyright (c) 2014, Paessler AG <support@paessler.com>
# All rights reserved.
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions
#    and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
#    and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse
#    or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
ping.py

Módulo para ejecutar el comando ping en Windows y procesar su salida
en inglés y español.
"""

import os
import gc
import logging

logging.basicConfig(level=logging.DEBUG)

class Ping(object):
    def __init__(self):
        gc.enable()  # Está activo por defecto, pero es buena práctica.

    @staticmethod
    def get_itemdef():
        """
        Definición del item y los datos a mostrar.
        """
        sensordefinition = {
            "name": "Ping",
            "description": "Monitors the availability of a target using ICMP",
            "help": "Monitors the availability of a target using ICMP",
            "tag": "mwrping",
            "groups": [
                {
                    "name": "Ping Settings",
                    "caption": "Ping Settings",
                    "fields": [
                        {
                            "type": "integer",
                            "name": "timeout",
                            "caption": "Timeout (in s)",
                            "required": "1",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 300,
                            "help": "Timeout in seconds. A maximum value of 300 is allowed."
                        },
                        {
                            "type": "integer",
                            "name": "packsize",
                            "caption": "Packetsize (Bytes)",
                            "required": "1",
                            "default": 32,
                            "minimum": 1,
                            "maximum": 10000,
                            "help": "The default packet size for Ping requests is 32 bytes, "
                                    "but you can choose any other packet size between 1 and 10,000 bytes."
                        },
                        {
                            "type": "integer",
                            "name": "pingcount",
                            "caption": "Ping Count",
                            "required": "1",
                            "default": 1,
                            "minimum": 1,
                            "maximum": 20,
                            "help": "Enter the count of Ping requests will send to the device during an interval"
                        }
                    ]
                }
            ]
        }
        return sensordefinition

    def ping(self, target, count, timeout, packetsize):
        """
        Ejecuta el comando ping en Windows y parsea la salida para extraer:
         - Tiempos de respuesta (mínimo, promedio, máximo)
         - Pérdida de paquetes

        Soporta salida en inglés y español.
        """
        # Generar el comando de ping para Windows:
        # -n : Número de pings
        # -l : Tamaño del paquete en bytes
        # -w : Timeout en milisegundos
        command = "ping -n {} -l {} -w {} {}".format(count, packetsize, timeout * 1000, target)
        ret = os.popen(command)
        pingdata = ret.readlines()
        ret.close()
        
        logging.debug("Salida completa del comando ping: %s", pingdata)
        
        tiempos = []
        pack_loss = None

        # Función auxiliar para extraer el tiempo a partir de una línea dada y un marcador
        def extraer_tiempo(line_lower, marker):
            start_idx = line_lower.index(marker) + len(marker)
            # Buscamos la letra "m" que aparece en "ms" o en "m" (caso de <)
            end_idx = line_lower.find("m", start_idx)
            tiempo_str = line_lower[start_idx:end_idx].strip()
            # Si el valor es de la forma "<1" se asigna un valor fijo de 1 ms
            if tiempo_str.startswith("<"):
                return 1
            # Si se utiliza notación como "1m" (por error, pero se contempla) se convierte
            if tiempo_str.endswith("m"):
                try:
                    return int(tiempo_str[:-1]) * 1000
                except:
                    return 1
            return int(tiempo_str)

        for line in pingdata:
            line_lower = line.lower()

            # Verificar si la línea es respuesta del ping (inglés o español)
            if line_lower.startswith("reply from") or line_lower.startswith("respuesta desde"):
                # Comprobamos múltiples variantes: "time=" o "time<" para inglés y "tiempo=" o "tiempo<" para español
                marcador = None
                if "time=" in line_lower:
                    marcador = "time="
                elif "time<" in line_lower:
                    marcador = "time<"
                elif "tiempo=" in line_lower:
                    marcador = "tiempo="
                elif "tiempo<" in line_lower:
                    marcador = "tiempo<"
                
                if marcador:
                    try:
                        tiempo = extraer_tiempo(line_lower, marcador)
                        tiempos.append(tiempo)
                    except Exception as e:
                        logging.debug("Error al extraer el tiempo en la línea: %s | %s", line.strip(), e)
            
            # Procesar la línea que indica la pérdida de paquetes (inglés o español)
            if "lost =" in line_lower or "perdidos =" in line_lower:
                try:
                    partes = line.split(",")
                    for part in partes:
                        part_lower = part.lower()
                        if "lost =" in part_lower or "perdidos =" in part_lower:
                            # Extrae el número que sigue al signo "="
                            lost_str = part.split("=")[1].strip().split(" ")[0]
                            pack_loss = int(lost_str)
                except Exception as e:
                    logging.debug("Error al extraer la pérdida de paquetes en la línea: %s | %s", line.strip(), e)

        # Si no se obtuvieron tiempos o pérdida de paquetes, se considera que el host no es reachable.
        if not tiempos or pack_loss is None:
            return "Not reachable!"

        tiempo_min = min(tiempos)
        tiempo_max = max(tiempos)
        tiempo_avg = sum(tiempos) / len(tiempos)
        tiempo_mdev = 0  # En Windows se deja en 0

        channel_list = [
            {
                "name": "Ping Time Min",
                "mode": "float",
                "kind": "TimeResponse",
                "value": float(tiempo_min)
            },
            {
                "name": "Ping Time Avg",
                "mode": "float",
                "kind": "TimeResponse",
                "value": float(tiempo_avg)
            },
            {
                "name": "Ping Time Max",
                "mode": "float",
                "kind": "TimeResponse",
                "value": float(tiempo_max)
            },
            {
                "name": "Ping Time MDEV",
                "mode": "float",
                "kind": "TimeResponse",
                "value": float(tiempo_mdev)
            },
            {
                "name": "Packet Loss",
                "mode": "integer",
                "kind": "Percent",
                "value": pack_loss
            }
        ]
        return channel_list

    @staticmethod
    # def get_data(data, out_queue):
    def get_data(data):
        ping = Ping()
        try:
            pingdata = ping.ping(data['host'], data['pingcount'], data['timeout'], data['packsize'])
            if pingdata == "Not reachable!":
                data_r = {
                    "itemid": int(data['itemid']),
                    "error": "Exception",
                    "code": 1,
                    "message": f"{data['host']} is {pingdata}",
                    #"type": int(data['type'])
                    "type": 2
                }
            else:
                data_r = {
                    "itemid": int(data['itemid']),
                    "message": "OK",
                    "channel": pingdata,
                    "type": 2
                }
            logging.debug("Running item")
            logging.debug("Host: %s Pingcount: %s Timeout: %s Packetsize: %s", data['host'], data['pingcount'], data['timeout'], data['packsize'])
        except Exception as e:
            logging.error("Something went wrong with item %s. Error: %s", data['itemid'], e)
            data_r = {
                "itemid": int(data['itemid']),
                "error": "Exception",
                "code": 1,
                "message": "Ping failed.",
                "type": 2
            }
            # out_queue.put(data_r)
            # return 1
        finally:
            del ping
            gc.collect()
        # out_queue.put(data_r)
        return data_r
