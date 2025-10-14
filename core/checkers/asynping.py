import asyncio
import gc
import logging

logging.basicConfig(level=logging.DEBUG)

class AsyPing:
    def __init__(self):
        gc.enable()

    async def ping(self, target, count, timeout, packetsize):
        """
        Ejecuta el comando ping en Windows de forma asíncrona.
        """
        command = f"ping -n {count} -l {packetsize} -w {int(timeout * 1000)} {target}"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        ping_output = stdout.decode(errors="ignore").splitlines()
        logging.debug("Salida completa del comando ping: %s", ping_output)

        tiempos = []
        pack_loss = None

        def extraer_tiempo(line_lower, marker):
            start_idx = line_lower.index(marker) + len(marker)
            end_idx = line_lower.find("m", start_idx)
            tiempo_str = line_lower[start_idx:end_idx].strip()
            if tiempo_str.startswith("<"):
                return 1
            if tiempo_str.endswith("m"):
                try:
                    return int(tiempo_str[:-1]) * 1000
                except:
                    return 1
            return int(tiempo_str)

        for line in ping_output:
            line_lower = line.lower()

            if line_lower.startswith("reply from") or line_lower.startswith("respuesta desde"):
                marcador = None
                for key in ("time=", "time<", "tiempo=", "tiempo<"):
                    if key in line_lower:
                        marcador = key
                        break
                if marcador:
                    try:
                        tiempos.append(extraer_tiempo(line_lower, marcador))
                    except Exception as e:
                        logging.debug("Error al extraer el tiempo en la línea: %s | %s", line.strip(), e)

            if "lost =" in line_lower or "perdidos =" in line_lower:
                try:
                    partes = line.split(",")
                    for part in partes:
                        part_lower = part.lower()
                        if "lost =" in part_lower or "perdidos =" in part_lower:
                            lost_str = part.split("=")[1].strip().split(" ")[0]
                            pack_loss = int(lost_str)
                except Exception as e:
                    logging.debug("Error al extraer la pérdida de paquetes en la línea: %s | %s", line.strip(), e)

        if not tiempos or pack_loss is None:
            return "Not reachable!"

        tiempo_min = min(tiempos)
        tiempo_max = max(tiempos)
        tiempo_avg = sum(tiempos) / len(tiempos)

        return [
            {"name": "Ping Time Min", "mode": "float", "kind": "TimeResponse", "value": float(tiempo_min)},
            {"name": "Ping Time Avg", "mode": "float", "kind": "TimeResponse", "value": float(tiempo_avg)},
            {"name": "Ping Time Max", "mode": "float", "kind": "TimeResponse", "value": float(tiempo_max)},
            {"name": "Ping Time MDEV", "mode": "float", "kind": "TimeResponse", "value": 0.0},
            {"name": "Packet Loss", "mode": "integer", "kind": "Percent", "value": pack_loss},
        ]

    @staticmethod
    async def get_data(data):
        ping = AsyPing()
        try:
            pingdata = await ping.ping(data['host'], data['pingcount'], data['timeout'], data['packsize'])
            if pingdata == "Not reachable!":
                data_r = {
                    "itemid": int(data['itemid']),
                    "error": "Exception",
                    "code": 1,
                    "message": f"{data['host']} is {pingdata}",
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
        except Exception as e:
            logging.error("Something went wrong with item %s. Error: %s", data['itemid'], e)
            data_r = {
                "itemid": int(data['itemid']),
                "error": "Exception",
                "code": 1,
                "message": "Ping failed.",
                "type": 2
            }
        finally:
            del ping
            gc.collect()
        return data_r
