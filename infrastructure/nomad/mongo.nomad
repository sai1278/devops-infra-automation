job "mongo" {
  datacenters = ["dc1"]
  type = "service"

  group "db" {
    count = 1

    task "mongo" {
      driver = "docker"

      config {
        image = "mongo:7"
        ports = ["db"]
        volumes = ["local/mongo:/data/db"]
      }

      resources {
        cpu    = 500
        memory = 512
      }
    }

    network {
      port "db" { to = 27017 }
    }

    service {
      name = "mongo"
      port = "db"
      check {
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }
  }
}
