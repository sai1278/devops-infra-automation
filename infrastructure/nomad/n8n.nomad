job "n8n" {
  datacenters = ["dc1"]
  type = "service"

  group "workflow" {
    count = 1

    task "n8n" {
      driver = "docker"

      config {
        image = "n8nio/n8n:latest"
        ports = ["web"]
      }

      env {
        N8N_BASIC_AUTH_ACTIVE = "true"
        N8N_BASIC_AUTH_USER = "admin"
        N8N_BASIC_AUTH_PASSWORD = "password"
      }

      resources {
        cpu    = 500
        memory = 512
      }
    }

    network {
      port "web" { to = 5678 }
    }

    service {
      name = "n8n"
      port = "web"
      check {
        type     = "http"
        path     = "/healthz"
        interval = "10s"
        timeout  = "2s"
      }
    }
  }
}
