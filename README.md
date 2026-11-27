# TIENDAS S.M — Sistema de gestión de inventario, ventas y créditos para tiendas de barrio

MVP académico (Ingeniería de Software I, Universidad de Pamplona). Autor: Yamid Sneider Merchan Castro.

## Tecnología (decisión registrada en la FPI-12)
- Lenguaje: **Python 3**. El núcleo y las pruebas usan solo la biblioteca estándar.
- Base de datos: **SQLite** (viene con Python; un solo archivo, sin servidor).
- Tipo de aplicación: **escritorio**, con la visual del borrador HTML del autor (opción B en `docs/contexto/DECISIONES.md`):
  ventana nativa de Windows con **pywebview** y archivo **TIENDAS_SM.exe** armado con **PyInstaller**. Secciones: Punto de venta,
  Ventas, Productos, Existencias, Clientes, Créditos y abonos, y para el jefe Reportes y Usuarios.
- Ingreso con usuario y clave (fase 2): la primera vez se crea la cuenta del jefe; después el jefe crea a los empleados.
  La versión anterior en Tkinter ya no se abre (no pide clave). Hoja de ruta: `docs/HOJA_DE_RUTA_APP_COMPLETA.md`.
- Pruebas: `unittest`.
- Dinero: números enteros en pesos colombianos (sin centavos).

## Cómo abrir la aplicación
**Con el .exe:** doble clic en `dist\TIENDAS_SM.exe` (no necesita Python). Para armarlo, una sola vez en esta carpeta:

    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements-escritorio.txt
    .venv\Scripts\python construir_exe.py --acceso-directo     (sin la opción, no crea el acceso directo)

Con `--acceso-directo` queda «TIENDAS S.M» en el escritorio, con el ícono de la tienda.

**Desde el código:** `.venv\Scripts\python iniciar_tienda.py --datos-de-ejemplo`

- `--datos-de-ejemplo` carga productos y clientes **ficticios**, solo si la base está vacía. Sin esa opción se abre con los datos guardados
  (también sirve con el .exe: `TIENDAS_SM.exe --datos-de-ejemplo`).
- Respaldos para el jefe en `Documentos\TIENDAS_SM respaldos` (sección Respaldos: cambiar carpeta, respaldar ahora y
  restaurar); se copian solos al cerrar la app y al cerrar la caja.
- Los datos se guardan en `%LOCALAPPDATA%\TIENDAS_SM\tiendas_sm.db`. Al cerrar la ventana se crea un respaldo verificado en esa misma
  carpeta (conserva los 7 más recientes).
- Atajos del punto de venta: **F2** buscar producto · **Enter** agregar · **F9** cobrar de contado · **F4** vender a crédito · **Esc** cerrar
  la ventana emergente o limpiar la búsqueda.

## Cómo correr las pruebas
Desde esta carpeta:

    python -m unittest discover -s tests -v

Resultado esperado: 592 pruebas, `OK`. Las mismas pruebas se ejecutan solas en cada Pull Request (ver `docs/CI.md`);
allí las 37 pruebas de pantallas se saltan porque el servidor no tiene pantalla.

