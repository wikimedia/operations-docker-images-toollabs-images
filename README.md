Tool Labs Images
================

Docker image configuration and management for Wikimedia Tool Labs.


Usage
-----
```
$ ./build.py --push php/web
```

Adding a new image
------------------
* Create a `Dockerfile.template` in the appropriate directory.
* Add a `.dockerignore` to exclude the template from being imported into the
  container.
* Add the image name to `IMAGES` in `build.py`.
* Profit!

Dockerfile.template files should use `{registry}` and `{image_prefix}`
parameters to adapt to the command line options provided when running
`build.py`.

Conventions
-----------
* Each Dockerfile should only use `apt-get install` once.
  This rule can be bent if some packages need to come from pinned repositories
  (e.g. jessie-backports), but that may imply that an intermediate image is
  more appropriate.
* Packages should be listed one per line and sorted in alphabetical order.
* Each `apt-get install` should be preceded by an `apt-get update` and
  followed by an `apt-get clean`. See base/Dockerfile.template for an example.

License
-------
[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)
