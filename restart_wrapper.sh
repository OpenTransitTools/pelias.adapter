# step 1: get into the wrapper directory
BASEDIR=$(dirname "$0")
cd $BASEDIR

# step 2: force get latest and greatest code
git reset --hard HEAD
git pull

# step 3: remove (potentially) outdated dependencies and buildout to get latest / greatest
RM_DEPS="rm -rf *egg*/ott.utils* nohup.out *~"
echo $RM_DEPS
eval $RM_DEPS
buildout

# step 4: stop & restart wrapper
pkill -9 -f -c local_pelias
cmd="bin/pserve config/local_pelias.ini"
eval "${cmd}" &>/dev/null & disown;

# step 5: really done hopefully...
echo 
echo "DONE"
