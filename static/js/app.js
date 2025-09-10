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

// Controlador para Empleados (N Capas)
app.controller("empleadosCtrl", function ($scope, $http) {
    function buscarEmpleados() {
        $.get("/tbodyEmpleados", function (trsHTML) {
            $("#tbodyEmpleados").html(trsHTML)
        })
    }
    buscarEmpleados()

    $(document).on("submit", "#frmEmpleado", function (event) {
        event.preventDefault()
        // CREATE/UPDATE
        $.post("/empleado", $(this).serialize())
        .done(function() {
            buscarEmpleados();
        })
    })
})

// Controlador para Asistencias (Dirigida por Eventos)
app.controller("asistenciasCtrl", function ($scope, $http) {
    function buscarAsistencias() {
        $.get("/tbodyAsistencias", function (trsHTML) {
            $("#tbodyAsistencias").html(trsHTML)
        })
    }
    buscarAsistencias()
    
    // Configuración de Pusher
    Pusher.logToConsole = true
    var pusher = new Pusher("686124f7505c58418f23", { // Tu KEY
      cluster: "us2"
    })
    var channel = pusher.subscribe("canalAsistencias")
    // Consumidor del evento: Llama a la función de búsqueda cuando hay un evento
    channel.bind("eventoAsistencias", function(data) {
        buscarAsistencias()
    })

    $(document).on("submit", "#frmAsistencia", function (event) {
        event.preventDefault()
        // CREATE
        $.post("/asistencia", $(this).serialize())
    })

    $(document).on("click", ".btn-editar-asistencia", function () {
    const id = $(this).data("id")
    const fecha = $(this).data("fecha")
    const comentarios = $(this).data("comentarios")

    $("#txtFecha").val(fecha)
    $("#txtComentarios").val(comentarios)

    // Guarda el ID en un campo oculto para saber si es edición
    if ($("#hiddenId").length === 0) {
        $("#frmAsistencia").append(`<input type="hidden" id="hiddenId" name="id">`)
    }
    $("#hiddenId").val(id)
})

})

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
app.controller("departamentosCtrl", function ($scoope, $http) {
     function buscarDepartamentos() {
        $.get("/tbodyDepartamentos", function (trsHTML) {
            $("#tbodyDepartamentos").html(trsHTML)
        })
    }
    buscarDepartamentos()
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
