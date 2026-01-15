# step 1: get into the wrapper directory
WRAPDIR=$(dirname "$0")
cd $WRAPDIR

LOG=${1:-"pserve.out"}
LATEST=${2:-"NOPE"}

# step 2: optionally force get latest and greatest code
if [ $LATEST == "YES" ]; then
  git reset --hard HEAD
  git pull
fi

# step 3: stop existing wrapper process(s)
pkill -9 -f -c local_pelias
rm -f $LOG

# step 4: start new wrapper process
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
