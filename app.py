import os
import shutil
import threading
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog

# Extensiones de imagen soportadas de entrada
EXTENSIONES_SOPORTADAS = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp', '.avif'}

class CTkTooltip:
    """Clase personalizada para mostrar información flotante moderna al pasar el ratón o hacer clic."""
    def __init__(self, widget, text, delay=300):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id_after = None
        
        # Vincular eventos tanto al pasar el ratón como al hacer clic
        self.widget.bind("<Enter>", self.programar_mostrar)
        self.widget.bind("<Leave>", self.ocultar)
        self.widget.bind("<ButtonPress>", self.mostrar_inmediato)

    def programar_mostrar(self, event=None):
        self.id_after = self.widget.after(self.delay, self.mostrar)

    def mostrar_inmediato(self, event=None):
        if self.id_after:
            self.widget.after_cancel(self.id_after)
        self.mostrar()

    def mostrar(self):
        if self.tooltip_window:
            return
        
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.withdraw()
        self.tooltip_window.overrideredirect(True)
        
        modo_oscuro = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if modo_oscuro else "#e0e0e0"
        fg_color = "#ffffff" if modo_oscuro else "#1a1a1a"
        
        label = ctk.CTkLabel(
            self.tooltip_window, 
            text=self.text, 
            justify="left",
            font=ctk.CTkFont(size=11),
            fg_color=bg_color,
            text_color=fg_color,
            corner_radius=6,
            padx=10,
            pady=8
        )
        label.pack()
        
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 15
        
        self.tooltip_window.geometry(f"+{x}+{y}")
        self.tooltip_window.deiconify()
        self.tooltip_window.attributes("-topmost", True)

    def ocultar(self, event=None):
        if self.id_after:
            self.widget.after_cancel(self.id_after)
            self.id_after = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class OptimizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Optimizador y Conversor Profesional de Imágenes")
        self.geometry("820x840")
        self.minsize(780, 780)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables de estado
        self.ruta_origen = ctk.StringVar()
        self.ruta_destino = ctk.StringVar()  
        self.ruta_backup = ctk.StringVar()   
        self.modo_trabajo_var = ctk.StringVar(value="sitio")
        
        self.formato_salida_var = ctk.StringVar(value="WebP")
        self.eliminar_exif_var = ctk.BooleanVar(value=True)
        self.calidad_var = ctk.IntVar(value=80)
        self.lossless_var = ctk.BooleanVar(value=False)
        self.esfuerzo_var = ctk.StringVar(value="6")
        self.max_size_var = ctk.StringVar(value="")
        
        self.esta_procesando = False

        self.construir_interfaz()

    def crear_icono_info(self, parent, texto_ayuda, padx=5):
        """Genera un botón interactivo 'ⓘ' con su tooltip integrado."""
        btn_info = ctk.CTkButton(
            parent, 
            text="ⓘ", 
            width=20, 
            height=20, 
            fg_color="transparent", 
            text_color=("#1f538d", "#66b3ff"), 
            hover_color=("#e0e0e0", "#3a3a3a"),
            font=ctk.CTkFont(size=13, weight="bold"),
            cursor="hand2"
        )
        btn_info.pack(side="left", padx=padx)
        CTkTooltip(btn_info, texto_ayuda)
        return btn_info

    def construir_interfaz(self):
        # --- SECCIÓN 1: CONFIGURACIÓN DE FLUJO ---
        frame_flujo = ctk.CTkFrame(self)
        frame_flujo.pack(pady=(15, 10), padx=20, fill="x")
        
        lbl_titulo1 = ctk.CTkLabel(frame_flujo, text="📁 Origen y Modo de Trabajo", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_titulo1.grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 5), sticky="w")

        # Carpeta Origen
        ctk.CTkLabel(frame_flujo, text="Carpeta Origen:").grid(row=1, column=0, padx=15, pady=8, sticky="w")
        self.entry_origen = ctk.CTkEntry(frame_flujo, textvariable=self.ruta_origen, placeholder_text="Selecciona la carpeta con las fotos originales...", state="readonly")
        self.entry_origen.grid(row=1, column=1, padx=10, pady=8, sticky="we")
        self.btn_explorar_origen = ctk.CTkButton(frame_flujo, text="Explorar...", width=100, command=self.seleccionar_origen)
        self.btn_explorar_origen.grid(row=1, column=2, padx=15, pady=8)

        # Modo de Operación
        ctk.CTkLabel(frame_flujo, text="Acción:").grid(row=2, column=0, padx=15, pady=8, sticky="w")
        
        frame_modo_inline = ctk.CTkFrame(frame_flujo, fg_color="transparent")
        frame_modo_inline.grid(row=2, column=1, columnspan=2, padx=10, pady=8, sticky="w")
        
        self.seg_modo = ctk.CTkSegmentedButton(
            frame_modo_inline, 
            values=["Optimizar en el sitio", "Exportar a nueva carpeta"],
            command=self.cambiar_modo_trabajo
        )
        self.seg_modo.pack(side="left")
        # 🛠️ SOLUCIÓN: Forzar la selección visual inicial en la interfaz
        self.seg_modo.set("Optimizar en el sitio")
        
        self.crear_icono_info(
            frame_modo_inline, 
            "• Optimizar en el sitio: Reemplaza las fotos originales directamente en su carpeta.\n"
            "• Exportar a nueva carpeta: Deja los originales intactos y guarda las copias en otra ruta limpia.",
            padx=10
        )

        # Separador visual
        canvas_sep = ctk.CTkCanvas(frame_flujo, height=2, highlightthickness=0, bg="#404040" if ctk.get_appearance_mode() == "Dark" else "#d0d0d0")
        canvas_sep.grid(row=3, column=0, columnspan=3, padx=15, pady=10, sticky="we")

        # Carpeta Destino (Exportar)
        self.lbl_destino = ctk.CTkLabel(frame_flujo, text="Carpeta Destino:")
        self.lbl_destino.grid(row=4, column=0, padx=15, pady=8, sticky="w")
        self.entry_destino = ctk.CTkEntry(frame_flujo, textvariable=self.ruta_destino)
        self.entry_destino.grid(row=4, column=1, padx=10, pady=8, sticky="we")
        self.btn_explorar_destino = ctk.CTkButton(frame_flujo, text="Cambiar...", width=100, command=self.seleccionar_destino)
        self.btn_explorar_destino.grid(row=4, column=2, padx=15, pady=8)

        # Carpeta Backup (Sitio)
        self.lbl_backup = ctk.CTkLabel(frame_flujo, text="Carpeta Backup:")
        self.lbl_backup.grid(row=5, column=0, padx=15, pady=8, sticky="w")
        self.entry_backup = ctk.CTkEntry(frame_flujo, textvariable=self.ruta_backup)
        self.entry_backup.grid(row=5, column=1, padx=10, pady=8, sticky="we")
        self.btn_explorar_backup = ctk.CTkButton(frame_flujo, text="Cambiar...", width=100, command=self.seleccionar_backup)
        self.btn_explorar_backup.grid(row=5, column=2, padx=15, pady=8)

        frame_flujo.columnconfigure(1, weight=1)
        self.cambiar_modo_trabajo("Optimizar en el sitio")


        # --- SECCIÓN 2: AJUSTES DE COMPRESIÓN ---
        frame_ajustes = ctk.CTkFrame(self)
        frame_ajustes.pack(pady=10, padx=20, fill="x")
        
        lbl_titulo2 = ctk.CTkLabel(frame_ajustes, text="⚙️ Parámetros de Salida del Códec", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_titulo2.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")

        # Formato de Salida
        frame_lbl_formato = ctk.CTkFrame(frame_ajustes, fg_color="transparent")
        frame_lbl_formato.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        ctk.CTkLabel(frame_lbl_formato, text="Formato:").pack(side="left")
        self.crear_icono_info(frame_lbl_formato, 
                              "• WebP: Compresión de vanguardia (la más recomendada para web).\n"
                              "• JPEG: Formato clásico, máxima compatibilidad universal.\n"
                              "• PNG: Ideal para capturas de pantalla o imágenes con transparencias.", padx=5)

        self.combo_formato = ctk.CTkOptionMenu(
            frame_ajustes, values=["WebP", "JPEG", "PNG"], width=120,
            variable=self.formato_salida_var, command=self.ajustar_controles_por_formato
        )
        self.combo_formato.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Switch Metadatos (EXIF)
        frame_switch_exif = ctk.CTkFrame(frame_ajustes, fg_color="transparent")
        frame_switch_exif.grid(row=1, column=3, padx=15, pady=10, sticky="e")
        self.switch_exif = ctk.CTkSwitch(frame_switch_exif, text="Limpiar metadatos (EXIF)", variable=self.eliminar_exif_var)
        self.switch_exif.pack(side="left")
        self.crear_icono_info(frame_switch_exif, 
                              "Elimina datos invisibles de la foto (Coordenadas GPS, fecha de captura, modelo del móvil).\n"
                              "Se recomienda marcarlo para maximizar el ahorro de espacio en la web.", padx=5)

        # Calidad
        frame_lbl_calidad = ctk.CTkFrame(frame_ajustes, fg_color="transparent")
        frame_lbl_calidad.grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.lbl_calidad_txt = ctk.CTkLabel(frame_lbl_calidad, text="Calidad:")
        self.lbl_calidad_txt.pack(side="left")
        self.crear_icono_info(frame_lbl_calidad, 
                              "Controla la compresión. Menor número implica un archivo mucho más ligero,\n"
                              "pero reduce la nitidez introduciendo ruido visual. El estándar óptimo es 80.", padx=5)

        self.slider_calidad = ctk.CTkSlider(frame_ajustes, from_=0, to=100, number_of_steps=100, command=self.actualizar_label_calidad)
        self.slider_calidad.set(80)
        self.slider_calidad.grid(row=2, column=1, padx=10, pady=10, sticky="we")
        self.lbl_calidad_val = ctk.CTkLabel(frame_ajustes, text="80")
        self.lbl_calidad_val.grid(row=2, column=2, padx=5, pady=10, sticky="w")

        # Lossless
        frame_switch_lossless = ctk.CTkFrame(frame_ajustes, fg_color="transparent")
        frame_switch_lossless.grid(row=2, column=3, padx=15, pady=10, sticky="e")
        self.switch_lossless = ctk.CTkSwitch(frame_switch_lossless, text="Compresión sin pérdidas", variable=self.lossless_var, command=self.toggle_lossless)
        self.switch_lossless.pack(side="left")
        self.crear_icono_info(frame_switch_lossless, 
                              "Exclusivo de WebP. Guarda la imagen respetando el 100% de la fidelidad matemática original.\n"
                              "Desactiva el slider de calidad porque el archivo resultante nunca perderá nitidez.", padx=5)

        # Esfuerzo CPU
        frame_lbl_esfuerzo = ctk.CTkFrame(frame_ajustes, fg_color="transparent")
        frame_lbl_esfuerzo.grid(row=3, column=0, padx=15, pady=10, sticky="w")
        ctk.CTkLabel(frame_lbl_esfuerzo, text="Esfuerzo CPU:").pack(side="left")
        self.crear_icono_info(frame_lbl_esfuerzo, 
                              "Nivel de análisis del compresor (0 = Instantáneo pero más pesado, 6 = Lento pero ultraoptimizado).\n"
                              "Se aconseja dejarlo en 6 para que el archivo pese lo mínimo posible.", padx=5)

        self.combo_esfuerzo = ctk.CTkOptionMenu(frame_ajustes, values=[str(i) for i in range(7)], width=120, variable=self.esfuerzo_var)
        self.combo_esfuerzo.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Redimensionado Max
        frame_lbl_max = ctk.CTkFrame(frame_ajustes, fg_color="transparent")
        frame_lbl_max.grid(row=3, column=2, padx=10, pady=10, sticky="e")
        ctk.CTkLabel(frame_lbl_max, text="Lado Máx (px):").pack(side="left")
        self.crear_icono_info(frame_lbl_max, 
                              "Si tus imágenes son gigantescas (ej. 5000px), introduce un límite (ej. 1920).\n"
                              "El script las encogerá proporcionalmente para evitar subir resoluciones excesivas a la web.\n"
                              "Déjalo vacío para conservar el tamaño intacto.", padx=5)

        self.entry_max_size = ctk.CTkEntry(frame_ajustes, textvariable=self.max_size_var, placeholder_text="Ej: 1920", width=120)
        self.entry_max_size.grid(row=3, column=3, padx=15, pady=10, sticky="w")

        frame_ajustes.columnconfigure(1, weight=1)


        # --- SECCIÓN 3: CONSOLA DE REGISTRO Y LANZADOR ---
        frame_control = ctk.CTkFrame(self, fg_color="transparent")
        frame_control.pack(pady=10, padx=20, fill="both", expand=True)

        self.btn_iniciar = ctk.CTkButton(
            frame_control, text="🚀 Iniciar Optimización", height=45,
            font=ctk.CTkFont(size=14, weight="bold"), command=self.iniciar_hilo_optimizacion
        )
        self.btn_iniciar.pack(pady=(5, 10), fill="x")

        self.progreso_bar = ctk.CTkProgressBar(frame_control, orientation="horizontal", height=10)
        self.progreso_bar.set(0)
        self.progreso_bar.pack(pady=(0, 10), fill="x")

        self.log_box = ctk.CTkTextbox(frame_control, state="disabled", wrap="word", font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True)


    # --- LÓGICA DE CONTROL DINÁMICO UX ---
    def cambiar_modo_trabajo(self, valor_seleccionado):
        if valor_seleccionado == "Optimizar en el sitio":
            self.modo_trabajo_var.set("sitio")
            self.entry_backup.configure(state="normal", text_color=("black", "white"))
            self.btn_explorar_backup.configure(state="normal")
            self.lbl_backup.configure(text_color=("black", "white"))
            
            self.entry_destino.configure(state="disabled", text_color="gray")
            self.btn_explorar_destino.configure(state="disabled")
            self.lbl_destino.configure(text_color="gray")
        else:
            self.modo_trabajo_var.set("exportar")
            self.entry_destino.configure(state="normal", text_color=("black", "white"))
            self.btn_explorar_destino.configure(state="normal")
            self.lbl_destino.configure(text_color=("black", "white"))
            
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
        if self.ruta_origen.get():
            origen = Path(self.ruta_origen.get())
            estado_b = self.entry_backup.cget("state")
            estado_d = self.entry_destino.cget("state")
            
            self.entry_backup.configure(state="normal")
            self.entry_destino.configure(state="normal")
            
            self.ruta_backup.set(str(origen / "raw-imagenes"))
            self.ruta_destino.set(str(origen.parent / f"{origen.name}-optimizada"))
            
            self.entry_backup.configure(state=estado_b)
            self.entry_destino.configure(state=estado_d)

    def seleccionar_destino(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if carpeta:
            self.ruta_destino.set(carpeta)

    def seleccionar_backup(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de backup")
        if carpeta:
            self.ruta_backup.set(carpeta)

    def actualizar_label_calidad(self, valor):
        self.lbl_calidad_val.configure(text=str(int(valor)))
        self.calidad_var.set(int(valor))

    def toggle_lossless(self):
        if self.lossless_var.get():
            self.slider_calidad.configure(state="disabled")
            self.lbl_calidad_val.configure(text_color="gray")
            self.lbl_calidad_txt.configure(text_color="gray")
        else:
            self.slider_calidad.configure(state="normal")
            self.lbl_calidad_val.configure(text_color=("black", "white"))
            self.lbl_calidad_txt.configure(text_color=("black", "white"))

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


    # --- MOTOR DE PROCESAMIENTO ---
    def iniciar_hilo_optimizacion(self):
        if self.esta_procesando: return
            
        if not self.ruta_origen.get():
            self.escribir_log("❌ Error: Selecciona una carpeta de origen primero.")
            return

        modo = self.modo_trabajo_var.get()
        if modo == "sitio" and not self.ruta_backup.get():
            self.escribir_log("❌ Error: Se requiere una carpeta de Backup para continuar.")
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
        
        threading.Thread(target=self.procesar_imagenes, args=(configuracion,), daemon=True).start()

    def procesar_imagenes(self, config):
        origen = config['origen']
        modo = config['modo']
        ext_destino = ".jpg" if config['formato'] == "JPEG" else f".{config['formato'].lower()}"

        archivos_a_procesar = []
        for ruta_archivo in origen.rglob("*"):
            if modo == "sitio" and (config['backup'] in ruta_archivo.parents or ruta_archivo == config['backup']):
                continue
            if ruta_archivo.is_file() and ruta_archivo.suffix.lower() in EXTENSIONES_SOPORTADAS:
                archivos_a_procesar.append(ruta_archivo)

        total_archivos = len(archivos_a_procesar)
        if total_archivos == 0:
            self.escribir_log("ℹ️ No se encontraron imágenes para optimizar en el directorio.")
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
                destino_backup = config['backup'] / ruta_relativa
                try:
                    destino_backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ruta_archivo, destino_backup)
                except Exception as e:
                    self.escribir_log(f"⚠️ Alerta Backup: {e}")
                
                ruta_final_imagen = ruta_archivo.with_suffix(ext_destino)
            else:
                ruta_final_imagen = config['destino'] / ruta_relativa.with_suffix(ext_destino)
                ruta_final_imagen.parent.mkdir(parents=True, exist_ok=True)

            if self.optimizar_imagen(ruta_archivo, ruta_final_imagen, config):
                conteo_exitos += 1
                peso_total_original += peso_original
                peso_total_optimizado += ruta_final_imagen.stat().st_size

                if modo == "sitio" and ruta_archivo.suffix.lower() != ext_destino:
                    ruta_archivo.unlink()
            
            self.actualizar_barra_progreso((indice + 1) / total_archivos)

        self.escribir_log(f"\n✨ ¡Proceso finalizado! Éxito en {conteo_exitos}/{total_archivos} imágenes.")
        if peso_total_original > 0:
            ahorro = peso_total_original - peso_total_optimizado
            pct = (ahorro / peso_total_original) * 100
            self.escribir_log(f"📉 Reducción global de tamaño: {self.formatear_peso(ahorro)} (-{pct:.1f}%)")

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
            self.escribir_log(f"❌ Error al procesar {ruta_imagen.name}: {e}")
            return False

    def finalizar_proceso(self):
        self.esta_procesando = False
        self.after(0, lambda: self.alternar_estado_interfaz(True))

if __name__ == "__main__":
    app = OptimizadorApp()
    app.mainloop()