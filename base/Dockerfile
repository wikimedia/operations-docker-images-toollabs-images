# Base toollabs user image
# Name: docker-registry.tools.wmflabs.org/jessie-toollabs
# Source image: Debian Jessie
# Sets up:
#   Extra Apt repo: Tools repo
#   Users and Groups from labs LDAP (with mount required for nslcd)
FROM docker-registry.tools.wmflabs.org/wikimedia-jessie

# Add tools debian repo to this container
ADD tools.list /etc/apt/sources.list.d/tools.list

RUN apt-get update

# Setup NSS with LDAP. This requires that we mount /var/run/nslcd/socket from the
# underlying labs host to the container. If not mounted, it will fallback gracefully
# and just not use LDAP for NSS.
RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends libnss-ldapd
ADD nsswitch.conf /etc/nsswitch.conf
