# Generating Multi-Objective Pareto-Optimal Congressional Districts

## Optimization
Requires python3
```
cd optimize growth
python setup.py build_ext -i

./bin/make_test_state -t 1000 -o data/test_1000.json
./bin/draw_state data/test_1000.json
./bin/optimize -s data/test_1000.json -c config.json -o ../view/data/t1000
```

## Web Viewer
Requires node.js
```
cd viewer
npm install
npm install budo -g
npm start
open http://localhost:9966/?run=t1000&stage=2
```
