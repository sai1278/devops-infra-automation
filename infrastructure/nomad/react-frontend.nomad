job "react-frontend" {
  datacenters = ["dc1"]
  type = "service"

  group "frontend" {
    count = 2

    task "react" {
      driver = "docker"

      config {
        image = "ghcr.io/your-org/react-frontend:latest"
        ports = ["http"]
      }

      resources {
        cpu    = 500
        memory = 256
      }
    }

    network {
      port "http" { to = 3000 }
    }

    service {
      name = "react-frontend"
      port = "http"
      check {
        type     = "http"
        path     = "/"
        interval = "10s"
        timeout  = "2s"
      }
    }
  }
}
