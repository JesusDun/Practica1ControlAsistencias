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
    .when("/reportes", {
        templateUrl: "/reportes",
        controller: "reportesCtrl"
    })
    .otherwise({
        redirectTo: "/"
    })
})
app.run(["$rootScope", "$location", "$timeout", function($rootScope, $location, $timeout) {
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

app.controller("appCtrl", function ($scope, $http) {
    $("#frmInicioSesion").submit(function (event) {
        event.preventDefault()
        $.post("iniciarSesion", $(this).serialize(), function (respuesta) {
            if (respuesta.length) {
                alert("Iniciaste Sesión")
                window.location = "/#/empleados"
                return
            }
            alert("Usuario y/o Contraseña Incorrecto(s)")
        })
    })
})

// Controlador para Empleados
app.controller("empleadosCtrl", function ($scope, $http) {
    function cargarEmpleados() {
        $.get("/tbodyEmpleados", function (html) {
            $("#tbodyEmpleados").html(html)
        })
    }

    cargarEmpleados()

    $(document).on("submit", "#frmEmpleado", function (event) {
        event.preventDefault()
        
        $.post("/empleado", $(this).serialize(), function () {
            cargarEmpleados()
            $("#frmEmpleado")[0].reset()
            $("#txtId").val("")
            toast("Empleado guardado correctamente")
        }).fail(function() {
            toast("Error al guardar empleado", 3, null, "danger")
        })
    })

    $(document).on("click", ".btn-editar", function () {
        const id = $(this).data("id")
        
        $.get(`/empleado/${id}`, function (empleado) {
            $("#txtId").val(empleado.idEmpleado)
            $("#txtNombre").val(empleado.nombreEmpleado)
            $("#txtNumero").val(empleado.numero)
            $("#txtFechaIngreso").val(empleado.fechaIngreso)
        })
    })

    $(document).on("click", ".btn-eliminar", function () {
        if (confirm("¿Estás seguro de eliminar este empleado?")) {
            const id = $(this).data("id")
            
            $.post("/empleado/eliminar", {id: id}, function () {
                cargarEmpleados()
                toast("Empleado eliminado correctamente")
            }).fail(function() {
                toast("Error al eliminar empleado", 3, null, "danger")
            })
        }
    })
})

// Controlador para Asistencias
app.controller("asistenciasCtrl", function ($scope, $http) {
    function cargarAsistencias() {
        $.get("/tbodyAsistencias", function (html) {
            $("#tbodyAsistencias").html(html)
        })
    }

    cargarAsistencias()

    // Configurar Pusher para asistencias
    Pusher.logToConsole = true
    var pusher = new Pusher("e57a8ad0a9dc2e83d9a2", {
      cluster: "us2"
    })

    var channel = pusher.subscribe("canalAsistencias")
    channel.bind("eventoAsistencias", function(data) {
        cargarAsistencias()
    })

    $(document).on("submit", "#frmAsistencia", function (event) {
        event.preventDefault()
        
        $.post("/asistencia", $(this).serialize(), function () {
            cargarAsistencias()
            $("#frmAsistencia")[0].reset()
            toast("Asistencia registrada correctamente")
        }).fail(function() {
            toast("Error al registrar asistencia", 3, null, "danger")
        })
    })
})

// Controlador para Asistencias Pases
app.controller("asistenciaspasesCtrl", function ($scope, $http) {
    function cargarAsistenciasPases() {
        $.get("/tbodyAsistenciasPases", function (html) {
            $("#tbodyAsistenciasPases").html(html)
        })
    }

    cargarAsistenciasPases()

    $(document).on("submit", "#frmAsistenciaPase", function (event) {
        event.preventDefault()
        
        $.post("/asistenciapase", $(this).serialize(), function () {
            cargarAsistenciasPases()
            $("#frmAsistenciaPase")[0].reset()
            toast("Registro de asistencia guardado correctamente")
        }).fail(function() {
            toast("Error al guardar registro de asistencia", 3, null, "danger")
        })
    })
})

// Controlador para Reportes (Arquitectura Orientada a Servicios)
app.controller("reportesCtrl", function ($scope, $http) {
    // Cargar empleados para el selector
    function cargarEmpleados() {
        $.get("/tbodyEmpleados", function (html) {
            $("#tbodyEmpleadosReporte").html(html)
        })
    }

    cargarEmpleados()

    $(document).on("submit", "#frmReporte", function (event) {
        event.preventDefault()
        
        const fechaInicio = $("#txtFechaInicio").val()
        const fechaFin = $("#txtFechaFin").val()
        
        if (!fechaInicio || !fechaFin) {
            toast("Debe seleccionar ambas fechas", 3, null, "warning")
            return
        }
        
        $.get(`/reporte/asistencias?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`, function (data) {
            let html = ""
            if (data.length > 0) {
                data.forEach(function(item) {
                    html += `<tr>
                        <td>${item.fecha}</td>
                        <td>${item.total_registros}</td>
                        <td>${item.asistencias}</td>
                        <td>${item.retardos}</td>
                        <td>${item.faltas}</td>
                    </tr>`
                })
            } else {
                html = "<tr><td colspan='5' class='text-center'>No hay datos para el rango seleccionado</td></tr>"
            }
            
            $("#tbodyReporte").html(html)
        }).fail(function() {
            toast("Error al generar el reporte", 3, null, "danger")
        })
    })
})

const DateTime = luxon.DateTime
let lxFechaHora

document.addEventListener("DOMContentLoaded", function (event) {
    const configFechaHora = {
        locale: "es",
        weekNumbers: true,
        altInput: true,
        altFormat: "d/F/Y",
        dateFormat: "Y-m-d",
    }

    activeMenuOption(location.hash)
    
    // Establecer fechas por defecto para reportes (mes actual)
    const hoy = new Date()
    const primerDiaMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
    const ultimoDiaMes = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0)
    
    $("#txtFechaInicio").val(primerDiaMes.toISOString().split('T')[0])
    $("#txtFechaFin").val(ultimoDiaMes.toISOString().split('T')[0])
})
