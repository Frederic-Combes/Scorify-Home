# -*- mode: ruby -*-
# vi: set ft=ruby sw=2 st=2 et :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/buster64"
  config.vm.box_check_update = false

  config.vm.provider "virtualbox" do |vb|
    vb.gui = false
  end

  # Configure 'master'
  config.vm.define 'master' do |machine|
    machine.vm.provider "virtualbox" do |vb|
      vb.gui = false                                                            # No GUI
      vb.memory = "4096"                                                        # Give some RAM
      vb.cpus = 1                                                               # Give some CPU
    end

    machine.vm.hostname = "master"
    machine.vm.network "private_network", ip: "192.168.50.200"

    machine.vm.network "forwarded_port", guest: 80, host: 80                    # HTTP
    machine.vm.network "forwarded_port", guest: 5000, host: 5000                # Future Use
    machine.vm.network "forwarded_port", guest: 8080, host: 8080                # Future Use

    # Provisioning
    machine.vm.provision "shell", path: "provision/scripts/install-base-package.sh"
    machine.vm.provision "shell", path: "provision/scripts/install-ansible.sh"
    machine.vm.provision "shell", path: "provision/scripts/install-ssh-key.sh", env: {"KEY_NAME" => "github", "USER" => "vagarant"}
    machine.vm.provision "shell", path: "provision/scripts/install-ssh-key.sh", env: {"KEY_NAME" => "ansible", "USER" => "vagarant"}
    machine.vm.provision "shell", path: "provision/scripts/install-authorize-ssh-key.sh", env: {"KEY_NAME" => "ansible", "USER" => "root"}
    machine.vm.provision "shell", path: "provision/scripts/copy-files.sh", env: {"SRC" => "src", "DEST" => "src", "USER" => "vagrant", "USE_HOME" => true}
    machine.vm.provision "shell", path: "provision/scripts/copy-files.sh", env: {"SRC" => "ansible", "DEST" => "ansible", "USER" => "vagrant", "USE_HOME" => true}

    machine.vm.synced_folder ".", "/vagrant", disabled: true                          # Disable default folder syncing
    machine.vm.synced_folder "provision/files/master/", "/provision-files",
      type: "rsync"                                                                 # Sync the contents of sync-master to /provision-files
  end

  # Configure cluster nodes server0 ... server3
  # 4.times do |id|
  #   config.vm.define "server#{id}" do |machine|
  #     machine.vm.provider "virtualbox" do |vb|
  #       vb.gui = false                                                          # No GUI
  #       vb.memory = "2048"                                                      # Give less RAM
  #       vb.cpus = 1                                                             # Give less CPU
  #     end
  #
  #     machine.vm.hostname = "server#{id}"
  #     machine.vm.network "private_network", ip: "192.168.50.#{100+id}"
  #
  #     # Provisioning
  #     machine.vm.provision "shell", path: "provision-server.sh"
  #     machine.vm.synced_folder ".", "/vagrant", disabled: true                    # Disable default folder syncing
  #     machine.vm.synced_folder "sync-server/", "/provision-files", type: "rsync"  # Sync the contents of sync-master to /provision-files
  #   end
  # end
end
