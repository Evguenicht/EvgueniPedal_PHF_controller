"""Récepteur et décodeur UDP officiel Forza Horizon 6 Data Out."""
import socket
import struct

PACKET_SIZE = 324
UDP_HOST = "0.0.0.0"
DEFAULT_PORT = 20444

def decode_packet(packet):
    if len(packet) != PACKET_SIZE:
        raise ValueError(f"Paquet FH6 invalide : {len(packet)} octets (attendu {PACKET_SIZE})")
    race_on = struct.unpack_from("<i", packet, 0)[0]
    if race_on != 1:
        return None

    # Champs FH6 documentés : vitesse @256, slip ratio @84, frein @316.
    speed_ms = struct.unpack_from("<f", packet, 256)[0]
    slip_ratio = struct.unpack_from("<4f", packet, 84)
    slip_angle = struct.unpack_from("<4f", packet, 164)
    combined_slip = struct.unpack_from("<4f", packet, 180)
    brake_raw = packet[316]

    values = (speed_ms, *slip_ratio, *slip_angle, *combined_slip)
    if not all(struct.isfinite(v) if hasattr(struct, "isfinite") else
               (v == v and abs(v) != float("inf")) for v in values):
        raise ValueError("Valeur télémétrique FH6 non finie")

    # Le détecteur commun attend un glissement de freinage positif.
    # TireSlipRatio FH6 est signé ; on conserve la magnitude pour détecter
    # aussi bien le blocage que le patinage, avec freinage comme condition.
    wheel_slips = tuple(min(1.0, abs(float(v))) for v in slip_ratio)
    return {
        "speed_kmh": max(0.0, float(speed_ms) * 3.6),
        "brake": brake_raw / 255.0,
        "wheel_slips": wheel_slips,
        "tire_slip_ratio": tuple(float(v) for v in slip_ratio),
        "tire_slip_angle": tuple(float(v) for v in slip_angle),
        "tire_combined_slip": tuple(float(v) for v in combined_slip),
        "throttle": packet[315] / 255.0,
    }

class ForzaUDPReceiver:
    def __init__(self, port=DEFAULT_PORT, host=UDP_HOST):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, int(port)))
        self.socket.settimeout(0.001)

    def read(self):
        try:
            packet, _ = self.socket.recvfrom(2048)
        except socket.timeout:
            return None
        return decode_packet(packet)

    def close(self):
        self.socket.close()
