# Setting up the infrastructure

## Requirements

+ [Vagrant](https://www.vagrantup.com/downloads.html)
+ [Oracle VirtualBox](https://www.virtualbox.org/) version 6.0.x

## SSH keys

Generate two SSH key pairs
+ ansible key in
  - `provision/files/master/.ssh/ansible_rsa`
  - `provision/files/master/.ssh/ansible_rsa.pub `
+ github key in
  - `provision/files/master/.ssh/github_rsa`
  - `provision/files/master/.ssh/github_rsa.pub`

(The ansible key is used to provision the virtual machines, the github key is used to push to this git repository, if allowed)

## Starting the infrastructure

Starting the infrastructure
```bash
vagrant up
```

Provisioning the infrastructure
```bash
vagrant rsync && vagrant provision
```

Connecting to the VM
```bash
vagrant ssh master
```

## Running Ansible

Go to `~/ansible` and run `make`. After installing Docker, one should close the SSH connection and reconnect to ensure the user (vagrant) is correctly added to the `docker-users` group.

# Scorify

Go to `~/src/ansible`

## Building

To build all the docker images use
```bash
make build
```

To build a specific image use one of the `build-*` rules
+ `build-web`
+ `build-worker-split`
+ `build-worker-fft`
+ `build-worker-peak`
+ `build-worker-score`

## Runing

### Redis & MariaDB

```bash
make run
```

### Web & Workers

+ Detached: `make run-all` or make use one of the `run-*` rules:
  - `run-web`
  - `run-worker-split`
  - `run-worker-fft`
  - `run-worker-peak`
  - `run-worker-score`
+ Not detached: `docker-compose -f docker-files/compose.yml up web worker-split worker-fft worker-peak worker-score`
