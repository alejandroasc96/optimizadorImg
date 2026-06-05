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
        self.geometry("750x700")
        self.minsize(700, 650)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables de estado
        self.ruta_origen = ctk.StringVar()
        self.ruta_backup = ctk.StringVar()
        self.formato_salida_var = ctk.StringVar(value="WebP")
        self.eliminar_exif_var = ctk.BooleanVar(value=True) # NUEVA: Marcada por defecto (True)
        self.calidad_var = ctk.IntVar(value=80)
        self.lossless_var = ctk.BooleanVar(value=False)
        self.esfuerzo_var = ctk.StringVar(value="6")
        self.max_size_var = ctk.StringVar(value="")
        
        self.esta_procesando = False

        self.construir_interfaz()

    def construir_interfaz(self):
        # --- PANEL DE RUTAS ---
        frame_rutas = ctk.CTkFrame(self)
        frame_rutas.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(frame_rutas, text="Carpeta Origen:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_origen = ctk.CTkEntry(frame_rutas, textvariable=self.ruta_origen, width=400, state="readonly")
        self.entry_origen.grid(row=0, column=1, padx=10, pady=10, sticky="we")
        ctk.CTkButton(frame_rutas, text="Explorar...", command=self.seleccionar_origen).grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkLabel(frame_rutas, text="Carpeta Backup:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_backup = ctk.CTkEntry(frame_rutas, textvariable=self.ruta_backup, width=400)
        self.entry_backup.grid(row=1, column=1, padx=10, pady=10, sticky="we")
        ctk.CTkButton(frame_rutas, text="Explorar...", command=self.seleccionar_backup).grid(row=1, column=2, padx=10, pady=10)

        frame_rutas.columnconfigure(1, weight=1)

        # --- PANEL DE AJUSTES ---
        frame_ajustes = ctk.CTkFrame(self)
        frame_ajustes.pack(pady=10, padx=20, fill="x")
        
        # Formato de Salida
        ctk.CTkLabel(frame_ajustes, text="Formato Salida:").grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.combo_formato = ctk.CTkOptionMenu(
            frame_ajustes, 
            values=["WebP", "JPEG", "PNG"], 
            variable=self.formato_salida_var,
            command=self.ajustar_controles_por_formato
        )
        self.combo_formato.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        # NUEVO: Switch para eliminar metadatos EXIF (Alineado a la derecha)
        self.switch_exif = ctk.CTkSwitch(frame_ajustes, text="Eliminar metadatos (EXIF / Privacidad)", 
                                         variable=self.eliminar_exif_var)
        self.switch_exif.grid(row=0, column=3, padx=20, pady=15, sticky="e")

        # Calidad
        ctk.CTkLabel(frame_ajustes, text="Calidad:").grid(row=1, column=0, padx=10, pady=15, sticky="w")
        self.slider_calidad = ctk.CTkSlider(frame_ajustes, from_=0, to=100, number_of_steps=100, 
                                            command=self.actualizar_label_calidad)
        self.slider_calidad.set(80)
        self.slider_calidad.grid(row=1, column=1, padx=10, pady=15, sticky="we")
        self.lbl_calidad_val = ctk.CTkLabel(frame_ajustes, text="80")
        self.lbl_calidad_val.grid(row=1, column=2, padx=10, pady=15, sticky="w")

        # Lossless
        self.switch_lossless = ctk.CTkSwitch(frame_ajustes, text="Lossless (WebP)", 
                                             variable=self.lossless_var, command=self.toggle_lossless)
        self.switch_lossless.grid(row=1, column=3, padx=20, pady=15, sticky="e")

        # Esfuerzo CPU y Tamaño Máximo
        ctk.CTkLabel(frame_ajustes, text="Esfuerzo CPU:").grid(row=2, column=0, padx=10, pady=15, sticky="w")
        self.combo_esfuerzo = ctk.CTkOptionMenu(frame_ajustes, values=[str(i) for i in range(7)], variable=self.esfuerzo_var)
        self.combo_esfuerzo.grid(row=2, column=1, padx=10, pady=15, sticky="w")

        ctk.CTkLabel(frame_ajustes, text="Tamaño Max (px):").grid(row=2, column=2, padx=10, pady=15, sticky="e")
        self.entry_max_size = ctk.CTkEntry(frame_ajustes, textvariable=self.max_size_var, placeholder_text="Opcional")
        self.entry_max_size.grid(row=2, column=3, padx=20, pady=15, sticky="w")

        frame_ajustes.columnconfigure(1, weight=1)

        # --- LOG Y CONTROL ---
        frame_control = ctk.CTkFrame(self, fg_color="transparent")
        frame_control.pack(pady=10, padx=20, fill="both", expand=True)

        self.btn_iniciar = ctk.CTkButton(frame_control, text="🚀 Iniciar Optimización", height=40,
                                         font=ctk.CTkFont(size=14, weight="bold"), command=self.iniciar_hilo_optimizacion)
        self.btn_iniciar.pack(pady=(0, 10), fill="x")

        self.log_box = ctk.CTkTextbox(frame_control, state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True)

    # --- FUNCIONES DE INTERFAZ ---
    def seleccionar_origen(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de origen")
        if carpeta:
            self.ruta_origen.set(carpeta)
            backup_default = str(Path(carpeta) / "raw-imagenes")
            self.ruta_backup.set(backup_default)

    def seleccionar_backup(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta para backups")
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
            self.escribir_log("ℹ️ Info: PNG es un formato sin pérdidas. Ajustes de calidad e hilos de CPU ignorados.")
        elif formato == "JPEG":
            self.slider_calidad.configure(state="normal")
            self.switch_lossless.configure(state="disabled")
            self.combo_esfuerzo.configure(state="disabled")
            self.escribir_log("ℹ️ Info: JPEG no soporta transparencias ni 'esfuerzo de CPU'.")
        else: # WebP
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

    def alternar_estado_interfaz(self, estado):
        estado_ctk = "normal" if estado else "disabled"
        self.btn_iniciar.configure(state=estado_ctk)

    # --- LOGICA MULTIHILO Y OPTIMIZACIÓN ---
    def iniciar_hilo_optimizacion(self):
        if self.esta_procesando: return
            
        if not self.ruta_origen.get():
            self.escribir_log("❌ Error: Selecciona una carpeta de origen primero.")
            return

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        max_size_str = self.max_size_var.get().strip()
        max_size = int(max_size_str) if max_size_str.isdigit() else None

        configuracion = {
            'origen': Path(self.ruta_origen.get()).resolve(),
            'backup': Path(self.ruta_backup.get()).resolve(),
            'formato': self.formato_salida_var.get(),
            'eliminar_exif': self.eliminar_exif_var.get(), # Guardamos el estado del nuevo switch
            'calidad': self.calidad_var.get(),
            'lossless': self.lossless_var.get(),
            'esfuerzo': int(self.esfuerzo_var.get()),
            'max_size': max_size
        }

        self.esta_procesando = True
        self.alternar_estado_interfaz(False)
        self.escribir_log(f"🚀 Iniciando conversión a {configuracion['formato']} en: {configuracion['origen']}")
        
        threading.Thread(target=self.procesar_imagenes, args=(configuracion,), daemon=True).start()

    def procesar_imagenes(self, config):
        conteo_exitos = 0
        origen = config['origen']
        carpeta_backup = config['backup']
        
        ext_destino = ".jpg" if config['formato'] == "JPEG" else f".{config['formato'].lower()}"

        if not origen.exists() or not origen.is_dir():
            self.escribir_log("❌ Error: La carpeta de origen no existe.")
            self.finalizar_proceso()
            return

        try:
            for ruta_archivo in origen.rglob("*"):
                if carpeta_backup in ruta_archivo.parents or ruta_archivo == carpeta_backup:
                    continue
                    
                if ruta_archivo.is_file() and ruta_archivo.suffix.lower() in EXTENSIONES_SOPORTADAS:
                    
                    # Si ya es del formato destino y no hay redimensionamiento, revisamos si requiere limpiar EXIF
                    if ruta_archivo.suffix.lower() == ext_destino and not config['max_size'] and not config['eliminar_exif']:
                        continue

                    ruta_relativa = ruta_archivo.relative_to(origen)
                    destino_backup = carpeta_backup / ruta_relativa
                    
                    self.escribir_log(f"Procesando: {ruta_relativa}")
                    
                    try:
                        destino_backup.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(ruta_archivo, destino_backup)
                        
                        if self.optimizar_imagen(ruta_archivo, config, ext_destino):
                            conteo_exitos += 1
                            if ruta_archivo.suffix.lower() != ext_destino:
                                ruta_archivo.unlink()
                                
                    except Exception as e:
                        self.escribir_log(f"❌ No se pudo procesar {ruta_archivo.name}: {e}")

            self.escribir_log(f"\n✨ ¡Proceso finalizado! Se procesaron {conteo_exitos} imágenes.")
            self.escribir_log(f"📦 Originales a salvo en: '{carpeta_backup}'")

        except Exception as e:
            self.escribir_log(f"❌ Error inesperado: {e}")
        finally:
            self.finalizar_proceso()

    def optimizar_imagen(self, ruta_imagen, config, ext_destino):
        try:
            with Image.open(ruta_imagen) as img:
                # 1. Redimensionar si es necesario
                if config['max_size']:
                    ancho, alto = img.size
                    lado_mayor = max(ancho, alto)
                    if lado_mayor > config['max_size']:
                        escala = config['max_size'] / lado_mayor
                        img = img.resize((int(ancho * escala), int(alto * escala)), Image.Resampling.LANCZOS)

                ruta_salida = ruta_imagen.with_suffix(ext_destino)
                formato_pil = config['formato']

                # 2. Convertir color/canal alfa si el destino es JPEG
                if formato_pil == "JPEG":
                    if img.mode in ("RGBA", "P", "LA"):
                        fondo = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode in ("RGBA", "LA"):
                            fondo.paste(img, mask=img.split()[-1])
                        else:
                            fondo.paste(img)
                        img = fondo
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                
                # 3. Preparar parámetros de guardado dinámicos (Kwargs)
                save_kwargs = {}
                
                # Lógica EXIF: Si el usuario NO quiere eliminar los metadatos, intentamos preservarlos
                if not config['eliminar_exif']:
                    exif_data = img.info.get('exif')
                    if exif_data:
                        save_kwargs['exif'] = exif_data

                # Agregar parámetros específicos de formato
                if formato_pil == "WebP":
                    save_kwargs.update({
                        'format': 'WEBP', 'quality': config['calidad'],
                        'lossless': config['lossless'], 'method': config['esfuerzo'], 'exact': False
                    })
                elif formato_pil == "JPEG":
                    save_kwargs.update({'format': 'JPEG', 'quality': config['calidad'], 'optimize': True})
                elif formato_pil == "PNG":
                    save_kwargs.update({'format': 'PNG', 'optimize': True})

                # Guardar la imagen aplicando los parámetros resultantes
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