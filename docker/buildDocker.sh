export GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
docker build --debug --rm --progress=plain -f docker/Dockerfile -t pelias_adapter:$(git rev-parse --abbrev-ref HEAD) .

