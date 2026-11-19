Hier ist die reduzierte Spezifikation für das Projekt. Folge strikt dem KISS-Prinzip (Keep It Simple, Stupid): Keine unnötigen Abstraktionen, kein Overengineering, keine Mock-Frameworks.

---

# System Requirements: Simple Laser Galvo & Power Controller

**Projekt:** Minimalistischer Galvo- & Laser-Controller  
**Zielsystem:** Raspberry Pi 3 (`admin@pi3`)  
**Technologie:** Rust (ALSA für Audio/DMA, GPIO für Laser)

---

## 1. Kernaufgabe
Das System nimmt Steuerbefehle für Position ($X$, $Y$) und Laserleistung entgegen und gibt sie kontinuierlich aus:
- **Galvo-Position ($X, Y$):** Wird über einen PCM5102A I2S-DAC via ALSA ausgegeben (Stereo: Links = X, Rechts = Y).
- **Laser-Power:** Steuerung über einen Hardware-GPIO-Pin (An/Aus oder einfaches PWM).

> **Sicherheitshinweis:** Der Laser ist augensicher (eye-safe). Komplexe Sicherheitsüberwachungen (Scan-Fail-Circuit, Timeout-Watchdog, Not-Aus-Logik) sind **nicht erforderlich**. Bleibt der Laser bei einem Crash an oder steht der Strahl, ist das unkritisch.

---

## 2. Hardware & Schnittstellen

### 2.1 I2S-DAC (Galvos)
- **Chip:** PCM5102A Breakout (I2S) am Raspberry Pi.
- **ALSA-Device:** Standard-Audioausgang (z. B. `hw:0,0` oder konfiguriertes HiFiBerry-Device).
- **Format:** Stereo, 16-Bit Signed Integer (`i16_le`), Abtastrate z. B. 48 kHz.
- **Wertebereich:** Normierter Eingang $x, y \in [-1.0, 1.0]$ skaliert direkt linear auf `i16` ($-32768$ bis $32767$).

### 2.2 Laser
- **Pin:** Ein definierter GPIO-Pin via `rppal` (z. B. GPIO 18).
- **Modus:** Entweder simples TTL (Power > 0 = HIGH, sonst LOW) oder Basic Software-/Hardware-PWM ($0.0$ bis $1.0$).

---

## 3. Minimales Software-Design

Schreibe eine schlanke, pragmatische Rust-Anwendung (bevorzugt in einer Datei `src/main.rs` oder maximal 2–3 einfachen Modulen):

1. **ALSA Output Loop (Thread 1):**
   - Öffnet ALSA im Write-Modus.
   - Schreibt in einer Endlosschleife kontinuierlich den aktuellen Sollwert `(x_i16, y_i16)` in den Puffer, um ALSA-Buffer-Underruns (XRUNs) zu verhindern.
   - Der aktuelle Sollwert wird thread-safe über atomare Typen oder eine einfache `Arc<Atomic...>`- / Lock-freie Struktur geteilt.

2. **Steuerungs-Schnittstelle (Thread 2 / Server):**
   - Hört auf einen Unix Domain Socket (z. B. `/tmp/laser.sock`) oder einfachen UDP-Port.
   - Akzeptiert ein simples Text- oder Binärprotokoll mit genau drei Werten:
     ```text
     SET <x> <y> <laser_power>
     ```
     (Wobei $x, y \in [-1.0, 1.0]$ und `laser_power` $\in [0.0, 1.0]$).

3. **Fehlerkontrolle:**
   - **Nur Input Bounds:** Eingehende Werte strikt auf den gültigen Bereich clampen ($[-1.0, 1.0]$ für X/Y, $[0.0, 1.0]$ für Laser).
   - Ungültige Befehle/Strings einfach verwerfen, ohne abzustürzen. Keine Ausnahmen, keine komplexen Error-Recovery-Pipelines.

---

## 4. Build & Deployment auf Raspberry Pi 3

Es steht echte Testhardware zur Verfügung. Die Entwicklung und das Testen erfolgen direkt auf bzw. gegen das Zielsystem:

- **SSH-Zugang:** `ssh admin@pi3`
- **Rechte & Sudo:**
  - Du agierst als Benutzer `admin`.
  - Wenn für die Installation von Abhängigkeiten (z. B. `libasound2-dev`), Konfiguration von `/boot/firmware/config.txt` oder Kernel-Modulen **Root-Rechte** (`sudo`) nötig sind:
    - **Führe diese Befehle nicht blind aus.**
    - Halte an, gib mir die exakten Shell-Befehle und bitte mich, sie als Root für dich auszuführen.
- **Kompilierung:** 
  - Kann direkt auf dem Pi via `cargo build` ausgeführt werden (oder falls gewünscht als schlanker Cross-Build, solange es unkompliziert bleibt).
