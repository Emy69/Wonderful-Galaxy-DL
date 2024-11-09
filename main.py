import io
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

class DescargadorTextoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Descargador de Texto")
        self.root.geometry("800x600")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Campo de entrada para la URL
        self.label_url = ctk.CTkLabel(root, text="Ingresa la URL a escanear:")
        self.label_url.pack(pady=20)
        self.entry_url = ctk.CTkEntry(root, width=200)
        self.entry_url.pack(pady=10)

        # Campo de entrada para la contraseña
        self.label_password = ctk.CTkLabel(root, text="Ingresa la contraseña:")
        self.label_password.pack(pady=20)
        self.entry_password = ctk.CTkEntry(root, width=200, show='*')
        self.entry_password.pack(pady=10)

        # Cargar datos guardados si existen
        self.cargar_datos()

        # Botón para escanear
        self.boton_scanear = ctk.CTkButton(root, text="Acceder y Escanear", command=self.descargar_texto)
        self.boton_scanear.pack(pady=20)

        # Área de texto para mostrar el resultado
        self.text_area = ctk.CTkTextbox(root, width=500, height=200, state='normal')
        self.text_area.pack(pady=20)
        self.text_area.configure(state='disabled')  # Iniciar deshabilitada

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(root)
        self.progress_bar.pack(pady=20)

        # Etiqueta para mostrar la ruta del PDF
        self.label_pdf_path = ctk.CTkLabel(root, text="")
        self.label_pdf_path.pack(pady=10)

        # Inicializar el log
        self.log_mensajes = []  # Lista para almacenar los mensajes del log

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

    def seleccionar_ruta(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        return ruta

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
        with open("datos.json", "w", encoding="utf-8") as json_file:
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
                # options.add_argument('--headless')  # Comentar esta línea
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
        if os.path.exists("datos.json"):
            with open("datos.json", "r") as json_file:
                datos = json.load(json_file)
                self.entry_url.insert(0, datos.get("url", ""))
                self.entry_password.insert(0, datos.get("password", ""))


if __name__ == "__main__":
    ventana = ctk.CTk()
    app = DescargadorTextoApp(ventana)
    ventana.mainloop()
