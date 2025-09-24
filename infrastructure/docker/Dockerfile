FROM alpine:3.17

# Install essential packages
RUN apk update && apk add --no-cache \
    bash \
    curl \
    git \
    unzip \
    python3 \
    py3-pip \
    openssh \
    ansible

# Install Terraform (using pip fallback here, replace with official binary if needed)
RUN pip install --no-cache-dir terraform

# Install Nomad (official binary from HashiCorp)
RUN curl -fsSL https://releases.hashicorp.com/nomad/1.6.3/nomad_1.6.3_linux_amd64.zip -o nomad.zip && \
    unzip nomad.zip && \
    mv nomad /usr/local/bin/ && \
    rm nomad.zip

# Set working directory
WORKDIR /workspace

# Default shell
CMD ["/bin/sh"]
