import argparse
import time
from typing import Optional

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_ as hg_LowCmd, LowState_ as hg_LowState
from unitree_sdk2py.utils.crc import CRC


TOTAL_MOTORS = 35
LOWER_BODY_INDICES = list(range(0, 15))  # Legs + waist
ARM_INDICES = list(range(15, 29))  # Left/right arms


def copy_motor_cmd(dst_cmd, src_cmd) -> None:
    """Copy all low-level motor command fields."""
    dst_cmd.mode = src_cmd.mode
    dst_cmd.q = src_cmd.q
    dst_cmd.dq = src_cmd.dq
    dst_cmd.tau = src_cmd.tau
    dst_cmd.kp = src_cmd.kp
    dst_cmd.kd = src_cmd.kd
    dst_cmd.reserve = src_cmd.reserve


class LowCmdMiddleware:
    def __init__(
        self,
        publish_rate_hz: float,
        wbc_timeout_s: float,
        teleop_timeout_s: float,
        legs_topic: str,
        arms_topic: str,
        output_topic: str,
    ):
        self.publish_rate_hz = publish_rate_hz
        self.wbc_timeout_s = wbc_timeout_s
        self.teleop_timeout_s = teleop_timeout_s

        self.legs_sub = ChannelSubscriber(legs_topic, hg_LowCmd)
        self.legs_sub.Init()
        self.arms_sub = ChannelSubscriber(arms_topic, hg_LowCmd)
        self.arms_sub.Init()
        self.lowstate_sub = ChannelSubscriber("rt/lowstate", hg_LowState)
        self.lowstate_sub.Init()
        self.output_pub = ChannelPublisher(output_topic, hg_LowCmd)
        self.output_pub.Init()

        self.crc = CRC()
        self.merged_cmd = unitree_hg_msg_dds__LowCmd_()
        self._init_default_cmd(self.merged_cmd)

        self.latest_legs_cmd: Optional[hg_LowCmd] = None
        self.latest_arms_cmd: Optional[hg_LowCmd] = None
        self.latest_lowstate: Optional[hg_LowState] = None
        self.last_legs_ts = 0.0
        self.last_arms_ts = 0.0

    @staticmethod
    def _init_default_cmd(cmd) -> None:
        cmd.mode_pr = 0 # 0:pitch/roll mode; 1:AB mode;
        cmd.mode_machine = 0
        cmd.crc = 0
        for idx in range(TOTAL_MOTORS):
            cmd.motor_cmd[idx].mode = 0x01
            cmd.motor_cmd[idx].q = 0.0
            cmd.motor_cmd[idx].dq = 0.0
            cmd.motor_cmd[idx].tau = 0.0
            cmd.motor_cmd[idx].kp = 0.0
            cmd.motor_cmd[idx].kd = 1.0
            cmd.motor_cmd[idx].reserve = 0

    def _poll_inputs(self, now: float) -> None:
        legs_msg = self.legs_sub.Read()
        if legs_msg is not None:
            self.latest_legs_cmd = legs_msg
            self.last_legs_ts = now

        arms_msg = self.arms_sub.Read()
        if arms_msg is not None:
            self.latest_arms_cmd = arms_msg
            self.last_arms_ts = now

        lowstate_msg = self.lowstate_sub.Read()
        if lowstate_msg is not None:
            self.latest_lowstate = lowstate_msg

    def _apply_emergency_lower_body(self) -> None:
        """
        Apply emergency damping-like command to lower body when WBC stream is stale.

        We hold current positions with zero stiffness and high damping to avoid aggressive
        movements when lower-body commands are missing.
        """
        for idx in LOWER_BODY_INDICES:
            self.merged_cmd.motor_cmd[idx].mode = 0x01
            self.merged_cmd.motor_cmd[idx].kp = 0.0
            self.merged_cmd.motor_cmd[idx].kd = 8.0
            self.merged_cmd.motor_cmd[idx].dq = 0.0
            self.merged_cmd.motor_cmd[idx].tau = 0.0
            if self.latest_lowstate is not None:
                self.merged_cmd.motor_cmd[idx].q = self.latest_lowstate.motor_state[idx].q

    def _merge_frame(self, now: float) -> None:
        """Build one merged low-level command frame."""
        legs_fresh = self.latest_legs_cmd is not None and (now - self.last_legs_ts) <= self.wbc_timeout_s
        arms_fresh = self.latest_arms_cmd is not None and (now - self.last_arms_ts) <= self.teleop_timeout_s

        # Start from latest leg frame if available, otherwise keep previous merged frame.
        if self.latest_legs_cmd is not None:
            self.merged_cmd.mode_pr = self.latest_legs_cmd.mode_pr
            self.merged_cmd.mode_machine = self.latest_legs_cmd.mode_machine
            for idx in range(TOTAL_MOTORS):
                copy_motor_cmd(self.merged_cmd.motor_cmd[idx], self.latest_legs_cmd.motor_cmd[idx])
        elif self.latest_lowstate is not None:
            # Keep mode_machine aligned with robot state when no legs frame has arrived yet.
            self.merged_cmd.mode_machine = self.latest_lowstate.mode_machine

        if not legs_fresh:
            self._apply_emergency_lower_body()

        # Teleop timeout behavior: keep last known arm command (already in merged_cmd).
        if arms_fresh:
            for idx in ARM_INDICES:
                copy_motor_cmd(self.merged_cmd.motor_cmd[idx], self.latest_arms_cmd.motor_cmd[idx])

        self.merged_cmd.crc = self.crc.Crc(self.merged_cmd)

    def run(self) -> None:
        dt = 1.0 / self.publish_rate_hz
        print(
            f"[Middleware] Starting lowcmd mixer at {self.publish_rate_hz:.1f} Hz "
            f"(WBC timeout={self.wbc_timeout_s}s, teleop timeout={self.teleop_timeout_s}s)"
        )
        print("[Middleware] Press Ctrl+C to stop.")
        try:
            while True:
                start = time.time()
                self._poll_inputs(start)
                self._merge_frame(start)
                self.output_pub.Write(self.merged_cmd)
                elapsed = time.time() - start
                time.sleep(max(0.0, dt - elapsed))
        except KeyboardInterrupt:
            print("\n[Middleware] KeyboardInterrupt received. Shutting down mixer loop.")
            return


