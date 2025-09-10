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
    .when("/empleados", {
    templateUrl: "/empleados",
    controller: "empleadosCtrl"
})
.when("/asistencias", {
    templateUrl: "/asistencias",
    controller: "asistenciasCtrl"
})
.when("/asistenciaspases/:id", {
    templateUrl: function(params) { return "/asistenciaspases/" + params.id; },
    controller: "asistenciaspasesCtrl"
})

// Añadir estos controladores
app.controller("empleadosCtrl", function ($scope, $http) {
    // Enable pusher logging - don't include this in production
    Pusher.logToConsole = true;

    var pusher = new Pusher("686124f7505c58418f23", {
      cluster: "us2"
    });

    var channel = pusher.subscribe("canalEmpleados");
    channel.bind("eventoEmpleados", function(data) {
        cargarEmpleados();
    });
    
    function cargarEmpleados() {
        $.get("/tbodyEmpleados", function(html) {
            $("#tbodyEmpleados").html(html);
        });
    }
    
    cargarEmpleados();
});

app.controller("asistenciasCtrl", function ($scope, $http) {
    // Enable pusher logging - don't include this in production
    Pusher.logToConsole = true;

    var pusher = new Pusher("686124f7505c58418f23", {
      cluster: "us2"
    });

    var channel = pusher.subscribe("canalAsistencias");
    channel.bind("eventoAsistencias", function(data) {
        cargarAsistencias();
    });
    
    function cargarAsistencias() {
        $.get("/tbodyAsistencias", function(html) {
            $("#tbodyAsistencias").html(html);
        });
    }
    
    cargarAsistencias();
});

app.controller("asistenciaspasesCtrl", function ($scope, $http, $routeParams) {
    // No necesita Pusher ya que se actualiza con recarga de página
    // La arquitectura dirigida por eventos se maneja del lado del servidor
});
