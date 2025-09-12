function activeMenuOption(href) {
    $(".app-menu .nav-link")
    .removeClass("active")
    .removeAttr('aria-current')

    $(`[href="${(href ? href : "#/")}"]`)
    .addClass("active")
    .attr("aria-current", "page")
}

const app = angular.module("angularjsApp", ["ngRoute"])
app.config(function ($routeProvider, $locationProvider) {
    $locationProvider.hashPrefix("")

    $routeProvider
    .when("/", {
        templateUrl: "/app",
        controller: "appCtrl"
    })
    .when("/empleados", {
        templateUrl: "/empleados",
        controller: "empleadosCtrl"
    })
    .when("/asistencias", {
        templateUrl: "/asistencias",
        controller: "asistenciasCtrl"
    })
    .when("/asistenciaspases", {
        templateUrl: "/asistenciaspases",
        controller: "asistenciaspasesCtrl"
    })
    .when("/departamentos", {
        templateUrl: "/departamentos",
        controller: "departamentosCtrl"
    })
    .otherwise({
        redirectTo: "/"
    })
})

app.run(["$rootScope", "$location", "$timeout", function($rootScope, $location, $timeout) {
    // ... Código del profesor para fecha/hora y animaciones (sin cambios) ...
    function actualizarFechaHora() {
        lxFechaHora = DateTime
        .now()
        .setLocale("es")

        $rootScope.angularjsHora = lxFechaHora.toFormat("hh:mm:ss a")
        $timeout(actualizarFechaHora, 1000)
    }

    $rootScope.slide = ""

    actualizarFechaHora()

    $rootScope.$on("$routeChangeSuccess", function (event, current, previous) {
        $("html").css("overflow-x", "hidden")
        
        const path = current.$$route.originalPath

        if (path.indexOf("splash") == -1) {
            const active = $(".app-menu .nav-link.active").parent().index()
            const click  = $(`[href^="#${path}"]`).parent().index()

            if (active != click) {
                $rootScope.slide  = "animate__animated animate__faster animate__slideIn"
                $rootScope.slide += ((active > click) ? "Left" : "Right")
            }

            $timeout(function () {
                $("html").css("overflow-x", "auto")

                $rootScope.slide = ""
            }, 1000)

            activeMenuOption(`#${path}`)
        }
    })
}])

// Controlador para Login
app.controller("appCtrl", function ($scope, $http) {
    $("#frmInicioSesion").submit(function (event) {
        event.preventDefault()
        $.post("iniciarSesion", $(this).serialize(), function (respuesta) {
            if (respuesta.length) {
                alert("Iniciaste Sesión")
                window.location = "/#/empleados" // Redirige a Empleados
                return
            }
            alert("Usuario y/o Contraseña Incorrecto(s)")
        })
    })
})

// Controlador para Empleados
app.controller("empleadosCtrl", function ($scope, $http) {
    function buscarEmpleados() {
        $.get("/tbodyEmpleados", function (trsHTML) {
            $("#tbodyEmpleados").html(trsHTML)
        })
    }
    buscarEmpleados()

    // Evento para enviar el formulario (Crea o Actualiza)
    $(document).on("submit", "#frmEmpleado", function (event) {
        event.preventDefault();
        
        $.post("/empleado", $(this).serialize())
            .done(function() {
                buscarEmpleados();
                
                // IMPORTANTE: Limpiar el formulario después de guardar.
                // Esto resetea todos los campos y vacía el ID oculto,
                // dejando el formulario listo para un nuevo registro.
                $("#frmEmpleado")[0].reset();
                $("#idEmpleado").val(""); 
            })
            .fail(function(response) {
                // Muestra un error si algo sale mal en el servidor.
                alert("Error al guardar: " + response.responseJSON.error);
            });
    });

    // Evento para el botón "Editar" (Llena el formulario)
    $(document).on("click", ".btn-editar-empleado", function () {
        const id = $(this).data("id");
        const nombre = $(this).data("nombre");
        const numero = $(this).data("numero");
        const fecha = $(this).data("fecha");
        const idDepartamento = $(this).data("iddepartamento");

        // Llenamos todos los campos del formulario, incluyendo el ID oculto.
        $("#idEmpleado").val(id);
        $("#txtNombreEmpleado").val(nombre);
        $("#txtNumero").val(numero);
        $("#txtFechaIngreso").val(fecha);
        $("#selIdDepartamento").val(idDepartamento);
    });
});

