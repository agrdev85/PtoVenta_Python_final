# README - PtoVenta_Python_final

## Descripción
**PtoVenta_Python_final** es una aplicación de punto de venta desarrollada en Python que permite gestionar productos, órdenes, empleados e inventarios de manera eficiente. Esta aplicación está diseñada para pequeñas empresas o comercios, ofreciendo funcionalidades básicas como registro de productos, procesamiento de ventas, generación de reportes y administración de empleados.

## Características Principales
- **Gestión de Productos**: Añadir, editar y eliminar productos con detalles como nombre, categoría, imagen, costo, precio, stock y stock mínimo.
- **Procesamiento de Órdenes**: Registrar ventas, gestionar carritos y emitir facturas.
- **Reportes de Estadística**: Generar archivos PDF con detalles de ventas, productos más/menos vendidos y estado del inventario.
- **Administración de Empleados**: Añadir, editar y eliminar empleados.
- **Seguridad**: Cierre de sesión seguro para proteger los datos del sistema.

## Tecnologías utilizadas

- **Backend**: Flask
- **Frontend**: [Bootstrap / HTML / CSS / JavaScript]
- **Base de datos**: [SQLAlchemy, SQLite, PostgreSQL, etc.]
- **Otras herramientas**: [Cualquier otra tecnología que uses, como JWT para autenticación, Stripe para pagos, etc.]

## Instalación
1. Clona el repositorio desde GitHub:
   ```
   git clone https://github.com/agrdev85/PtoVenta_Python_final.git
   ```
2. Navega al directorio del proyecto:
   ```
   cd PtoVenta_Python_final
   ```
3. Instala las dependencias necesarias (asegúrate de tener Python instalado):
   ```
   pip install -r requirements.txt
   ```
   *Nota*: Si no existe un archivo `requirements.txt`, verifica las librerías utilizadas en el código (por ejemplo, para PDFs, estadísticas, etc.) y Instálalas manualmente (e.g., `pip install reportlab` para generación de PDFs).

4. Ejecuta la aplicación:

    ```bash
    flask run
    ```
5. Accede a la aplicación desde tu navegador en [http://localhost:5000](http://localhost:5000).

## Uso
Sigue estos pasos para utilizar la aplicación:

### Paso 1: Iniciar Sesión en el Sistema
- Abre la aplicación.
- En la ventana principal, presiona "Iniciar Sesión".
- Ingresa tu correo y contraseña.
- Haz clic en "Iniciar Sesión" para entrar al panel principal del sistema.

### Paso 2: Navegar por la Interfaz Principal
- Una vez iniciada la sesión, verás el panel principal con opciones como "Órdenes", "Panel", "Productos", "Estadísticas", "Configuración" y "Herramientas".
- Estas pestañas o botones permiten acceder a las funciones clave del sistema.
- Haz clic en cada una para gestionar productos, procesar órdenes o generar reportes.
- Ten en cuenta que cambiar el estado de las "Órdenes" es irreversible.

### Paso 3: Añadir un Nuevo Producto
- Ve a la sección "Productos" y haz clic en "Añadir Producto".
- Completa el formulario con detalles como nombre del producto, categoría, imagen, costo, precio, stock y stock_min.
- Presiona "Guardar" para registrar el producto en la base de datos.

### Paso 4: Editar o Eliminar Productos
- En "Productos", seleccione un producto de la lista.
- Haz clic en "Editar" para actualizar detalles como precio o stock, luego guarda los cambios.
- Para eliminar, seleccione "Eliminar" y confirma la acción. Esto actualiza la base de datos, asegurando que la información sea precisa.

### Paso 5: Procesar una Orden
- Diríjase a "Inicio".
- Seleccione un producto, ingrese la cantidad a vender y haga clic en "Agregar al Carrito".
- Repita para más productos si es necesario.
- Revise el total de la venta y haga clic en "Reservar" y confirme para registrar la transacción y reducir el inventario automáticamente.
- Una vez generada la "Orden", se puede "Eliminar" o emitir una factura en caso de que el cliente la requiera.

### Paso 6: Generar un Reporte de Estadística
- En la sección "Estadística", seleccione un rango de fechas o una venta específica.
- Haz clic en "Filtrar" para crear un archivo PDF con detalles de las ventas, como productos más o menos vendidos y totales, además del estado del inventario.

### Paso 7: Gestionar Empleados
- Acceda al panel de "Configuración" para ver todos los empleados.
- Para "Añadir", seleccione el botón correspondiente y para "Editar", haz clic en "Editar", luego guarda los cambios.
- Para eliminar, seleccione "Eliminar" y confirme la acción.

### Paso 8: Cerrar Sesión
- Cuando termine, haga clic en "Salir", ubicado en la interfaz principal o en un menú.
- Esto cierra su sesión de forma segura, asegurando que los datos del sistema queden protegidos hasta la próxima vez que inicie sesión.

## Requisitos
- Python 3.x
- Dependencias específicas (verifica el código para librerías como `reportlab` para PDFs o cualquier otra usada).

## Contribuciones
Si deseas contribuir al proyecto:
1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m "Descripción del cambio"`).
4. Envía un pull request.

## Licencia
Este proyecto está bajo la licencia [especificar licencia si aplica, e.g., MIT]. Consulta el archivo `LICENSE` para más detalles.

## Contacto
Para dudas o soporte, contacta al desarrollador en [agrdev85@github.com](mailto:agrdev85@github.com) o abre un issue en el repositorio.

## Agradecimientos
Gracias a la comunidad de desarrolladores y a las librerías utilizadas que hicieron posible este proyecto.

---