"""
SQLAlchemy ORM models — todas las tablas del diagrama ER.
Base compartida por todas las partes del proyecto.
"""

from sqlalchemy import (
    Column, Integer, String, DECIMAL, TIMESTAMP, Text,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(20), nullable=True)
    contrasena = Column(String(255), nullable=False)
    calificacion_promedio = Column(DECIMAL(3, 2), nullable=True, default=0.00)
    fecha_registro = Column(TIMESTAMP, server_default=func.now())

    conductor = relationship("Conductor", back_populates="usuario", uselist=False)
    viajes = relationship("Viaje", back_populates="usuario", foreign_keys="Viaje.id_usuario")


class Conductor(Base):
    __tablename__ = "conductores"

    id_conductor = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    nro_licencia = Column(String(50), unique=True, nullable=False)
    estado = Column(String(20), nullable=True, default="disponible")
    # estados posibles: disponible, ocupado, inactivo
    calificacion_promedio = Column(DECIMAL(3, 2), nullable=True, default=0.00)
    latitud_actual = Column(DECIMAL(10, 7), nullable=True)
    longitud_actual = Column(DECIMAL(10, 7), nullable=True)

    usuario = relationship("Usuario", back_populates="conductor")
    vehiculo = relationship("Vehiculo", back_populates="conductor", uselist=False)
    viajes = relationship("Viaje", back_populates="conductor", foreign_keys="Viaje.id_conductor")


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id_vehiculo = Column(Integer, primary_key=True, autoincrement=True)
    id_conductor = Column(Integer, ForeignKey("conductores.id_conductor"), nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    anio = Column(Integer, nullable=False)
    nro_placa = Column(String(20), unique=True, nullable=False)  # patente
    color = Column(String(30), nullable=True)
    tipo_vehiculo = Column(String(30), nullable=True)
    capacidad_pasajeros = Column(Integer, nullable=True)

    conductor = relationship("Conductor", back_populates="vehiculo")


class Viaje(Base):
    __tablename__ = "viajes"

    id_viaje = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_conductor = Column(Integer, ForeignKey("conductores.id_conductor"), nullable=True)
    latitud_inicio = Column(DECIMAL(10, 7), nullable=False)
    longitud_inicio = Column(DECIMAL(10, 7), nullable=False)
    latitud_destino = Column(DECIMAL(10, 7), nullable=False)
    longitud_destino = Column(DECIMAL(10, 7), nullable=False)
    distancia_km = Column(DECIMAL(8, 2), nullable=True)
    tiempo_minutos = Column(Integer, nullable=True)
    estado = Column(String(20), nullable=False, default="pendiente")
    # estados: pendiente, aceptado, en_curso, finalizado, cancelado
    fecha_hora = Column(TIMESTAMP, server_default=func.now())

    usuario = relationship("Usuario", back_populates="viajes", foreign_keys=[id_usuario])
    conductor = relationship("Conductor", back_populates="viajes", foreign_keys=[id_conductor])
    pago = relationship("Pago", back_populates="viaje", uselist=False)
    resenas = relationship("Resena", back_populates="viaje")


class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, autoincrement=True)
    id_viaje = Column(Integer, ForeignKey("viajes.id_viaje"), unique=True, nullable=False)
    monto_base = Column(DECIMAL(10, 2), nullable=True)
    tarifa_adicional = Column(DECIMAL(10, 2), nullable=True, default=0.00)
    monto_total = Column(DECIMAL(10, 2), nullable=True)
    metodo_pago = Column(String(30), nullable=True)
    # metodos: tarjeta_credito, tarjeta_debito, billetera_virtual, efectivo
    estado_transaccion = Column(String(20), nullable=False, default="pendiente")
    # estados: pendiente, aprobado, rechazado, reembolsado
    fecha_pago = Column(TIMESTAMP, nullable=True)

    viaje = relationship("Viaje", back_populates="pago")


class Resena(Base):
    __tablename__ = "resenas"

    id_resena = Column(Integer, primary_key=True, autoincrement=True)
    id_viaje = Column(Integer, ForeignKey("viajes.id_viaje"), nullable=False)
    id_autor = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_receptor = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    calificacion = Column(Integer, nullable=False)  # 1 a 5
    comentario = Column(Text, nullable=True)
    tipo = Column(String(20), nullable=False)
    # tipo: usuario_a_conductor, conductor_a_usuario
    fecha = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        # Un autor solo puede reseñar una vez por viaje
        UniqueConstraint("id_viaje", "id_autor", name="uq_resena_viaje_autor"),
    )

    viaje = relationship("Viaje", back_populates="resenas")
    autor = relationship("Usuario", foreign_keys=[id_autor])
    receptor = relationship("Usuario", foreign_keys=[id_receptor])
