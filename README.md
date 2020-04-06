# Velib

Make use of a dataset from opendata.paris.fr ([Vélib' - Disponibilité temps réel](https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel)), that is updated every minute, and describes the status of every Vélib' station. 

## Get the data

`get-records.sh` pulls the data from the API.

No need to create an account, the quota for an anonymous access is limited to 5000 queries a day, which is enough for this use case. (5000 queries/day == 3 queries/minute)

What I did was putting `get-records.sh` in a crontab to be executed every minute and 20 seconds. In case the data wasn't available at this time, I put a second cron entry 30 seconds later. The script make sure that it doesn't pull the same data twice in a row.

Here's a trick to get around the minute-resolution of crontab ([credits](https://stackoverflow.com/questions/9619362/running-a-cron-every-30-seconds)) :
```
* * * * * sleep 20 ; ~/velib/get-records.sh >> ~/velib/velib.log 2>&1
* * * * * sleep 50 ; ~/velib/get-records.sh >> ~/velib/velib.log 2>&1
```

## Python

Uses Cartopy, which depends on geos and proj. On archlinux: `sudo pacman -S geos proj`
and also Cython (pip)

Proj version error : see https://github.com/SciTools/cartopy/pull/1289#issuecomment-506025563
target cartopy@23e31dd to get the compatibility with proj >= 6

spécifier ça dans Pipfile : git+https://github.com/SciTools/cartopy.git@23e31dd#egg=Cartopy
