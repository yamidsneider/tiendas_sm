# TIENDAS S.M — Sistema de gestión de inventario, ventas y créditos para tiendas de barrio

MVP académico (Ingeniería de Software I, Universidad de Pamplona). Autor: Yamid Sneider Merchan Castro.

## Tecnología (decisión registrada en la FPI-12)
- Lenguaje: **Python 3** (solo biblioteca estándar, no hay que instalar nada).
- Base de datos: **SQLite** (viene con Python; un solo archivo, sin servidor).
- Tipo de aplicación: **escritorio**. La interfaz gráfica será con **Tkinter** (también viene con Python); todavía no está construida.
- Pruebas: `unittest`.
- Dinero: números enteros en pesos colombianos (sin centavos).

## Cómo correr las pruebas
Desde esta carpeta:

    python -m unittest discover -s tests -v

Resultado esperado: 77 pruebas, `OK`. Las mismas pruebas se ejecutan solas en cada Pull Request (ver `docs/CI.md`).

## Estructura
    tiendas_sm/
      dominio.py          Producto, Existencia, Cliente, Venta, DetalleVenta, CuentaPorCobrar
      servicios.py        ServicioDeProductos, ServicioDeClientes, ControlInventario, ControlCredito, ServicioDeVentas
      repositorios.py     RepositorioDeVentas (abstracción) y los repositorios con SQLite
      base_de_datos.py    Conexión y esquema de la base de datos
      validaciones.py     Validación compartida (cantidad mayor a cero)
      aplicacion.py       Arma el sistema (conecta los objetos)
    tests/
      test_comportamiento.py          Pruebas de flujo completo con SQLite real (escenarios de la FPI-06)
      test_unitarias_dobles.py        Pruebas unitarias aisladas con stubs y mocks (FPI-14)
      test_caja_negra.py              Pruebas de caja negra CN-01 a CN-08, derivadas de los criterios Gherkin (FPI-14)
      test_integracion_incremental.py Integración ascendente por niveles (FPI-14)
      test_defectos_corregidos.py     Regresión de los defectos BUG-01 y BUG-02 (FPI-15)
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
Implementa HU-01 a HU-04, HU-06 y CU-01 (RF-01 a RF-09). Diseño: FPI-10 y FPI-11.
Pendiente: interfaz Tkinter, lotes y vencimientos (Should Have), alertas, y las entidades de CR-02.

## Uso de IA
El primer borrador del código se generó con apoyo de IA a partir del diseño de la FPI-11. El desarrollador
debe leerlo, entenderlo y poder explicarlo antes de entregarlo (política de uso de IA del proyecto).
