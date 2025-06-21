import sqlite3
from base_usuario import BaseUsuario

class Usuario(BaseUsuario):
    def __init__(self, id, nombre, email, contrasena, img, cargo):
        super().__init__(id, nombre, email, contrasena, img)
        self.cargo = cargo

    @staticmethod
    def obtener_todos():
        with sqlite3.connect("biblio.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios")
            filas = cursor.fetchall()
            return [
                Usuario(
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
    def obtener_por_email(email):
        with sqlite3.connect("biblio.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
            fila = cursor.fetchone()
            if fila:
                return Usuario(
                    id=fila["id"],
                    nombre=fila["nombre"],
                    email=fila["email"],
                    contrasena=fila["contrasena"],
                    img=fila["img"],
                    cargo=fila["cargo"]
                )
            return None
    
    @staticmethod
    def obtener_por_id(id_usuario):
        with sqlite3.connect("biblio.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id_usuario,))
            fila = cursor.fetchone()
            if fila:
                return Usuario(
                    id=fila["id"],
                    nombre=fila["nombre"],
                    email=fila["email"],
                    contrasena=fila["contrasena"],
                    img=fila["img"],
                    cargo=fila["cargo"]
                )
            return None
        
    @staticmethod
    def cambiar_cargo(email, nuevo_cargo):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios
                SET cargo = ?
                WHERE email = ?
            """, (nuevo_cargo, email))
            conn.commit()
            
    @staticmethod
    def eliminar_por_id(id_usuario):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
            conn.commit()

    def guardar(self):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (img, nombre, email, contrasena, cargo)
                VALUES (?, ?, ?, ?, ?)
            """, (self.img, self.nombre, self.email, self.contrasena, self.cargo))
            conn.commit()
            self.id = cursor.lastrowid
            
    def modificar(self, nombre, email, contrasena, img):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios
                SET nombre = ?, email = ?, contrasena = ?, img = ?
                WHERE id = ?
            """, (nombre, email, contrasena, img, self.id))
            conn.commit()
