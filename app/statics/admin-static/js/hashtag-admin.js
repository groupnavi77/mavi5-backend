// [tu_app]/static/product_ins/js/hashtag-admin.js

(function ($) {
    // Usamos el alias de jQuery en el Admin
    let typingTimer;
    const DEBOUNCE_TIME = 300;

    /**
     * Crea y posiciona el menú de sugerencias con los datos de la API.
     * @param {jQuery} input El elemento input donde se escribe.
     * @param {Array<Object>} data Lista de objetos Tag [{name: "etiqueta"}, ...]
     */
    function createSuggestionDropdown(input, data) {
        // Elimina cualquier dropdown anterior
        input.next('.tag-suggestion-dropdown').remove();

        if (!data || data.length === 0) return;

        // --- Creación y Estilos del Dropdown (Estilos básicos del Admin) ---
        const dropdown = $('<div>').addClass('tag-suggestion-dropdown').css({
            position: 'absolute',
            zIndex: 1000,
            // Estilos que imitan el Admin oscuro o usan colores neutros
            backgroundColor: '#434343',
            border: '1px solid #ccc',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            maxHeight: '200px',
            overflowY: 'auto',
            width: input.outerWidth()
        });

        // Llenar el dropdown con sugerencias
        data.forEach(function (item) {
            const suggestion = $('<div>')
                .addClass('suggestion-item')
                .text('#' + item.name) // Muestra la sugerencia con '#'
                .css({
                    padding: '5px 10px',
                    cursor: 'pointer',
                    fontSize: '13px'
                })
                .hover(function () { 
                    $(this).css('background-color', 'rgba(43, 43, 43, 1)'); 
                }, function () { 
                    // Color de fondo normal (puede necesitar ajuste dependiendo del tema exacto)
                    $(this).css('background-color', '#434343'); 
                })
                .on('click', function () {
                    // Lógica para insertar la etiqueta completa

                    const currentValue = input.val();
                    const lastHashIndex = currentValue.lastIndexOf('#');

                    if (lastHashIndex !== -1) {
                        // Corta la cadena antes del último '#'. Esto incluye todos los tags anteriores.
                        const beforeHash = currentValue.substring(0, lastHashIndex);
                        
                        // Nuevo valor: Tags anteriores + nueva etiqueta + espacio
                        const newValue = beforeHash.trim() + ' #' + item.name + ', ';
                        input.val(newValue);
                    } else {
                        // Si no hay tags previos, simplemente añade el tag
                        input.val(item.name + ', ');
                    }
                    
                    dropdown.remove();
                    input.focus();
                });
            dropdown.append(suggestion);
        });

        // Posicionar el dropdown justo debajo del input
        dropdown.css({ 
            top: input.position().top + input.outerHeight(), 
            left: input.position().left 
        });
        
        // Añadir el dropdown después del input
        input.after(dropdown);
    }

    // --- Inicialización del Widget ---

    $(document).ready(function () {
        // Itera sobre todos los campos que tienen nuestro atributo de URL
        $('input[data-autocomplete-url]').each(function () {
            const input = $(this);
            const autocompleteUrl = input.data('autocomplete-url');

            // 1. Escuchar la entrada de teclado
            input.on('keyup', function (e) {
                // Si se presiona una tecla de navegación (Enter, Flechas), ignorar el debounce
                if (e.key === 'Enter' || e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                    // Manejo de navegación por teclado aquí si es necesario
                    return;
                }

                clearTimeout(typingTimer);
                const currentValue = input.val();

                // Buscar el último '#' para enfocarnos en el hashtag actual
                const lastHashIndex = currentValue.lastIndexOf('#');

                if (lastHashIndex === -1) {
                    input.next('.tag-suggestion-dropdown').remove();
                    return;
                }

                // --- Lógica de Extracción de Término de Búsqueda (Más robusta) ---

                // Subcadena que contiene el término de búsqueda actual (después del último '#')
                const subString = currentValue.substring(lastHashIndex + 1);

                // Buscar el primer separador (espacio o coma) después del #
                const nextSeparatorIndex = subString.search(/[\s,]/);

                let searchTerm;
                if (nextSeparatorIndex !== -1) {
                    // Si hay un separador, el término de búsqueda es lo que está antes.
                    searchTerm = subString.substring(0, nextSeparatorIndex).trim();
                } else {
                    // Si no hay separador, el término es el resto de la subcadena.
                    searchTerm = subString.trim();
                }

                // 2. Comprobaciones de validación (longitud mínima y término no vacío)
                if (searchTerm.length < 2) {
                    input.next('.tag-suggestion-dropdown').remove();
                    return;
                }

                // 3. Usar Debounce para evitar sobrecargar el servidor
                typingTimer = setTimeout(function () {
                    
                    // 4. Petición AJAX (Ninja espera '?q=' por tu endpoint)
                    $.ajax({
                        // La URL debe ser: /api/tags/autocomplete?q=termino
                        url: autocompleteUrl + '?q=' + encodeURIComponent(searchTerm),
                        
                        success: function (data) {
                            // Django Ninja devuelve la lista directamente [{}, {}, ...]
                            createSuggestionDropdown(input, data);
                        },
                        error: function (xhr, status, error) {
                            // Opcional: Mostrar error en la consola
                            console.error("Error fetching tags:", status, error);
                        }
                    });
                }, DEBOUNCE_TIME);
            });

            // 5. Ocultar el dropdown cuando el campo pierde el foco
            input.on('blur', function () {
                // Pequeño retraso para que el clic en el dropdown funcione antes de que desaparezca
                setTimeout(function () {
                    input.next('.tag-suggestion-dropdown').remove();
                }, 200);
            });
        });
    });

})(django.jQuery);