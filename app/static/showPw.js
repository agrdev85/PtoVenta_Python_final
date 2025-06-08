    function togglePassword(id) {
        const input = document.getElementById(id);
        const icon = input.nextElementSibling.querySelector('.toggle-icon');
        if (input.type === "password") {
            input.type = "text";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
            icon.title = "Ocultar contraseña";
        } else {
            input.type = "password";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
            icon.title = "Mostrar contraseña";
        }
    }

    // Función para alternar visibilidad de contraseña para Actualizacion de Usuarios en Configuracion
        function togglePasswords(inputId, iconId) {
            const input = document.getElementById(inputId); // Obtiene el input por su id
            const icon = document.getElementById(iconId);   // Obtiene el ícono por su id
            if (input.type === "password") {
                input.type = "text";
                icon.classList.remove("fa-eye");
                icon.classList.add("fa-eye-slash");
                icon.title = "Ocultar contraseña";
            } else {
                input.type = "password";
                icon.classList.remove("fa-eye-slash");
                icon.classList.add("fa-eye");
                icon.title = "Mostrar contraseña";
            }
        }