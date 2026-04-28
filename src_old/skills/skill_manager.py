import time
import json
import math
import os
import socket
import struct
import global_vars

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
    def __init__(self, sport_client=None, semantic_map=None, state_client=None):
        self.sport_client = sport_client
        self.map = semantic_map if semantic_map is not None else global_vars.map
        self.state_client = state_client
        self.nav_host = os.getenv("GO2_NAV_HOST", DEFAULT_NAV_HOST)
        try:
            self.nav_port = int(os.getenv("GO2_NAV_PORT", str(DEFAULT_NAV_PORT)))
        except ValueError:
            self.nav_port = DEFAULT_NAV_PORT
        try:
            self.nav_timeout = float(os.getenv("GO2_NAV_TIMEOUT", str(DEFAULT_NAV_TIMEOUT)))
        except ValueError:
            self.nav_timeout = DEFAULT_NAV_TIMEOUT
        nav_frame = os.getenv("GO2_NAV_FRAME", DEFAULT_NAV_FRAME)
        self.nav_frame = str(nav_frame).strip() if nav_frame is not None else DEFAULT_NAV_FRAME
        if not self.nav_frame:
            self.nav_frame = DEFAULT_NAV_FRAME
        state_frame = os.getenv("GO2_STATE_FRAME", DEFAULT_STATE_FRAME)
        self.state_frame = str(state_frame).strip() if state_frame is not None else DEFAULT_STATE_FRAME
        if not self.state_frame:
            self.state_frame = DEFAULT_STATE_FRAME

    @staticmethod
    def _normalize_frame(frame_id, default_frame):
        frame = str(frame_id).strip() if frame_id is not None else ""
        return frame or default_frame

    def _ensure_nav_frame_pose(self, pose, fallback_frame):
        frame_id = self._normalize_frame(pose.get("frame_id"), fallback_frame)
        if frame_id != self.nav_frame:
            return (
                False,
                frame_id,
                {
                    "success": False,
                    "error": "pose_frame_not_in_nav_frame",
                    "detail": (
                        f"pose frame_id is '{frame_id}', but persistent map requires "
                        f"'{self.nav_frame}'. Convert pose to nav frame before saving or navigation."
                    ),
                    "source_frame": frame_id,
                    "target_frame": self.nav_frame,
                },
            )
        pose["frame_id"] = self.nav_frame
        return True, frame_id, None

    @staticmethod
    def _clamp(value, lower, upper, name):
        clamped = max(lower, min(upper, value))
        if clamped != value:
            print(f"参数{name}={value}超出范围[{lower}, {upper}]，已截断为{clamped}")
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

        # Full quaternion -> yaw, then rebuild a pure planar quaternion.
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

    # ======== 原子技能 ========
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

    # ======== 语义技能 ========
    def memory_position(self, name: str, pose: dict = None):
        if self.map is None:
            return {"success": False, "error": "map_not_initialized"}

        name = str(name).strip()
        if not name:
            return {"success": False, "error": "invalid_name"}

        if pose is not None:
            valid_pose, pose_error = self._validate_pose(pose)
            if not valid_pose:
                return {
                    "success": False,
                    "error": "invalid_pose",
                    "detail": pose_error,
                }
            is_nav_frame_pose, _, frame_error = self._ensure_nav_frame_pose(
                pose, self.nav_frame
            )
            if not is_nav_frame_pose:
                return frame_error
            self.map.memory(name, pose)
            print(f"已记忆位置: {name} -> {pose}")
            return {"success": True, "name": name, "pose": pose}

        state_client = self.state_client or getattr(global_vars, "state_client", None)
        if state_client is None:
            return {"success": False, "error": "state_client_not_initialized"}

        current_state = state_client.get_state()
        if current_state is None:
            return {"success": False, "error": "state_unavailable"}

        valid_pose, pose_error = self._validate_pose(current_state)
        if not valid_pose:
            return {
                "success": False,
                "error": "invalid_current_state_pose",
                "detail": pose_error,
            }

        state_frame = self._normalize_frame(current_state.get("frame_id"), self.state_frame)
        current_state["frame_id"] = state_frame
        is_nav_frame_pose, _, frame_error = self._ensure_nav_frame_pose(
            current_state, self.state_frame
        )
        if not is_nav_frame_pose:
            return {
                "success": False,
                "error": "state_pose_not_in_nav_frame",
                "detail": (
                    f"current state is in '{state_frame}', but persistent map requires "
                    f"'{self.nav_frame}'. Convert odom pose to map pose before memory_position."
                ),
                "source_frame": state_frame,
                "target_frame": self.nav_frame,
            }

        self.map.memory(name, current_state)
        print(f"已记忆当前位置: {name} -> {current_state}")
        return {"success": True, "name": name, "pose": current_state}

    def go_to(self, location: str = None):
        """
        根据语义位置名称，从地图中取出 pose 并通过 TCP 发送给导航桥接节点。

        入参:
            location: 语义位置名称，如 "dock_station"

        返回:
            {
                "success": bool,
                "location": str,
                "pose": dict,            # success 时返回
                "error": str,            # fail 时返回
                "detail": str            # fail 时可选
            }
        """
        if self.map is None:
            return {"success": False, "error": "map_not_initialized"}

        if location is None:
            return {"success": False, "error": "invalid_location_name"}

        location = str(location).strip()
        if not location:
            return {"success": False, "error": "invalid_location_name"}

        # 1) 从语义地图查位姿
        pose = self.map.get(location)
        if pose is None:
            return {"success": False, "error": "location_not_found", "location": location}

        # 2) 校验位姿结构
        valid_pose, pose_error = self._validate_pose(pose)
        if not valid_pose:
            return {
                "success": False,
                "error": "invalid_pose_in_map",
                "location": location,
                "detail": pose_error,
            }
        is_nav_frame_pose, pose_frame, frame_error = self._ensure_nav_frame_pose(
            pose, self.nav_frame
        )
        if not is_nav_frame_pose:
            frame_error["error"] = "pose_frame_mismatch_for_navigation"
            frame_error["location"] = location
            frame_error["detail"] = (
                f"saved pose frame is '{pose_frame}', but navigation is configured for "
                f"'{self.nav_frame}'. Refuse to send mixed-frame goal."
            )
            return frame_error

        # 3) 组包（协议: 4字节大端长度 + JSON）
        planar_qx, planar_qy, planar_qz, planar_qw = self._extract_planar_quat(
            pose["orientation"]
        )

        payload = {
            "frame_id": self.nav_frame,
            "position": {
                "x": float(pose["position"]["x"]),
                "y": float(pose["position"]["y"]),
                # Nav2 planar navigation: lock z to zero to avoid vertical jitter.
                "z": 0.0,
            },
            "orientation": {
                # Use yaw-only orientation for stable planar goals.
                "x": planar_qx,
                "y": planar_qy,
                "z": planar_qz,
                "w": planar_qw,
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            length_prefix = struct.pack("!I", len(data))

            # 4) 发送导航目标
            with socket.create_connection((self.nav_host, self.nav_port), timeout=self.nav_timeout) as sock:
                sock.sendall(length_prefix + data)

            print(f"已发送导航目标: {location} -> {payload}")
            return {
                "success": True,
                "sent": True,
                "status": "navigation_goal_sent",
                "message": "导航目标已发送，未等待机器人抵达目标点。",
                "location": location,
                "pose": payload,
            }

        except Exception as e:
            print(f"发送导航目标失败: {str(e)}")
            return {
                "success": False,
                "error": "navigation_send_failed",
                "detail": str(e),
            }

    def patrol(self, locations: list, continue_on_error: bool = False):
        if not isinstance(locations, list) or not locations:
            return {"success": False, "error": "invalid_locations"}

        results = []
        for location in locations:
            if not isinstance(location, str) or not location.strip():
                item_result = {
                    "success": False,
                    "location": location,
                    "error": "invalid_location_name",
                }
            else:
                item_result = self.go_to(location.strip())

            results.append(item_result)
            if not item_result.get("success", False) and not continue_on_error:
                return {"success": False, "results": results}

        return {
            "success": all(item.get("success", False) for item in results),
            "results": results,
        }
