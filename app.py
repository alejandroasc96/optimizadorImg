import os
import shutil
import threading
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog

# Extensiones de imagen soportadas de entrada
EXTENSIONES_SOPORTADAS = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp', '.avif'}

class OptimizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Optimizador y Conversor Profesional de Imágenes")
        self.geometry("800x780")
        self.minsize(750, 720)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables de estado independientes (¡Adiós a la confusión!)
        self.ruta_origen = ctk.StringVar()
        self.ruta_destino = ctk.StringVar()  # Exclusivo para Modo Exportar
        self.ruta_backup = ctk.StringVar()   # Exclusivo para Modo Sitio
        self.modo_trabajo_var = ctk.StringVar(value="sitio")
        
        self.formato_salida_var = ctk.StringVar(value="WebP")
        self.eliminar_exif_var = ctk.BooleanVar(value=True)
        self.calidad_var = ctk.IntVar(value=80)
        self.lossless_var = ctk.BooleanVar(value=False)
        self.esfuerzo_var = ctk.StringVar(value="6")
        self.max_size_var = ctk.StringVar(value="")
        
        self.esta_procesando = False

        self.construir_interfaz()

    def construir_interfaz(self):
        # --- PANEL DE RUTAS Y MODOS ---
        frame_rutas = ctk.CTkFrame(self)
        frame_rutas.pack(pady=15, padx=20, fill="x")

        # 1. Carpeta Origen
        ctk.CTkLabel(frame_rutas, text="1. Carpeta Origen:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_origen = ctk.CTkEntry(frame_rutas, textvariable=self.ruta_origen, width=400, state="readonly")
        self.entry_origen.grid(row=0, column=1, padx=10, pady=10, sticky="we")
        self.btn_explorar_origen = ctk.CTkButton(frame_rutas, text="Explorar...", command=self.seleccionar_origen)
        self.btn_explorar_origen.grid(row=0, column=2, padx=10, pady=10)

        # 2. Selector de Modo
        ctk.CTkLabel(frame_rutas, text="2. Modo de Operación:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.seg_modo = ctk.CTkSegmentedButton(
            frame_rutas, 
            values=["Optimizar en el sitio", "Exportar a nueva carpeta"],
            command=self.cambiar_modo_trabajo
        )
        self.seg_modo.set("Optimizar en el sitio")
        self.seg_modo.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # 3. Carpeta Destino (Solo para Modo Exportar)
        self.lbl_destino = ctk.CTkLabel(frame_rutas, text="3. Carpeta Destino:")
        self.lbl_destino.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_destino = ctk.CTkEntry(frame_rutas, textvariable=self.ruta_destino, width=400)
        self.entry_destino.grid(row=2, column=1, padx=10, pady=10, sticky="we")
        self.btn_explorar_destino = ctk.CTkButton(frame_rutas, text="Explorar...", command=self.seleccionar_destino)
        self.btn_explorar_destino.grid(row=2, column=2, padx=10, pady=10)

        # 4. Carpeta Backup (Solo para Modo Sitio)
        self.lbl_backup = ctk.CTkLabel(frame_rutas, text="3. Carpeta Backup:")
        self.lbl_backup.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_backup = ctk.CTkEntry(frame_rutas, textvariable=self.ruta_backup, width=400)
        self.entry_backup.grid(row=3, column=1, padx=10, pady=10, sticky="we")
        self.btn_explorar_backup = ctk.CTkButton(frame_rutas, text="Explorar...", command=self.seleccionar_backup)
        self.btn_explorar_backup.grid(row=3, column=2, padx=10, pady=10)

        frame_rutas.columnconfigure(1, weight=1)
        
        # Inicializar el estado de los campos de texto según el modo por defecto
        self.cambiar_modo_trabajo("Optimizar en el sitio")

        # --- PANEL DE AJUSTES ---
        frame_ajustes = ctk.CTkFrame(self)
        frame_ajustes.pack(pady=10, padx=20, fill="x")
        
        # Formato de Salida
        ctk.CTkLabel(frame_ajustes, text="Formato Salida:").grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.combo_formato = ctk.CTkOptionMenu(
            frame_ajustes, values=["WebP", "JPEG", "PNG"], 
            variable=self.formato_salida_var, command=self.ajustar_controles_por_formato
        )
        self.combo_formato.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        # Switch Metadatos
        self.switch_exif = ctk.CTkSwitch(frame_ajustes, text="Eliminar metadatos (EXIF)", variable=self.eliminar_exif_var)
        self.switch_exif.grid(row=0, column=3, padx=20, pady=15, sticky="e")

        # Calidad
        ctk.CTkLabel(frame_ajustes, text="Calidad:").grid(row=1, column=0, padx=10, pady=15, sticky="w")
        self.slider_calidad = ctk.CTkSlider(frame_ajustes, from_=0, to=100, number_of_steps=100, command=self.actualizar_label_calidad)
        self.slider_calidad.set(80)
        self.slider_calidad.grid(row=1, column=1, padx=10, pady=15, sticky="we")
        self.lbl_calidad_val = ctk.CTkLabel(frame_ajustes, text="80")
        self.lbl_calidad_val.grid(row=1, column=2, padx=10, pady=15, sticky="w")

        # Lossless
        self.switch_lossless = ctk.CTkSwitch(frame_ajustes, text="Lossless (WebP)", variable=self.lossless_var, command=self.toggle_lossless)
        self.switch_lossless.grid(row=1, column=3, padx=20, pady=15, sticky="e")

        # Esfuerzo CPU y Tamaño Máximo
        ctk.CTkLabel(frame_ajustes, text="Esfuerzo CPU:").grid(row=2, column=0, padx=10, pady=15, sticky="w")
        self.combo_esfuerzo = ctk.CTkOptionMenu(frame_ajustes, values=[str(i) for i in range(7)], variable=self.esfuerzo_var)
        self.combo_esfuerzo.grid(row=2, column=1, padx=10, pady=15, sticky="w")

        ctk.CTkLabel(frame_ajustes, text="Tamaño Max (px):").grid(row=2, column=2, padx=10, pady=15, sticky="e")
        self.entry_max_size = ctk.CTkEntry(frame_ajustes, textvariable=self.max_size_var, placeholder_text="Opcional")
        self.entry_max_size.grid(row=2, column=3, padx=20, pady=15, sticky="w")

        frame_ajustes.columnconfigure(1, weight=1)

        # --- LOG, PROGRESO Y CONTROL ---
        frame_control = ctk.CTkFrame(self, fg_color="transparent")
        frame_control.pack(pady=10, padx=20, fill="both", expand=True)

        self.btn_iniciar = ctk.CTkButton(frame_control, text="🚀 Iniciar Optimización", height=40,
                                         font=ctk.CTkFont(size=14, weight="bold"), command=self.iniciar_hilo_optimizacion)
        self.btn_iniciar.pack(pady=(0, 10), fill="x")

        self.progreso_bar = ctk.CTkProgressBar(frame_control, orientation="horizontal")
        self.progreso_bar.set(0)
        self.progreso_bar.pack(pady=(0, 10), fill="x")

        self.log_box = ctk.CTkTextbox(frame_control, state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True)

    # --- LÓGICA DE CONTROL DE INTERFAZ (UX MEJORADA) ---
    def cambiar_modo_trabajo(self, valor_seleccionado):
        """Activa y desactiva los campos correspondientes para que el usuario no se confunda."""
        if valor_seleccionado == "Optimizar en el sitio":
            self.modo_trabajo_var.set("sitio")
            # Activar Backup
            self.entry_backup.configure(state="normal", text_color=("black", "white"))
            self.btn_explorar_backup.configure(state="normal")
            self.lbl_backup.configure(text_color=("black", "white"))
            # Desactivar Destino (No se necesita)
            self.entry_destino.configure(state="disabled", text_color="gray")
            self.btn_explorar_destino.configure(state="disabled")
            self.lbl_destino.configure(text_color="gray")
        else:
            self.modo_trabajo_var.set("exportar")
            # Activar Destino
            self.entry_destino.configure(state="normal", text_color=("black", "white"))
            self.btn_explorar_destino.configure(state="normal")
            self.lbl_destino.configure(text_color=("black", "white"))
            # Desactivar Backup (No se necesita)
            self.entry_backup.configure(state="disabled", text_color="gray")
            self.btn_explorar_backup.configure(state="disabled")
            self.lbl_backup.configure(text_color="gray")
        
        self.calcular_rutas_automaticas()

    def seleccionar_origen(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de origen")
        if carpeta:
            self.ruta_origen.set(carpeta)
            self.calcular_rutas_automaticas()

    def calcular_rutas_automaticas(self):
        """Genera sugerencias inteligentes de carpetas basadas en el origen."""
        if self.ruta_origen.get():
            origen = Path(self.ruta_origen.get())
            # Forzar estados normales temporalmente para poder escribir los valores por defecto
            estado_b = self.entry_backup.cget("state")
            estado_d = self.entry_destino.cget("state")
            
            self.entry_backup.configure(state="normal")
            self.entry_destino.configure(state="normal")
            
            self.ruta_backup.set(str(origen / "raw-imagenes"))
            self.ruta_destino.set(str(origen.parent / f"{origen.name}-optimizada"))
            
            # Devolver a su estado correcto
            self.entry_backup.configure(state=estado_b)
            self.entry_destino.configure(state=estado_d)

    def seleccionar_destino(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de destino final")
        if carpeta:
            self.ruta_destino.set(carpeta)

    def seleccionar_backup(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta para salvaguardar originales")
        if carpeta:
            self.ruta_backup.set(carpeta)

    def actualizar_label_calidad(self, valor):
        self.lbl_calidad_val.configure(text=str(int(valor)))
        self.calidad_var.set(int(valor))

    def toggle_lossless(self):
        if self.lossless_var.get():
            self.slider_calidad.configure(state="disabled")
            self.lbl_calidad_val.configure(text_color="gray")
        else:
            self.slider_calidad.configure(state="normal")
            self.lbl_calidad_val.configure(text_color=("black", "white"))

    def ajustar_controles_por_formato(self, formato):
        if formato == "PNG":
            self.slider_calidad.configure(state="disabled")
            self.switch_lossless.configure(state="disabled")
            self.combo_esfuerzo.configure(state="disabled")
        elif formato == "JPEG":
            self.slider_calidad.configure(state="normal")
            self.switch_lossless.configure(state="disabled")
            self.combo_esfuerzo.configure(state="disabled")
        else:
            self.slider_calidad.configure(state="normal")
            self.switch_lossless.configure(state="normal")
            self.combo_esfuerzo.configure(state="normal")
            self.toggle_lossless()

    def escribir_log(self, mensaje):
        def actualizar_gui():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", mensaje + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, actualizar_gui)

    def actualizar_barra_progreso(self, porcentaje):
        self.after(0, lambda: self.progreso_bar.set(porcentaje))

    def alternar_estado_interfaz(self, estado):
        estado_ctk = "normal" if estado else "disabled"
        self.btn_iniciar.configure(state=estado_ctk)
        self.seg_modo.configure(state=estado_ctk)
        self.btn_explorar_origen.configure(state=estado_ctk)
        if self.modo_trabajo_var.get() == "sitio" and estado:
            self.btn_explorar_backup.configure(state="normal")
        elif self.modo_trabajo_var.get() == "exportar" and estado:
            self.btn_explorar_destino.configure(state="normal")

    def formatear_peso(self, bytes_val):
        if bytes_val >= 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.2f} MB"
        elif bytes_val >= 1024:
            return f"{bytes_val / 1024:.2f} KB"
        return f"{bytes_val} Bytes"

    # --- LÓGICA DE PROCESAMIENTO ---
    def iniciar_hilo_optimizacion(self):
        if self.esta_procesando: return
            
        if not self.ruta_origen.get():
            self.escribir_log("❌ Error: Selecciona una carpeta de origen primero.")
            return

        modo = self.modo_trabajo_var.get()
        if modo == "sitio" and not self.ruta_backup.get():
            self.escribir_log("❌ Error: Se requiere una carpeta de Backup para este modo.")
            return
        if modo == "exportar" and not self.ruta_destino.get():
            self.escribir_log("❌ Error: Se requiere una carpeta de Destino para exportar.")
            return

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.actualizar_barra_progreso(0)

        max_size_str = self.max_size_var.get().strip()
        max_size = int(max_size_str) if max_size_str.isdigit() else None

        configuracion = {
            'origen': Path(self.ruta_origen.get()).resolve(),
            'destino': Path(self.ruta_destino.get()).resolve() if modo == "exportar" else None,
            'backup': Path(self.ruta_backup.get()).resolve() if modo == "sitio" else None,
            'modo': modo,
            'formato': self.formato_salida_var.get(),
            'eliminar_exif': self.eliminar_exif_var.get(),
            'calidad': self.calidad_var.get(),
            'lossless': self.lossless_var.get(),
            'esfuerzo': int(self.esfuerzo_var.get()),
            'max_size': max_size
        }

        self.esta_procesando = True
        self.alternar_estado_interfaz(False)
        self.escribir_log(f"🚀 Modo: {'Optimización Local (En el sitio)' if modo == 'sitio' else 'Exportación a Carpeta Nueva'}")
        
        threading.Thread(target=self.procesar_imagenes, args=(configuracion,), daemon=True).start()

    def procesar_imagenes(self, config):
        origen = config['origen']
        modo = config['modo']
        ext_destino = ".jpg" if config['formato'] == "JPEG" else f".{config['formato'].lower()}"

        archivos_a_procesar = []
        for ruta_archivo in origen.rglob("*"):
            # Evitar procesar la carpeta de backup si está dentro del origen
            if modo == "sitio" and (config['backup'] in ruta_archivo.parents or ruta_archivo == config['backup']):
                continue
            if ruta_archivo.is_file() and ruta_archivo.suffix.lower() in EXTENSIONES_SOPORTADAS:
                archivos_a_procesar.append(ruta_archivo)

        total_archivos = len(archivos_a_procesar)
        if total_archivos == 0:
            self.escribir_log("ℹ️ No se encontraron imágenes válidas para procesar.")
            self.finalizar_proceso()
            return

        self.escribir_log(f"📸 Analizando {total_archivos} imágenes...\n")

        peso_total_original = 0
        peso_total_optimizado = 0
        conteo_exitos = 0

        for indice, ruta_archivo in enumerate(archivos_a_procesar):
            ruta_relativa = ruta_archivo.relative_to(origen)
            self.escribir_log(f"[{indice + 1}/{total_archivos}] Procesando: {ruta_relativa}")

            peso_original = ruta_archivo.stat().st_size

            if modo == "sitio":
                # Resguardo obligatorio en carpeta de Backup
                destino_backup = config['backup'] / ruta_relativa
                try:
                    destino_backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ruta_archivo, destino_backup)
                except Exception as e:
                    self.escribir_log(f"⚠️ Alerta Backup: {e}")
                
                ruta_final_imagen = ruta_archivo.with_suffix(ext_destino)
            else:
                # Modo Exportar: Directo al destino sin tocar el origen ni hacer backups redundantes
                ruta_final_imagen = config['destino'] / ruta_relativa.with_suffix(ext_destino)
                ruta_final_imagen.parent.mkdir(parents=True, exist_ok=True)

            if self.optimizar_imagen(ruta_archivo, ruta_final_imagen, config):
                conteo_exitos += 1
                peso_total_original += peso_original
                peso_total_optimizado += ruta_final_imagen.stat().st_size

                # En el sitio: si cambió de extensión, borramos la antigua (.png, .jpg...)
                if modo == "sitio" and ruta_archivo.suffix.lower() != ext_destino:
                    ruta_archivo.unlink()
            
            self.actualizar_barra_progreso((indice + 1) / total_archivos)

        # Log Final Detallado
        self.escribir_log(f"\n✨ ¡Proceso finalizado! Éxito en {conteo_exitos}/{total_archivos} imágenes.")
        if peso_total_original > 0:
            ahorro = peso_total_original - peso_total_optimizado
            pct = (ahorro / peso_total_original) * 100
            self.escribir_log(f"📉 Ahorro total: {self.formatear_peso(ahorro)} ({pct:.1f}% de optimización)")

        if modo == "sitio":
            self.escribir_log(f"📦 Tus fotos originales quedaron seguras en: '{config['backup']}'")
        else:
            self.escribir_log(f"📂 Tus fotos optimizadas se guardaron en: '{config['destino']}'\n⚠️ Nota: Las imágenes de tu carpeta origen no sufrieron ningún cambio.")

        self.finalizar_proceso()

    def optimizar_imagen(self, ruta_imagen, ruta_salida, config):
        try:
            with Image.open(ruta_imagen) as img:
                if config['max_size']:
                    ancho, alto = img.size
                    lado_mayor = max(ancho, alto)
                    if lado_mayor > config['max_size']:
                        escala = config['max_size'] / lado_mayor
                        img = img.resize((int(ancho * escala), int(alto * escala)), Image.Resampling.LANCZOS)

                formato_pil = config['formato']
                if formato_pil == "JPEG":
                    if img.mode in ("RGBA", "P", "LA"):
                        fondo = Image.new("RGB", img.size, (255, 255, 255))
                        fondo.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                        img = fondo
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                
                save_kwargs = {}

                # Extraemos el perfil de color original (si la imagen lo tiene)
                perfil_icc = img.info.get('icc_profile')
                if perfil_icc:
                    save_kwargs['icc_profile'] = perfil_icc


                if not config['eliminar_exif']:
                    exif_data = img.info.get('exif')
                    if exif_data: save_kwargs['exif'] = exif_data

                if formato_pil == "WebP":
                    save_kwargs.update({'format': 'WEBP', 'quality': config['calidad'], 'lossless': config['lossless'], 'method': config['esfuerzo'], 'exact': False})
                elif formato_pil == "JPEG":
                    save_kwargs.update({'format': 'JPEG', 'quality': config['calidad'], 'optimize': True})
                elif formato_pil == "PNG":
                    save_kwargs.update({'format': 'PNG', 'optimize': True})

                img.save(ruta_salida, **save_kwargs)
                return True
        except Exception as e:
            self.escribir_log(f"❌ Error al optimizar {ruta_imagen.name}: {e}")
            return False

    def finalizar_proceso(self):
        self.esta_procesando = False
        self.after(0, lambda: self.alternar_estado_interfaz(True))

if __name__ == "__main__":
    app = OptimizadorApp()
    app.mainloop()