def parse_args():
    parser = argparse.ArgumentParser(description="Merge WBC and XR lowcmd streams into rt/lowcmd.")
    parser.add_argument("--network-interface", type=str, default=None, help="DDS network interface, e.g. eno1.")
    parser.add_argument("--domain-id", type=int, default=0, help="DDS domain id.")
    parser.add_argument("--publish-rate", type=float, default=50.0, help="Merged lowcmd publish frequency.")
    parser.add_argument("--wbc-timeout", type=float, default=0.15, help="Timeout for WBC leg frames.")
    parser.add_argument("--teleop-timeout", type=float, default=0.5, help="Timeout for XR arm frames.")
    parser.add_argument("--legs-topic", type=str, default="rt/lowcmd_legs", help="Input topic for WBC lowcmd.")
    parser.add_argument("--arms-topic", type=str, default="rt/lowcmd_arms", help="Input topic for XR lowcmd.")
    parser.add_argument("--output-topic", type=str, default="rt/lowcmd", help="Output merged lowcmd topic.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        ChannelFactoryInitialize(args.domain_id, networkInterface=args.network_interface)
        mixer = LowCmdMiddleware(
            publish_rate_hz=args.publish_rate,
            wbc_timeout_s=args.wbc_timeout,
            teleop_timeout_s=args.teleop_timeout,
            legs_topic=args.legs_topic,
            arms_topic=args.arms_topic,
            output_topic=args.output_topic,
        )
        mixer.run()
    except KeyboardInterrupt:
        print("[Middleware] Exited cleanly after interrupt.")
    except Exception as exc:
        print(f"[Middleware] Fatal error: {exc}")
        raise
