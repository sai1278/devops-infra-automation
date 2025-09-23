job "flowbit" {
  datacenters = ["dc1"]
  type = "service"

  group "flowbit" {
    count = 1

    task "flowbit" {
      driver = "docker"

      config {
        image = "your-org/flowbit:latest"
        ports = ["api"]
      }

      resources {
        cpu    = 500
        memory = 256
      }
    }

    network {
      port "api" { to = 8080 }
    }

    service {
      name = "flowbit"
      port = "api"
      check {
        type     = "http"
        path     = "/health"
        interval = "10s"
        timeout  = "2s"
      }
    }
  }
}
