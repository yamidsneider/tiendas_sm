def exigir_mayor_a_cero(valor):
    if valor <= 0:
        raise ValueError("La cantidad debe ser mayor a cero")


def exigir_no_negativo(valor, mensaje):
    if valor < 0:
        raise ValueError(mensaje)


def exigir_texto_obligatorio(texto, mensaje):
    if texto is None or texto.strip() == "":
        raise ValueError(mensaje)
