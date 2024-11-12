import os
import json
from tkinter import messagebox
import customtkinter as ctk

def cargar_historial():
    """Carga el historial desde un archivo JSON."""
    if os.path.exists("Historial/historial.json"):
        with open("Historial/historial.json", "r", encoding="utf-8") as json_file:
            return [json.loads(line) for line in json_file]
    return []

def guardar_historial(nombre, calificacion, comentario):
    """Guarda un nuevo registro en el historial."""
    if not os.path.exists("Historial"):
        os.makedirs("Historial")

    historial = {
        "nombre": nombre,
        "calificacion": calificacion,
        "comentario": comentario
    }

    with open("Historial/historial.json", "a", encoding="utf-8") as json_file:
        json.dump(historial, json_file)
        json_file.write("\n")  # Añadir una nueva línea para cada entrada

def guardar_cambios_historial(index, entry_calificacion, entry_comentario, guardar_button, cargar_historial):
    """Guarda los cambios realizados en el historial y actualiza la interfaz."""
    historial = cargar_historial()
    if 0 <= index < len(historial):
        calificacion = entry_calificacion.get()
        comentario = entry_comentario.get()
        historial[index]["calificacion"] = calificacion
        historial[index]["comentario"] = comentario

        # Guardar el historial actualizado
        with open("Historial/historial.json", "w", encoding="utf-8") as json_file:
            for item in historial:
                json.dump(item, json_file)
                json_file.write("\n")

        messagebox.showinfo("Guardado", "Los cambios han sido guardados exitosamente.")

        # Convertir los entrys en labels
        entry_calificacion.grid_forget()
        entry_comentario.grid_forget()

        label_calificacion = ctk.CTkLabel(entry_calificacion.master, text=calificacion, width=30)
        label_calificacion.grid(row=index, column=1, padx=5, pady=5)

        label_comentario = ctk.CTkLabel(entry_comentario.master, text=comentario, width=60)
        label_comentario.grid(row=index, column=2, padx=5, pady=5)

        # Cambiar el botón a "Editar"
        guardar_button.configure(text="Editar", command=lambda: editar_historial(index, label_calificacion, label_comentario, guardar_button, cargar_historial))

def editar_historial(index, label_calificacion, label_comentario, editar_button, cargar_historial):
    """Permite editar la calificación y el comentario."""
    label_calificacion.grid_forget()
    label_comentario.grid_forget()

    entry_calificacion = ctk.CTkEntry(label_calificacion.master, width=90)
    entry_calificacion.insert(0, label_calificacion.cget("text"))
    entry_calificacion.grid(row=index, column=1, padx=5, pady=5)

    entry_comentario = ctk.CTkEntry(label_comentario.master, width=60)
    entry_comentario.insert(0, label_comentario.cget("text"))
    entry_comentario.grid(row=index, column=2, padx=5, pady=5)

    # Cambiar el botón a "Guardar"
    editar_button.configure(text="Guardar", command=lambda: guardar_cambios_historial(index, entry_calificacion, entry_comentario, editar_button, cargar_historial))