// Controlador para Asistencias (Dirigida por Eventos)
app.controller("asistenciasCtrl", function ($scope, $http) {
    function buscarAsistencias() {
        $.get("/tbodyAsistencias", function (trsHTML) {
            $("#tbodyAsistencias").html(trsHTML);
        });
    }
    buscarAsistencias();
    
    // Configuración de Pusher
    Pusher.logToConsole = true;
    var pusher = new Pusher("686124f7505c58418f23", { // Tu KEY
      cluster: "us2"
    });
    var channel = pusher.subscribe("canalAsistencias");
    channel.bind("eventoAsistencias", function(data) {
        buscarAsistencias();
    });

    // Botón de Editar
    $(document).on("click", ".btn-editar-asistencia", function () {
        const id = $(this).data("id");
        const fecha = $(this).data("fecha");
        const comentarios = $(this).data("comentarios");

        $("#txtFecha").val(fecha);
        $("#txtComentarios").val(comentarios);
        
        // CORRECCIÓN: Toda la lógica de edición (incluyendo crear el input oculto)
        // debe estar DENTRO del evento 'click'.
        if ($("#hiddenId").length === 0) {
            $("#frmAsistencia").append(`<input type="hidden" id="hiddenId" name="idAsistencia">`);
        }
        $("#hiddenId").val(id);
    });

    $(document).on("submit", "#frmAsistencia", function (event) {
        event.preventDefault();

        const id = $("#hiddenId").val();
        // Si hay un ID en el campo oculto, es una edición. Si no, es una creación.
        const url = id ? "/asistencia/editar" : "/asistencia";

        $.post(url, $(this).serialize())
            .done(function () {
                buscarAsistencias();
                $("#frmAsistencia")[0].reset();
                // Si el campo oculto existe, lo eliminamos para dejar el form listo para crear.
                if ($("#hiddenId").length > 0) {
                    $("#hiddenId").remove();
                }
            })
            .fail(function() {
                alert("Hubo un error al guardar la asistencia.");
            });
    });
});

// Controlador para AsistenciasPases (N Capas)
app.controller("asistenciaspasesCtrl", function ($scope, $http) {
    function buscarAsistenciasPases() {
        $.get("/tbodyAsistenciasPases", function (trsHTML) {
            $("#tbodyAsistenciasPases").html(trsHTML)
        })
    }
    buscarAsistenciasPases()

    $(document).on("click", ".btn-eliminar-pase", function (event) {
        const id = $(this).data("id")
        // DELETE (ELIMINAR)
        if (confirm(`¿Estás seguro de eliminar el pase #${id}?`)) {
            $.post("/asistenciapase/eliminar", { id: id })
            .done(function() {
                buscarAsistenciasPases();
            })
        }
    })
})

//Controlador para departamentos.
app.controller("departamentosCtrl", function ($scope, $http) {
    console.log("Se ha iniciado departamentosCtrl")

    function buscarDepartamentos() {
        $.get("/tbodyDepartamentos", function (trsHTML) {
            $("#tbodyDepartamentos").html(trsHTML)
        })
    }
    buscarDepartamentos()

    $(document).on("submit", "#frmDepartamento", function (event) {
        event.preventDefault()
        $.post("/departamento", $(this).serialize())
        .done(function () {
            buscarDepartamentos()
            $("#frmDepartamento")[0].reset()
            $("#idDepartamento").val("")
        })
    })
})



const DateTime = luxon.DateTime
let lxFechaHora

document.addEventListener("DOMContentLoaded", function (event) {
    const configFechaHora = {
        locale: "es",
        weekNumbers: true,
        minuteIncrement: 15,
        altInput: true,
        altFormat: "d/F/Y",
        dateFormat: "Y-m-d",
    }
    activeMenuOption(location.hash)
})
