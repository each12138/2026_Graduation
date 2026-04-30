#!/usr/bin/env python3
import math
import sys
import yaml
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid


class MapSaver(Node):
    def __init__(self, map_topic, out_prefix):
        super().__init__('manual_map_saver')
        self.out_prefix = out_prefix
        self.map_msg = None
        self.done = False

        # Match map_saver_cli behavior for latched /map topics.
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.sub = self.create_subscription(
            OccupancyGrid, map_topic, self.cb, qos
        )
        self.get_logger().info(f'Waiting for map on topic: {map_topic}')

    def cb(self, msg):
        if self.done:
            return
        self.map_msg = msg
        self.get_logger().info(
            f"Received map: {msg.info.width}x{msg.info.height}, "
            f"res={msg.info.resolution}"
        )
        self.save_map(msg)
        self.done = True
        self.destroy_subscription(self.sub)

    def save_map(self, msg: OccupancyGrid):
        w = msg.info.width
        h = msg.info.height
        data = np.array(msg.data, dtype=np.int16).reshape((h, w))

        # Match nav2_map_server trinary output:
        # occupied >= 65 -> 0 (black)
        # free <= 25     -> 254 (white)
        # otherwise      -> 205 (gray/unknown)
        img = np.full((h, w), 205, dtype=np.uint8)
        img[data >= 65] = 0
        img[(data >= 0) & (data <= 25)] = 254

        # Flip vertically for standard ROS map image orientation
        img = np.flipud(img)

        pgm_path = self.out_prefix + '.pgm'
        yaml_path = self.out_prefix + '.yaml'

        with open(pgm_path, 'wb') as f:
            f.write(bytearray(f'P5\n{w} {h}\n255\n', 'ascii'))
            img.tofile(f)

        origin = [
            float(msg.info.origin.position.x),
            float(msg.info.origin.position.y),
            self.get_yaw_from_quat(msg.info.origin.orientation)
        ]

        meta = {
            'image': pgm_path.split('/')[-1],
            'mode': 'trinary',
            'resolution': float(msg.info.resolution),
            'origin': origin,
            'negate': 0,
            'occupied_thresh': 0.65,
            'free_thresh': 0.25
        }

        with open(yaml_path, 'w') as f:
            yaml.safe_dump(meta, f, sort_keys=False)

        self.get_logger().info(f'Saved map to: {pgm_path} and {yaml_path}')

    @staticmethod
    def get_yaw_from_quat(q):
        # yaw from quaternion
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)


def main():
    rclpy.init()
    map_topic = '/map'
    out_prefix = '/home/unitree/map/go2_slam_ninelab_around'

    if len(sys.argv) > 1:
        out_prefix = sys.argv[1]
    if len(sys.argv) > 2:
        map_topic = sys.argv[2]

    node = MapSaver(map_topic, out_prefix)

    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()