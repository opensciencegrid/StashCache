#!/bin/sh -xe

# This script starts docker and systemd (if el7)

# Version of CentOS/RHEL
el_version=$1
cache=$2

if [ "${BUILD_TYPE}" = "http" ]; then
  # Run the test without a container
  # Copy in the .job.ad file:
  cp bin/stashcp2/tests/job.ad ./.job.ad
  python setup.py install

  # Test against a file that is known to not exist
  set +e
  stashcp --cache=$XRD_CACHE /blah/does/not/exist ./
  if [ $? -eq 0 ]; then
    echo "Failed to exit with non-zero exit status when it should have"
    exit 1
  fi
  set -e

  # Try copying with different destintion filename
  stashcp --cache=$XRD_CACHE -d /osgconnect/dweitzel/blast/queries/query1 query.test

  result=`md5sum query.test | awk '{print $1;}'`

  if [ "$result" != "12bdb9a96cd5e8ca469b727a81593201" ]; then
    exit 1
  fi

  rm -f query.test

  # Perform tests
  stashcp --cache=$XRD_CACHE -d /osgconnect/dweitzel/blast/queries/query1 ./

  result=`md5sum query1 | awk '{print $1;}'`

  if [ "$result" != "12bdb9a96cd5e8ca469b727a81593201" ]; then
    exit 1
  fi

 # Run tests in Container
elif [ "$el_version" = "6" ]; then

sudo docker run --privileged --rm=true -v `pwd`:/StashCache:rw centos:centos${OS_VERSION} /bin/bash -c "bash -xe /StashCache/bin/stashcp2/tests/test_inside_docker.sh ${OS_VERSION} ${XRD_CACHE}"

elif [ "$el_version" = "7" ]; then

docker run --privileged --cap-add SYS_ADMIN -d -ti -e "container=docker"  -v /sys/fs/cgroup:/sys/fs/cgroup -v `pwd`:/StashCache:rw  centos:centos${OS_VERSION}   /usr/sbin/init
DOCKER_CONTAINER_ID=$(docker ps | grep centos | awk '{print $1}')
docker logs $DOCKER_CONTAINER_ID
docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -xec "bash -xe /StashCache/bin/stashcp2/tests/test_inside_docker.sh ${OS_VERSION} ${XRD_CACHE};
echo -ne \"------\nEND stashcp TESTS\n\";"
docker ps -a
docker stop $DOCKER_CONTAINER_ID
docker rm -v $DOCKER_CONTAINER_ID

fi
