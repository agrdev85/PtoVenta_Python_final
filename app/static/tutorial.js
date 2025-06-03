function showTutorial() {
    console.log("Tutorial modal opened"); // Debug
    Swal.fire({
        html: `
            <div class="tutorial-slider-container">
                <!-- Step 1: Login -->
                <div class="tutorial-card active" data-index="0">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='login.png') }}" alt="Paso 1">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-1-circle-fill"></i> Iniciar Sesión en el Sistema</h5>
                        <p>Abra la aplicación. En la ventana principal presionar "Iniciar Sesión" y en la ventana de inicio de sesión, ingrese su correo y contraseña. Haga clic en "Iniciar Sesión" para entrar al panel principal del sistema.</p>
                    </div>
                </div>
                <!-- Step 2: Main Interface -->
                <div class="tutorial-card" data-index="1">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='img/panel.png') }}" alt="Paso 2">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-2-circle-fill"></i> Navegar por la Interfaz Principal</h5>
                        <p>Una vez iniciada la sesión, verá el panel principal con opciones como "Órdenes" <i class="bi bi-bell" style=" font-size: 1.5em;"></i>, "Panel" <i class="bi bi-speedometer2" style="font-size: 1.5em;"></i>, "Productos" <i class="bi bi-bag-fill" style="font-size: 1.5em;"></i>, "Estadísticas" <i class="bi bi-graph-up-arrow" style=" font-size: 1.5em;"></i>, "Configuración" <i class="bi bi-sliders" style="font-size: 1.5em;"></i> y "Herramientas" <i class="bi bi-tools" style="font-size: 1.5em;"></i>. Estas pestañas o botones le permiten acceder a las funciones claves del sistema. Haga clic en cada una para gestionar productos, procesar ordenes o generar reportes. En el panel puedes "Eliminar" <span class="tutorial-fill" style="font-size: 1.5em;"> <i class="bi bi-trash3 text-danger"></i></span> y atualizar el estado de las "Órdenes" que emitió cada uno de sus empleados cuando los mismos coticen, ten en cuenta que al cambiar el estado este será irreversible</p>
                    </div>
                </div>
                <!-- Step 3: Add Product -->
                <div class="tutorial-card" data-index="2">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='img/productos.png') }}" alt="Paso 3">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-3-circle-fill"></i> Añadir un Nuevo Producto</h5>
                        <p>Vaya a la sección "Productos" y haga clic en "Añadir Producto" <i class="bi bi-database-fill-add" style=" font-size: 1.5em;"></i>. Complete el formulario con detalles como nombre del producto, categoria, imagen, costo, precio, stock y stock_min. Presione "Guardar" para registrar el producto en la base de datos.</p>
                    </div>
                </div>
                <!-- Step 4: Edit/Delete Product -->
                <div class="tutorial-card" data-index="3">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='img/gestionproductos.png') }}" alt="Paso 4">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-4-circle-fill"></i> Editar o Eliminar Productos</h5>
                        <p>En "Productos", seleccione un producto de la lista. Haga clic en "Editar" <span class="tutorial-fill"><strong><i class="bi bi-pencil-square text-success"></i></strong></span> para actualizar detalles como precio o stock, luego guarde los cambios. Para eliminar, seleccione "Eliminar" <span class="tutorial-fill"><i class="bi bi-trash3 text-danger"></i></span> y confirme la acción. Esto actualiza la base de datos, asegurando que la información sea precisa.</p>
                    </div>
                </div>
                <!-- Step 5: Process Sale -->
                <div class="tutorial-card" data-index="4">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='./img/factura.png') }}" alt="Paso 5">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-5-circle-fill"></i> Procesar una Orden</h5>
                        <p>Diríjase a "Inicio". Seleccione un producto, ingrese la cantidad a vender y haga clic en "Agregar al Carrito". Repita para más productos si es necesario. Revise el total de la venta y haga clic en "Reservar" y confirmar para registrar la transacción y reducir el inventario automáticamente. Una vez generada la "Órden" se puede "Eliminar" <span class="tutorial-fill" style="font-size: 1.5em;"> <i class="bi bi-trash3 text-danger"></i></span> o emitir una factura en caso de que el cliente la requiera <i class="bi bi-file-earmark-pdf" style="color: #ff1212; font-size: 1.5em;"></i>Factura</p>
                    </div>
                </div>
                <!-- Step 6: Generate Report -->
                <div class="tutorial-card" data-index="5">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='img/estadisticas.png') }}" alt="Paso 6">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-6-circle-fill"></i> Generar un Reporte de Estadística</h5>
                        <p>En la sección "Estadística", seleccione un rango de fechas o una venta específica. Haga clic en "<i class="bi bi-file-earmark-pdf-fill" style="color: #ff1212; font-size: 1.5em;"></i>Filtrar" para crear un archivo PDF con detalles de las ventas, como productos más o menos vendidos y totales, además del estado del inventario.</p>
                    </div>
                </div>
                <!-- Step 7: Manage Inventory -->
                <div class="tutorial-card" data-index="6">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='img/ConfgGestionEmpleados.png') }}" alt="Paso 7">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-7-circle-fill"></i> Gestionar Empleados</h5>
                        <p>Acceda al panel de "Configuración" para ver todos los empleados. Para "Añadir" seleccione <i class="bi bi-person-plus" style="font-size: 1.5em;"></i> y para "Editar" <span class="tutorial-fill"><i class="bi bi-pencil-square text-success"></i></span>, luego guarde los cambios. Para eliminar, seleccione "Eliminar" <span class="tutorial-fill"><i class="bi bi-trash3 text-danger"></i></span>, y confirme la acción.</p>
                    </div>
                </div>
                <!-- Step 8: Log Out -->
                <div class="tutorial-card" data-index="7">
                    <div class="tutorial-image-container">
                        <img src="{{ url_for('static', filename='img/cerrarSesion.png') }}" alt="Paso 8">
                        <button class="tutorial-zoom-button" onclick="toggleZoom(this)">
                            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm0-2a2.5 2.5 0 002.5-2.5c0-.28-.05-.54-.14-.79L12.29 10H11.5v-.5h.79l-.43-1.29c-.25-.09-.51-.14-.79-.14A2.5 2.5 0 009 10.5c0 .28.05.54.14.79l.43 1.29h-.79v.5h-.79l.43 1.29c.25.09.51.14.79.14z"/></svg>
                        </button>
                    </div>
                    <div class="tutorial-text-container">
                        <h5>Paso <i class="bi bi-8-circle-fill"></i> Cerrar Sesión</h5>
                        <p>Cuando termine, haga clic en "Salir", ubicado en la interfaz principal o en un menú. Esto cierra su sesión de forma segura, asegurando que los datos del sistema queden protegidos hasta la próxima vez que inicie sesión.</p>
                    </div>
                </div>
                <!-- Zoom overlay -->
                <div class="tutorial-zoom-overlay" onclick="toggleZoom(this)">
                    <img src="" alt="Zoomed image">
                </div>
                <!-- Navigation buttons -->
                <button class="tutorial-nav-button prev" onclick="changeSlide(-1)">
                    <svg viewBox="0 0 24 24"><path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6z"/></svg>
                </button>
                <button class="tutorial-nav-button next" onclick="changeSlide(1)">
                    <svg viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>
                </button>
            </div>
        `,
        showConfirmButton: false,
        showCloseButton: true,
        allowOutsideClick: false,
        customClass: {
            popup: 'tutorial-modal'
        },
        didOpen: () => {
            console.log("Slider initialized"); // Debug
            const cards = document.querySelectorAll('.tutorial-card');
            let currentIndex = 0;

            function updateSlider() {
                cards.forEach((card, index) => {
                    card.classList.toggle('active', index === currentIndex);
                    card.style.opacity = index === currentIndex ? '1' : '0';
                    card.style.transform = index === currentIndex ? 'translateY(0)' : 'translateY(20px)';
                });
                console.log(`Current slide: ${currentIndex + 1}`); // Debug
            }

            window.changeSlide = function(direction) {
                currentIndex = (currentIndex + direction + cards.length) % cards.length;
                updateSlider();
            };

            window.toggleZoom = function(element) {
                const overlay = document.querySelector('.tutorial-zoom-overlay');
                const overlayImg = overlay.querySelector('img');
                if (element.classList.contains('tutorial-zoom-button')) {
                    const img = element.parentElement.querySelector('img');
                    overlayImg.src = img.src;
                    overlay.classList.add('active');
                    console.log("Zoom opened"); // Debug
                } else {
                    overlay.classList.remove('active');
                    console.log("Zoom closed"); // Debug
                }
            };

            updateSlider();
        }
    });
}