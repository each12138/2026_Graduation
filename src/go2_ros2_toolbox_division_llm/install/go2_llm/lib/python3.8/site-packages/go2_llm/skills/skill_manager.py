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


class SkillManager:
    def __init__(self, sport_client=None, semantic_map=None, state_reader=None):
        self.sport_client = sport_client
        self.semantic_map = semantic_map
        self.state_reader = state_reader
        self.nav_host = os.getenv("GO2_NAV_TCP_HOST", DEFAULT_NAV_HOST)
        try:
            self.nav_port = int(os.getenv("GO2_NAV_TCP_PORT", str(DEFAULT_NAV_PORT)))
        except ValueError:
            self.nav_port = DEFAULT_NAV_PORT
        try:
            self.nav_timeout = float(os.getenv("GO2_NAV_TIMEOUT", str(DEFAULT_NAV_TIMEOUT)))
        except ValueError:
            self.nav_timeout = DEFAULT_NAV_TIMEOUT
        nav_frame = os.getenv("GO2_NAV_FRAME_ID", DEFAULT_NAV_FRAME)
        self.nav_frame = str(nav_frame).strip() if nav_frame is not None else DEFAULT_NAV_FRAME
        if not self.nav_frame:
            self.nav_frame = DEFAULT_NAV_FRAME

    def _require_nav_frame_pose(self, pose):
        frame_id = str(pose.get("frame_id", "")).strip() or self.nav_frame
        if frame_id != self.nav_frame:
            return {
                "success": False,
                "error": "pose_frame_not_in_nav_frame",
                "detail": (
                    f"pose frame_id is '{frame_id}', but persistent map requires "
                    f"'{self.nav_frame}'."
                ),
                "source_frame": frame_id,
                "target_frame": self.nav_frame,
            }
        pose["frame_id"] = self.nav_frame
        return None

    @staticmethod
    def _clamp(value, lower, upper, name):
        clamped = max(lower, min(upper, value))
        if clamped != value:
            print(f"参数 {name}={value} 超出范围 [{lower}, {upper}]，已截断为 {clamped}")
        return clamped

    @staticmethod
    def _is_number(value):
        return isinstance(value, (int, float))

    @staticmethod
    def _normalize_quaternion(qx, qy, qz, qw):
        norm = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
        if norm <= 1e-9:
            return 0.0, 0.0, 0.0, 1.0
        return qx / norm, qy / norm, qz / norm, qw / norm

    def _extract_planar_quat(self, orientation):
        qx = float(orientation.get("x", 0.0))
        qy = float(orientation.get("y", 0.0))
        qz = float(orientation.get("z", 0.0))
        qw = float(orientation.get("w", 1.0))
        qx, qy, qz, qw = self._normalize_quaternion(qx, qy, qz, qw)

        yaw = math.atan2(
            2.0 * (qw * qz + qx * qy),
            1.0 - 2.0 * (qy * qy + qz * qz),
        )
        half_yaw = 0.5 * yaw
        return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)

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
            value = position.get(axis)
            if not self._is_number(value):
                return False, f"position_{axis}_must_be_number"
            if not math.isfinite(float(value)):
                return False, f"position_{axis}_must_be_finite"

        for axis in ("x", "y", "z", "w"):
            value = orientation.get(axis)
            if not self._is_number(value):
                return False, f"orientation_{axis}_must_be_number"
            if not math.isfinite(float(value)):
                return False, f"orientation_{axis}_must_be_finite"

        return True, None

    def stand_up(self):
        self.sport_client.RecoveryStand()
        return {"success": True}

    def stand_down(self):
        self.sport_client.StandDown()
        return {"success": True}

    def move_forward(self, vx=0.0):
        vx = self._clamp(vx, VX_RANGE[0], VX_RANGE[1], "vx")
        self.sport_client.Move(vx, 0.0, 0.0)
        return {"success": True}

    def move_lateral(self, vy=0.0):
        vy = self._clamp(vy, VY_RANGE[0], VY_RANGE[1], "vy")
        self.sport_client.Move(0.0, vy, 0.0)
        return {"success": True}

    def move_rotate(self, vyaw=0.0):
        vyaw = self._clamp(vyaw, VYAW_RANGE[0], VYAW_RANGE[1], "vyaw")
        self.sport_client.Move(0.0, 0.0, vyaw)
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
        if self.semantic_map is None:
            return {"success": False, "error": "map_not_initialized"}

        name = str(name).strip()
        if not name:
            return {"success": False, "error": "invalid_name"}

        from_current_state = pose is None
        if pose is None:
            if self.state_reader is None:
                return {"success": False, "error": "state_reader_not_initialized"}
            pose = self.state_reader.get_state()
            if pose is None:
                return {"success": False, "error": "state_unavailable"}

        valid_pose, pose_error = self._validate_pose(pose)
        if not valid_pose:
            return {
                "success": False,
                "error": "invalid_pose",
                "detail": pose_error,
            }

        frame_error = self._require_nav_frame_pose(pose)
        if frame_error is not None:
            if from_current_state:
                frame_error["error"] = "state_pose_not_in_nav_frame"
            return frame_error

        self.semantic_map.memory(name, pose)
        print(f"已记忆位置 {name} -> {pose}")
        return {"success": True, "name": name, "pose": pose}

    def navigate(self, location: str = None):
        if self.semantic_map is None:
            return {"success": False, "error": "map_not_initialized"}

        if location is None:
            return {"success": False, "error": "invalid_location_name"}

        location = str(location).strip()
        if not location:
            return {"success": False, "error": "invalid_location_name"}

        pose = self.semantic_map.get(location)
        if pose is None:
            return {"success": False, "error": "location_not_found", "location": location}

        valid_pose, pose_error = self._validate_pose(pose)
        if not valid_pose:
            return {
                "success": False,
                "error": "invalid_pose_in_map",
                "location": location,
                "detail": pose_error,
            }

        frame_error = self._require_nav_frame_pose(pose)
        if frame_error is not None:
            frame_error["error"] = "pose_frame_mismatch_for_navigation"
            frame_error["location"] = location
            return frame_error

        planar_qx, planar_qy, planar_qz, planar_qw = self._extract_planar_quat(
            pose["orientation"]
        )

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

            print(f"已发送导航目标 {location} -> {payload}")
            return {
                "success": True,
                "sent": True,
                "status": "navigation_goal_sent",
                "message": "导航目标已发送，未等待机器人抵达目标点。",
                "location": location,
                "pose": payload,
            }
        except Exception as exc:
            print(f"发送导航目标失败: {exc}")
            return {
                "success": False,
                "error": "navigation_send_failed",
                "detail": str(exc),
            }
