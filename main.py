import io
import os
import sys
import json
import shutil
import requests
import threading
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk  # Importar ttk para usar Progressbar
import customtkinter as ctk

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import filedialog, messagebox
from PIL import Image as PilImage, ImageTk
from msg import Mensaje  
from bs4 import BeautifulSoup
from googletrans import Translator
from deep_translator import GoogleTranslator

from historial import cargar_historial, guardar_historial, guardar_cambios_historial, editar_historial


class DescargadorTextoApp:
    def __init__(self, root):
        self.root = root
        self.app_version = "V0.0.4"
        self.root.title(f"Wonderful Galaxy DL - {self.app_version}")

        # Ajusta esta ruta para que apunte EXACTAMENTE a tu ejecutable local
        # por ejemplo: "wkhtmltox/bin/wkhtmltopdf.exe"
        self.wkhtmltopdf_path = os.path.abspath("wkhtmltox/bin/wkhtmltopdf.exe")

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
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)

        # Centrar la ventana
        self.root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        # Menú personalizado en la parte superior
        self.menu_bar = ctk.CTkFrame(root)
        self.menu_bar.pack(side='top', fill='x', pady=5)

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

    def load_image(self, image_path):
        """Carga una imagen y la devuelve como un objeto PhotoImage."""
        return ctk.CTkImage(Image.open(image_path), size=(24, 24))

    def create_custom_menubar(self):
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

        self.archivo_menu_frame = None
        self.ayuda_menu_frame = None
        self.donaciones_menu_frame = None

    def toggle_archivo_menu(self):
        if self.archivo_menu_frame and self.archivo_menu_frame.winfo_exists():
            self.archivo_menu_frame.destroy()
        else:
            self.close_all_menus()
            self.archivo_menu_frame = self.create_menu_frame([
                ("Configuraciones", self.open_settings),
                ("separator", None),
                ("Salir", self.salir_aplicacion),
            ], x=0)

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
        menu_frame = ctk.CTkFrame(self.root, corner_radius=5, fg_color="gray25", border_color="black", border_width=1)
        menu_frame.place(x=x, y=30)
        
        for option in options:
            if option[0] == "separator":
                separator = ctk.CTkFrame(menu_frame, height=1, fg_color="gray50")
                separator.pack(fill="x", padx=5, pady=5)
            elif option[1] is None:
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
        self.log_mensajes.append(mensaje)
        self.text_area.configure(state='normal')
        self.text_area.delete(1.0, ctk.END)
        self.text_area.insert(ctk.END, "\n".join(self.log_mensajes))
        self.text_area.configure(state='disabled')

    def guardar_datos(self, url, password):
        if not os.path.exists("Guardado"):
            os.makedirs("Guardado")

        datos = {"url": url, "password": password}
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

        self.guardar_datos(url, password)

        self.progress_bar.start()
        self.progress_bar.set(0)

        def tarea():
            try:
                self.mostrar_mensaje("Iniciando el navegador y accediendo a la página...")

                options = webdriver.ChromeOptions()
                options.add_argument("--disable-javascript")
                options.add_argument('--headless')
                driver = webdriver.Chrome(options=options)

                driver.get(url)

                password_field = driver.find_element(By.NAME, "password_protected_pwd")
                password_field.send_keys(password)
                password_field.send_keys(Keys.RETURN)

                self.mostrar_mensaje("Contraseña ingresada, esperando respuesta...")

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'entry-content-wrap'))
                )

                contenedor = driver.find_element(By.CLASS_NAME, 'entry-content-wrap')
                contenido_texto = []
                for elemento in contenedor.find_elements(By.XPATH, './/p | .//strong | .//em'):
                    texto = elemento.text.strip()
                    if texto and texto not in contenido_texto:
                        contenido_texto.append(texto)

                # Buscar la primera imagen
                imagenes = []
                for figura in contenedor.find_elements(By.CLASS_NAME, 'swiper-slide-inner'):
                    try:
                        imagen = figura.find_element(By.TAG_NAME, 'img')
                        src = imagen.get_attribute("src")
                        img_data = requests.get(src)
                        if 'image' in img_data.headers['Content-Type']:
                            ext = img_data.headers['Content-Type'].split('/')[1]
                            img_path = f"temp_{len(imagenes)}.{ext}"
                            with open(img_path, "wb") as img_file:
                                img_file.write(img_data.content)
                            imagenes.append(img_path)
                            break
                    except Exception as e:
                        self.mostrar_mensaje(f"Error al procesar la imagen: {str(e)}")

                driver.quit()

                self.mostrar_mensaje("Extrayendo contenido y creando el PDF...")
                self.text_area.configure(state='normal')
                self.text_area.delete(1.0, ctk.END)
                self.text_area.insert(ctk.END, "\n".join(contenido_texto))
                self.text_area.configure(state='disabled')

                ruta_pdf = self.seleccionar_ruta()
                if ruta_pdf:
                    self.crear_pdf_wkhtmltopdf(contenido_texto, imagenes, ruta_pdf)
                    self.mostrar_mensaje(f"PDF creado: {ruta_pdf}")
                    self.label_pdf_path.configure(text=f"PDF guardado en: {ruta_pdf}")
                    self.label_pdf_path.bind("<Button-1>", lambda e: os.startfile(ruta_pdf))

                    nombre_pdf = os.path.basename(ruta_pdf)
                    self.guardar_historial(nombre_pdf, "", "")

                    messagebox.showinfo("Descarga Completa", f"El PDF ha sido guardado exitosamente en: {ruta_pdf}")

                for img in imagenes:
                    if os.path.exists(img):
                        os.remove(img)

            except Exception as e:
                self.mostrar_mensaje(f"Error en la tarea: {str(e)}")
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
            finally:
                self.progress_bar.stop()

        hilo = threading.Thread(target=tarea)
        hilo.start()

    def cargar_datos(self):
        if os.path.exists("Guardado/datos.json"):
            with open("Guardado/datos.json", "r") as json_file:
                datos = json.load(json_file)
                self.entry_url.insert(0, datos.get("url", ""))
                self.entry_password.insert(0, datos.get("password", ""))

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Configuraciones")
        
        width = 400
        height = 300
        settings_window.geometry(f"{width}x{height}")
        self.center_window(settings_window)

        self.mostrar_mensaje("Abrir ventana de configuraciones...")

    def salir_aplicacion(self):
        self.root.quit()

    def show_contributors_window(self):
        contributors_window = tk.Toplevel(self.root)
        contributors_window.title("Acerca de mí")
        
        width = 400
        height = 400
        contributors_window.geometry(f"{width}x{height}")
        self.center_window(contributors_window)

        self.show_personal_info(contributors_window)

    def show_personal_info(self, parent_frame):
        try:
            nombre = "Emy"
            bio = "Holis."
            avatar_url = "https://avatars.githubusercontent.com/u/142945265?v=4"
            perfil_url = "https://github.com/emy69"

            frame = ctk.CTkFrame(parent_frame)
            frame.pack(pady=20)

            avatar_image = PilImage.open(requests.get(avatar_url, stream=True).raw)
            avatar_image = avatar_image.resize((100, 100), PilImage.Resampling.LANCZOS)
            avatar_photo = ImageTk.PhotoImage(avatar_image)

            avatar_label = tk.Label(frame, image=avatar_photo)
            avatar_label.image = avatar_photo
            avatar_label.pack(side="top", pady=10)

            name_label = ctk.CTkLabel(frame, text=nombre, font=("Helvetica", 16))
            name_label.pack(side="top", pady=5)

            bio_label = ctk.CTkLabel(frame, text=bio, font=("Helvetica", 12))
            bio_label.pack(side="top", pady=5)

            link_button = ctk.CTkButton(
                frame,
                text="Ver Perfil en GitHub",
                command=lambda: webbrowser.open(perfil_url)
            )
            link_button.pack(side="top", pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar la información personal.\nError: {e}")

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        window.geometry(f"{width}x{height}+{x}+{y}")

    def seleccionar_ruta(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Guardar PDF como"
        )
        return ruta

    def crear_pdf_wkhtmltopdf(self, contenido_texto, imagenes, ruta_final):
        html_temporal = "temp_document.html"
        self.generar_html_para_pdf(contenido_texto, imagenes, html_temporal)

        # Usar la ruta absoluta que definimos en __init__
        comando = [self.wkhtmltopdf_path, "--encoding", "UTF-8", html_temporal, ruta_final]

        try:
            subprocess.run(comando, check=True)
        except Exception as e:
            self.mostrar_mensaje(f"Error al generar PDF con wkhtmltopdf: {e}")
        finally:
            if os.path.exists(html_temporal):
                os.remove(html_temporal)

    def generar_html_para_pdf(self, contenido_texto, imagenes, ruta_html):
        estilo = """
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1, h2, h3 {
                text-align: center;
            }
            p {
                text-align: justify;
            }
            img {
                display: block;
                margin: 10px auto;
                max-width: 80%%;
                height: auto;
            }
        </style>
        """

        html_content = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{estilo}</head><body>"
        html_content += "<h1>Documento Generado</h1>"

        # Agregar el texto
        for texto in contenido_texto:
            texto_html = (
                texto.replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;")
            )
            html_content += f"<p>{texto_html}</p>"

        # Insertar la primera imagen (si existe)
        for path_img in imagenes:
            if os.path.exists(path_img):
                html_content += f"<img src='{path_img}' alt='Imagen' />"

        html_content += "</body></html>"

        with open(ruta_html, "w", encoding="utf-8") as f:
            f.write(html_content)

    def show_historial_window(self):
        historial_window = tk.Toplevel(self.root)
        historial_window.title("Historial de Descargas")

        width = 800
        height = 400
        historial_window.geometry(f"{width}x{height}")
        self.center_window(historial_window)

        frame = ctk.CTkFrame(historial_window)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        historial = cargar_historial()
        for idx, item in enumerate(historial):
            label_nombre = ctk.CTkLabel(frame, text=f"PDF: {item['nombre']}", font=("Helvetica", 12))
            label_nombre.grid(row=idx, column=0, padx=5, pady=5)

            entry_calificacion = ctk.CTkEntry(frame, width=100)
            entry_calificacion.insert(0, item.get("calificacion", ""))
            entry_calificacion.grid(row=idx, column=1, padx=5, pady=5)

            entry_comentario = ctk.CTkEntry(frame, width=100)
            entry_comentario.insert(0, item.get("comentario", ""))
            entry_comentario.grid(row=idx, column=2, padx=5, pady=5)

            guardar_button = ctk.CTkButton(
                frame, 
                text="Guardar", 
                command=lambda i=idx: guardar_cambios_historial(
                    i, 
                    entry_calificacion, 
                    entry_comentario, 
                    guardar_button, 
                    cargar_historial
                )
            )
            guardar_button.grid(row=idx, column=3, padx=5, pady=5)

    def procesar_url(self):
        url = self.entry_url.get()
        if not url:
            messagebox.showerror("Error", "Por favor, ingresa una URL.")
            return

        if "archiveofourown.org" in url:
            self.descargar_y_traducir_html(url)
        else:
            self.descargar_texto()

    def descargar_y_traducir_html(self, url):
        threading.Thread(target=self._descargar_y_traducir_html, args=(url,)).start()

    def _descargar_y_traducir_html(self, url):
        try:
            self.mostrar_mensaje("Iniciando la descarga de la página...")

            response = requests.get(url)
            response.raise_for_status()
            self.mostrar_mensaje("Página descargada exitosamente.")

            soup = BeautifulSoup(response.content, 'html.parser')
            workskin_div = soup.find('div', id='workskin')

            if not workskin_div:
                messagebox.showerror("Error", "No se encontró el div con id 'workskin'.")
                return

            title_element = workskin_div.find('h2', class_='title heading')
            main_title = title_element.get_text(strip=True) if title_element else "Sin título"

            preface_div = workskin_div.find('div', class_='preface group')
            preface_text = ""
            if preface_div:
                preface_text = preface_div.get_text(separator="\n", strip=True)
                preface_text = traducir_texto(preface_text)

            chapters_div = workskin_div.find('div', id='chapters')
            translated_texts = []
            if chapters_div:
                chapters = chapters_div.find_all('div', class_='chapter')
                for chapter in chapters:
                    chapter_title_element = chapter.find('h2', class_='title heading')
                    chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Sin título"
                    chapter_text = chapter.get_text(separator="\n", strip=True)

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

            ruta = self.seleccionar_ruta()
            if ruta:
                self.crear_pdf_traducido_wkhtmltopdf(main_title, preface_text, translated_texts, ruta)

        except requests.exceptions.RequestException as e:
            self.mostrar_mensaje(f"Error al descargar la página: {e}")
        except Exception as e:
            self.mostrar_mensaje(f"Error al procesar la página: {e}")

    def crear_pdf_traducido_wkhtmltopdf(self, main_title, preface_text, contenido_texto, ruta_pdf):
        html_temp = "temp_traducido.html"
        self.generar_html_traducido(main_title, preface_text, contenido_texto, html_temp)

        comando = [self.wkhtmltopdf_path, "--encoding", "UTF-8", html_temp, ruta_pdf]
        try:
            subprocess.run(comando, check=True)
            self.mostrar_mensaje(f"PDF creado con la traducción en: {ruta_pdf}")
        except Exception as e:
            self.mostrar_mensaje(f"Error al generar PDF traducido con wkhtmltopdf: {e}")
        finally:
            if os.path.exists(html_temp):
                os.remove(html_temp)

    def generar_html_traducido(self, main_title, preface_text, contenido_texto, html_path):
        estilo = """
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h1, h2 {
                text-align: center;
            }
            p {
                text-align: justify;
                line-height: 1.6;
            }
        </style>
        """
        html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{estilo}</head><body>"

        # Título principal
        html += f"<h1>{self.escapar_html(main_title)}</h1>"

        # Prefacio
        if preface_text:
            html += f"<h2>Prefacio</h2>"
            html += f"<p>{self.escapar_html(preface_text)}</p>"

        # Capítulos
        for chapter_title, chapter_text in contenido_texto:
            html += f"<h2>{self.escapar_html(chapter_title)}</h2>"
            html += f"<p>{self.escapar_html(chapter_text)}</p>"

        html += "</body></html>"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    def escapar_html(self, texto):
        return (
            texto.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace("\"", "&quot;")
                 .replace("'", "&#39;")
        )


def traducir_texto(texto):
    try:
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
