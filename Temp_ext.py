import queue
import subprocess
import sys
import threading
from dataclasses import dataclass, field


DEFAULT_PORT = "COM3"
INVALID_EXTERNAL_TEMP_MIN = 84.5
INVALID_EXTERNAL_TEMP_MAX = 85.5


def is_invalid_external_temperature(value: float) -> bool:
    return INVALID_EXTERNAL_TEMP_MIN <= value <= INVALID_EXTERNAL_TEMP_MAX


@dataclass
class TemperatureMeasurement:
    port: str = DEFAULT_PORT
    script: str = "on_Pico.py"
    values: list[float] = field(default_factory=list)
    internal_values: list[float] = field(default_factory=list)
    raw_messages: list[str] = field(default_factory=list)
    ignored_external_values: int = 0
    total_external_measurements: int = 0
    ignored_value_pairs: list[tuple[int, float, float | None]] = field(default_factory=list)
    _proc: subprocess.Popen | None = field(default=None, init=False, repr=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _queue: queue.Queue[tuple[str, float | tuple[float, float] | str]] = field(
        default_factory=queue.Queue, init=False, repr=False
    )

    def start(self) -> None:
        if self.is_running():
            return

        self.values.clear()
        self.internal_values.clear()
        self.raw_messages.clear()
        self.ignored_external_values = 0
        self.total_external_measurements = 0
        self.ignored_value_pairs.clear()
        self._queue = queue.Queue()
        cmd = [
            sys.executable,
            "-m",
            "mpremote",
            "connect",
            self.port,
            "run",
            self.script,
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        proc = self._proc
        if proc is None:
            return

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)

        self._proc = None
        self.drain()

    def clear_output(self) -> None:
        self.values.clear()
        self.internal_values.clear()
        self.raw_messages.clear()
        self.ignored_external_values = 0
        self.total_external_measurements = 0
        self.ignored_value_pairs.clear()
        self._queue = queue.Queue()

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def return_code(self) -> int | None:
        if self._proc is None:
            return None
        return self._proc.poll()

    def drain(self) -> list[float]:
        new_values = []
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break

            if kind == "temperature":
                value = float(payload)
                self.total_external_measurements += 1
                if is_invalid_external_temperature(value):
                    self.ignored_external_values += 1
                    self.ignored_value_pairs.append(
                        (self.total_external_measurements, value, None)
                    )
                    continue

                self.values.append(value)
                new_values.append(value)
            elif kind == "temperature_pair":
                external_temp, internal_temp = payload
                external_temp = float(external_temp)
                internal_temp = float(internal_temp)
                self.total_external_measurements += 1
                self.internal_values.append(internal_temp)

                if is_invalid_external_temperature(external_temp):
                    self.ignored_external_values += 1
                    self.ignored_value_pairs.append(
                        (self.total_external_measurements, external_temp, internal_temp)
                    )
                    continue

                self.values.append(external_temp)
                new_values.append(external_temp)
            else:
                self.raw_messages.append(str(payload))

        return new_values

    def _read_stdout(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return

        for line in proc.stdout:
            text = line.strip()
            if not text:
                continue

            try:
                parts = [part.strip() for part in text.split(",")]
                if len(parts) == 2:
                    self._queue.put(("temperature_pair", (float(parts[0]), float(parts[1]))))
                else:
                    self._queue.put(("temperature", float(text)))
            except ValueError:
                self._queue.put(("message", text))


def create_measurement(port: str = DEFAULT_PORT) -> TemperatureMeasurement:
    return TemperatureMeasurement(port=port)
