1.run middleware interface:

```bash
python Teleop_Simulator/lowcmd_middleware.py --network-interface eno1 --domain-id 0 --publish-rate 50
```

2.run WBC:

```bash
python Teleop_Simulator/GR00T-WholeBodyControl/gr00t_wbc/control/main/teleop/run_g1_control_loop.py --interface eno1 --no-with_hands
```

3.run xr_teleoperation:

```bash
python Teleop_Simulator/xr_teleoperate/teleop/teleop_hand_and_arm.py --mixer --ee inspire_ftp --network-interface eno1 --img-server-ip 192.168.123.164
```

