# SO-101 Deployment — Fallback Plans

## Robot won't connect

1. Check USB: `ls /dev/ttyACM*`
2. In Windows PowerShell (admin): `usbipd wsl list` — verify device attached
3. If not attached: `usbipd wsl attach --busid <ID> --distribution LeRobot-Ubuntu-F`
4. Check kernel driver: `sudo modprobe cdc-acm`
5. Check permissions: `ls -la /dev/ttyACM0` (should be dialout group)
6. Last resort: reboot WSL: `wsl --shutdown LeRobot-Ubuntu-F`

## Camera not responding

1. Ping camera server: `ping 172.28.48.1`
2. Check ZMQ stream: `python3 -c "import zmq; ctx=zmq.Context(); s=ctx.socket(zmq.SUB); s.connect('tcp://172.28.48.1:5555'); s.setsockopt(zmq.SUBSCRIBE, b''); print(s.recv())"` (timeout ~2s)
3. Restart camera server on Windows side
4. Verify IP has not changed (check `ipconfig` in Windows)

## Unsafe robot motion

1. **IMMEDIATE:** Hit physical E-stop OR press ESC in terminal
2. Reduce `max_relative_target` to 0.02
3. Reduce `max_delta_per_step_deg` to 2
4. Re-run no-cube test first
5. Check if policy outputs are clipped by unnormalizer
6. Check if action stats.json matches robot range

## Zero grasp success rate

1. Switch to next-best checkpoint from eval_ranking.json
2. Check camera lighting — consistent with training data?
3. Verify cube position is in workspace (visible in scene camera)
4. Check gripper calibration — does it close fully?
5. Try with longer duration (10s instead of 5s)
6. Reduce chunk_size from 100 to 50
7. Disable temporal ensemble (set temporal_ensemble_coeff=null)

## High inference latency (>50ms)

1. Check GPU usage: `nvidia-smi`
2. Reduce chunk_size to 50
3. Disable temporal aggregation
4. Check if another process is using GPU
5. Try on CPU (export CUDA_VISIBLE_DEVICES="")

## Policy produces NaN or extreme values

1. Check normalizer stats match current robot
2. Reload checkpoint from sim (no fine-tune)
3. Verify action range in preprocessor matches
4. Check if observation images are within [0,1] range
