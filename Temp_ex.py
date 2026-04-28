import subprocess
import sys
import matplotlib.pyplot as plt

PORT = "COM3"

cmd = [
    sys.executable, "-m", "mpremote",
    "connect", PORT,
    "run", "on_Pico.py"
]

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

plt.ion()
fig, ax = plt.subplots()

temps = []

print("Starte Live-Plot... (Strg+C zum Beenden)")

try:
    while True:
        line = proc.stdout.readline()

        if not line:
            plt.pause(0.01)
            continue

        print("RAW:", line.strip())  # DEBUG

        try:
            temp = float(line.strip())
            temps.append(temp)

            # 👉 WICHTIG: Daten setzen
            ax.cla()
            ax.plot(range(len(temps)), temps, marker='o')

            ax.set_title("Live Temperatur")
            ax.set_ylabel("°C")
            ax.set_xlabel("Messung")

            # 👉 FIX: Achsen explizit setzen
            ax.set_xlim(0, max(10, len(temps)))
            ax.set_ylim(min(temps) - 1, max(temps) + 1)

            # 👉 zwingt Matplotlib zum Zeichnen
            fig.canvas.draw()
            fig.canvas.flush_events()

        except ValueError:
            pass

except KeyboardInterrupt:
    print("Beendet.")
    proc.terminate()