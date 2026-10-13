<div align="center">

# H₂S Smart Wristband

### A hackathon demo for visual H₂S indicator-strip analysis and worker-safety workflows

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-0d9488?style=for-the-badge)](https://h2s-smart-wristband.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20App-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

**[Try the live demo](https://h2s-smart-wristband.onrender.com) · [Explore the code](https://github.com/mirusnan2025it-del/H2S)**

</div>

> [!CAUTION]
> **Prototype only — not a gas detector.** This project is not certified, calibrated, or validated for measuring H₂S concentration. It must not be used to decide whether an area is safe, replace approved gas-detection equipment, or guide emergency response. Follow your organization's safety procedures and use certified instruments.

## The idea

H₂S Smart Wristband demonstrates how a digital safety workflow could combine a **visual indicator-strip reading** with worker and manager views. The demo lets you explore image analysis, simulated readings, and example detection history in one web app.

It is designed for demonstrating a concept at a hackathon—not for real-world exposure monitoring.

## Explore the demo

Open **[h2s-smart-wristband.onrender.com](https://h2s-smart-wristband.onrender.com)** on a phone, tablet, or computer. On the sign-in screen, choose **Manager demo** or **Worker demo** to fill a sample account.

> The free hosting service may need about a minute to wake after inactivity. Its local SQLite data is temporary and may reset.

## What you can try

- **Worker dashboard** — explore a worker-oriented safety workspace.
- **Manager dashboard** — view example team and detection summaries.
- **Strip image analysis** — submit an indicator-strip image for a visual demo analysis.
- **Simulator** — explore the simulated reading workflow.
- **Detection history** — view example records within the app.
- **Responsive interface** — open the same hosted demo from different devices.

## How it works

1. Select a demo role and sign in.
2. Explore the dashboards, simulator, or strip-image analysis.
3. Review example summaries and history in the app.

The web app is built with Flask. OpenCV and NumPy support the image-processing workflow; SQLite stores demo accounts and records locally.

## Run it locally

You need Python 3.10 or newer.

```powershell
git clone https://github.com/mirusnan2025it-del/H2S.git
cd H2S
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>. Use the demo buttons on the login page.

## Deployment

This repository includes a [`render.yaml`](./render.yaml) Blueprint configured for a **free Render web service**.

To deploy your own copy:

1. Sign in to Render and connect your GitHub account.
2. Create a new **Blueprint** and select this repository.
3. Review the service settings and deploy.

Free services can spin down when idle, which makes the next visit slower. The service's local filesystem is temporary, so this SQLite setup is for demos only—not permanent data storage.

## Built with

- [Python](https://www.python.org/) and [Flask](https://flask.palletsprojects.com/)
- [OpenCV](https://opencv.org/) and [NumPy](https://numpy.org/)
- SQLite
- HTML, CSS, and JavaScript
- [Render](https://render.com/) for the hosted demo

## Important limitations

- The application is a **software prototype**; it does not establish that a physical wristband or gas sensor is connected.
- Visual image analysis is sensitive to image quality, lighting, camera settings, strip condition, and other factors. It is not a validated ppm measurement.
- Example logins and sample records are for exploration only. Do not enter real worker, health, or other sensitive information.
- The hosted demo uses temporary local storage, and its records can be lost when the service restarts or redeploys.

## License

No license has been added yet. Unless a license is added, standard copyright applies and reuse is not automatically granted.
