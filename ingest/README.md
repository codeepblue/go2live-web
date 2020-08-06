# Go2Live Ingest

> Entrypoint for all steamings

[![Build Status](https://travis-ci.com/codeepblue/go2live-ingest.svg?token=xjXbzspn7M7zybiGkp7q&branch=master)](https://travis-ci.com/codeepblue/go2live-ingest)

### Getting started

```
$ docker-compose up -d
```

Open OBS and start streaming to `rtmp://localhost/live` with streaming key with the name of your streaming, like `testing`

Access https://players.akamai.com/players/hlsjs and use http://localhost:8080/testing as input stream URL.

That's it, you are live!

### Building

```shell script
$ ./build.bash
```

### Publishing new version

```shell script
$ ./publish.bash
```

### See more

[Nginx RTMP mod](https://github.com/arut/nginx-rtmp-module)
