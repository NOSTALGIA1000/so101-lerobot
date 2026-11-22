from lerobot.cameras.zmq import ZMQCamera, ZMQCameraConfig


def check(name: str) -> None:
    camera = ZMQCamera(
        ZMQCameraConfig(
            server_address="172.28.48.1",
            port=5555,
            camera_name=name,
            width=640,
            height=480,
            fps=30,
            timeout_ms=5000,
        )
    )
    try:
        camera.connect()
        frame = camera.async_read(timeout_ms=5000)
        print(f"{name}: shape={frame.shape}, dtype={frame.dtype}")
    finally:
        camera.disconnect()


for camera_name in ("wrist", "scene"):
    check(camera_name)
