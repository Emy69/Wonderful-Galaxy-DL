import customtkinter as ctk

class Mensaje:
    def __init__(self):
        self.ventana_mensaje = ctk.CTkToplevel()
        self.ventana_mensaje.title("Acerca de la Aplicación")
        self.ventana_mensaje.geometry("800x400")
        
        # Configurar la ventana para que esté siempre al frente
        self.ventana_mensaje.overrideredirect(True)  # Elimina los botones de la barra de título
        self.ventana_mensaje.attributes('-topmost', True)

        # Centrar la ventana
        self.center_window(self.ventana_mensaje)

        # Crear un frame para contener el contenido de la ventana
        frame_contenido = ctk.CTkFrame(self.ventana_mensaje)
        frame_contenido.pack(pady=20, padx=20, fill='both', expand=True)

        # Crear el contenido de la ventana dentro del frame
        mensaje = (
            "Bienvenido a Wonderful Galaxy DL!\n\n"
            "Esta aplicación te permite escanear y descargar contenido de texto en la web https://wgalaxy.xyz/\n"
            "La aplicación es de uso libre y gratuito.\n"
            "Agradeceríamos cualquier donación para seguir mejorando la aplicación.\n"
            "Aun la aplicación es muy básica, pronto habrán más funciones y mejoras.\n\n"
            "Esperamos que disfrutes usando esta aplicación."
            "\n\n"
            "Nota: Esta ventana se usara para mostrar mejoras futuras y agradecimientos."
        )
        
        label_mensaje = ctk.CTkLabel(frame_contenido, text=mensaje, font=("Helvetica", 12))
        label_mensaje.pack(pady=20, padx=20)

        # Botón para cerrar la ventana dentro del frame
        boton_aceptar = ctk.CTkButton(frame_contenido, text="Aceptar", command=self.cerrar_ventana)
        boton_aceptar.pack(pady=10)

    def cerrar_ventana(self):
        """Cierra la ventana de mensaje."""
        self.ventana_mensaje.destroy()

    def center_window(self, window):
        """Centrar la ventana en la pantalla."""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
