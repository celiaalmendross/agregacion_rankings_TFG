"""
Rol de cliente en la simulación federada del OBOP.

La clase ClienteFederado separa explícitamente las operaciones que, en un
despliegue federado real, ocurrirían dentro de cada cliente:

- construir la matriz local C_i a partir de sus rankings;
- construir la matriz de soporte M_i;
- resolver opcionalmente el OBOP local para evaluación experimental;
- introducir ruido localmente C_i para obtener C_i_ruido;
- enviar al servidor solo C_i_ruido y M_i;
- recibir el bucket order federado y calcular métricas locales.
"""

from federado.agregacion_federada import (
    construir_W_M_desde_rankings,
    construir_C_desde_W_M,
    introducir_ruido_matriz_observada,
)
from metricas.metricas_federada import calcular_metricas_cliente_federado


class ClienteFederado:
    """
    Cliente de la simulación federada
    """

    def __init__(self, cliente_id, rankings, num_alternativas):
        self.cliente_id = cliente_id
        self.rankings = rankings
        self.num_alternativas = num_alternativas

        self.m_cliente = len(rankings)

        self.W_i = None
        self.M_i = None
        self.C_i = None

        self.C_i_ruido = None

        self.obj_local = None
        self.buckets_local = None

    def construir_informacion_local(self):
        self.W_i, self.M_i = construir_W_M_desde_rankings(
            rankings=self.rankings,
            num_alternativas=self.num_alternativas,
        )
        self.C_i = construir_C_desde_W_M(self.W_i, self.M_i)

        # Reiniciamos los resultados derivados si se reconstruye la información local.
        self.C_i_ruido = None
        self.obj_local = None
        self.buckets_local = None

    def resolver_bucket_order_local(self, resolver_obop_ponderado_completo):
        if self.C_i is None or self.M_i is None:
            raise RuntimeError("Antes hay que construir C_i y M_i.")
        P_i = (self.M_i > 0).astype(float)
        self.obj_local, self.buckets_local = (
            resolver_obop_ponderado_completo(
                self.C_i,
                pesos=P_i,
            )
        )

    def introducir_ruido_matriz_local(self, b, tecnica, rng):
        if self.C_i is None or self.M_i is None:
            raise RuntimeError("Antes hay que construir C_i y M_i.")

        self.C_i_ruido = introducir_ruido_matriz_observada(
            C=self.C_i,
            M=self.M_i,
            b=b,
            tecnica=tecnica,
            rng=rng,
        )

    def crear_mensaje_para_servidor(self):
        """
        Crea el mensaje que el cliente envía al servidor.
        """
        if self.C_i_ruido is None:
            raise RuntimeError("Antes hay que introducir ruido en C_i.")

        return {
            "cliente_id": self.cliente_id,
            "m_cliente": self.m_cliente,
            "C_i_ruido": self.C_i_ruido,
            "M_i": self.M_i.copy(),
        }

    def evaluar_bucket_order_federado(self, buckets_federado):
        if self.C_i is None or self.C_i_ruido is None:
            raise RuntimeError("Falta información local del cliente.")

        if self.buckets_local is None:
            raise RuntimeError("Primero debe resolverse el bucket order local.")

        P_i = (self.M_i > 0).astype(float)
        return calcular_metricas_cliente_federado(
            C_i=self.C_i,
            P_i=P_i,
            C_i_ruido=self.C_i_ruido,
            buckets_federado=buckets_federado,
            obj_local=self.obj_local,
        )
