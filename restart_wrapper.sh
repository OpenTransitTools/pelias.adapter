# step 1: get into the wrapper directory
WRAPDIR=$(dirname "$0")
cd $WRAPDIR

CFG=${1:-"config/local_pelias.ini"}
LOG=${2:-"pserve.out"}
LATEST=${3:-"NOPE"}

# step 2: optionally force get latest and greatest code
if [ $LATEST == "YES" ]; then
  git reset --hard HEAD
  git pull
fi

# step 3: stop existing wrapper process(s)
pkill -9 -f -c pserve > /dev/null
rm -f $LOG

# step 4: start new wrapper process
cmd="poetry run pserve $CFG"
echo "${cmd}"
eval "${cmd} > $LOG 2>&1 & disown;"
echo

# step 5: really done hopefully...
sleep 1
echo "pserve should be running now:"
echo "  http://$HOSTNAME:45554/pelias/rtp/autocomplete?text=9"
echo "  http://$HOSTNAME:45554/solr/select?q=3414%20SW%20Willow"
echo
sleep 1
ps -ef | grep pserve | grep -v grep
echo
