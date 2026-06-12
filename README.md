<div align="center">
  <img src="assets/logo.png" alt="PiloPress Logo" width="120" />
  <h1>PiloPress</h1>
  <p><strong>Optimizador y conversor profesional de imágenes para escritorio</strong></p>

  <p>
    <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white">
    <img alt="Licencia" src="https://img.shields.io/github/license/alejandroasc96/PiloPress">
    <img alt="Versión" src="https://img.shields.io/badge/versi%C3%B3n-v0.5.12--beta-orange">
  </p>
</div>

---

## ¿Qué es PiloPress?

PiloPress es una aplicación de escritorio que te permite **comprimir y convertir imágenes** de forma masiva y sin complicaciones. Está pensada para diseñadores, desarrolladores web y cualquier persona que necesite preparar imágenes para la web sin sacrificar el control sobre el resultado.

**¿Qué puedes hacer con él?**

- 🗂️ **Optimizar una carpeta entera** de imágenes de forma recursiva.
- 🖼️ **Procesar una sola foto** con una vista previa del resultado antes de guardar.
- 📋 **Armar una cola de selección múltiple** con archivos de distintas carpetas.
- ⚙️ Convertir a **WebP, JPEG o PNG** con control total del nivel de compresión.
- 📐 Establecer un **tamaño máximo** de forma intuitiva (ej. Full HD, Redes sociales…).
- 🛡️ Eliminar **metadatos EXIF** (GPS, modelo del dispositivo, fecha) para mayor privacidad.
- 💾 Trabajar **en el sitio** (con backup automático) o **exportar a una carpeta nueva**.

Todo el procesamiento ocurre de forma **local y privada**, sin telemetría ni envío de datos.

---

## Instalación desde el repositorio

> [!NOTE]
> Esta vía de instalación requiere tener **Python 3.11 o superior** instalado en tu sistema. Es la opción recomendada si el ejecutable descargable genera advertencias de seguridad en tu sistema operativo.

### 1. Clona o descarga el repositorio

```bash
git clone https://github.com/alejandroasc96/PiloPress.git
cd PiloPress
```

O si prefieres sin Git, descarga el [.zip del repositorio](https://github.com/alejandroasc96/PiloPress/archive/refs/heads/main.zip) y descomprímelo.

### 2. Crea un entorno virtual e instala las dependencias

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Lanza la aplicación

```bash
python app.py
```

La ventana de PiloPress se abrirá directamente. No requiere instalación adicional.

---

## Dependencias

| Paquete | Uso |
|---|---|
| `Pillow` | Motor de procesamiento y conversión de imágenes |
| `customtkinter` | Interfaz gráfica moderna sobre Tkinter |

---

## Licencia

Distribuido bajo los términos de la licencia incluida en este repositorio. Consulta el archivo [`LICENSE`](LICENSE) para más detalles.