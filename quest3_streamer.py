import threading
import socket
import numpy as np

from gr00t_wbc.control.teleop.streamers.base_streamer import BaseStreamer, StreamerOutput

class Quest3Streamer(BaseStreamer):
    def __init__(self, listen_ip="0.0.0.0", listen_port=5005):
        self.latest_lin_x = 0.0
        self.latest_lin_y = 0.0
        self.latest_ang_z = 0.0
        self.current_base_height = 0.74 
        self.toggle_activation = False
        
        self.is_running = True

        # Setup standard Python UDP Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((listen_ip, listen_port))
        
        # Start background thread to listen for UDP packets
        self.thread = threading.Thread(target=self._udp_listener_loop, daemon=True)
        self.thread.start()

    def _udp_listener_loop(self):
        while self.is_running:
            try:
                # Receive up to 1024 bytes
                data, _ = self.sock.recvfrom(1024)
                decoded_data = data.decode('utf-8')
                
                # Parse the CSV string: "lin_x,lin_y,ang_z"
                values = decoded_data.split(',')
                if len(values) == 3:
                    self.latest_lin_x = float(values[0])
                    self.latest_lin_y = float(values[1])
                    self.latest_ang_z = float(values[2])
            except Exception as e:
                pass

    def start_streaming(self):
        pass

    def stop_streaming(self):
        self.is_running = False
        self.sock.close()

    def get(self) -> StreamerOutput:
        # Define velocity scaling factors
        MAX_LINEAR_VEL = 0.5
        MAX_ANGULAR_VEL = 1.0

        # Calculate final velocities
        lin_vel_x = self.latest_lin_x * MAX_LINEAR_VEL
        lin_vel_y = self.latest_lin_y * MAX_LINEAR_VEL
        ang_vel_z = self.latest_ang_z * MAX_ANGULAR_VEL

        # Dummy arm data
        identity_matrix = np.eye(4)
        zero_fingers = np.zeros([25, 4, 4])

        return StreamerOutput(
            ik_data={
                "left_wrist": identity_matrix,
                "right_wrist": identity_matrix,
                "left_fingers": {"position": zero_fingers},
                "right_fingers": {"position": zero_fingers},
            },
            control_data={
                "base_height_command": self.current_base_height,
                "navigate_cmd": [lin_vel_x, lin_vel_y, ang_vel_z],
                "toggle_policy_action": False, 
            },
            teleop_data={
                "toggle_activation": self.toggle_activation,
            },
            data_collection_data={
                "toggle_data_collection": False,
                "toggle_data_abort": False,
            },
            source="quest3_udp"
        )