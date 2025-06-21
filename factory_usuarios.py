from usuario import Usuario
from usuario_pendiente import UsuarioPendiente

class FabricaUsuario:
    @staticmethod
    def crear_postulante(**kwargs):
        requeridos = ["nombre", "email", "contrasena", "img"]
        for campo in requeridos:
            if campo not in kwargs:
                raise ValueError(f"Falta el parámetro obligatorio: {campo}")
    
        return UsuarioPendiente(
            id=None,
            nombre=kwargs["nombre"],
            email=kwargs["email"],
            contrasena=kwargs["contrasena"],
            img=kwargs["img"],
            cargo=kwargs.get("cargo", "colaborador")
        )


    @staticmethod
    def promover_desde_postulante(postulante):
        return Usuario(
            id=None,
            nombre=postulante.nombre,
            email=postulante.email,
            contrasena=postulante.contrasena,
            img=postulante.img,
            cargo=postulante.cargo
        )
