# Demo video tooling

Used to make `media/perde-demo.mp4`.

1. Start the app: `streamlit run app.py` (port 8501).
2. `python tools/video/capture.py tools/video/shots` takes real screenshots of the running app with headless Chrome.
3. `python tools/video/render_v2.py . media/perde-demo-v2.mp4` renders the 60 s main video (1080p30, beat-synced, synthesized soundtrack). `render.py` made the shorter first cut.

Needs `pillow numpy imageio-ffmpeg websockets qrcode` and Google Chrome. Fonts: Segoe UI and Cascadia Mono (Windows).
