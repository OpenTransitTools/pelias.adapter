# step 1: get into the wrapper directory
BASEDIR=$(dirname "$0")
cd $BASEDIR

LATEST=${1:-"NOPE"}
if [ $LATEST == "YES" ]; then
  # step 2: force get latest and greatest code
  git reset --hard HEAD
  git pull
fi

# step 4: stop & restart wrapper
pkill -9 -f -c local_pelias
cmd="poetry run pserve config/local_pelias.ini"
eval "${cmd}" &>/dev/null & disown;

# step 5: really done hopefully...
echo
ps -ef | grep pserve | grep -v grep
echo "DONE"
echo
