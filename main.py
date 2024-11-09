import io
import subprocess
import sys
import zipfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import customtkinter as ctk
import threading
from fpdf import FPDF
from tkinter import filedialog, messagebox
import os
import requests
import json
from PIL import Image
import webbrowser
import tkinter as tk
from tkinter import messagebox
from PIL import Image as PilImage, ImageTk

class ActualizadorApp:
    def __init__(self, app_version):
        self.app_version = app_version
        self.repo_url = "https://api.github.com/repos/Emy69/Scans/releases/latest"  # Reemplaza con la URL de tu repositorio
        self.download_url = None

    def verificar_actualizacion(self):
        """Verifica si existe una actualización disponible en GitHub."""
        try:
            response = requests.get(self.repo_url)
            data = response.json()

            latest_version = data["tag_name"]  # Última versión disponible
            if latest_version > self.app_version:
                self.download_url = data["assets"][0]["browser_download_url"]
                return True
            return False
        except Exception as e:
            print(f"Error al verificar actualización: {e}")
            return False

    def descargar_y_actualizar(self):
        """Descarga la actualización, la descomprime y reinicia la aplicación."""
        try:
            if not self.download_url:
                raise ValueError("No hay URL de descarga disponible.")

            response = requests.get(self.download_url)
            if response.status_code == 200:
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                zip_file.extractall("update_folder")  # Extrae los archivos en una carpeta temporal
                print("Actualización descargada y descomprimida.")
                
                # Aquí debes reemplazar con la lógica para actualizar tu app
                # (esto dependerá de cómo se haya organizado el código y cómo se construye el archivo ejecutable)
                self.reiniciar_aplicacion()
            else:
                print(f"Error al descargar la actualización: {response.status_code}")
        except Exception as e:
            print(f"Error al descargar o descomprimir la actualización: {e}")

    def reiniciar_aplicacion(self):
        """Reinicia la aplicación después de actualizar."""
        print("Reiniciando la aplicación...")
        subprocess.Popen([sys.executable] + sys.argv)  # Reinicia la aplicación
        os._exit(0)  # Cierra la aplicación actual


class DescargadorTextoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Descargador de Texto")

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
        self.menu_bar.pack(side='top', fill='x')

        # Llamar al verificador de actualizaciones
        self.actualizador = ActualizadorApp(app_version="0.0.1")  # Tu versión actual
        self.verificar_actualizacion()

        self.create_custom_menubar()

        # Crear un frame para contener todos los elementos
        self.frame = ctk.CTkFrame(root)
        self.frame.pack(pady=20, padx=20, fill='both', expand=True)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Campo de entrada para la URL
        self.label_url = ctk.CTkLabel(self.frame, text="Ingresa la URL a escanear:")
        self.label_url.pack(pady=20)
        self.entry_url = ctk.CTkEntry(self.frame, width=200)
        self.entry_url.pack(pady=10)

        # Campo de entrada para la contraseña
        self.label_password = ctk.CTkLabel(self.frame, text="Ingresa la contraseña:")
        self.label_password.pack(pady=20)
        self.entry_password = ctk.CTkEntry(self.frame, width=200, show='*')
        self.entry_password.pack(pady=10)

        # Cargar datos guardados si existen
        self.cargar_datos()

        # Botón para escanear
        self.boton_scanear = ctk.CTkButton(self.frame, text="Acceder y Escanear", command=self.descargar_texto)
        self.boton_scanear.pack(pady=20)

        # Área de texto para mostrar el resultado
        self.text_area = ctk.CTkTextbox(self.frame, width=500, height=200, state='normal')
        self.text_area.pack(pady=20)
        self.text_area.configure(state='disabled')  # Iniciar deshabilitada

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(self.frame)
        self.progress_bar.pack(pady=20)

        # Etiqueta para mostrar la ruta del PDF
        self.label_pdf_path = ctk.CTkLabel(self.frame, text="")
        self.label_pdf_path.pack(pady=10)

        # Inicializar el log
        self.log_mensajes = []  # Lista para almacenar los mensajes del log

    def verificar_actualizacion(self):
        """Verifica si hay una actualización disponible y la descarga si es necesario."""
        def tarea():
            if self.actualizador.verificar_actualizacion():
                respuesta = messagebox.askyesno("Actualización disponible", "¿Hay una nueva actualización disponible. ¿Quieres actualizar ahora?")
                if respuesta:
                    self.actualizador.descargar_y_actualizar()
            else:
                print("Ya tienes la última versión.")

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

                # Verificar si hubo un error de contraseña
                try:
                    error_login = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "login_error"))
                    )
                    self.mostrar_mensaje("Contraseña incorrecta. Por favor, inténtalo de nuevo.")
                    driver.quit()
                    return
                except Exception as e:
                    self.mostrar_mensaje("Error al verificar la contraseña: No se encontró el mensaje de error.")

                # Encontrar y extraer el contenido en etiquetas <strong> y <p>
                contenedor = driver.find_element(By.CLASS_NAME, 'entry-content-wrap')
                contenido_texto = []
                for elemento in contenedor.find_elements(By.XPATH, './/strong | .//p'):
                    contenido_texto.append(elemento.text)

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

        # Establecer fuente a DejaVuSans (soporta Unicode)
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)  # Usar la fuente DejaVuSans

        # Añadir contenido de texto
        for texto in contenido_texto:
            pdf.multi_cell(0, 10, texto)

        # Añadir imágenes
        for imagen in imagenes:
            pdf.add_page()
            pdf.image(imagen, x=10, y=10, w=100)  # Ajustar según sea necesario

        pdf.output(ruta)

if __name__ == "__main__":
    ventana = ctk.CTk()
    app = DescargadorTextoApp(ventana)
    ventana.mainloop()
