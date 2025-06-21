import sqlite3
from base_usuario import BaseUsuario

class UsuarioPendiente(BaseUsuario):
    def __init__(self, id, nombre, email, contrasena, img, cargo='colaborador'):
        super().__init__(id, nombre, email, contrasena, img)
        self.cargo = cargo

    @staticmethod
    def obtener_todos():
        with sqlite3.connect("biblio.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios_pendientes")
            filas = cursor.fetchall()
            return [
                UsuarioPendiente(
                    id=fila["id"],
                    nombre=fila["nombre"],
                    email=fila["email"],
                    contrasena=fila["contrasena"],
                    img=fila["img"],
                    cargo=fila["cargo"]
                )
                for fila in filas
            ]

    @staticmethod
    def eliminar_por_id(id_usuario):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios_pendientes WHERE id=?", (id_usuario,))
            conn.commit()
            
    def guardar(self):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios_pendientes (img, nombre, email, contrasena, cargo)
                VALUES (?, ?, ?, ?, ?)
            """, (self.img, self.nombre, self.email, self.contrasena, self.cargo))
            conn.commit()
            self.id = cursor.lastrowid
