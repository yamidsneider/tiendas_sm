"""Arma la página de la app de escritorio en un solo texto (opción B en DECISIONES).

index.html trae dos marcas, /*ESTILOS*/ y /*CODIGO*/, que se reemplazan por app.css y app.js. pywebview recibe
el texto completo, así no hace falta un servidor ni un puerto abierto, y la página no carga nada de internet.
Path(__file__) también funciona dentro del .exe: PyInstaller copia la carpeta estatico junto a este módulo.
"""
from pathlib import Path

CARPETA_ESTATICA = Path(__file__).resolve().parent / "estatico"
MARCA_DE_ESTILOS = "/*ESTILOS*/"
MARCA_DE_CODIGO = "/*CODIGO*/"


def armar_pagina(carpeta=CARPETA_ESTATICA):
    def leer(nombre):
        return (carpeta / nombre).read_text(encoding="utf-8")
    return leer("index.html").replace(MARCA_DE_ESTILOS, leer("app.css")).replace(MARCA_DE_CODIGO, leer("app.js"))
