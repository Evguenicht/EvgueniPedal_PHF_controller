"""F1 26 (format UDP 2026) telemetry receiver for MOZA Integration."""
import math
import socket
import struct

DEFAULT_PORT = 20777
HEADER_SIZE = 29
PACKET_CAR_TELEMETRY = 6
PACKET_MOTION_EX = 13
PACKET_CAR_DAMAGE = 10
CAR_TELEMETRY_SIZE = 59
CAR_DAMAGE_SIZE = 46
CAR_DAMAGE_PACKET_SIZE = HEADER_SIZE + 24 * CAR_DAMAGE_SIZE


def _header(packet):
    if len(packet) < HEADER_SIZE:
        raise ValueError("F1 26 packet too short")
    packet_format = struct.unpack_from("<H", packet, 0)[0]
    packet_version = packet[5]
    packet_id = packet[6]
    frame_id = struct.unpack_from("<I", packet, 19)[0]
    player_index = packet[27]
    if packet_format != 2026:
        return None
    if player_index >= 24:
        return None
    return packet_version, packet_id, frame_id, player_index


def decode_car_telemetry(packet):
    """Decode player's speed/throttle/brake from packet ID 6 (1448 bytes)."""
    h = _header(packet)
    if h is None:
        return None
    version, packet_id, frame_id, player_index = h
    if packet_id != PACKET_CAR_TELEMETRY:
        return None
    if version != 1 or len(packet) != 1448:
        raise ValueError(f"F1 26 Car Telemetry invalid: version={version}, size={len(packet)}")
    base = HEADER_SIZE + player_index * CAR_TELEMETRY_SIZE
    speed_kmh = struct.unpack_from("<H", packet, base)[0]
    throttle = struct.unpack_from("<f", packet, base + 2)[0]
    brake = struct.unpack_from("<f", packet, base + 10)[0]
    if not all(math.isfinite(v) for v in (throttle, brake)):
        raise ValueError("F1 26 non-finite pedal telemetry")
    return {
        "frame_id": frame_id,
        "speed_kmh": float(speed_kmh),
        "throttle": max(0.0, min(1.0, float(throttle))),
        "brake": max(0.0, min(1.0, float(brake))),
    }


def decode_motion_ex(packet):
    """Decode wheel speed and slip ratio from packet ID 13 (273 bytes)."""
    h = _header(packet)
    if h is None:
        return None
    version, packet_id, frame_id, _player_index = h
    if packet_id != PACKET_MOTION_EX:
        return None
    if version != 1 or len(packet) != 273:
        raise ValueError(f"F1 26 Motion Ex invalid: version={version}, size={len(packet)}")
    # PacketMotionExData: 29-byte header, then suspension position/velocity/
    # acceleration (3 x 4 floats), wheelSpeed[4], wheelSlipRatio[4].
    wheel_speeds = struct.unpack_from("<4f", packet, HEADER_SIZE + 48)
    wheel_slips_raw = struct.unpack_from("<4f", packet, HEADER_SIZE + 64)
    if not all(math.isfinite(v) for v in (*wheel_speeds, *wheel_slips_raw)):
        raise ValueError("F1 26 non-finite wheel telemetry")
    return {
        "frame_id": frame_id,
        "wheel_speeds": tuple(float(v) for v in wheel_speeds),
        # Preserve the four per-wheel ratios; the common detector expects 0..1.
        "wheel_slips": tuple(max(0.0, min(1.0, abs(float(v)))) for v in wheel_slips_raw),
        "wheel_slip_ratio_raw": tuple(float(v) for v in wheel_slips_raw),
    }


def decode_car_damage(packet):
    """Decode per-wheel tyre wear from packet ID 10 (Car Damage, 1133 bytes).

    F1 26 m_tyresWear is expressed as percent worn: 0 = new, 100 = fully worn.
    """
    h = _header(packet)
    if h is None:
        return None
    version, packet_id, frame_id, player_index = h
    if packet_id != PACKET_CAR_DAMAGE:
        return None
    if version != 1 or len(packet) != CAR_DAMAGE_PACKET_SIZE:
        raise ValueError(
            f"F1 26 Car Damage invalid: version={version}, size={len(packet)}"
        )
    base = HEADER_SIZE + player_index * CAR_DAMAGE_SIZE
    wear_pct = struct.unpack_from("<4f", packet, base)
    if not all(math.isfinite(v) and -0.5 <= v <= 100.5 for v in wear_pct):
        raise ValueError("F1 26 invalid tyre-wear values")
    return {
        "frame_id": frame_id,
        "wheel_wear": tuple(max(0.0, min(1.0, float(v) / 100.0)) for v in wear_pct),
    }


class F126UDPReceiver:
    """Pairs Car Telemetry and Motion Ex packets by frame identifier."""
    def __init__(self, port=DEFAULT_PORT, host="0.0.0.0"):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, int(port)))
        self.socket.setblocking(False)
        self.telemetry = {}
        self.motion = {}
        self.damage = {}
        self.last_emitted_frame = None

    def read(self):
        # Drain all currently queued datagrams so the two packet types can be paired.
        for _ in range(128):
            try:
                packet, _addr = self.socket.recvfrom(4096)
            except BlockingIOError:
                break
            h = _header(packet)
            if h is None:
                continue
            packet_id = h[1]
            if packet_id == PACKET_CAR_TELEMETRY:
                item = decode_car_telemetry(packet)
                if item:
                    self.telemetry[item["frame_id"]] = item
            elif packet_id == PACKET_MOTION_EX:
                item = decode_motion_ex(packet)
                if item:
                    self.motion[item["frame_id"]] = item
            elif packet_id == PACKET_CAR_DAMAGE:
                item = decode_car_damage(packet)
                if item:
                    self.damage[item["frame_id"]] = item

        common = set(self.telemetry).intersection(self.motion)
        if not common:
            # Bound caches if one packet type is missing.
            if len(self.telemetry) > 8:
                self.telemetry = dict(sorted(self.telemetry.items())[-8:])
            if len(self.motion) > 8:
                self.motion = dict(sorted(self.motion.items())[-8:])
            if len(self.damage) > 8:
                self.damage = dict(sorted(self.damage.items())[-8:])
            return None

        frame_id = max(common)
        if frame_id == self.last_emitted_frame:
            return None
        telem = self.telemetry[frame_id]
        motion = self.motion[frame_id]
        available_damage_frames = [f for f in self.damage if f <= frame_id]
        damage = self.damage[max(available_damage_frames)] if available_damage_frames else None
        self.last_emitted_frame = frame_id
        self.telemetry = {k: v for k, v in self.telemetry.items() if k > frame_id}
        self.motion = {k: v for k, v in self.motion.items() if k > frame_id}
        self.damage = {k: v for k, v in self.damage.items() if k > frame_id - 120}
        result = {
            "speed_kmh": telem["speed_kmh"],
            "brake": telem["brake"],
            "throttle": telem["throttle"],
            "wheel_slips": motion["wheel_slips"],
            "wheel_slip_ratio_raw": motion["wheel_slip_ratio_raw"],
            "wheel_speeds": motion["wheel_speeds"],
            "telemetry_frame": frame_id,
        }
        if damage is not None:
            result["wheel_wear"] = damage["wheel_wear"]
            result["wear_frame"] = damage["frame_id"]
        return result

    def close(self):
        try:
            self.socket.close()
        except OSError:
            pass
