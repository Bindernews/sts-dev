
mvn-build:
    docker build -t sts-maven ./sts-maven

mvn-cli:
    docker run -it --rm \
        --mount source=m2cache,target=/root/.m2/repository \
        --mount type=bind,source=$(pwd)/lib,target=/host \
        sts-maven
