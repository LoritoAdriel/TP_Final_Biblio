class BaseUsuario:
    def __init__(self, id, nombre, email, contrasena, img):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.contrasena = contrasena
        self.img = img

    def cambiar_contrasena(self, nueva_contrasena):
        self.contrasena = nueva_contrasena

    def cambiar_imagen(self, nueva_ruta):
        self.img = nueva_ruta

    def mostrar_info(self):
        return f"{self.nombre} ({self.email})"