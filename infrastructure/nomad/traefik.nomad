job "traefik" {
  datacenters = ["dc1"]
  type = "service"

  group "traefik" {
    count = 1

    task "traefik" {
      driver = "docker"

      config {
        image = "traefik:v2.11"
        args  = ["--api.insecure=true", "--providers.consulcatalog=true", "--entrypoints.web.address=:80"]
        ports = ["web"]
      }

      resources {
        cpu    = 500
        memory = 256
      }
    }

    network {
      port "web" { to = 80 }
    }

    service {
      name = "traefik"
      port = "web"
      check {
        type     = "http"
        path     = "/ping"
        interval = "10s"
        timeout  = "2s"
      }
    }
  }
}
