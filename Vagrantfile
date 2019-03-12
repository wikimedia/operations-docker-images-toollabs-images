# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# Quick and dirty testing environment for building our images locally on
# machines which do not support Docker natively (OS X, Windows).
#
# Provisions a Debian Stretch vm with minimal configuration needed to allow
# the default vagrant user to run Docker commands.
Vagrant.configure('2') do |config|
    config.vm.hostname = 'toollabs-images.dev'

    # Default VirtualBox provider
    config.vm.provider :virtualbox do |_vb, override|
        override.vm.box = 'debian/contrib-stretch64'
    end

    config.vm.synced_folder '.', '/home/vagrant/toollabs-images'
    config.vm.network :forwarded_port, guest: 9000, host: 9000
    config.vm.network :forwarded_port, guest: 9001, host: 9001

    config.vm.provider :virtualbox do |vb|
        # See http://www.virtualbox.org/manual/ch08.html for additional options.
        vb.customize ['modifyvm', :id, '--memory', '768']
        vb.customize ['modifyvm', :id, '--cpus', '2']
        vb.customize ['modifyvm', :id, '--ostype', 'Ubuntu_64']
        vb.customize ['modifyvm', :id, '--ioapic', 'on']
        vb.customize ['modifyvm', :id, '--cableconnected1', 'on']
        vb.customize ['modifyvm', :id, '--natdnshostresolver1', 'on']
        vb.customize ['modifyvm', :id, '--natdnsproxy1', 'on']
        vb.customize ['guestproperty', 'set', :id, '/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold', 10000]
    end

    config.vm.provision :shell do |shell|
        shell.inline = <<-SHELL
            sudo apt-get install -y wget gnupg2 software-properties-common
            wget -qO - "https://wikitech.wikimedia.org/w/index.php?title=APT_repository/Stretch-Key&action=raw" | sudo apt-key add -
            sudo add-apt-repository "deb http://apt.wikimedia.org/wikimedia stretch-wikimedia main"
            sudo add-apt-repository "deb http://apt.wikimedia.org/wikimedia stretch-wikimedia thirdparty/k8s"
            sudo apt-get update
            sudo apt-get install -y docker docker-engine vim git
            sudo apt-get clean
            sudo usermod -aG docker vagrant
        SHELL
    end
end