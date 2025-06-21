import sqlite3

class Libro:
    def __init__(self, id, titulo, autor, descarga, portada, es_inicio=0):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.descarga = descarga
        self.portada = portada
        self.es_inicio = es_inicio

    @staticmethod
    def obtener_todos():
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM libros")
            filas = cursor.fetchall()
            return [Libro(*fila) for fila in filas]
    
    @staticmethod
    def obtener_por_id(id_libro):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM libros WHERE id=?", (id_libro,))
            fila = cursor.fetchone()
            return Libro(*fila) if fila else None
        
    @staticmethod
    def obtener_por_ids(lista_ids):
        if not lista_ids:
            return []
        placeholders = ','.join(['?'] * len(lista_ids))
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM libros WHERE id IN ({placeholders})", lista_ids)
            filas = cursor.fetchall()
            return [Libro(*fila) for fila in filas]
        
    @staticmethod
    def obtener_por_titulo(titulo):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM libros WHERE LOWER(titulo) = ?", (titulo.lower(),))
            fila = cursor.fetchone()
            return Libro(*fila) if fila else None
    
    @staticmethod
    def buscar_por_titulo_o_autor(consulta):
        consulta = f"%{consulta.lower()}%"
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM libros
                WHERE LOWER(titulo) LIKE ? OR LOWER(autor) LIKE ?
            """, (consulta, consulta))
            filas = cursor.fetchall()
            return [Libro(*fila) for fila in filas]

    def guardar(self):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO libros (titulo, autor, descarga, portada)
                VALUES (?, ?, ?, ?)
            """, (self.titulo, self.autor, self.descarga, self.portada))
            conn.commit()
            self.id = cursor.lastrowid
            
    def actualizar(self):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE libros
                SET titulo = ?, autor = ?, descarga = ?, portada = ?
                WHERE id = ?
            """, (self.titulo, self.autor, self.descarga, self.portada, self.id))
            conn.commit()
            
    def eliminar(self):
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM libros WHERE id = ?", (self.id,))
            conn.commit()

