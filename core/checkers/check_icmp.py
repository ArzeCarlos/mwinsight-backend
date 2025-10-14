import subprocess

def check_icmp_pinger(ip: str) -> bool:
    """
    Ejecuta un ping a la dirección IP dada.
    Args:
        ip (str): La dirección IP del host al que se va a hacer ping.
    Returns:
        bool: True si el ping fue exitoso, False si falló.
    """
    try:
        command = ['ping', '-n', '1', ip]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:  
            return True
        else:  
            return False

    except Exception as e:
        return False
