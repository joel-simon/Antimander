# Antimander - [antimander.org](https://antimander.org/)
## Multi-Objective Optimization of Congressional Districts 🗺️👩‍💻🇺🇸

[Discord](https://discord.gg/UmgaE74)

The source code for the [Antimander.org](http://antimander.org/) website is here [github/joel-simon/Antimander-blog](https://github.com/joel-simon/Antimander-blog)


## Installation 
Requires python3
```
cd optimize
conda create -n antimander python=3.6 // Optional
pip install -r requirements.txt
conda install -c conda-forge pykdtree 
// May also install by source instead at https://github.com/storpipfugl/pykdtree
python setup.py build_ext -i
```

## Use Antimander via the scripts in /bin

### ./bin/sp2statefile
Converts a shapefile from the [mggg states repo](https://github.com/mggg-states/) to the Antimander state json format that incudes adjacency info. Currenlty only supports Wisconsin and North Carolina but is simple to add others.

Example
```
./bin/shp2statefile --save -n WI -s ~/Downloads/WI_wards_12_16/WI_ltsb_corrected_final.shp
./bin/shp2statefile --save -n NC -s ~/Downloads/NC_VTD/NC_VTD.shp
```
This can take a few minutes and there a pre-computed files available on google drive.
```
pip install gdown 
// WI.json.zip (Wisconsin)
gdown https://drive.google.com/uc?id=1afLh0gCfXqFI8NqRo0tyHWp7oPKxu4qQ

// NC.json.zip (North Carolina)
gdown https://drive.google.com/uc?id=1b-LZf91_ImtLuGQgj5kqaBlt53JM6Cj3
```
### ./bin/draw_state 
Draws a state json file to the window and saves it as a png.
```
./bin/draw_state data/NC.json
```
![North Carolina Map](img/NC.png "North Carolina Map")

### ./bin/make_test_state
Create a fake test state on a Voronoi grid. The number of cities and tiles is parameterized and the total populations for each party are normalized to be equal. This is useful for faster testing.

This requires manually installing pyvoro from the [python3 branch](https://github.com/joe-jordan/pyvoro/tree/feature/python3).

Example
```
./bin/make_test_state -t 2000 -c 2 -s 2 -o data/t2000_c2.json
./bin/draw_state data/t2000_c2.json
```
And you should see

![Test Map](img/t2000_c2.png "Test Map")


### ./bin/optimize
The main script that runs the optimization. See "./bin/optimize --help" for full options.
Example: This command optimizes for three metrics and uses the "centers" novelty method and feasible-infeasible search:
```
./bin/optimize -i ./data/t2000_c2.json -o ../view/data/test_out -g 2000 -p 400 \
    --metrics polsby_popper efficiency_gap competitiveness \
    --novelty centers --feasinfeas
```
This will create an output directory with a lot of output files and hypervolume plots. If you output it to the viewer directory you can then interact with via the web viewer. For real world states more generations and larger population size is suggested. ~600 pop and ~5000 gens are good but it depends on the specific state and the number of metrics. 

All metric implementations are in the optimize/src/metrics directory. Current ones are:
* convex_hull
* equality
* polsby_popper
* competitiveness
* efficiency_gap
* reock
* center_distance

## Web Viewer
Requires node.js

NOTE: this viewer is deprecated since it is pretty slow for full state files but is fine for test states, the very fast WebGL viewer is in the website repo. TODO: merge them.
```
cd viewer
npm install
npm install budo -g
npm start
open http://localhost:9966/?run=test_out&stage=4
```
