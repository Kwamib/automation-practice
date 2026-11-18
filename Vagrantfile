# Lesson 2's server: a small Ubuntu web server with this folder inside it at /practice.
#   vagrant up                            build it (runs server/setup.sh)
#   vagrant ssh                           log in
#   vagrant snapshot save before-patch    a restore point
#   vagrant snapshot restore before-patch go back to it
#   vagrant destroy -f                    delete it
Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-24.04"
  config.vm.hostname = "web-1"
  config.vm.synced_folder ".", "/practice"
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.provision "shell", path: "server/setup.sh"

  config.vm.provider "vmware_desktop" do |v|
    v.memory = 1024
    v.cpus = 1
    v.vmx["ethernet0.pcislotnumber"] = "160"
  end

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
    v.cpus = 1
  end
end
