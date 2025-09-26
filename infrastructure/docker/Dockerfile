# Use a specific Alpine version (already pinned)
FROM alpine:3.17

# Install essential packages (no apk update, use --no-cache)
RUN apk add --no-cache \
    bash=5.2.15-r0 \
    curl=8.9.0-r0 \
    git=2.39.5-r0 \
    unzip=6.0-r13 \
    python3=3.10.15-r0 \
    py3-pip=22.3.1-r1 \
    openssh=9.1_p1-r6 \
    ansible=6.6.0-r0

# Install Terraform (official binary instead of pip)
ENV TERRAFORM_VERSION=1.6.6
RUN curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip

# Install Nomad (official binary from HashiCorp)
ENV NOMAD_VERSION=1.6.3
RUN curl -fsSL "https://releases.hashicorp.com/nomad/${NOMAD_VERSION}/nomad_${NOMAD_VERSION}_linux_amd64.zip" -o nomad.zip \
    && unzip nomad.zip \
    && mv nomad /usr/local/bin/ \
    && rm nomad.zip

# Set working directory
WORKDIR /workspace

# Default shell
CMD ["/bin/sh"]
