#!/bin/sh

if [ "${TRAVIS_PULL_REQUEST}" = "false" ]; then

  openssl aes-256-cbc -K $encrypted_e92dfea3fdc7_key -iv $encrypted_e92dfea3fdc7_iv -in deploy-key.enc -out deploy-key -d
  chmod 600 deploy_key
  eval `ssh-agent -s`
  ssh-add deploy_key
  git config user.name "Automatic Publish"
  git config user.email "djw8605@gmail.com"
  git remote add gh-token "git@github.com:opensciencegrid/StashCache.git"
  git fetch gh-token && git fetch gh-token gh-pages:gh-pages
  echo "Pushing to github"
  mkdocs gh-deploy -v --clean --remote-name gh-token
  git push gh-token gh-pages

else

  mkdocs build

fi


