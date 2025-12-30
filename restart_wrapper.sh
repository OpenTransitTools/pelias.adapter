# step 1: get into the wrapper directory
WRAPDIR=$(dirname "$0")
cd $WRAPDIR

LATEST=${1:-"NOPE"}
if [ $LATEST == "YES" ]; then
  # step 2: force get latest and greatest code
  git reset --hard HEAD
  git pull
fi

# step 4: stop & restart wrapper
pkill -9 -f -c local_pelias
LOG="$WRAPDIR/pserve.out"
rm -f $LOG
cmd="$HOME/venv/bin/poetry run pserve config/local_pelias.ini"
echo "${cmd}"
eval "${cmd} > $LOG 2>&1 & disown;"
echo

# step 5: really done hopefully...
sleep 2
echo
echo "pserve should be running now:"
ps -ef | grep pserve | grep -v grep
echo
