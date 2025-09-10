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
    $rootScope.usuarioLogueado = false
    $rootScope.nombreUsuario = ""

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

app.controller("appCtrl", function ($scope, $http, $rootScope) {
    // Verificar si ya está logueado
    if (localStorage.getItem('user_id')) {
        $rootScope.usuarioLogueado = true
        $rootScope.nombreUsuario = localStorage.getItem('user_name')
        window.location = "/#/empleados"
    }

    $("#frmInicioSesion").submit(function (event) {
        event.preventDefault()
        $.post("iniciarSesion", $(this).serialize(), function (respuesta) {
            if (respuesta.success) {
                localStorage.setItem('user_id', respuesta.user.idEmpleado)
                localStorage.setItem('user_name', respuesta.user.nombreEmpleado)
                $rootScope.$apply(function() {
                    $rootScope.usuarioLogueado = true
                    $rootScope.nombreUsuario = respuesta.user.nombreEmpleado
                })
                window.location = "/#/empleados"
            } else {
                alert("Usuario y/o Contraseña Incorrecto(s)")
            }
        })
    })

    $scope.cerrarSesion = function() {
        localStorage.removeItem('user_id')
        localStorage.removeItem('user_name')
        $rootScope.usuarioLogueado = false
        $rootScope.nombreUsuario = ""
        window.location = "/#/"
    }
})

app.controller("empleadosCtrl", function ($scope, $http) {
    $scope.empleados = []
    $scope.nuevoEmpleado = {}
    $scope.empleadoEditando = null

    function cargarEmpleados() {
        $.get("/tbodyEmpleados", function (trsHTML) {
            $("#tbodyEmpleados").html(trsHTML)
        })
    }

    cargarEmpleados()
    
    // Configurar Pusher para actualizaciones en tiempo real
    Pusher.logToConsole = true
    var pusher = new Pusher("686124f7505c58418f23", {
      cluster: "us2"
    })

    var channel = pusher.subscribe("canal-empleados")
    channel.bind("evento-empleados", function(data) {
        cargarEmpleados()
    })

    $scope.guardarEmpleado = function() {
        $.post("/empleado", {
            id: $scope.empleadoEditando ? $scope.empleadoEditando.idEmpleado : "",
            nombre: $scope.nuevoEmpleado.nombre,
            numero: $scope.nuevoEmpleado.numero,
            fechaIngreso: $scope.nuevoEmpleado.fechaIngreso
        }).done(function() {
            cargarEmpleados()
            $scope.nuevoEmpleado = {}
            $scope.empleadoEditando = null
            $scope.$apply()
        })
    }

    $scope.editarEmpleado = function(id) {
        $.get(`/empleado/${id}`, function(empleado) {
            $scope.empleadoEditando = empleado
            $scope.nuevoEmpleado = {
                nombre: empleado.nombreEmpleado,
                numero: empleado.numero,
                fechaIngreso: new Date(empleado.fechaIngreso).toISOString().split('T')[0]
            }
            $scope.$apply()
        })
    }

    $scope.eliminarEmpleado = function(id) {
        if (confirm("¿Estás seguro de eliminar este empleado?")) {
            $.post("/empleado/eliminar", {id: id}, function() {
                cargarEmpleados()
            })
        }
    }

    $scope.cancelarEdicion = function() {
        $scope.empleadoEditando = null
        $scope.nuevoEmpleado = {}
    }
})

app.controller("asistenciasCtrl", function ($scope, $http) {
    $scope.asistencias = []
    $scope.nuevaAsistencia = {
        fecha: new Date().toISOString().split('T')[0],
        comentarios: '',
        empleados: []
    }
    $scope.empleados = []

    function cargarAsistencias() {
        $.get("/tbodyAsistencias", function (trsHTML) {
            $("#tbodyAsistencias").html(trsHTML)
        })
    }

    function cargarEmpleados() {
        $.get("/empleados", function (data) {
            $scope.empleados = data
            $scope.$apply()
        })
    }

    cargarAsistencias()
    cargarEmpleados()

    $scope.agregarEmpleadoAsistencia = function() {
        $scope.nuevaAsistencia.empleados.push({
            idEmpleado: null,
            estado: 'A'
        })
    }

    $scope.removerEmpleadoAsistencia = function(index) {
        $scope.nuevaAsistencia.empleados.splice(index, 1)
    }

    $scope.guardarAsistencia = function() {
        const formData = new FormData()
        formData.append('fecha', $scope.nuevaAsistencia.fecha)
        formData.append('comentarios', $scope.nuevaAsistencia.comentarios)
        
        $scope.nuevaAsistencia.empleados.forEach((emp, index) => {
            if (emp.idEmpleado) {
                formData.append('empleados[]', emp.idEmpleado)
                formData.append('estados[]', emp.estado)
            }
        })

        $.ajax({
            url: '/asistencia',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function() {
                cargarAsistencias()
                $scope.nuevaAsistencia = {
                    fecha: new Date().toISOString().split('T')[0],
                    comentarios: '',
                    empleados: []
                }
                $scope.$apply()
                alert('Asistencia registrada correctamente')
            }
        })
    }
})

app.controller("reportesCtrl", function ($scope, $http) {
    $scope.reporte = {
        tipo: 'asistencias',
        fechaInicio: new Date().toISOString().split('T')[0],
        fechaFin: new Date().toISOString().split('T')[0]
    }
    $scope.resultados = []

    $scope.generarReporte = function() {
        $.post("/generarReporte", $scope.reporte, function(data) {
            $scope.resultados = data
            $scope.$apply()
        })
    }

    $scope.exportarPDF = function() {
        alert('Funcionalidad de exportación a PDF será implementada próximamente')
    }
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
