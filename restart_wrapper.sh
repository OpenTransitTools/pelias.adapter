# step 1: get into the wrapper directory
BASEDIR=$(dirname "$0")
cd $BASEDIR

# step 2: force get latest and greatest code
git reset --hard HEAD
git pull

# step 3: remove (potentially) outdated dependencies and buildout to get latest / greatest
RM_DEPS="rm -rf *egg*/ott.utils"
echo $RM_DEPS
eval $RM_DEPS

RM_JUNK="rm -f nohup.out *~"
echo $RM_JUNK
eval $RM_JUNK

buildout

# step 4: stop & restart wrapper
pkill -9 -f -c local_pelias
nohup bin/pserve config/local_pelias.ini & disown
echo 
echo "DONE"
