import json
import math
import os
import socket
import struct
import time

DEFAULT_DURATION = 0.5
VX_RANGE = (-2.5, 3.8)
VY_RANGE = (-1.0, 1.0)
VYAW_RANGE = (-4.0, 4.0)

DEFAULT_NAV_HOST = "127.0.0.1"
DEFAULT_NAV_PORT = 5432
DEFAULT_NAV_TIMEOUT = 5.0
DEFAULT_NAV_FRAME = "map"
DEFAULT_STATE_FRAME = "odom"


class SkillManager:
    def __init__(self, sport_client, place_memory, state_reader):
        self.sport_client = sport_client
        self.place_memory = place_memory
        self.state_reader = state_reader

        self.nav_host = os.getenv("GO2_NAV_HOST", DEFAULT_NAV_HOST)
        self.nav_port = int(os.getenv("GO2_NAV_PORT", str(DEFAULT_NAV_PORT)))
        self.nav_timeout = float(os.getenv("GO2_NAV_TIMEOUT", str(DEFAULT_NAV_TIMEOUT)))
        self.nav_frame = (os.getenv("GO2_NAV_FRAME", DEFAULT_NAV_FRAME) or DEFAULT_NAV_FRAME).strip()
        self.state_frame = (os.getenv("GO2_STATE_FRAME", DEFAULT_STATE_FRAME) or DEFAULT_STATE_FRAME).strip()

    @staticmethod
    def _clamp(value, lower, upper):
        return max(lower, min(upper, value))

    @staticmethod
    def _is_number(value):
        return isinstance(value, (int, float))

    @staticmethod
    def _normalize_quaternion(qx, qy, qz, qw):
        norm = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
        if norm <= 1e-9:
            return 0.0, 0.0, 0.0, 1.0
        return qx / norm, qy / norm, qz / norm, qw / norm

    def _validate_pose(self, pose):
        if not isinstance(pose, dict):
            return False, "pose_must_be_dict"
        position = pose.get("position")
        orientation = pose.get("orientation")
        if not isinstance(position, dict):
            return False, "pose_missing_position"
        if not isinstance(orientation, dict):
            return False, "pose_missing_orientation"
        for axis in ("x", "y", "z"):
            if not self._is_number(position.get(axis)):
                return False, f"position_{axis}_must_be_number"
        for axis in ("x", "y", "z", "w"):
            if not self._is_number(orientation.get(axis)):
                return False, f"orientation_{axis}_must_be_number"
        return True, None

    def _extract_planar_quat(self, orientation):
        qx = float(orientation.get("x", 0.0))
        qy = float(orientation.get("y", 0.0))
        qz = float(orientation.get("z", 0.0))
        qw = float(orientation.get("w", 1.0))
        qx, qy, qz, qw = self._normalize_quaternion(qx, qy, qz, qw)
        yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
        half_yaw = 0.5 * yaw
        return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)

    def stand_up(self):
        self.sport_client.RecoveryStand()
        return {"success": True}

    def stand_down(self):
        self.sport_client.StandDown()
        return {"success": True}

    def move_forward(self, vx=0.0):
        self.sport_client.Move(self._clamp(vx, VX_RANGE[0], VX_RANGE[1]), 0.0, 0.0)
        return {"success": True}

    def move_lateral(self, vy=0.0):
        self.sport_client.Move(0.0, self._clamp(vy, VY_RANGE[0], VY_RANGE[1]), 0.0)
        return {"success": True}

    def move_rotate(self, vyaw=0.0):
        self.sport_client.Move(0.0, 0.0, self._clamp(vyaw, VYAW_RANGE[0], VYAW_RANGE[1]))
        return {"success": True}

    def sit_down(self):
        self.sport_client.Sit()
        return {"success": True}

    def hello(self):
        self.sport_client.Hello()
        return {"success": True}

    def stretch(self):
        self.sport_client.Stretch()
        return {"success": True}

    def wallow(self):
        self.sport_client.Wallow()
        return {"success": True}

    def scrape(self):
        self.sport_client.Scrape()
        return {"success": True}

    def front_jump(self):
        self.sport_client.FrontJump()
        return {"success": True}

    def hand_stand(self):
        self.sport_client.HandStand(True)
        time.sleep(4)
        self.sport_client.HandStand(False)
        return {"success": True}

    def memory_position(self, name: str, pose: dict = None):
        name = str(name).strip()
        if not name:
            return {"success": False, "error": "invalid_name"}

        if pose is None:
            pose = self.state_reader.get_state()
            if pose is None:
                return {"success": False, "error": "state_unavailable"}

        valid, err = self._validate_pose(pose)
        if not valid:
            return {"success": False, "error": "invalid_pose", "detail": err}

        frame = str(pose.get("frame_id", self.state_frame)).strip() or self.state_frame
        if frame != self.nav_frame:
            return {
                "success": False,
                "error": "pose_frame_not_in_nav_frame",
                "source_frame": frame,
                "target_frame": self.nav_frame,
            }

        pose["frame_id"] = self.nav_frame
        self.place_memory.save_place(name, pose)
        return {"success": True, "name": name, "pose": pose}

    def go_to(self, location: str = None):
        if location is None:
            return {"success": False, "error": "invalid_location_name"}
        key = str(location).strip()
        if not key:
            return {"success": False, "error": "invalid_location_name"}

        pose = self.place_memory.get_place(key)
        if pose is None:
            return {"success": False, "error": "location_not_found", "location": key}

        valid, err = self._validate_pose(pose)
        if not valid:
            return {"success": False, "error": "invalid_pose_in_place_memory", "detail": err}

        frame = str(pose.get("frame_id", self.nav_frame)).strip() or self.nav_frame
        if frame != self.nav_frame:
            return {
                "success": False,
                "error": "pose_frame_mismatch_for_navigation",
                "source_frame": frame,
                "target_frame": self.nav_frame,
            }

        planar_qx, planar_qy, planar_qz, planar_qw = self._extract_planar_quat(pose["orientation"])
        payload = {
            "frame_id": self.nav_frame,
            "position": {
                "x": float(pose["position"]["x"]),
                "y": float(pose["position"]["y"]),
                "z": 0.0,
            },
            "orientation": {
                "x": planar_qx,
                "y": planar_qy,
                "z": planar_qz,
                "w": planar_qw,
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            length_prefix = struct.pack("!I", len(data))
            with socket.create_connection((self.nav_host, self.nav_port), timeout=self.nav_timeout) as sock:
                sock.sendall(length_prefix + data)
            return {"success": True, "location": key, "pose": payload}
        except Exception as err:
            return {"success": False, "error": "navigation_send_failed", "detail": str(err)}

    def patrol(self, locations: list, continue_on_error: bool = False):
        if not isinstance(locations, list) or not locations:
            return {"success": False, "error": "invalid_locations"}

        results = []
        for location in locations:
            item_result = self.go_to(location)
            results.append(item_result)
            if not item_result.get("success", False) and not continue_on_error:
                return {"success": False, "results": results}

        return {"success": all(item.get("success", False) for item in results), "results": results}