## Estructura
    tiendas_sm/
      dominio.py          Producto, Existencia, Cliente, Venta, DetalleVenta, CuentaPorCobrar
      servicios.py        ServicioDeProductos, ServicioDeClientes, ControlInventario, ControlCredito, ServicioDeVentas
      puertos.py          Contratos de persistencia del núcleo (ADR-04)
      repositorios.py     Repositorios con SQLite (implementan los puertos)
      base_de_datos.py    Conexión y esquema de la base de datos
      validaciones.py     Validaciones compartidas
      presentador.py      Lógica de la pantalla del punto de venta, sin Tkinter (se prueba sin abrir ventanas)
      presentador_*.py    Lógica de Clientes, Créditos, Productos, Existencias y Ventas, sin Tkinter
      datos_de_ejemplo.py Datos ficticios para la demo
      aplicacion.py       Arma el sistema (conecta los objetos)
    interfaz_tk/
      ventana_principal.py       Menú lateral con las 6 secciones
      tema.py · pantalla.py      Colores del borrador HTML y base común de cada sección
      ventana_punto_de_venta.py · pantalla_*.py  Pantallas (solo dibujan y llaman a su presentador)
    iniciar_tienda.py     Abre la aplicación de escritorio (ventana pywebview; --tkinter abre la anterior)
    construir_exe.py      Arma dist/TIENDAS_SM.exe con PyInstaller
    interfaz_web/         api.py (lo que la página pide a Python), pagina.py y estatico/ (HTML, CSS y JS con la visual del borrador)
    tests/
      test_comportamiento.py          Pruebas de flujo completo con SQLite real (escenarios de la FPI-06)
      test_unitarias_dobles.py        Pruebas unitarias aisladas con stubs y mocks (FPI-14)
      test_caja_negra.py              Pruebas de caja negra CN-01 a CN-08, derivadas de los criterios Gherkin (FPI-14)
      test_integracion_incremental.py Integración ascendente por niveles (FPI-14)
      test_defectos_corregidos.py     Regresión de BUG-01, BUG-02, DT-09, TD-01 y TD-14
      test_venta_de_contado.py        Venta de contado (UC-02)
      test_arquitectura.py            El núcleo no importa SQLite (ADR-04)
      test_presentador.py             Punto de venta sin abrir ventanas
      test_presentador_*.py           Clientes, Créditos, Productos, Existencias y Ventas sin abrir ventanas
      test_iniciar_tienda.py          Ruta de datos y datos de ejemplo
      test_interfaz_tk.py · test_ventana_principal.py · test_pantalla_*.py  Pantallas (se saltan sin pantalla)
      test_escenarios_calidad.py      Escenarios E-02 (fallos), E-03 (desempeño) y E-05 (trazabilidad)
      test_migracion_esquema.py       Abrir una base vieja sin perder datos (columnas nuevas de ventas)
      test_medir_cobertura.py         TD-05: el medidor de cobertura no falla con líneas None (Python 3.13)
      test_healthcheck_paquete.py     Healthcheck del paquete publicado (CD)
    scripts/healthcheck_paquete.py  Revisa el .zip publicado en GitHub Releases (FPI-27)
    medir_calidad.py      Funciones largas, números mágicos y código muerto (FPI-12)
    medir_complejidad.py  Complejidad ciclomática V(G) por función (FPI-14)
    medir_cobertura.py    Cobertura de líneas con el módulo trace de Python; con --minimo 90 falla si baja (FPI-14/15)
    demo_en_vivo.py       Demostración narrada del flujo crítico (FPI-16): python demo_en_vivo.py
    calcular_metricas.py  Métricas reales de Git/GitHub para la retrospectiva (FPI-16)
    correr_regresion.py   Selecciona y corre las pruebas de regresión según los archivos que cambiaron (FPI-15)
    .github/workflows/ci.yml  Pipeline de CI de 3 jobs: linter, test (3.12 y 3.13) y analysis (FPI-15, FPI-25)
    .github/workflows/deploy.yml  Entrega continua por GitHub Releases con healthcheck y rollback (FPI-27)
    .github/workflows/ci-security.yml  Seguridad: Semgrep (SAST) y Trivy (SCA y secretos) (FPI-28)
    ruff.toml · .trivyignore  Excepciones de seguridad justificadas
    docs/                 CI.md, informes de defecto BUG-01 y BUG-02, BITACORA_IA.md y HOJA_DE_RUTA_IS2.md
    evidencia_fpi12/      Código v1 (antes de refactorizar), resultados de pruebas y métricas antes/después
    evidencia_fpi14/      Caja negra antes y después del arreglo, complejidad ciclomática y cobertura
    evidencia_fpi15/      Defectos reproducidos antes de corregir, resultados después y simulación local del pipeline
    evidencia_fpi24/      TDD de la tarea 3: salida real de las pruebas en los commits rojo, verde y refactor (Guía 8)

## Trazabilidad
Implementa HU-01 a HU-06, CU-01 y CU-02 (RF-01 a RF-09) y la interfaz de escritorio con sus 6 secciones.
Pendiente: medir RNF-01/E-01 con personas, lotes y vencimientos (Should Have) y alertas.
CR-01 (usuarios) y CR-02 (proveedores, pedidos, caja) no están aprobadas.

## Uso de IA
El primer borrador del código se generó con apoyo de IA a partir del diseño de la FPI-11. El desarrollador
debe leerlo, entenderlo y poder explicarlo antes de entregarlo (política de uso de IA del proyecto).
