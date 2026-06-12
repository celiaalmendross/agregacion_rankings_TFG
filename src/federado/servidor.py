"""
Rol de servidor en la simulación federada del OBOP.

El servidor recibe únicamente mensajes agregados de los clientes:

    {cliente_id, m_cliente, C_i_ruido, M_i}

Con esa información construye la matriz federada, resuelve el OBOP y devuelve
el bucket order federado. El servidor no necesita conocer los rankings locales,
las matrices C_i originales ni los bucket orders locales B_i.
"""

from data.preflib_to_C import validar_C
from federado.agregacion_federada import agregar_matrices_clientes


class ServidorFederado:
    """
    Servidor de la simulación federada.
    """

    def __init__(self):
        self.mensajes_clientes = []
        self.C_federada = None
        self.obj_federado = None
        self.buckets_federado = None

    def recibir_mensajes_clientes(self, mensajes_clientes):
        """
        Recibe mensaje de los clientes, cada mensaje debe contener C_i_ruido y M_i    
        """
        if not mensajes_clientes:
            raise ValueError("Debe recibirse al menos un mensaje.")

        for mensaje in mensajes_clientes:
            if "C_i_ruido" not in mensaje or "M_i" not in mensaje:
                raise ValueError("Cada mensaje debe contener C_i_ruido y M_i.")

        self.mensajes_clientes = list(mensajes_clientes)

        # Reiniciar resultados anteriores
        self.C_federada = None
        self.obj_federado = None 
        self.buckets_federado = None

    def agregar_matrices(self):
        """
        Construye la matriz federada usando M_i como peso por par.
        """    
        if not self.mensajes_clientes:
            raise RuntimeError("No hay mensajes para agregar.")

        matrices = [mensaje["C_i_ruido"] for mensaje in self.mensajes_clientes]
        matrices_M = [mensaje["M_i"] for mensaje in self.mensajes_clientes]

        self.C_federada = agregar_matrices_clientes(
            matrices_clientes=matrices,
            matrices_M=matrices_M,
        )

        self.C_federada = validar_C(self.C_federada)
        return self.C_federada

    def resolver_bucket_order_federado(self, resolver_obop_completo):
        if self.C_federada is None:
            raise RuntimeError("Primero debe construirse la matriz federada.")

        self.obj_federado, self.buckets_federado = resolver_obop_completo(
            self.C_federada
        )

        return self.obj_federado, self.buckets_federado

    def obtener_bucket_order_para_clientes(self):
        if self.buckets_federado is None:
            raise RuntimeError("Primero debe resolverse el OBOP federado.")

        return self.buckets_federado
