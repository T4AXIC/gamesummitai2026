# Demo video tooling

Used to make `media/perde-demo.mp4`.

1. Start the app: `streamlit run app.py` (port 8501).
2. `python tools/video/capture.py tools/video/shots` takes real screenshots of the running app with headless Chrome.
3. `python tools/video/render.py . media/perde-demo.mp4` renders 56 s at 1080p30, with a soundtrack synthesized in code.

Needs `pillow numpy imageio-ffmpeg websockets` and Google Chrome. Fonts: Segoe UI and Cascadia Mono (Windows).
