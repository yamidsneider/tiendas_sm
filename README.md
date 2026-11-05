# TIENDAS S.M — Sistema de gestión de inventario, ventas y créditos para tiendas de barrio

MVP académico (Ingeniería de Software I, Universidad de Pamplona). Autor: Yamid Sneider Merchan Castro.

## Tecnología (decisión registrada en la FPI-12)
- Lenguaje: **Python 3** (solo biblioteca estándar, no hay que instalar nada).
- Base de datos: **SQLite** (viene con Python; un solo archivo, sin servidor).
- Tipo de aplicación: **escritorio** con **Tkinter** (viene con Python). Primera versión: el punto de venta.
- Pruebas: `unittest`.
- Dinero: números enteros en pesos colombianos (sin centavos).

## Cómo abrir la aplicación
Desde esta carpeta, con Python 3.12 en Windows:

    python iniciar_tienda.py --datos-de-ejemplo

- `--datos-de-ejemplo` carga productos y clientes **ficticios**, solo si la base está vacía. Sin esa opción se abre con los datos guardados.
- Los datos se guardan en `%LOCALAPPDATA%\TIENDAS_SM\tiendas_sm.db` (la ruta exacta aparece en la consola al abrir).
  **Respaldo manual:** con la aplicación cerrada, copia ese archivo a otra carpeta o memoria USB.
- Atajos: **F2** buscar producto · **Enter** agregar · **F9** cobrar de contado · **F4** vender a crédito · **Supr** quitar · **Esc** cerrar diálogo.

## Cómo correr las pruebas
Desde esta carpeta:

    python -m unittest discover -s tests -v

Resultado esperado: 160 pruebas, `OK`. Las mismas pruebas se ejecutan solas en cada Pull Request (ver `docs/CI.md`);
allí las 5 pruebas de la ventana se saltan porque el servidor no tiene pantalla.

## Estructura
    tiendas_sm/
      dominio.py          Producto, Existencia, Cliente, Venta, DetalleVenta, CuentaPorCobrar
      servicios.py        ServicioDeProductos, ServicioDeClientes, ControlInventario, ControlCredito, ServicioDeVentas
      puertos.py          Contratos de persistencia del núcleo (ADR-04)
      repositorios.py     Repositorios con SQLite (implementan los puertos)
      base_de_datos.py    Conexión y esquema de la base de datos
      validaciones.py     Validaciones compartidas
      presentador.py      Lógica de la pantalla del punto de venta, sin Tkinter (se prueba sin abrir ventanas)
      datos_de_ejemplo.py Datos ficticios para la demo
      aplicacion.py       Arma el sistema (conecta los objetos)
    interfaz_tk/
      ventana_punto_de_venta.py  Ventana Tkinter (solo dibuja y llama al presentador)
    iniciar_tienda.py     Abre la aplicación de escritorio
    tests/
      test_comportamiento.py          Pruebas de flujo completo con SQLite real (escenarios de la FPI-06)
      test_unitarias_dobles.py        Pruebas unitarias aisladas con stubs y mocks (FPI-14)
      test_caja_negra.py              Pruebas de caja negra CN-01 a CN-08, derivadas de los criterios Gherkin (FPI-14)
      test_integracion_incremental.py Integración ascendente por niveles (FPI-14)
      test_defectos_corregidos.py     Regresión de BUG-01, BUG-02, DT-09, TD-01 y TD-14
      test_venta_de_contado.py        Venta de contado (UC-02)
      test_arquitectura.py            El núcleo no importa SQLite (ADR-04)
      test_presentador.py             Punto de venta sin abrir ventanas
      test_iniciar_tienda.py          Ruta de datos y datos de ejemplo
      test_interfaz_tk.py             Pruebas de humo de la ventana (se saltan sin pantalla)
      test_escenarios_calidad.py      Escenarios E-02 (fallos), E-03 (desempeño) y E-05 (trazabilidad)
      test_migracion_esquema.py       Abrir una base vieja sin perder datos (columnas nuevas de ventas)
      test_medir_cobertura.py         TD-05: el medidor de cobertura no falla con líneas None (Python 3.13)
    medir_calidad.py      Funciones largas, números mágicos y código muerto (FPI-12)
    medir_complejidad.py  Complejidad ciclomática V(G) por función (FPI-14)
    medir_cobertura.py    Cobertura de líneas con el módulo trace de Python; con --minimo 90 falla si baja (FPI-14/15)
    demo_en_vivo.py       Demostración narrada del flujo crítico (FPI-16): python demo_en_vivo.py
    calcular_metricas.py  Métricas reales de Git/GitHub para la retrospectiva (FPI-16)
    correr_regresion.py   Selecciona y corre las pruebas de regresión según los archivos que cambiaron (FPI-15)
    .github/workflows/ci.yml  Pipeline de CI (Build, Lint, Test y cobertura) (FPI-15)
    docs/                 CI.md, informes de defecto BUG-01 y BUG-02, BITACORA_IA.md y HOJA_DE_RUTA_IS2.md
    evidencia_fpi12/      Código v1 (antes de refactorizar), resultados de pruebas y métricas antes/después
    evidencia_fpi14/      Caja negra antes y después del arreglo, complejidad ciclomática y cobertura
    evidencia_fpi15/      Defectos reproducidos antes de corregir, resultados después y simulación local del pipeline
    evidencia_fpi24/      TDD de la tarea 3: salida real de las pruebas en los commits rojo, verde y refactor (Guía 8)

## Trazabilidad
Implementa HU-01 a HU-06, CU-01 y CU-02 (RF-01 a RF-09) y el punto de venta de escritorio (tarea 8, TD-03).
Pendiente: medir RNF-01/E-01 con personas, las demás pantallas, lotes y vencimientos (Should Have) y alertas.
CR-01 (usuarios) y CR-02 (proveedores, pedidos, caja) no están aprobadas.

## Uso de IA
El primer borrador del código se generó con apoyo de IA a partir del diseño de la FPI-11. El desarrollador
debe leerlo, entenderlo y poder explicarlo antes de entregarlo (política de uso de IA del proyecto).
