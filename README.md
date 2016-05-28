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
