import io
import os
import sys
import json
import shutil
import zipfile
import requests
import threading
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk  # Importar ttk para usar Progressbar
import customtkinter as ctk

from fpdf import FPDF
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import filedialog, messagebox
from tkinter import messagebox
from PIL import Image as PilImage, ImageTk
from msg import Mensaje  
from packaging import version

from bs4 import BeautifulSoup
from googletrans import Translator
from deep_translator import GoogleTranslator

from historial import cargar_historial, guardar_historial, guardar_cambios_historial, editar_historial


class ActualizadorApp:
    def __init__(self, app_version):
        self.app_version = app_version
        self.repo_url = "https://api.github.com/repos/Emy69/Scans/releases/latest"  
        self.download_url = None
        self.config_file = "config.json"
        self.app_folder = None  # Inicializamos sin la ruta

    def cargar_ruta_app(self):
        """Carga la ruta de la carpeta de la aplicación desde un archivo de configuración,
        o pide la ruta al usuario usando filedialog si no existe el archivo de configuración."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config = json.load(f)
                return config.get("app_folder", "")
        else:
            return None  # No hay ruta configurada aún

    def seleccionar_carpeta(self):
        """Abre un cuadro de diálogo para seleccionar la carpeta de la aplicación y guarda la ruta en un archivo de configuración."""
        root = tk.Tk()
        root.withdraw()  # Ocultar la ventana principal de Tkinter
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta de la aplicación")
        if carpeta:
            self.app_folder = carpeta
            self.guardar_ruta_app()
            return carpeta
        else:
            raise ValueError("No se seleccionó una carpeta válida")

    def guardar_ruta_app(self):
        """Guarda la ruta de la carpeta de la aplicación en un archivo de configuración."""
        config = {"app_folder": self.app_folder}
        with open(self.config_file, "w") as f:
            json.dump(config, f)

    def verificar_actualizacion(self):
        """Verifica si existe una actualización disponible en GitHub."""
        try:
            response = requests.get(self.repo_url)
            data = response.json()

            latest_version = data["tag_name"]  # Última versión disponible
            if version.parse(latest_version) > version.parse(self.app_version):
                self.download_url = data["assets"][0]["browser_download_url"]
                # Preguntar al usuario si desea actualizar
                respuesta = messagebox.askyesno("Actualización disponible", "Hay una nueva actualización disponible. ¿Quieres actualizar ahora?")
                if respuesta:
                    self.mostrar_ventana_actualizacion()
                return True
            return False
        except Exception as e:
            print(f"Error al verificar actualización: {e}")
            return False

    def mostrar_ventana_actualizacion(self):
        """Muestra una ventana de actualización con una barra de progreso y un área de log."""
        root = ctk.CTkToplevel()  # Usar Toplevel para crear una ventana secundaria
        root.title("Actualización de la aplicación")
        
        # Centrar la ventana
        window_width = 400
        window_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
        
        # Mantener la ventana en primer plano
        root.attributes('-topmost', True)

        # Frame principal
        main_frame = ctk.CTkFrame(root)
        main_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Barra de progreso
        progreso_label = ctk.CTkLabel(main_frame, text="Progreso de la actualización...")
        progreso_label.pack(pady=10)
        progreso = tk.DoubleVar()
        barra_progreso = ttk.Progressbar(main_frame, variable=progreso, maximum=100)
        barra_progreso.pack(pady=10, fill='x')

        # Área de log usando tk.Text
        log_text = tk.Text(main_frame, height=10, wrap='word', state='disabled')
        log_text.pack(pady=10, fill='both', expand=True)

        def log_mensaje(mensaje, error=False):
            def update_log():
                log_text.configure(state='normal')
                if error:
                    log_text.insert(tk.END, f"ERROR: {mensaje}\n", 'error')
                else:
                    log_text.insert(tk.END, f"{mensaje}\n")
                log_text.configure(state='disabled')
                log_text.see(tk.END)

            root.after(0, update_log)

        log_text.tag_configure('error', foreground='red')

        # Función para realizar la actualización
        def iniciar_actualizacion():
            def tarea():
                try:
                    # Aquí cargamos la ruta de la carpeta solo al ejecutar la actualización
                    if not self.app_folder:
                        self.app_folder = self.cargar_ruta_app()
                    if not self.app_folder:
                        self.app_folder = self.seleccionar_carpeta()  # Solicitar la carpeta si no se ha configurado

                    # Asegúrate de pasar todos los argumentos necesarios
                    self.descargar_y_actualizar(barra_progreso, progreso, log_mensaje)
                    root.after(0, lambda: messagebox.showinfo("Éxito", "La aplicación se actualizó correctamente."))
                except Exception as e:
                    log_mensaje(f"Hubo un error durante la actualización: {e}", error=True)

            # Ejecutar la tarea en un hilo separado
            hilo = threading.Thread(target=tarea)
            hilo.start()

        # Botón para iniciar la actualización
        actualizar_button = ctk.CTkButton(main_frame, text="Iniciar actualización", command=iniciar_actualizacion)
        actualizar_button.pack(pady=20, side='bottom')  # Asegurar que el botón esté siempre visible

        # Manejar el evento de cierre de la ventana
        def on_closing():
            if messagebox.askokcancel("Cerrar", "¿Estás seguro de que deseas cerrar la ventana de actualización?"):
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()

    def descargar_y_actualizar(self, barra_progreso, progreso, log_mensaje):
        """Descarga la actualización, la descomprime y reinicia la aplicación."""
        try:
            if not self.download_url:
                raise ValueError("No hay URL de descarga disponible.")

            # Descargar la actualización
            log_mensaje(f"Descargando actualización desde {self.download_url}...")
            response = requests.get(self.download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Descargar archivo y actualizar la barra de progreso
            with open("update.zip", "wb") as f:
                for data in response.iter_content(chunk_size=1024):
                    downloaded += len(data)
                    f.write(data)
                    progreso.set((downloaded / total_size) * 100)
                    barra_progreso.update_idletasks()

            # Descomprimir el archivo ZIP recibido
            log_mensaje("Descomprimiendo archivos...")
            update_folder = "update_folder"
            if not os.path.exists(update_folder):
                os.makedirs(update_folder)

            with zipfile.ZipFile("update.zip", 'r') as zip_file:
                total_files = len(zip_file.namelist())
                extracted = 0

                for file in zip_file.namelist():
                    zip_file.extract(file, update_folder)
                    extracted += 1
                    progreso.set(50 + (extracted / total_files) * 25)  # Ajuste para reflejar el progreso
                    barra_progreso.update_idletasks()

            # Crear una copia de seguridad antes de reemplazar los archivos
            log_mensaje("Creando copia de seguridad...")
            self.respaldo_archivos()

            # Reemplazar los archivos antiguos con los nuevos
            log_mensaje("Reemplazando archivos...")
            total_files_to_replace = len(os.listdir(update_folder))
            replaced = 0
            for item in os.listdir(update_folder):
                source = os.path.join(update_folder, item)
                destination = os.path.join(self.app_folder, item)
                if os.path.isdir(source):
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    self.reemplazar_archivos(source, destination)  # Llamada recursiva si hay subdirectorios
                else:
                    shutil.copy2(source, destination)  # Copiar archivo (manteniendo metadatos)
                replaced += 1
                progreso.set(75 + (replaced / total_files_to_replace) * 25)  # Ajuste para reflejar el progreso
                barra_progreso.update_idletasks()

            # Limpiar la carpeta temporal de la actualización
            log_mensaje("Limpiando archivos temporales...")
            shutil.rmtree(update_folder)
            os.remove("update.zip")

            # Reiniciar la aplicación
            log_mensaje("Reiniciando la aplicación...")
            self.reiniciar_aplicacion()
        except Exception as e:
            log_mensaje(f"Error al descargar o descomprimir la actualización: {e}", error=True)
            # Restaurar la aplicación a su estado anterior si ocurrió un error
            self.restaurar_respaldo()

    def respaldo_archivos(self):
        """Crea una copia de seguridad de los archivos de la aplicación."""
        backup_folder = "app_backup"  # Ruta donde se almacenará el respaldo

        try:
            # Verificar si ya existe una copia de seguridad
            if os.path.exists(backup_folder):
                print("Ya existe una copia de seguridad.")
            else:
                # Crear una copia de seguridad de la carpeta de la aplicación
                shutil.copytree(self.app_folder, backup_folder)
                print("Copia de seguridad creada exitosamente.")
        except Exception as e:
            print(f"Error al crear la copia de seguridad: {e}")

    def restaurar_respaldo(self):
        """Restaura los archivos de la aplicación desde el respaldo en caso de error."""
        backup_folder = "app_backup"

        try:
            if os.path.exists(backup_folder):
                # Eliminar los archivos actuales de la aplicación
                shutil.rmtree(self.app_folder)
                # Restaurar la copia de seguridad
                shutil.copytree(backup_folder, self.app_folder)
                print("Respaldo restaurado correctamente.")
            else:
                print("No se encontró la copia de seguridad para restaurar.")
        except Exception as e:
            print(f"Error al restaurar el respaldo: {e}")

    def reemplazar_archivos(self, source, destination):
        """Reemplaza los archivos actuales con los archivos extraídos de la actualización."""
        try:
            if os.path.isdir(source):
                if not os.path.exists(destination):
                    os.makedirs(destination)
                for item in os.listdir(source):
                    s_item = os.path.join(source, item)
                    d_item = os.path.join(destination, item)
                    self.reemplazar_archivos(s_item, d_item)  # Llamada recursiva si hay subdirectorios
            else:
                shutil.copy2(source, destination)  # Copiar archivo
        except Exception as e:
            print(f"Error al reemplazar los archivos: {e}")

    def reiniciar_aplicacion(self):
        """Reinicia la aplicación después de la actualización."""
        print("Reiniciando la aplicación...")
        python = sys.executable
        os.execl(python, python, *sys.argv)  # Reiniciar la aplicación


class DescargadorTextoApp:
    def __init__(self, root):
        self.root = root
        self.app_version = "V0.0.4"
        self.root.title(f"Wonderful Galaxy DL - {self.app_version}")

        # Mostrar el mensaje inicial
        Mensaje()  # Crear una instancia de Mensaje para mostrar la ventana emergente

        # Establecer el icono de la ventana
        icon_path = "img/cropped-Wonderful-32x32.png"  # Ruta a la imagen de 32x32
        icon_image = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(False, icon_image)

        # Obtener el tamaño de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Establecer el tamaño de la ventana
        window_width = 800
        window_height = 700

        # Calcular las coordenadas para centrar la ventana
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)

        # Establecer la geometría de la ventana
        self.root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        # Menú personalizado en la parte superior
        self.menu_bar = ctk.CTkFrame(root)
        self.menu_bar.pack(side='top', fill='x', pady=5)

        # Llamar al verificador de actualizaciones
        self.actualizador = ActualizadorApp(self.app_version)
        self.verificar_actualizacion()

        self.create_custom_menubar()

        # Crear un frame para contener todos los elementos
        self.frame = ctk.CTkFrame(root)
        self.frame.pack(pady=20, padx=20, fill='both', expand=True)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Campo de entrada para la URL
        self.label_url = ctk.CTkLabel(self.frame, text="Ingresa la URL a escanear:", font=("Helvetica", 14))
        self.label_url.pack(pady=10)
        self.entry_url = ctk.CTkEntry(self.frame, width=300)
        self.entry_url.pack(pady=5)

        # Campo de entrada para la contraseña
        self.label_password = ctk.CTkLabel(self.frame, text="Ingresa la contraseña:", font=("Helvetica", 14))
        self.label_password.pack(pady=10)
        self.entry_password = ctk.CTkEntry(self.frame, width=300, show='*')
        self.entry_password.pack(pady=5)

        # Cargar datos guardados si existen
        self.cargar_datos()

        # Botón para escanear o descargar y traducir
        self.boton_scanear = ctk.CTkButton(self.frame, text="Acceder y Escanear", command=self.procesar_url)
        self.boton_scanear.pack(pady=20)

        # Área de texto para mostrar el resultado
        self.text_area = ctk.CTkTextbox(self.frame, width=600, height=250, state='normal')
        self.text_area.pack(pady=20)
        self.text_area.configure(state='disabled')

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(self.frame, width=600)
        self.progress_bar.pack(pady=20)

        # Etiqueta para mostrar la ruta del PDF
        self.label_pdf_path = ctk.CTkLabel(self.frame, text="", font=("Helvetica", 12))
        self.label_pdf_path.pack(pady=10)

        # Inicializar el log
        self.log_mensajes = []

    def verificar_actualizacion(self):
        """Verifica si hay una actualización disponible y la descarga si es necesario."""
        def tarea():
            if self.actualizador.verificar_actualizacion():
                respuesta = messagebox.askyesno("Actualización disponible", "¿Hay una nueva actualización disponible. ¿Quieres actualizar ahora?")
                if respuesta:
                    self.actualizador.descargar_y_actualizar()
            else:
                self.mostrar_mensaje("Ya tienes la última versión.")  # Mostrar en el log

        # Ejecutar la tarea en un hilo para no bloquear la interfaz
        hilo = threading.Thread(target=tarea)
        hilo.start()


    def load_image(self, image_path):
        """Carga una imagen y la devuelve como un objeto PhotoImage."""
        return ctk.CTkImage(Image.open(image_path), size=(24, 24))  # Ajusta el tamaño según sea necesario

    def create_custom_menubar(self):
        # Botón Archivo
        archivo_button = ctk.CTkButton(
            self.menu_bar,
            text="Archivo",
            width=80,
            fg_color="transparent",
            hover_color="gray25",
            command=self.toggle_archivo_menu
        )
        archivo_button.pack(side="left")
        archivo_button.bind("<Button-1>", lambda e: "break")

        # Botón About
        about_button = ctk.CTkButton(
            self.menu_bar,
            text="About",
            width=80,
            fg_color="transparent",
            hover_color="gray25",
            command=self.show_contributors_window
        )
        about_button.pack(side="left")
        about_button.bind("<Button-1>", lambda e: "break")

        # Botón Donaciones
        donaciones_button = ctk.CTkButton(
            self.menu_bar,
            text="Donaciones",
            width=80,
            fg_color="transparent",
            hover_color="gray25",
            command=self.toggle_donaciones_menu
        )
        donaciones_button.pack(side="left")
        donaciones_button.bind("<Button-1>", lambda e: "break")

        # Botón Historial
        historial_button = ctk.CTkButton(
            self.menu_bar,
            text="Historial",
            width=80,
            fg_color="transparent",
            hover_color="gray25",
            command=self.show_historial_window
        )
        historial_button.pack(side="left")
        historial_button.bind("<Button-1>", lambda e: "break")

        # Inicializar variables para los menús desplegables
        self.archivo_menu_frame = None
        self.ayuda_menu_frame = None
        self.donaciones_menu_frame = None

    def toggle_archivo_menu(self):
        if self.archivo_menu_frame and self.archivo_menu_frame.winfo_exists():
            self.archivo_menu_frame.destroy()
        else:
            self.close_all_menus()
            self.archivo_menu_frame = self.create_menu_frame([
                ("Configuraciones", self.open_settings),  # Cambia a tu método para abrir configuraciones
                ("separator", None),
                ("Salir", self.salir_aplicacion),  # Cambia a un método que cierre la aplicación
            ], x=0)

    def toggle_ayuda_menu(self):
        if self.ayuda_menu_frame and self.ayuda_menu_frame.winfo_exists():
            self.ayuda_menu_frame.destroy()
        else:
            self.close_all_menus()
            self.ayuda_menu_frame = self.create_menu_frame([
                ("Notas de Parche", self.open_patch_notes),
                ("separator", None),
                ("Reportar un Error", None),
                ("   GitHub", lambda: webbrowser.open("https://github.com/Emy69/CoomerDL/issues")),
                ("   Discord", lambda: webbrowser.open("https://discord.gg/ku8gSPsesh")),
            ], x=80)

    def toggle_donaciones_menu(self):
        if self.donaciones_menu_frame and self.donaciones_menu_frame.winfo_exists():
            self.donaciones_menu_frame.destroy()
        else:
            self.close_all_menus()
            self.donaciones_menu_frame = self.create_menu_frame([
                ("PayPal", lambda: webbrowser.open("https://www.paypal.com/paypalme/Emy699")),
                ("Buy me a coffee", lambda: webbrowser.open("https://buymeacoffee.com/emy_69")),
            ], x=160)

    def create_menu_frame(self, options, x):
        # Crear el marco del menú con fondo oscuro y borde de sombra para resaltar
        menu_frame = ctk.CTkFrame(self.root, corner_radius=5, fg_color="gray25", border_color="black", border_width=1)
        menu_frame.place(x=x, y=30)
        
        # Añadir opciones al menú con separación entre elementos
        for option in options:
            if option[0] == "separator":
                separator = ctk.CTkFrame(menu_frame, height=1, fg_color="gray50")
                separator.pack(fill="x", padx=5, pady=5)
            elif option[1] is None:
                # Texto sin comando (por ejemplo, título de submenú)
                label = ctk.CTkLabel(menu_frame, text=option[0], anchor="w", fg_color="gray30")
                label.pack(fill="x", padx=5, pady=2)
            else:
                btn = ctk.CTkButton(
                    menu_frame,
                    text=option[0],
                    fg_color="transparent",
                    hover_color="gray35",
                    anchor="w",
                    text_color="white",
                    command=lambda cmd=option[1]: cmd()
                )
                btn.pack(fill="x", padx=5, pady=2)

        return menu_frame

    def close_all_menus(self):
        for menu_frame in [self.archivo_menu_frame, self.ayuda_menu_frame, self.donaciones_menu_frame]:
            if menu_frame and menu_frame.winfo_exists():
                menu_frame.destroy()

    def mostrar_mensaje(self, mensaje):
        """Función para actualizar el panel de texto en la interfaz."""
        self.log_mensajes.append(mensaje)  # Agregar mensaje al log
        self.text_area.configure(state='normal')
        self.text_area.delete(1.0, ctk.END)  # Limpiar el área de texto
        self.text_area.insert(ctk.END, "\n".join(self.log_mensajes))  # Mostrar el log completo
        self.text_area.configure(state='disabled')

    def guardar_datos(self, url, password):
        # Verificar si la carpeta 'Guardado' existe, si no, crearla
        if not os.path.exists("Guardado"):
            os.makedirs("Guardado")

        datos = {
            "url": url,
            "password": password
        }
        with open("Guardado/datos.json", "w", encoding="utf-8") as json_file:
            json.dump(datos, json_file)

    def descargar_texto(self):
        url = self.entry_url.get()
        password = self.entry_password.get()
        
        if not url:
            messagebox.showerror("Error", "Por favor, ingresa una URL.")
            return
        if not password:
            messagebox.showerror("Error", "Por favor, ingresa una contraseña.")
            return

        self.guardar_datos(url, password)  # Guardar datos en JSON

        # Iniciar la barra de progreso
        self.progress_bar.start()
        self.progress_bar.set(0)

        def tarea():
            try:
                self.mostrar_mensaje("Iniciando el navegador y accediendo a la página...")

                # Configuración de Selenium y ChromeDriver
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-javascript")  # Desactiva JavaScript
                options.add_argument('--headless')  # Comentar esta línea
                driver = webdriver.Chrome(options=options)

                driver.get(url)

                # Ingresar la contraseña y enviar
                password_field = driver.find_element(By.NAME, "password_protected_pwd")
                password_field.send_keys(password)
                password_field.send_keys(Keys.RETURN)

                self.mostrar_mensaje("Contraseña ingresada, esperando respuesta...")

                # Esperar a que el contenido se cargue y buscar el contenedor de texto
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'entry-content-wrap'))
                )

                # Encontrar y extraer el contenido en etiquetas <strong>, <em>, y <p>
                contenedor = driver.find_element(By.CLASS_NAME, 'entry-content-wrap')
                contenido_texto = []
                for elemento in contenedor.find_elements(By.XPATH, './/p | .//strong | .//em'):
                    # Evitar duplicados verificando si el texto ya está en la lista
                    texto = elemento.text.strip()
                    if texto and texto not in contenido_texto:
                        contenido_texto.append(texto)

                # Buscar imágenes en <figure class="swiper-slide-inner"> con <img class="swiper-slide-image">
                imagenes = []
                for figura in contenedor.find_elements(By.CLASS_NAME, 'swiper-slide-inner'):
                    try:
                        imagen = figura.find_element(By.TAG_NAME, 'img')  # Definir 'imagen' correctamente
                        src = imagen.get_attribute("src")
                        img_data = requests.get(src)

                        # Verificar si la respuesta es una imagen válida
                        if 'image' in img_data.headers['Content-Type']:
                            try:
                                img_path = f"temp_{len(imagenes)}.{img_data.headers['Content-Type'].split('/')[1]}"
                                with open(img_path, "wb") as img_file:
                                    img_file.write(img_data.content)
                                imagenes.append(img_path)
                                break  # Salir del bucle después de encontrar la primera imagen
                            except Exception as e:
                                self.mostrar_mensaje(f"Error al guardar la imagen: {str(e)}")
                        else:
                            self.mostrar_mensaje("La URL no apunta a una imagen válida.")
                    except Exception as e:
                        self.mostrar_mensaje(f"Error al procesar la imagen: {str(e)}")

                driver.quit()

                # Mostrar el texto en el área de texto
                self.mostrar_mensaje("Extrayendo contenido y creando el PDF...")
                self.text_area.configure(state='normal')
                self.text_area.delete(1.0, ctk.END)
                self.text_area.insert(ctk.END, "\n".join(contenido_texto))
                self.text_area.configure(state='disabled')

                # Seleccionar ruta y crear el PDF
                ruta_pdf = self.seleccionar_ruta()
                if ruta_pdf:
                    self.crear_pdf(contenido_texto, imagenes, ruta_pdf)  # Solo la primera imagen se pasará aquí
                    self.mostrar_mensaje(f"PDF creado: {ruta_pdf}")
                    self.label_pdf_path.configure(text=f"PDF guardado en: {ruta_pdf}")
                    self.label_pdf_path.bind("<Button-1>", lambda e: os.startfile(ruta_pdf))

                    # Guardar en el historial
                    nombre_pdf = os.path.basename(ruta_pdf)
                    self.guardar_historial(nombre_pdf, "", "")

                    # Mostrar un popup informando al usuario que el PDF se ha guardado
                    messagebox.showinfo("Descarga Completa", f"El PDF ha sido guardado exitosamente en: {ruta_pdf}")

                # Eliminar imágenes temporales después de crear el PDF
                for img in imagenes:
                    if os.path.exists(img):
                        os.remove(img)
            except Exception as e:
                self.mostrar_mensaje(f"Error en la tarea: {str(e)}")
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
            finally:
                self.progress_bar.stop()

        # Ejecutar la tarea en un hilo separado
        hilo = threading.Thread(target=tarea)
        hilo.start()

    def cargar_datos(self):
        """Cargar datos guardados desde el archivo JSON."""
        if os.path.exists("Guardado/datos.json"):
            with open("Guardado/datos.json", "r") as json_file:
                datos = json.load(json_file)
                self.entry_url.insert(0, datos.get("url", ""))
                self.entry_password.insert(0, datos.get("password", ""))

    def open_settings(self):
        """Método para abrir la ventana de configuraciones."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Configuraciones")
        
        # Aquí se establece el tamaño de la ventana
        width = 400
        height = 300
        settings_window.geometry(f"{width}x{height}")

        # Centrar la ventana
        self.center_window(settings_window)

        # Aquí puedes implementar la lógica para abrir la ventana de configuraciones
        self.mostrar_mensaje("Abrir ventana de configuraciones...")  # Mensaje de ejemplo

    def salir_aplicacion(self):
        """Método para salir de la aplicación."""
        self.root.quit()  # O usa self.root.destroy() si deseas cerrar la ventana

    def mostrar_info_about(self):
        """Obtiene información de GitHub y muestra en una ventana emergente."""
        try:
            response = requests.get("https://api.github.com/users/emy69")  # Reemplaza 'tu_usuario' con tu nombre de usuario de GitHub
            data = response.json()

            # Extraer información relevante
            nombre = data.get("name", "Nombre no disponible")
            bio = data.get("bio", "Bio no disponible")
            repos_url = data.get("repos_url", "")
            repos_count = data.get("public_repos", 0)

            # Crear el mensaje para mostrar
            mensaje = f"Nombre: {nombre}\nBio: {bio}\nRepositorios Públicos: {repos_count}\nMás información: {repos_url}"

            # Mostrar la ventana emergente
            messagebox.showinfo("Acerca de", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la información: {str(e)}")

    def show_contributors_window(self):
        """Muestra una ventana con la información personal del usuario."""
        contributors_window = tk.Toplevel(self.root)
        contributors_window.title("Acerca de mí")
        
        # Aquí se establece el tamaño de la ventana
        width = 400
        height = 400
        contributors_window.geometry(f"{width}x{height}")

        # Centrar la ventana
        self.center_window(contributors_window)

        self.show_personal_info(contributors_window)

    def show_personal_info(self, parent_frame):
        """Muestra la información personal del usuario en la ventana."""
        try:
            # Aquí puedes personalizar tu información
            nombre = "Emy"  # Reemplaza con tu nombre
            bio = "Holis."  # Reemplaza con tu biografía
            avatar_url = "https://avatars.githubusercontent.com/u/142945265?v=4"  # Reemplaza con la URL de tu avatar
            perfil_url = "https://github.com/emy69"  # Reemplaza con tu URL de GitHub

            # Crear un marco para la información
            frame = ctk.CTkFrame(parent_frame)
            frame.pack(pady=20)

            # Cargar y mostrar el avatar
            avatar_image = PilImage.open(requests.get(avatar_url, stream=True).raw)
            avatar_image = avatar_image.resize((100, 100), PilImage.Resampling.LANCZOS)
            avatar_photo = ImageTk.PhotoImage(avatar_image)

            avatar_label = tk.Label(frame, image=avatar_photo)
            avatar_label.image = avatar_photo  # Guardar referencia para evitar recolección de basura
            avatar_label.pack(side="top", pady=10)

            # Mostrar el nombre
            name_label = ctk.CTkLabel(frame, text=nombre, font=("Helvetica", 16))
            name_label.pack(side="top", pady=5)

            # Mostrar la biografía
            bio_label = ctk.CTkLabel(frame, text=bio, font=("Helvetica", 12))
            bio_label.pack(side="top", pady=5)

            # Botón para abrir el perfil de GitHub
            link_button = ctk.CTkButton(
                frame,
                text="Ver Perfil en GitHub",
                command=lambda: webbrowser.open(perfil_url)
            )
            link_button.pack(side="top", pady=10)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al cargar la información personal.\nError: {e}"
            )

    def center_window(self, window):
        """Centrar la ventana en la pantalla."""
        window.update_idletasks()  # Actualiza las tareas pendientes para obtener el tamaño correcto
        width = window.winfo_width()
        height = window.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        window.geometry(f"{width}x{height}+{x}+{y}")

    def seleccionar_ruta(self):
        """Abre un cuadro de diálogo para seleccionar la ruta donde se guardará el PDF."""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Guardar PDF como"
        )
        return ruta
    
    def crear_pdf(self, contenido_texto, imagenes, ruta):
        pdf = FPDF()
        pdf.add_page()

        # Ruta de la carpeta de fuentes
        font_path = 'fonts/'

        # Establecer fuentes Roboto desde la carpeta de fuentes
        pdf.add_font('Roboto', '', f'{font_path}Roboto-Regular.ttf', uni=True)
        pdf.add_font('Roboto', 'I', f'{font_path}Roboto-Italic.ttf', uni=True)  # Fuente itálica
        pdf.set_font('Roboto', '', 12)  # Ajustar el tamaño de la fuente según sea necesario

        # Añadir contenido de texto
        for texto in contenido_texto:
            if texto.startswith('<em>') and texto.endswith('</em>'):
                pdf.set_font('Roboto', 'I', 12)  # Cambiar a fuente itálica
                texto = texto[4:-5]  # Remover etiquetas <em>
            else:
                pdf.set_font('Roboto', '', 12)  # Volver a la fuente normal

            # Reemplazar guiones y comillas si es necesario
            texto = texto.replace("—", "-").replace("“", "\"").replace("”", "\"")

        self.mostrar_mensaje("PDF creado exitosamente.")

    def show_historial_window(self):
        """Muestra una ventana para gestionar el historial de descargas."""
        historial_window = tk.Toplevel(self.root)
        historial_window.title("Historial de Descargas")

        # Configurar tamaño y centrar la ventana
        width = 800
        height = 400
        historial_window.geometry(f"{width}x{height}")
        self.center_window(historial_window)

        # Crear un frame para el contenido
        frame = ctk.CTkFrame(historial_window)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        # Cargar historial desde JSON
        historial = cargar_historial()

        # Crear una lista para mostrar el historial
        for idx, item in enumerate(historial):
            label_nombre = ctk.CTkLabel(frame, text=f"PDF: {item['nombre']}", font=("Helvetica", 12))
            label_nombre.grid(row=idx, column=0, padx=5, pady=5)

            # Crear campos de entrada para calificación y comentario
            entry_calificacion = ctk.CTkEntry(frame, width=100)
            entry_calificacion.insert(0, item.get("calificacion", ""))
            entry_calificacion.grid(row=idx, column=1, padx=5, pady=5)

            entry_comentario = ctk.CTkEntry(frame, width=100)
            entry_comentario.insert(0, item.get("comentario", ""))
            entry_comentario.grid(row=idx, column=2, padx=5, pady=5)

            # Botón para guardar cambios
            guardar_button = ctk.CTkButton(frame, text="Guardar", command=lambda i=idx: guardar_cambios_historial(i, entry_calificacion, entry_comentario, guardar_button, cargar_historial))
            guardar_button.grid(row=idx, column=3, padx=5, pady=5)

    def procesar_url(self):
        """Determina el tipo de URL y ejecuta la acción correspondiente."""
        url = self.entry_url.get()
        if not url:
            messagebox.showerror("Error", "Por favor, ingresa una URL.")
            return

        if "archiveofourown.org" in url:
            self.descargar_y_traducir_html(url)
        else:
            self.descargar_texto()

    def descargar_y_traducir_html(self, url):
        """Inicia un hilo para descargar y traducir el HTML."""
        threading.Thread(target=self._descargar_y_traducir_html, args=(url,)).start()

    def _descargar_y_traducir_html(self, url):
        """Descarga el HTML de una página de AO3, traduce el texto y lo guarda en un PDF."""
        try:
            self.mostrar_mensaje("Iniciando la descarga de la página...")

            # Descargar el contenido de la página
            response = requests.get(url)
            response.raise_for_status()
            self.mostrar_mensaje("Página descargada exitosamente.")

            # Parsear el HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            workskin_div = soup.find('div', id='workskin')

            if not workskin_div:
                messagebox.showerror("Error", "No se encontró el div con id 'workskin'.")
                return

            # Extraer el título principal
            title_element = workskin_div.find('h2', class_='title heading')
            main_title = title_element.get_text(strip=True) if title_element else "Sin título"

            # Extraer el prefacio o introducción
            preface_div = workskin_div.find('div', class_='preface group')
            preface_text = ""
            if preface_div:
                preface_text = preface_div.get_text(separator="\n", strip=True)
                preface_text = traducir_texto(preface_text)

            # Extraer títulos y texto de los capítulos
            chapters_div = workskin_div.find('div', id='chapters')
            translated_texts = []
            if chapters_div:
                chapters = chapters_div.find_all('div', class_='chapter')
                for chapter in chapters:
                    chapter_title_element = chapter.find('h2', class_='title heading')
                    chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Sin título"
                    chapter_text = chapter.get_text(separator="\n", strip=True)

                    # Remover el título del capítulo del texto
                    if chapter_title in chapter_text:
                        chapter_text = chapter_text.replace(chapter_title, '', 1).strip()

                    translated_text = traducir_texto(chapter_text)
                    if translated_text is None:
                        messagebox.showerror("Error", "Error al traducir el texto.")
                        return
                    translated_texts.append((chapter_title, translated_text))
            else:
                translated_text = traducir_texto(workskin_div.get_text(separator="\n", strip=True))
                if translated_text is None:
                    messagebox.showerror("Error", "Error al traducir el texto.")
                    return
                translated_texts = [(main_title, translated_text)]

            self.mostrar_mensaje("Traducción completada, creando PDF...")

            # Crear el PDF traducido
            ruta = self.seleccionar_ruta()
            if ruta:
                self.crear_pdf_traducido(main_title, preface_text, translated_texts, ruta)

        except requests.exceptions.RequestException as e:
            self.mostrar_mensaje(f"Error al descargar la página: {e}")
        except Exception as e:
            self.mostrar_mensaje(f"Error al procesar la página: {e}")

    def crear_pdf_traducido(self, main_title, preface_text, contenido_texto, ruta):
        pdf = FPDF()
        pdf.add_page()

        # Ruta de la carpeta de fuentes
        font_path = 'fonts/'

        # Establecer fuentes Roboto desde la carpeta de fuentes
        pdf.add_font('Roboto', '', f'{font_path}Roboto-Regular.ttf', uni=True)
        pdf.add_font('Roboto', 'B', f'{font_path}Roboto-Bold.ttf', uni=True)  # Fuente en negrita
        pdf.add_font('Roboto', 'I', f'{font_path}Roboto-Italic.ttf', uni=True)  # Fuente itálica

        # Añadir el título principal
        pdf.set_font('Roboto', 'B', 32)  # Negrita y tamaño 32
        pdf.cell(0, 10, main_title, ln=True, align='C')  # Centrar el título
        pdf.ln(10)  # Espacio después del título

        # Añadir prefacio o introducción
        if preface_text:
            pdf.set_font('Roboto', '', 12)
            pdf.multi_cell(0, 10, preface_text, align='J')
            pdf.ln(10)  # Espacio después del prefacio

        # Añadir contenido de texto
        for title, texto in contenido_texto:
            # Formatear el título del capítulo
            pdf.set_font('Roboto', 'B', 20)  # Negrita y tamaño 24
            pdf.cell(0, 10, title, ln=True, align='C')  # Centrar el título del capítulo
            pdf.ln(10)  # Espacio después del título del capítulo

            # Formatear el texto del capítulo
            pdf.set_font('Roboto', '', 12)  # Fuente normal
            texto = texto.replace("—", "-").replace("“", "\"").replace("”", "\"")
            pdf.multi_cell(0, 10, texto, align='J')  # Justificar el texto
            pdf.ln(5)  # Espacio entre capítulos

        pdf.output(ruta)

def traducir_texto(texto):
    try:
        # Dividir el texto en fragmentos de 1000 caracteres
        fragmentos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]
        texto_traducido = ""
        
        for fragmento in fragmentos:
            texto_traducido += GoogleTranslator(source='auto', target='es').translate(fragmento) + "\n"
        
        return texto_traducido
    except Exception as e:
        print(f"Error al traducir el texto: {e}")
        return None

if __name__ == "__main__":
    ventana = ctk.CTk()
    app = DescargadorTextoApp(ventana)
    ventana.mainloop()
